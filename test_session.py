from onewordrelay.config import SessionConfig, load_persona_configs
from onewordrelay.session import GameSession

def test_session_skeleton():
    # Setup
    config = SessionConfig(turn_budget=5, drunk=0.0)
    personas = load_persona_configs("personas.json")
    session = GameSession(config, personas)
    
    session.initialize_agents()
    
    # Run few turns
    for i in range(3):
        session.run_turn()
        
    assert session.turn_count == 3
    assert len(session.transcript.entries) == 3
    assert session.current_player_idx == 0 # 3 players, 3 turns -> back to 0
    
    # Test budget stopping
    session.config.turn_budget = 3
    # Now we are at turn 3, it should stop
    assert session.check_stopping_conditions() is True
    print("Session skeleton tests passed!")

if __name__ == "__main__":
    test_session_skeleton()
