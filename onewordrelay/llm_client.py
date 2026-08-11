import random
from typing import List

class LLMClientStub:
    """
    A stub LLM client that returns fixed or random words 
    to simulate candidate generation without real API calls.
    """
    def __init__(self):
        # A list of words to randomly pick from to simulate variety
        self.vocabulary = [
            "the", "a", "cat", "dog", "happily", "sadly", "jumped", 
            "over", "blue", "green", "fast", "slowly", "thought", 
            "about", "existence", "cake", "coffee", "moon", "sun"
        ]

    def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Simulates a model response. Returns a single word 
        (occasionally with punctuation).
        """
        word = random.choice(self.vocabulary)
        # Occasionally add punctuation to test boundaries
        if random.random() < 0.1:
            word += random.choice([".", "!", "?"])
        return f" {word} "
