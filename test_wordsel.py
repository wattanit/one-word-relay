from onewordrelay.wordsel import extract_word, select_word, roll_impurity

def test_extract_word():
    assert extract_word("  Hello world  ") == "Hello"
    assert extract_word("Cake!") == "Cake!"
    assert extract_word("   ") == ""
    print("Extract word tests passed!")

def test_selection():
    # Test majority
    candidates = ["apple", "banana", "apple"]
    word, rule = select_word(candidates, confusion_triggered=False)
    assert word == "apple"
    assert rule == "majority"

    # Test tie-break (first one wins)
    candidates = ["apple", "banana"]
    word, rule = select_word(candidates, confusion_triggered=False)
    assert word == "apple"
    assert rule == "majority"

    # Test confusion (pick minority)
    candidates = ["apple", "banana", "apple"]
    word, rule = select_word(candidates, confusion_triggered=True)
    assert word == "banana"
    assert rule == "confusion"

    # Test confusion fallback (all same)
    candidates = ["apple", "apple", "apple"]
    word, rule = select_word(candidates, confusion_triggered=True)
    assert word == "apple"
    assert rule == "fallback"
    print("Selection tests passed!")

def test_impurity_rolls():
    # HC-3: Drunk=0 must be deterministic False
    assert roll_impurity(0.0, 10.0) is False
    
    # Test probabilities (roughly)
    results = [roll_impurity(1.0, 1.0) for _ in range(1000)]
    # Roughly 1000 rolls at 100% should be all True
    assert all(results)
    
    results_zero = [roll_impurity(0.0, 1.0) for _ in range(1000)]
    assert not any(results_zero)
    print("Impurity roll tests passed!")

if __name__ == "__main__":
    test_extract_word()
    test_selection()
    test_impurity_rolls()
