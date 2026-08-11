from dataclasses import dataclass
from onewordrelay.config import PersonaConfig

@dataclass
class AgentState:
    persona: PersonaConfig
    private_intent: str = ""
