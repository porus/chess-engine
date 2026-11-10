"""Start a local text-based chess game against the built-in baseline opponent."""

from chess_engine import play_game


if __name__ == "__main__":
    print("Chess Rules Engine")
    print("Enter moves using the format shown by the game. Enter 'q' to quit.")
    play_game()
