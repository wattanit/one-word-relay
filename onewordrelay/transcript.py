from typing import List, Tuple
import re

class Transcript:
    def __init__(self):
        # Stores (word, player_name)
        self.entries: List[Tuple[str, str]] = []

    def append(self, word: str, player_name: str):
        self.entries.append((word, player_name))

    def get_full_text(self) -> str:
        """Returns the joined words as a single string."""
        return " ".join(word for word, _ in self.entries)

    def get_last_k_words(self, k: int) -> str:
        """Returns the last k words as a single string."""
        words = [word for word, _ in self.entries]
        return " ".join(words[-k:])

    def is_sentence_boundary(self, word: str) -> bool:
        """Checks if the word ends with sentence-terminal punctuation."""
        return bool(re.search(r'[.!?]$', word))

    def __str__(self):
        return self.get_full_text()
