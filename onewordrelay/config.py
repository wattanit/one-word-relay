from dataclasses import dataclass
from typing import List, Optional
import json
import os

@dataclass
class SessionConfig:
    prompt: str = ""
    num_players: int = 0
    turn_budget: int = 50
    k_forgetfulness: int = 10
    num_candidates: int = 3
    drunk: float = 0.0
    log_path: str = "" # Now initialized in session.py to include timestamp

@dataclass
class PersonaConfig:
    name: str
    personality_prompt: str
    forgetfulness_multiplier: float
    confusion_multiplier: float

def load_persona_configs(path: str) -> List[PersonaConfig]:
    with open(path, 'r') as f:
        data = json.load(f)
        return [PersonaConfig(**p) for p in data]

def get_llm_env_config():
    return {
        "base_url": os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        "model": os.getenv("LLM_MODEL", "llama3"),
        "api_key": os.getenv("LLM_API_KEY", "ollama"),
    }
