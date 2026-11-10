"""
Test en passant interaction with checkmate and stalemate detection.

These tests verify that is_checkmate and is_stalemate correctly accept
the en_passant_target parameter, addressing the Codex AI Review finding.
"""

import unittest
from chess_engine import (
    initialize_board, make_move, is_checkmate, is_stalemate,
    get_all_legal_moves, WHITE, BLACK, PAWN, QUEEN, KING
)


def setup_board(pieces_to_place):
    """Creates a custom board setup for testing."""
    board = [[None for _ in range(8)] for _ in range(8)]
    for (row, col), (piece_type, piece_color) in pieces_to_place:
        board[row][col] = (piece_type, piece_color)
    return board


class TestEnPassantWithCheckmateStalemate(unittest.TestCase):
    """Test that checkmate/stalemate functions accept en_passant_target parameter."""

    def test_en_passant_in_legal_moves(self):
        """Verify that en passant moves are included in legal move generation."""
        # Setup: White Ke1, White Pe5, Black Pd5 (just moved d7-d5)
        board = setup_board([
            ((7, 4), (KING, WHITE)),   # Ke1
            ((3, 4), (PAWN, WHITE)),   # Pe5
            ((3, 3), (PAWN, BLACK)),   # Pd5 (just moved from d7)
            ((0, 4), (KING, BLACK)),   # Ke8
        ])
        
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        # En passant target is d6 (row 2, col 3)
        en_passant_target = (2, 3)
        
        # Get legal moves with en passant
        legal_moves = get_all_legal_moves(board, WHITE, has_moved, en_passant_target)
        
        # En passant capture: e5xd6 = ((3,4), (2,3), None)
        en_passant_move = ((3, 4), (2, 3), None)
        self.assertIn(en_passant_move, legal_moves,
                     "En passant capture should be in legal moves")
        
        # Without en_passant_target, it shouldn't appear
        legal_moves_no_ep = get_all_legal_moves(board, WHITE, has_moved, None)
        self.assertNotIn(en_passant_move, legal_moves_no_ep,
                        "En passant shouldn't appear without en_passant_target")

    def test_checkmate_with_en_passant_parameter(self):
        """Test that is_checkmate accepts en_passant_target parameter."""
        # Use Fool's Mate (no en passant involved)
        board = initialize_board()
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        # Execute Fool's Mate sequence
        make_move(board, ((6, 5), (5, 5), None), has_moved)  # f3
        make_move(board, ((1, 4), (3, 4), None), has_moved)  # e5
        make_move(board, ((6, 6), (4, 6), None), has_moved)  # g4
        make_move(board, ((0, 3), (4, 7), None), has_moved)  # Qh4#
        
        # Should be checkmate with or without en_passant_target
        self.assertTrue(is_checkmate(board, WHITE, has_moved, None))
        self.assertTrue(is_checkmate(board, WHITE, has_moved, (2, 0)))

    def test_stalemate_with_en_passant_parameter(self):
        """Test that is_stalemate accepts en_passant_target parameter."""
        # Classic stalemate: Ka1 vs Ka3+Qb3
        board = setup_board([
            ((7, 0), (KING, WHITE)),   # Ka1
            ((5, 0), (KING, BLACK)),   # Ka3
            ((5, 1), (QUEEN, BLACK)),  # Qb3
        ])
        
        has_moved = {
            'WK': True, 'WR_a1': True, 'WR_h1': True,
            'BK': True, 'BR_a8': True, 'BR_h8': True
        }
        
        # Should be stalemate with or without en_passant_target
        self.assertTrue(is_stalemate(board, WHITE, has_moved, None))
        self.assertTrue(is_stalemate(board, WHITE, has_moved, (2, 0)))

    def test_not_stalemate_with_en_passant_available(self):
        """Test that available en passant prevents stalemate."""
        # Setup where en passant provides a legal move
        board = setup_board([
            ((7, 4), (KING, WHITE)),   # Ke1
            ((3, 4), (PAWN, WHITE)),   # Pe5
            ((3, 3), (PAWN, BLACK)),   # Pd5
            ((0, 4), (KING, BLACK)),   # Ke8
        ])
        
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        # With en passant available
        self.assertFalse(is_stalemate(board, WHITE, has_moved, (2, 3)))
        
        # Even without en passant, not stalemate (king can move)
        self.assertFalse(is_stalemate(board, WHITE, has_moved, None))


if __name__ == '__main__':
    unittest.main()
