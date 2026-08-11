from onewordrelay.config import SessionConfig, PersonaConfig, load_persona_configs, get_llm_env_config
import json

def test_config_loading():
    # Test personas loading
    personas = load_persona_configs("personas.json")
    assert len(personas) == 3
    assert personas[0].name == "Alice"
    
    # Test session config defaults
    session = SessionConfig()
    assert session.turn_budget == 50
    
    # Test LLM env config
    env = get_llm_env_config()
    assert "base_url" in env
    print("Config loading tests passed!")

if __name__ == "__main__":
    test_config_loading()
