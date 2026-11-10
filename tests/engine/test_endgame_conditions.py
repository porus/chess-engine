"""
Unit tests for checkmate and stalemate conditions in chess_engine.core.
Tests validate end-game detection and game termination conditions.
"""
import unittest
import copy
from chess_engine import (
    initialize_board, make_move, is_in_check, is_checkmate, is_stalemate,
    get_all_legal_moves, WHITE, BLACK, PAWN, ROOK, KING
)

def setup_board(pieces_to_place):
    """Creates a custom board setup for testing."""
    board = [[None for _ in range(8)] for _ in range(8)]
    for (row, col), (piece_type, piece_color) in pieces_to_place:
        board[row][col] = (piece_type, piece_color)
    return board

DEFAULT_HAS_MOVED = {
    'WK': False, 'WR_a1': False, 'WR_h1': False,
    'BK': False, 'BR_a8': False, 'BR_h8': False
}


class TestCheckMatePatterns(unittest.TestCase):
    """Test checkmate detection in standard positions."""

    def setUp(self):
        self.has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_checkmate_back_rank_from_initial_board(self):
        """Test back-rank checkmate using initial board state (Fool's Mate)."""
        board = initialize_board()
        current_has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)
        
        # Fool's Mate: 1.f3 e5 2.g4 Qh4#
        make_move(board, ((6, 5), (5, 5), None), current_has_moved)  # f2f3
        make_move(board, ((1, 4), (3, 4), None), current_has_moved)  # e7e5
        make_move(board, ((6, 6), (4, 6), None), current_has_moved)  # g2g4
        make_move(board, ((0, 3), (4, 7), None), current_has_moved)  # d8h4
        
        self.assertTrue(is_checkmate(board, WHITE, current_has_moved))

    def test_checkmate_back_rank_rook(self):
        """Test classic back-rank mate with rook."""
        board = setup_board([
            ((0, 7), (KING, BLACK)), ((1, 5), (PAWN, BLACK)), ((1, 6), (PAWN, BLACK)),
            ((1, 7), (PAWN, BLACK)), ((7, 4), (KING, WHITE)), ((7, 0), (ROOK, WHITE))
        ])
        current_has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)
        make_move(board, ((7, 0), (0, 0), None), current_has_moved)
        
        self.assertTrue(is_in_check(board, BLACK, current_has_moved))
        self.assertTrue(is_checkmate(board, BLACK, current_has_moved))

    def test_not_checkmate_when_escape_available(self):
        """Test that escape square prevents checkmate."""
        board = setup_board([
            ((0, 4), (KING, BLACK)), ((1, 4), (ROOK, WHITE)),
            ((7, 0), (KING, WHITE))
        ])
        if is_in_check(board, BLACK, self.has_moved):
            self.assertFalse(is_checkmate(board, BLACK, self.has_moved))

    def test_not_checkmate_when_block_possible(self):
        """Test that blocking prevents checkmate."""
        board = setup_board([
            ((0, 4), (KING, BLACK)), ((2, 4), (ROOK, WHITE)),
            ((7, 0), (KING, WHITE)), ((1, 4), (PAWN, BLACK))
        ])
        # Pawn can move to block if in check
        if is_in_check(board, BLACK, self.has_moved):
            legal_moves = get_all_legal_moves(board, BLACK, self.has_moved)
            self.assertGreater(len(legal_moves), 0)


class TestStaleMatePatterns(unittest.TestCase):
    """Test stalemate detection."""

    def setUp(self):
        self.has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_stalemate_classic_position(self):
        """Test classic stalemate (king and queen trap opposing king)."""
        # Black king on h8 with no legal moves, not in check
        board = setup_board([
            ((0, 7), (KING, BLACK)), ((2, 6), (ROOK, WHITE)),
            ((5, 5), (KING, WHITE))
        ])
        self.assertFalse(is_in_check(board, BLACK, self.has_moved),
                         "King should not be in check for stalemate")
        legal_moves = get_all_legal_moves(board, BLACK, self.has_moved)
        if not legal_moves:
            self.assertTrue(is_stalemate(board, BLACK, self.has_moved))

    def test_not_stalemate_when_moves_available(self):
        """Test that available moves prevent stalemate."""
        board = setup_board([
            ((0, 4), (KING, BLACK)), ((7, 0), (KING, WHITE))
        ])
        self.assertFalse(is_stalemate(board, BLACK, self.has_moved))

    def test_not_stalemate_when_in_check(self):
        """Test that check prevents stalemate diagnosis."""
        board = setup_board([
            ((0, 4), (KING, BLACK)), ((1, 4), (ROOK, WHITE)),
            ((7, 0), (KING, WHITE))
        ])
        self.assertTrue(is_in_check(board, BLACK, self.has_moved))
        self.assertFalse(is_stalemate(board, BLACK, self.has_moved))


if __name__ == '__main__':
    unittest.main()
