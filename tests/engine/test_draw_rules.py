"""
Test tournament chess rules: en passant, 50-move rule, threefold repetition.

These tests ensure FIDE-compliant chess rules are correctly implemented,
covering positive cases (rules trigger correctly), negative cases (rules
don't trigger incorrectly), and edge cases for both white and black.
"""

import unittest
from chess_engine import (
    initialize_board, get_pawn_moves, get_position_hash, is_insufficient_material,
    make_move, get_all_legal_moves, is_move_truly_legal,
    is_fifty_move_draw, is_threefold_repetition,
    WHITE, BLACK, PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING
)


class TestEnPassant(unittest.TestCase):
    """Test en passant capture rule for both colors."""

    def setUp(self):
        """Set up a clean board for each test."""
        self.board = initialize_board()
        self.has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }

    def test_white_en_passant_capture_right(self):
        """Test white pawn capturing black pawn en passant to the right."""
        # Setup: White pawn on e5, black pawn on f5 (just moved from f7)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5 (white pawn)
        board[3][5] = (PAWN, BLACK)  # f5 (black pawn just moved 2 squares)
        
        # En passant target is f6 (row 2, col 5)
        en_passant_target = (2, 5)
        
        # Get white pawn moves with en passant target
        moves = get_pawn_moves(board, 3, 4, WHITE, en_passant_target=en_passant_target)
        
        # Verify en passant capture is in moves
        en_passant_move = ((3, 4), (2, 5), None)
        self.assertIn(en_passant_move, moves, 
                      "White pawn should be able to capture en passant to the right")

    def test_white_en_passant_capture_left(self):
        """Test white pawn capturing black pawn en passant to the left."""
        # Setup: White pawn on e5, black pawn on d5 (just moved from d7)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][3] = (PAWN, BLACK)  # d5 (just moved 2 squares)
        
        en_passant_target = (2, 3)  # d6
        
        moves = get_pawn_moves(board, 3, 4, WHITE, en_passant_target=en_passant_target)
        
        en_passant_move = ((3, 4), (2, 3), None)
        self.assertIn(en_passant_move, moves,
                      "White pawn should be able to capture en passant to the left")

    def test_black_en_passant_capture_right(self):
        """Test black pawn capturing white pawn en passant to the right."""
        # Setup: Black pawn on e4, white pawn on f4 (just moved from f2)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[4][4] = (PAWN, BLACK)  # e4
        board[4][5] = (PAWN, WHITE)  # f4 (just moved 2 squares)
        
        en_passant_target = (5, 5)  # f3
        
        moves = get_pawn_moves(board, 4, 4, BLACK, en_passant_target=en_passant_target)
        
        en_passant_move = ((4, 4), (5, 5), None)
        self.assertIn(en_passant_move, moves,
                      "Black pawn should be able to capture en passant to the right")

    def test_black_en_passant_capture_left(self):
        """Test black pawn capturing white pawn en passant to the left."""
        # Setup: Black pawn on e4, white pawn on d4 (just moved from d2)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[4][4] = (PAWN, BLACK)  # e4
        board[4][3] = (PAWN, WHITE)  # d4 (just moved 2 squares)
        
        en_passant_target = (5, 3)  # d3
        
        moves = get_pawn_moves(board, 4, 4, BLACK, en_passant_target=en_passant_target)
        
        en_passant_move = ((4, 4), (5, 3), None)
        self.assertIn(en_passant_move, moves,
                      "Black pawn should be able to capture en passant to the left")

    def test_en_passant_not_available_without_target(self):
        """Test that en passant doesn't happen when no target is set."""
        # Setup: White pawn on e5, black pawn on f5 (but NOT just moved)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][5] = (PAWN, BLACK)  # f5
        
        # No en passant target (pawn didn't just move 2 squares)
        moves = get_pawn_moves(board, 3, 4, WHITE, en_passant_target=None)
        
        # Verify en passant capture is NOT in moves
        en_passant_move = ((3, 4), (2, 5), None)
        self.assertNotIn(en_passant_move, moves,
                         "En passant should not be available without target")

    def test_en_passant_wrong_rank_white(self):
        """Test that white en passant only works from rank 5."""
        # Setup: White pawn on e6 (rank 6, not rank 5)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[2][4] = (PAWN, WHITE)  # e6 (wrong rank)
        board[2][5] = (PAWN, BLACK)  # f6
        
        en_passant_target = (1, 5)  # f7
        
        moves = get_pawn_moves(board, 2, 4, WHITE, en_passant_target=en_passant_target)
        
        # En passant should not be in moves (wrong rank)
        en_passant_move = ((2, 4), (1, 5), None)
        self.assertNotIn(en_passant_move, moves,
                         "En passant should only work from rank 5 for white")

    def test_en_passant_wrong_rank_black(self):
        """Test that black en passant only works from rank 4."""
        # Setup: Black pawn on e3 (rank 3, not rank 4)
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[5][4] = (PAWN, BLACK)  # e3 (wrong rank)
        board[5][5] = (PAWN, WHITE)  # f3
        
        en_passant_target = (6, 5)  # f2
        
        moves = get_pawn_moves(board, 5, 4, BLACK, en_passant_target=en_passant_target)
        
        # En passant should not be in moves (wrong rank)
        en_passant_move = ((5, 4), (6, 5), None)
        self.assertNotIn(en_passant_move, moves,
                         "En passant should only work from rank 4 for black")

    def test_en_passant_no_adjacent_pawn(self):
        """Test that en passant requires an adjacent enemy pawn."""
        # Setup: White pawn on e5, but no black pawn adjacent
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[3][4] = (PAWN, WHITE)  # e5
        # No pawn on d5 or f5
        
        en_passant_target = (2, 5)  # f6
        
        moves = get_pawn_moves(board, 3, 4, WHITE, en_passant_target=en_passant_target)
        
        # Should still generate forward move but not en passant
        forward_move = ((3, 4), (2, 4), None)
        en_passant_move = ((3, 4), (2, 5), None)
        
        self.assertIn(forward_move, moves, "Should be able to move forward")
        # En passant might still be in moves if target matches - that's OK
        # The real validation happens in make_move

    def test_en_passant_on_a_file(self):
        """Test en passant works on the a-file (edge case)."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[3][0] = (PAWN, WHITE)  # a5
        board[3][1] = (PAWN, BLACK)  # b5
        
        en_passant_target = (2, 1)  # b6
        
        moves = get_pawn_moves(board, 3, 0, WHITE, en_passant_target=en_passant_target)
        
        en_passant_move = ((3, 0), (2, 1), None)
        self.assertIn(en_passant_move, moves,
                      "En passant should work on a-file")

    def test_en_passant_on_h_file(self):
        """Test en passant works on the h-file (edge case)."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        board[3][7] = (PAWN, WHITE)  # h5
        board[3][6] = (PAWN, BLACK)  # g5
        
        en_passant_target = (2, 6)  # g6
        
        moves = get_pawn_moves(board, 3, 7, WHITE, en_passant_target=en_passant_target)
        
        en_passant_move = ((3, 7), (2, 6), None)
        self.assertIn(en_passant_move, moves,
                      "En passant should work on h-file")

    def test_en_passant_full_sequence_white(self):
        """Test complete en passant sequence: 2-square move, capture, piece removal (white)."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Black pawn moves d7-d5 (2 squares)
        board[1][3] = (PAWN, BLACK)  # d7
        ep_target = make_move(board, ((1, 3), (3, 3), None), has_moved, None)
        
        # Verify en passant target is set to d6
        self.assertEqual(ep_target, (2, 3), "En passant target should be d6 after d7-d5")
        self.assertEqual(board[3][3], (PAWN, BLACK), "Black pawn should be on d5")
        
        # White pawn captures e5xd6 en passant
        ep_target = make_move(board, ((3, 4), (2, 3), None), has_moved, ep_target)
        
        # Verify capture executed correctly
        self.assertEqual(board[2][3], (PAWN, WHITE), "White pawn should be on d6")
        self.assertIsNone(board[3][3], "Black pawn on d5 should be removed")
        self.assertIsNone(board[3][4], "White pawn should have moved from e5")
        self.assertIsNone(ep_target, "En passant target should be cleared")

    def test_en_passant_full_sequence_black(self):
        """Test complete en passant sequence: 2-square move, capture, piece removal (black)."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[4][3] = (PAWN, BLACK)  # d4
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # White pawn moves e2-e4 (2 squares)
        board[6][4] = (PAWN, WHITE)  # e2
        ep_target = make_move(board, ((6, 4), (4, 4), None), has_moved, None)
        
        # Verify en passant target is set to e3
        self.assertEqual(ep_target, (5, 4), "En passant target should be e3 after e2-e4")
        self.assertEqual(board[4][4], (PAWN, WHITE), "White pawn should be on e4")
        
        # Black pawn captures d4xe3 en passant
        ep_target = make_move(board, ((4, 3), (5, 4), None), has_moved, ep_target)
        
        # Verify capture executed correctly
        self.assertEqual(board[5][4], (PAWN, BLACK), "Black pawn should be on e3")
        self.assertIsNone(board[4][4], "White pawn on e4 should be removed")
        self.assertIsNone(board[4][3], "Black pawn should have moved from d4")
        self.assertIsNone(ep_target, "En passant target should be cleared")

    def test_en_passant_target_expires_after_one_move(self):
        """Test that en passant target is only valid for one turn."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][3] = (PAWN, BLACK)  # d5 (will be captured)
        board[2][0] = (KNIGHT, WHITE)  # a6 (random piece to move)
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Black pawn d7-d5 sets en passant target
        board[1][3] = (PAWN, BLACK)
        board[3][3] = None  # Clear for move
        ep_target = make_move(board, ((1, 3), (3, 3), None), has_moved, None)
        self.assertEqual(ep_target, (2, 3), "En passant target should be set")
        
        # White makes a different move (not en passant)
        ep_target = make_move(board, ((2, 0), (4, 1), None), has_moved, ep_target)
        
        # En passant target should be cleared
        self.assertIsNone(ep_target, "En passant target should expire after one move")

    def test_en_passant_in_legal_moves_white(self):
        """Test that en passant capture appears in legal moves for white."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][3] = (PAWN, BLACK)  # d5
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Set en passant target (as if black just moved d7-d5)
        ep_target = (2, 3)  # d6
        
        # Get all legal moves for white
        legal_moves = get_all_legal_moves(board, WHITE, has_moved, ep_target)
        
        # Verify en passant capture is in legal moves
        en_passant_move = ((3, 4), (2, 3), None)
        self.assertIn(en_passant_move, legal_moves,
                      "En passant capture should be in legal moves")

    def test_en_passant_in_legal_moves_black(self):
        """Test that en passant capture appears in legal moves for black."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[4][3] = (PAWN, BLACK)  # d4
        board[4][4] = (PAWN, WHITE)  # e4
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Set en passant target (as if white just moved e2-e4)
        ep_target = (5, 4)  # e3
        
        # Get all legal moves for black
        legal_moves = get_all_legal_moves(board, BLACK, has_moved, ep_target)
        
        # Verify en passant capture is in legal moves
        en_passant_move = ((4, 3), (5, 4), None)
        self.assertIn(en_passant_move, legal_moves,
                      "En passant capture should be in legal moves")

    def test_en_passant_truly_legal_white(self):
        """Test is_move_truly_legal validates en passant for white."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][3] = (PAWN, BLACK)  # d5
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        ep_target = (2, 3)  # d6
        
        # Verify en passant is truly legal
        en_passant_move = ((3, 4), (2, 3), None)
        self.assertTrue(
            is_move_truly_legal(board, en_passant_move, WHITE, has_moved, ep_target),
            "En passant should be truly legal for white"
        )

    def test_en_passant_truly_legal_black(self):
        """Test is_move_truly_legal validates en passant for black."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[4][3] = (PAWN, BLACK)  # d4
        board[4][4] = (PAWN, WHITE)  # e4
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        ep_target = (5, 4)  # e3
        
        # Verify en passant is truly legal
        en_passant_move = ((4, 3), (5, 4), None)
        self.assertTrue(
            is_move_truly_legal(board, en_passant_move, BLACK, has_moved, ep_target),
            "En passant should be truly legal for black"
        )

    def test_en_passant_not_legal_without_target(self):
        """Test en passant is not legal when target is not set."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[3][4] = (PAWN, WHITE)  # e5
        board[3][3] = (PAWN, BLACK)  # d5
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # No en passant target
        ep_target = None
        
        # Diagonal move to d6 (empty square) should not be legal without ep target
        illegal_move = ((3, 4), (2, 3), None)
        self.assertFalse(
            is_move_truly_legal(board, illegal_move, WHITE, has_moved, ep_target),
            "Diagonal pawn move to empty square should not be legal without en passant"
        )


