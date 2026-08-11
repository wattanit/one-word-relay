import re
import random
from typing import List, Tuple
from onewordrelay.config import SessionConfig

def extract_word(text: str) -> str:
    """
    Extracts the first actual word from the text. 
    A word is defined as a sequence of alphanumeric characters (including internal hyphens/apostrophes).
    This prevents strings like 'bread...can...' from being treated as a single word.
    (FR-6)
    """
    match = re.search(r"[a-zA-Z0-9\u00C0-\u017F]+(?:['\-][a-zA-Z0-9\u00C0-\u017F]+)*", text)
    if match:
        return match.group(0)
    return ""

def select_word(candidates: List[str], confusion_triggered: bool, recent_words: List[str]) -> Tuple[str, str]:
    """
    Selects a word based on majority or confusion rules, with a penalty 
    for words that have appeared too frequently recently.
    (FR-10, FR-12)
    Returns (selected_word, rule_name).
    """
    if not candidates:
        return "", "none"

    # Repetition Penalty: identify words that appear too often in recent history
    # If a word appears more than 2 times in the recent window, we treat it as 'tainted'
    tainted_words = set()
    for word in set(recent_words):
        if recent_words.count(word) >= 3:
            tainted_words.add(word)

    # Count occurrences of each candidate
    counts = {}
    for word in candidates:
        counts[word] = counts.get(word, 0) + 1

    # Find the majority word
    sorted_words = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    majority_word, majority_count = sorted_words[0]

    # If the majority word is tainted and there is a non-tainted alternative, 
    # we shift the selection to the next best non-tainted candidate.
    if majority_word in tainted_words:
        for word, count in sorted_words:
            if word not in tainted_words:
                majority_word = word
                break
        # Note: if all candidates are tainted, we still stick with the original majority_word

    if not confusion_triggered:
        # Rule: Majority word (or best non-tainted alternative). 
        return majority_word, "majority"
    else:
        # Rule: Random non-majority word (FR-12)
        minority_words = [word for word in candidates if word != majority_word]
        if minority_words:
            return random.choice(minority_words), "confusion"
        else:
            return majority_word, "fallback"

def roll_impurity(drunk: float, multiplier: float) -> bool:
    """
    Rolls for forgetfulness or confusion.
    (FR-11, HC-3)
    """
    # HC-3: Drunk=0 must deterministically disable both forgetfulness and confusion
    if drunk == 0:
        return False
        
    # Probability = global drunk parameter * per-player multiplier (FR-11)
    return random.random() < (drunk * multiplier)
