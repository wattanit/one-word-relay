import re
import random
from typing import List, Tuple
from onewordrelay.config import SessionConfig

def extract_word(text: str) -> str:
    """
    Extracts the first whole word from the text, respecting real word boundaries.
    Removes trailing ellipses or filler punctuation that might disturb the turn end system.
    (FR-6)
    """
    match = re.search(r'\S+', text)
    if match:
        word = match.group(0)
        # Remove trailing ellipses (...) or repeated punctuation that doesn't 
        # constitute a formal sentence boundary (. ! ?)
        word = re.sub(r'\.{2,}$', '', word)
        return word
    return ""

def select_word(candidates: List[str], confusion_triggered: bool) -> Tuple[str, str]:
    """
    Selects a word based on majority or confusion rules.
    (FR-10, FR-12)
    Returns (selected_word, rule_name).
    """
    if not candidates:
        return "", "none"

    # Count occurrences of each word
    counts = {}
    for word in candidates:
        counts[word] = counts.get(word, 0) + 1

    # Find the majority word
    # Sorted by count desc, then by first appearance (stable sort in Python)
    sorted_words = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    majority_word, majority_count = sorted_words[0]

    if not confusion_triggered:
        # Rule: Majority word. Tie-break: first generated (handled by stable sort)
        return majority_word, "majority"
    else:
        # Rule: Random non-majority word (FR-12)
        minority_words = [word for word in candidates if word != majority_word]
        if minority_words:
            return random.choice(minority_words), "confusion"
        else:
            # Fallback: if all candidates agree, confusion has no visible effect
            return majority_word, "fallback"

def roll_impurity(drunk: float, multiplier: float) -> bool:
    """
    Rolls for forgetfulness or confusion.
    (FR-11, HC-3)
    """
    if drunk == 0:
        return False
    return random.random() < (drunk * multiplier)
