from typing import List
import random

from onewordrelay.config import SessionConfig, PersonaConfig
from onewordrelay.agent import AgentState
from onewordrelay.transcript import Transcript
from onewordrelay.llm_client import LLMClient
from onewordrelay.wordsel import extract_word, select_word, roll_impurity
from onewordrelay.logger import SessionLogger

class GameSession:
    def __init__(self, session_config: SessionConfig, personas: List[PersonaConfig]):
        self.config = session_config
        self.transcript = Transcript()
        self.logger = SessionLogger(session_config.log_path)
        self.llm = LLMClient()
        
        # Initialize players
        self.players = [AgentState(p) for p in personas]
        self.num_players = len(self.players)
        
        # To be set during init phase
        self.current_player_idx = 0
        self.turn_count = 0

    def initialize_agents(self, original_prompt: str):
        """
        Initializes each player with a private intent generated via the LLM.
        (FR-3)
        """
        for player in self.players:
            system_msg = player.persona.personality_prompt
            user_msg = (
                f"The group is answering the question: '{original_prompt}'\n\n"
                "Silently decide on a private direction or a specific goal for your "
                "contribution to the answer. Answer with ONLY this private intent, "
                "nothing else. Do not explain your reasoning."
            )
            
            try:
                intent = self.llm.generate_completion(system_msg, user_msg).strip()
                player.private_intent = intent
            except RuntimeError as e:
                # Re-raise to trigger the session halt (Error Handling Policy)
                raise RuntimeError(f"Failed to initialize intent for {player.persona.name}: {e}")
            
            # Log init entry immediately (FR-21)
            self.logger.log_init(
                player.persona.name, 
                player.persona.personality_prompt, 
                player.private_intent
            )

    def run_turn(self, original_prompt: str) -> bool:
        """
        Runs a single turn. Returns True if the game should continue, 
        False if a stopping condition was met.
        """
        player = self.players[self.current_player_idx]
        
        # 1. Roll Impurities
        forgetfulness = roll_impurity(self.config.drunk, player.persona.forgetfulness_multiplier)
        confusion = roll_impurity(self.config.drunk, player.persona.confusion_multiplier)
        
        # 2. Assemble Context (FR-7, FR-8)
        # Common base context
        base_context = (
            f"Original Prompt: {original_prompt}\n"
            f"Your Private Intent: {player.private_intent}\n\n"
            "You are collaborating to write a coherent, grammatically correct answer to the prompt. "
            "While following your private intent, suggest the next few words of the sentence. "
            "The system will only use the first word you provide, but thinking ahead will help maintain coherence."
        )
        
        if forgetfulness:
            # Forgetful turn: Only the last k words (FR-8)
            transcript_text = self.transcript.get_last_k_words(self.config.k_forgetfulness)
            context = (
                f"{base_context}\n\n"
                f"Note: You've lost the thread of the conversation. "
                f"The last few words were: ...{transcript_text}"
            )
        else:
            # Normal turn: Full transcript (FR-7)
            transcript_text = self.transcript.get_full_text()
            context = (
                f"{base_context}\n\n"
                f"Current Transcript: {transcript_text if transcript_text else '[No words yet]'}"
            )
            
        # 3. Generate Candidates
        candidates_raw = []
        candidates_extracted = []
        for _ in range(self.config.num_candidates):
            # In M2 we use the real LLMClient
            try:
                resp = self.llm.generate_completion(player.persona.personality_prompt, context)
            except RuntimeError as e:
                # Halt the session (Error Handling Policy)
                raise RuntimeError(f"Turn failed for {player.persona.name}: {e}")
                
            candidates_raw.append(resp)
            candidates_extracted.append(extract_word(resp))
            
        # 4. Select Word
        selected_word, rule = select_word(candidates_extracted, confusion)
        
        # 5. Log Turn
        self.logger.log_turn(
            turn_index=self.turn_count,
            player_name=player.persona.name,
            forgetfulness_triggered=forgetfulness,
            confusion_triggered=confusion,
            context_sent=context,
            candidates=candidates_extracted,
            selected_word=selected_word,
            selection_rule=rule
        )
        
        # 6. Update Transcript
        self.transcript.append(selected_word, player.persona.name)
        
        # Increment turn indices
        self.turn_count += 1
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        
        return True

    def check_stopping_conditions(self) -> bool:
        """
        Returns True if the game must pause/stop.
        """
        # Sentence boundary check
        if self.transcript.entries:
            last_word = self.transcript.entries[-1][0]
            if self.transcript.is_sentence_boundary(last_word):
                return True
        
        # Budget check
        if self.turn_count >= self.config.turn_budget:
            return True
            
        return False

    def extend_budget(self):
        """
        Increments the turn budget by the original budget amount.
        """
        # We use a fixed increment based on the initial budget 
        # (or we could use a stored initial_budget value).
        # For now, we'll just double it or add a fixed amount.
        self.config.turn_budget += 20 # Adding a fixed 20-turn extension
