# One-Word Relay POC

A Proof-of-Concept (POC) implementation of a collaborative storytelling game where several LLM-powered personas attempt to answer a prompt one word at a time.

## 🎮 Overview

The game simulates a group of distinct personalities collaborating on a single sentence. To prevent the result from being too "perfect" or boring, the system introduces **controlled divergence** through two main mechanics:
- **Forgetfulness**: Agents may occasionally "lose the thread" and only see the last few words of the transcript.
- **Confusion**: Agents may occasionally ignore the majority consensus and pick a "minority" candidate word.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `uv` (recommended package manager)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd one-word-relay

# Install dependencies using uv
uv sync
```

### Running the Game
Run the game via the CLI:
```bash
uv run python3 -m onewordrelay.cli
```

### CLI Options
- `--drunk <float>`: Set the global probability of forgetfulness and confusion (0.0 to 1.0). Default is `0.1`.
- `--verbose`: Enable verbose mode to see private intents, impurity triggers (FORGETFUL/CONFUSED), and the polishing process.

Example:
```bash
uv run python3 -m onewordrelay.cli --drunk 0.3 --verbose
```

## 🛠 How it Works

1. **Intent Initialization**: Each player is given a secret "Private Intent" (e.g., *"make the answer cynical"*) to steer the conversation.
2. **Candidate Generation**: For every turn, the current player generates multiple candidate words based on their persona and the current transcript.
3. **Word Selection**: 
    - **Sober**: The most common word among candidates is chosen.
    - **Confused**: A random minority word is chosen.
    - **Repetition Penalty**: If a word has appeared too often recently, the system forces a different choice to prevent loops.
4. **Transcript Polish**: After the game ends, the raw sequence of words is passed through a final "Polish" pass to add proper punctuation and capitalization without changing the word order.

## 📂 Project Structure
- `onewordrelay/cli.py`: Entry point and user interface.
- `onewordrelay/session.py`: Core game loop and state management.
- `onewordrelay/llm_client.py`: Integration with OpenAI-compatible LLM endpoints.
- `onewordrelay/wordsel.py`: Word extraction and selection logic.
- `onewordrelay/transcript.py`: History management.
- `personas.json`: Configuration for the available player personalities.
- `sessions/`: Directory containing timestamped `.jsonl` logs of every game.
