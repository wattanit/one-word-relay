import json
import os
from datetime import datetime
from typing import Any, Dict

class SessionLogger:
    """
    Append-only JSONL logger that flushes every entry to disk immediately.
    (FR-21)
    """
    def __init__(self, log_path: str):
        self.log_path = log_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log_init(self, player_name: str, persona_prompt: str, private_intent: str):
        entry = {
            "type": "init",
            "timestamp": datetime.now().isoformat(),
            "player_name": player_name,
            "persona_prompt": persona_prompt,
            "private_intent": private_intent
        }
        self._write(entry)

    def log_turn(self, turn_index: int, player_name: str, forgetfulness_triggered: bool, 
                 confusion_triggered: bool, context_sent: str, candidates: list, 
                 selected_word: str, selection_rule: str):
        entry = {
            "type": "turn",
            "turn_index": turn_index,
            "player_name": player_name,
            "forgetfulness_triggered": forgetfulness_triggered,
            "confusion_triggered": confusion_triggered,
            "context_sent": context_sent,
            "candidates": candidates,
            "selected_word": selected_word,
            "selection_rule": selection_rule
        }
        self._write(entry)

    def _write(self, entry: Dict[str, Any]):
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
