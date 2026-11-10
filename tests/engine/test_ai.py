"""
Unit tests for AI-related functionalities in chess_engine.core.
This includes tests for board evaluation (`evaluate_board`) and
the greedy AI move selection logic (`get_greedy_ai_move`).
"""
import unittest
import copy
from chess_engine import (
    initialize_board, evaluate_board,
    get_greedy_ai_move, get_all_legal_moves,
    WHITE, BLACK, PAWN, ROOK, KNIGHT, QUEEN, KING, PIECE_VALUES
)

# Helper to set up a specific board scenario for a test
def setup_board(pieces_to_place):
    """
    Creates a custom board setup for testing.

    Args:
        pieces_to_place (list of tuple): A list where each item is
            ((row, col), (PIECE_TYPE, PLAYER_COLOR)).

    Returns:
        list of list: An 8x8 board with the specified pieces.
    """
    board = [[None for _ in range(8)] for _ in range(8)]
    for (row, col), (piece_type, piece_color) in pieces_to_place:
        board[row][col] = (piece_type, piece_color)
    return board

class TestEvaluateBoard(unittest.TestCase):
    """Tests for the `evaluate_board` function."""

    def test_initial_board_evaluation(self):
        """Tests that the evaluation of the standard initial board setup is zero."""
        board = initialize_board()
        self.assertEqual(
            evaluate_board(board), 0.0,
            "Initial board score should be 0, assuming symmetrical piece values."
        )

    def test_white_ahead_material(self):
        """Tests that the evaluation is positive when White has a material advantage."""
        board = setup_board([
            ((3,3), (ROOK, WHITE)),
            ((0,0), (KING, WHITE)),
            ((7,7), (KING, BLACK))
        ])
        expected_score = PIECE_VALUES[ROOK]
        self.assertEqual(
            evaluate_board(board), expected_score,
            "Score should reflect White's extra Rook."
        )

    def test_black_ahead_material(self):
        """Tests that the evaluation is negative when Black has a material advantage."""
        board = setup_board([
            ((3,3), (QUEEN, BLACK)),
            ((0,0), (KING, WHITE)),
            ((7,7), (KING, BLACK))
        ])
        expected_score = -PIECE_VALUES[QUEEN]
        self.assertEqual(
            evaluate_board(board), expected_score,
            "Score should reflect Black's extra Queen."
        )

    def test_empty_board_evaluation(self):
        """Tests that the evaluation of an empty board is zero."""
        board = [[None for _ in range(8)] for _ in range(8)]
        self.assertEqual(evaluate_board(board), 0, "Empty board score should be 0.")

class TestGetGreedyAIMove(unittest.TestCase):
    """Tests for the `get_greedy_ai_move` function."""

    def setUp(self):
        """
        Initializes a default `has_moved` state for AI tests.
        This represents a state where no castling-relevant pieces have moved yet.
        Using string keys for consistency.
        """
        self.initial_has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }

    def test_ai_makes_a_valid_move(self):
        """
        Tests that the AI picks a valid move if legal moves are available from the
        initial board state.
        """
        board = initialize_board()
        current_has_moved = copy.deepcopy(self.initial_has_moved)

        all_moves = get_all_legal_moves(board, WHITE, current_has_moved)
        self.assertTrue(
            len(all_moves) > 0,
            "White should have legal moves from the initial position."
        )

        ai_move = get_greedy_ai_move(board, WHITE, current_has_moved)
        self.assertIsNotNone(ai_move, "Greedy AI should pick a move if legal moves exist.")
        self.assertIn(
            ai_move, all_moves,
            "Greedy AI's chosen move should be in the list of all legal moves."
        )

    def test_capture_undefended_piece(self):
        """
        Tests that the Greedy AI chooses to capture an undefended opponent piece
        when it results in a material advantage.
        """
        board = setup_board([
            ((3,3), (QUEEN, WHITE)),
            ((3,6), (ROOK, BLACK)),
            ((0,0), (KING, WHITE)),
            ((7,7), (KING, BLACK))
        ])
        expected_move = ((3,3), (3,6), None) # 3-part tuple
        ai_move = get_greedy_ai_move(board, WHITE, copy.deepcopy(self.initial_has_moved))
        self.assertEqual(
            ai_move, expected_move,
            "Greedy AI should capture the undefended rook."
        )

    def test_choice_between_captures(self):
        """
        Tests that the Greedy AI picks the capture that yields the highest material gain
        when multiple capture options are available.
        """
        board = setup_board([
            ((3,3), (ROOK, WHITE)),
            ((3,6), (PAWN, BLACK)),
            ((1,3), (KNIGHT, BLACK)),
            ((7,0), (KING, WHITE)),
            ((0,0), (KING, BLACK))
        ])
        expected_best_move = ((3,3), (1,3), None) # 3-part tuple

        ai_move = get_greedy_ai_move(board, WHITE, copy.deepcopy(self.initial_has_moved))
        self.assertEqual(
            ai_move, expected_best_move,
            "Greedy AI should capture the Knight (higher value) over the Pawn."
        )

    def test_black_ai_captures_undefended(self):
        """
        Tests that the Greedy AI, when playing as Black, captures an undefended opponent piece
        for material gain.
        """
        board = setup_board([
            ((4,4), (QUEEN, BLACK)),
            ((4,1), (ROOK, WHITE)),
            ((0,4), (KING, BLACK)),
            ((7,4), (KING, WHITE))
        ])
        expected_move = ((4,4), (4,1), None) # 3-part tuple
        ai_move = get_greedy_ai_move(board, BLACK, copy.deepcopy(self.initial_has_moved))
        self.assertEqual(
            ai_move, expected_move,
            "Black Greedy AI should capture the undefended white rook."
        )

if __name__ == '__main__':
    unittest.main()