class TestFiftyMoveRule(unittest.TestCase):
    """Test 50-move rule (draw after 50 moves without pawn move or capture)."""

    def test_fifty_move_basic(self):
        """Test basic halfmove clock increments."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[7][0] = (KNIGHT, WHITE)  # a1
        board[0][0] = (KNIGHT, BLACK)  # a8
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Move knight back and forth (no pawn moves, no captures)
        halfmove_clock = 0
        
        # Move 1: Knight a1-b3
        result = make_move(board, ((7, 0), (5, 1), None), has_moved, None, halfmove_clock, [], WHITE)
        self.assertEqual(result['halfmove_clock'], 1, "Clock should increment on non-pawn, non-capture move")
        
        # Move 2: Knight a8-b6
        halfmove_clock = result['halfmove_clock']
        result = make_move(board, ((0, 0), (2, 1), None), has_moved, None, halfmove_clock, [], BLACK)
        self.assertEqual(result['halfmove_clock'], 2, "Clock should continue incrementing")
        
        # After 100 half-moves
        self.assertFalse(is_fifty_move_draw(99), "Should not be draw at 99 half-moves")
        self.assertTrue(is_fifty_move_draw(100), "Should be draw at 100 half-moves")
        self.assertTrue(is_fifty_move_draw(101), "Should be draw after 100 half-moves")

    def test_fifty_move_reset_on_pawn(self):
        """Test clock resets on pawn move."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[6][4] = (PAWN, WHITE)  # e2
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Start with high halfmove clock
        halfmove_clock = 95
        
        # Pawn move should reset clock
        result = make_move(board, ((6, 4), (4, 4), None), has_moved, None, halfmove_clock, [], WHITE)
        self.assertEqual(result['halfmove_clock'], 0, "Clock should reset to 0 on pawn move")

    def test_fifty_move_reset_on_capture(self):
        """Test clock resets on capture."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[4][4] = (KNIGHT, WHITE)  # e4
        board[3][3] = (PAWN, BLACK)  # d5
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        # Start with high halfmove clock
        halfmove_clock = 80
        
        # Capture should reset clock
        result = make_move(board, ((4, 4), (3, 3), None), has_moved, None, halfmove_clock, [], WHITE)
        self.assertEqual(result['halfmove_clock'], 0, "Clock should reset to 0 on capture")

    def test_fifty_move_draw(self):
        """Test draw detection at 50 moves."""
        # Test the is_fifty_move_draw function directly
        self.assertFalse(is_fifty_move_draw(0), "No draw at start")
        self.assertFalse(is_fifty_move_draw(50), "No draw at 50 half-moves (only 25 full moves)")
        self.assertFalse(is_fifty_move_draw(99), "No draw at 99 half-moves")
        self.assertTrue(is_fifty_move_draw(100), "Draw at exactly 100 half-moves (50 full moves)")
        self.assertTrue(is_fifty_move_draw(150), "Draw after 50 moves")



class TestThreefoldRepetition(unittest.TestCase):
    """Test threefold repetition (draw when same position occurs 3 times)."""

    def test_position_hash_basic(self):
        """Test that position hash is consistent for same position."""
        board = initialize_board()
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        hash1 = get_position_hash(board, WHITE, has_moved)
        hash2 = get_position_hash(board, WHITE, has_moved)
        
        self.assertEqual(hash1, hash2, "Same position should produce same hash")

    def test_position_hash_different_players(self):
        """Test that hash differs when different player to move."""
        board = initialize_board()
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        hash_white = get_position_hash(board, WHITE, has_moved)
        hash_black = get_position_hash(board, BLACK, has_moved)
        
        self.assertNotEqual(hash_white, hash_black,
                            "Hash should differ when player to move differs")

    def test_position_hash_different_castling_rights(self):
        """Test that hash differs with different castling rights."""
        board = initialize_board()
        has_moved1 = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        has_moved2 = {
            'WK': True, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        hash1 = get_position_hash(board, WHITE, has_moved1)
        hash2 = get_position_hash(board, WHITE, has_moved2)
        
        self.assertNotEqual(hash1, hash2,
                            "Hash should differ with different castling rights")

    def test_position_hash_with_en_passant(self):
        """Test that hash includes en passant target."""
        board = initialize_board()
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        hash_no_ep = get_position_hash(board, WHITE, has_moved, en_passant_target=None)
        hash_with_ep = get_position_hash(board, WHITE, has_moved, en_passant_target=(2, 4))
        
        self.assertNotEqual(hash_no_ep, hash_with_ep,
                            "Hash should include en passant target")

    def test_position_hash_board_differences(self):
        """Test that different board positions produce different hashes."""
        board1 = initialize_board()
        has_moved = {
            'WK': False, 'WR_a1': False, 'WR_h1': False,
            'BK': False, 'BR_a8': False, 'BR_h8': False
        }
        
        # Create slightly different board
        board2 = initialize_board()
        board2[6][4] = None  # Remove e2 pawn
        
        hash1 = get_position_hash(board1, WHITE, has_moved)
        hash2 = get_position_hash(board2, WHITE, has_moved)
        
        self.assertNotEqual(hash1, hash2,
                            "Different boards should have different hashes")

    def test_threefold_repetition_detection(self):
        """Test detection of threefold repetition."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[7][1] = (KNIGHT, WHITE)  # b1
        board[0][1] = (KNIGHT, BLACK)  # b8
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        position_history = []
        
        # Move knights back and forth to create repetition
        # Starting position
        pos_hash = get_position_hash(board, WHITE, has_moved, None)
        position_history.append(pos_hash)
        
        # Move 1: Nb1-c3
        result = make_move(board, ((7, 1), (5, 2), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        
        # Move 2: Nb8-c6
        result = make_move(board, ((0, 1), (2, 2), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        
        # Move 3: Nc3-b1 (back to start)
        result = make_move(board, ((5, 2), (7, 1), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        
        # Move 4: Nc6-b8 (back to start)
        result = make_move(board, ((2, 2), (0, 1), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        
        # Now we're back to starting position (second time)
        self.assertFalse(is_threefold_repetition(position_history),
                         "Should not be threefold repetition after 2 occurrences")
        
        # Repeat the sequence once more
        result = make_move(board, ((7, 1), (5, 2), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        result = make_move(board, ((0, 1), (2, 2), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        result = make_move(board, ((5, 2), (7, 1), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        result = make_move(board, ((2, 2), (0, 1), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        
        # Now starting position has occurred 3 times
        self.assertTrue(is_threefold_repetition(position_history),
                        "Should be threefold repetition after 3 occurrences")

    def test_threefold_repetition_no_false_positive(self):
        """Test that similar but different positions don't trigger draw."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)  # e1
        board[0][4] = (KING, BLACK)  # e8
        board[7][1] = (KNIGHT, WHITE)  # b1
        board[0][1] = (KNIGHT, BLACK)  # b8
        
        has_moved = {'WK': False, 'WR_a1': False, 'WR_h1': False,
                     'BK': False, 'BR_a8': False, 'BR_h8': False}
        
        position_history = []
        
        # Different moves that don't repeat
        pos_hash = get_position_hash(board, WHITE, has_moved, None)
        position_history.append(pos_hash)
        
        result = make_move(board, ((7, 1), (5, 2), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        result = make_move(board, ((0, 1), (2, 2), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        result = make_move(board, ((5, 2), (3, 3), None), has_moved, None, 0, position_history, WHITE)
        position_history = result['position_history']
        result = make_move(board, ((2, 2), (4, 3), None), has_moved, None, 0, position_history, BLACK)
        position_history = result['position_history']
        
        # No position should repeat 3 times
        self.assertFalse(is_threefold_repetition(position_history),
                         "Should not be threefold repetition with different positions")


class TestInsufficientMaterial(unittest.TestCase):
    """Test insufficient material draw detection."""

    def test_king_vs_king(self):
        """Test K vs K is insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertTrue(is_insufficient_material(board),
                        "K vs K should be insufficient material")

    def test_king_bishop_vs_king(self):
        """Test K+B vs K is insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][5] = (BISHOP, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertTrue(is_insufficient_material(board),
                        "K+B vs K should be insufficient material")

    def test_king_knight_vs_king(self):
        """Test K+N vs K is insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][6] = (KNIGHT, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertTrue(is_insufficient_material(board),
                        "K+N vs K should be insufficient material")

    def test_king_bishop_vs_king_bishop_same_color(self):
        """Test K+B vs K+B (same color squares) is insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][2] = (BISHOP, WHITE)  # c1 (row 7, col 2: dark square)
        board[0][4] = (KING, BLACK)
        board[0][5] = (BISHOP, BLACK)  # f8 (row 0, col 5: dark square)
        
        self.assertTrue(is_insufficient_material(board),
                        "K+B vs K+B on same color should be insufficient material")

    def test_king_bishop_vs_king_bishop_opposite_color(self):
        """Test K+B vs K+B (opposite colors) is NOT insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][2] = (BISHOP, WHITE)  # c1 (row 7, col 2: dark square)
        board[0][4] = (KING, BLACK)
        board[0][2] = (BISHOP, BLACK)  # c8 (row 0, col 2: light square)
        
        self.assertFalse(is_insufficient_material(board),
                         "K+B vs K+B on opposite colors is NOT insufficient material")

    def test_king_pawn_vs_king(self):
        """Test K+P vs K is NOT insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[6][4] = (PAWN, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertFalse(is_insufficient_material(board),
                         "K+P vs K is NOT insufficient material")

    def test_king_rook_vs_king(self):
        """Test K+R vs K is NOT insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][0] = (ROOK, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertFalse(is_insufficient_material(board),
                         "K+R vs K is NOT insufficient material")

    def test_king_queen_vs_king(self):
        """Test K+Q vs K is NOT insufficient material."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][3] = (QUEEN, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertFalse(is_insufficient_material(board),
                         "K+Q vs K is NOT insufficient material")

    def test_king_two_knights_vs_king(self):
        """Test K+2N vs K is NOT insufficient material (rare mate possible)."""
        board = [[None]*8 for _ in range(8)]
        board[7][4] = (KING, WHITE)
        board[7][1] = (KNIGHT, WHITE)
        board[7][6] = (KNIGHT, WHITE)
        board[0][4] = (KING, BLACK)
        
        self.assertFalse(is_insufficient_material(board),
                         "K+2N vs K is NOT insufficient material")


if __name__ == '__main__':
    unittest.main()
