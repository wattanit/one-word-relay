import sys
import random
import argparse
import select
from onewordrelay.config import SessionConfig, load_persona_configs
from onewordrelay.session import GameSession

def main():
    parser = argparse.ArgumentParser(description="One-Word Relay POC")
    parser.add_argument("--drunk", type=float, default=0.1, help="Global drunk parameter (0.0 to 1.0)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode to see internal mechanics")
    args = parser.parse_args()

    print("--- One-Word Relay POC ---")
    
    # FR-1: Collect input
    try:
        prompt = input("Enter the prompt/question for the group: ")
        if not prompt:
            print("Prompt cannot be empty.")
            return
            
        num_players_input = input("Number of players (2-6): ")
        num_players = int(num_players_input)
        if not (2 <= num_players <= 6):
            print("Please enter a number between 2 and 6.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    # Load persona configs
    try:
        all_personas = load_persona_configs("personas.json")
        if len(all_personas) < num_players:
            print(f"Error: Not enough personas in personas.json (found {len(all_personas)}, need {num_players}).")
            return
        personas = random.sample(all_personas, num_players)
    except FileNotFoundError:
        print("Error: personas.json not found.")
        return

    # Session configuration
    config = SessionConfig(
        prompt=prompt,
        num_players=num_players,
        drunk=args.drunk,
        turn_budget=20
    )

    # Setup session
    session = GameSession(config, personas)
    
    if args.verbose:
        print("\n[Verbose] Initializing player intents...")
    
    try:
        session.initialize_agents(prompt)
        if args.verbose:
            for p in session.players:
                print(f"  - {p.persona.name}'s intent: {p.private_intent}")
    except RuntimeError as e:
        print(f"Fatal Error: {e}")
        return

    print(f"\nStarting game with {num_players} players...")
    print(f"Prompt: {prompt}")
    print(f"Drunk Level: {args.drunk}")
    print("Press 'q' + Enter at any turn to interrupt and end the game.")
    print("-" * 30)

    # Game Loop
    while True:
        # To allow a 'q' interrupt without blocking the whole game, 
        # we'll check for input before each turn.
        # Since we are in a simple terminal app, we'll use a non-blocking check.
        print("... ", end="", flush=True)
        # Check if user pressed 'q' (non-blocking)
        if select.select([sys.stdin], [], [], 0.1)[0]:
            user_input = sys.stdin.readline().strip().lower()
            if user_input == 'q':
                print("\nInterrupted by user.")
                break

        # Run a turn
        try:
            turn_meta = session.run_turn(prompt)
        except RuntimeError as e:
            print(f"\nFatal Error: {e}")
            break
        
        # FR-17: Print newly appended word
        last_word, player_name = session.transcript.entries[-1]
        
        if args.verbose:
            f, c, rule = turn_meta
            status = []
            if f: status.append("FORGETFUL")
            if c: status.append("CONFUSED")
            if not f and not c: status.append("SOBER")
            status_str = f" [{', '.join(status)} | Rule: {rule}]"
            print(f"{player_name}: {last_word}{status_str}")
        else:
            print(f"{player_name}: {last_word}")

        # Check stopping conditions (FR-14, FR-15)
        if session.check_stopping_conditions():
            print("-" * 30)
            is_budget_pause = session.turn_count >= session.config.turn_budget
            reason = "Turn budget reached" if is_budget_pause else "Sentence boundary reached"
            print(f"{reason}. Continue? (y/n) or 'q' to quit: ", end="")
            choice = input().strip().lower()
            if choice == 'q' or choice != 'y':
                break
            if is_budget_pause:
                session.extend_budget()
                print(f"Budget extended to {session.config.turn_budget} turns.")

    # End of game
    print("\n" + "=" * 30)
    print("RAW TRANSCRIPT:")
    raw_text = session.transcript.get_full_text()
    print(raw_text)
    
    print("\n" + "-" * 30)
    if args.verbose:
        print("[Verbose] Polishing transcript...")
    print("POLISHED VERSION:")
    polished = session.llm.polish_transcript(raw_text)
    print(polished)
    print("=" * 30)
    print(f"Log saved to: {config.log_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        sys.exit(0)
