from onewordrelay.transcript import Transcript
from onewordrelay.agent import AgentState
from onewordrelay.config import PersonaConfig

def test_transcript():
    t = Transcript()
    t.append("Hello", "Alice")
    t.append("there", "Bob")
    t.append("world!", "Charlie")
    
    assert t.get_full_text() == "Hello there world!"
    assert t.get_last_k_words(2) == "there world!"
    assert t.is_sentence_boundary("world!") is True
    assert t.is_sentence_boundary("there") is False
    print("Transcript tests passed!")

def test_agent():
    p = PersonaConfig("Alice", "Optimist", 1.0, 1.0)
    a = AgentState(p)
    a.private_intent = "Make it a story about cake"
    assert a.persona.name == "Alice"
    assert a.private_intent == "Make it a story about cake"
    print("Agent tests passed!")

if __name__ == "__main__":
    test_transcript()
    test_agent()
