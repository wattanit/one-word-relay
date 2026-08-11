import sys
import random
from onewordrelay.config import SessionConfig, load_persona_configs
from onewordrelay.session import GameSession

def main():
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
        # Use a random sample of the requested number of players
        personas = random.sample(all_personas, num_players)
    except FileNotFoundError:
        print("Error: personas.json not found.")
        return

    # Session configuration (defaults for M1)
    # In a real scenario, this would be loaded from a config file as per FR-20
    config = SessionConfig(
        prompt=prompt,
        num_players=num_players,
        drunk=0.1, # Set to slightly > 0 to see some variety in M1
        turn_budget=20
    )

    # Setup session
    session = GameSession(config, personas)
    try:
        session.initialize_agents(prompt)
    except RuntimeError as e:
        print(f"Fatal Error: {e}")
        return

    print(f"\nStarting game with {num_players} players...")
    print(f"Prompt: {prompt}\n")
    print("-" * 30)

    # Game Loop
    while True:
        # Run a turn
        try:
            session.run_turn(prompt)
        except RuntimeError as e:
            print(f"\nFatal Error: {e}")
            break
        
        # FR-17: Print newly appended word
        last_word, player_name = session.transcript.entries[-1]
        print(f"{player_name}: {last_word}")

        # Check stopping conditions (FR-14, FR-15)
        if session.check_stopping_conditions():
            print("-" * 30)
            
            # Determine why we paused to give a better message and action
            is_budget_pause = session.turn_count >= session.config.turn_budget
            reason = "Turn budget reached" if is_budget_pause else "Sentence boundary reached"
            
            print(f"{reason}. Continue? (y/n): ", end="")
            choice = input().strip().lower()
            
            if choice != 'y':
                break
            
            if is_budget_pause:
                session.extend_budget()
                print(f"Budget extended to {session.config.turn_budget} turns.")

    # End of game
    print("\n" + "=" * 30)
    print("FINAL TRANSCRIPT:")
    print(session.transcript.get_full_text())
    print("=" * 30)
    print(f"Log saved to: {config.log_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        sys.exit(0)
