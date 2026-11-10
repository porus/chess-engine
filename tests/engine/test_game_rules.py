"""
Unit tests for game rules and state logic in chess_engine.core.
This includes tests for square attacks, check, checkmate, stalemate,
truly legal move generation (considering checks), castling rules, and pawn promotion.
"""
import unittest
import copy
from chess_engine import (
    initialize_board, parse_move, make_move, is_move_truly_legal,
    get_king_moves, # Only get_king_moves is directly used by some castling tests here
    is_in_check, is_checkmate, is_stalemate, get_all_legal_moves,
    is_square_attacked,
    WHITE, BLACK, PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING
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

# Default has_moved state for tests
# Using string keys for consistency with chess_engine.core
DEFAULT_HAS_MOVED = {
    'WK': False, 'WR_a1': False, 'WR_h1': False,
    'BK': False, 'BR_a8': False, 'BR_h8': False
}

class TestCoreGameRules(unittest.TestCase):
    """Tests core game rule evaluations like square attacks, check, and move legality."""

    def setUp(self):
        """Initializes a fresh `has_moved_initial` dictionary for each test method."""
        self.has_moved_initial = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_is_square_attacked(self):
        """
        Tests the `is_square_attacked` function for various pieces and scenarios,
        including pawn attacks, sliding piece attacks (rook, bishop, queen),
        knight attacks, king attacks, blocked attacks, and multiple attackers.
        """
        wp_board = setup_board([((6,4), (PAWN, WHITE))])
        self.assertTrue(
            is_square_attacked(wp_board, 5, 3, WHITE, self.has_moved_initial),
            "WP e2 attacks d3"
        )
        self.assertTrue(
            is_square_attacked(wp_board, 5, 5, WHITE, self.has_moved_initial),
            "WP e2 attacks f3"
        )
        self.assertFalse(
            is_square_attacked(wp_board, 5, 4, WHITE, self.has_moved_initial),
            "WP e2 does not 'attack' e3 (moves to it)"
        )

        bp_board = setup_board([((1,4), (PAWN, BLACK))])
        self.assertTrue(
            is_square_attacked(bp_board, 2, 3, BLACK, self.has_moved_initial),
            "BP e7 attacks d6"
        )

        wr_board = setup_board([((3,3), (ROOK, WHITE))])
        self.assertTrue(
            is_square_attacked(wr_board, 3, 0, WHITE, self.has_moved_initial),
            "WR d5 attacks a5"
        )

        wk_board = setup_board([((3,3), (KING, WHITE))])
        # King at (3,3) is not on its starting square, so for castling purposes, it has "moved".
        # The has_moved_state should reflect the status of 'WK' or 'BK'.
        temp_has_moved_wk_d5 = {**copy.deepcopy(self.has_moved_initial), 'WK': True}
        self.assertTrue(
            is_square_attacked(wk_board, 2, 2, WHITE, temp_has_moved_wk_d5), # Passing WHITE as attacker for its own king.
            "WK d5 attacks c6"
        )

        multi_attack_board = setup_board([
            ((3,3), (ROOK, WHITE)), ((1,3), (BISHOP, WHITE))
        ])
        self.assertTrue(
            is_square_attacked(multi_attack_board, 2, 3, WHITE, self.has_moved_initial),
            "Square d6 attacked by both Rook and Bishop"
        )

    def test_is_in_check(self):
        """
        Tests the `is_in_check` function for various scenarios, including checks
        by different piece types and a discovered check. Also tests non-check situations.
        """
        board_check_r = setup_board([((0,4), (KING, BLACK)), ((1,4), (ROOK, WHITE))])
        self.assertTrue(
            is_in_check(board_check_r, BLACK, self.has_moved_initial),
            "BK e8 should be in check by WR e7"
        )

        discovered_check_board = setup_board([
            ((4,0), (BISHOP, WHITE)), ((2,2), (KNIGHT, WHITE)), ((0,4), (KING, BLACK))
        ])
        current_has_moved = copy.deepcopy(self.has_moved_initial)
        # make_move expects a 3-part tuple
        make_move(discovered_check_board, ((2,2), (4,3), None), current_has_moved)
        self.assertTrue(
            is_in_check(discovered_check_board, BLACK, current_has_moved),
            "BK e8 should be in discovered check from WB a4"
        )

        board_no_check = setup_board([((0,4), (KING, BLACK)), ((3,7), (ROOK, WHITE))])
        self.assertFalse(
            is_in_check(board_no_check, BLACK, self.has_moved_initial),
            "BK e8 should not be in check by WR h5"
        )

        initial_b = initialize_board()
        self.assertFalse(
            is_in_check(initial_b, WHITE, self.has_moved_initial),
            "White king should not be in check on initial board"
        )

    def test_is_move_truly_legal_and_get_all_legal(self):
        """
        Tests `is_move_truly_legal` and `get_all_legal_moves`, focusing on scenarios
        like king moving into check, pinned pieces, and escaping check.
        """
        board_k_into_check = setup_board([((7,4), (KING, WHITE)), ((0,3), (ROOK, BLACK))])
        # Ensure 'WK' is False for this specific test, others default from DEFAULT_HAS_MOVED
        has_moved_wk_e1_unmoved = {**copy.deepcopy(self.has_moved_initial), 'WK':False}
        self.assertFalse(
            is_move_truly_legal(
                board_k_into_check, ((7,4), (7,3), None), WHITE, has_moved_wk_e1_unmoved
            ), "WK e1 to d1 (attacked) is illegal"
        )
        self.assertTrue(
            is_move_truly_legal(
                board_k_into_check, ((7,4), (7,5), None), WHITE, has_moved_wk_e1_unmoved
            ), "WK e1 to f1 (not attacked) is legal"
        )

        board_pinned_pawn = setup_board([
            ((7,4), (KING, WHITE)), ((6,4), (PAWN, WHITE)), ((0,4), (ROOK, BLACK))
        ])
        self.assertFalse(
            is_move_truly_legal( # Pawn move, non-promotion
                board_pinned_pawn, ((6,4), (5,3), None), WHITE, self.has_moved_initial
            ), "Pinned WP e2 cannot move to d3 (capturing off pin line)"
        )
        self.assertTrue(
            is_move_truly_legal( # Pawn move, non-promotion
                board_pinned_pawn, ((6,4), (5,4), None), WHITE, self.has_moved_initial
            ), "Pinned WP e2 CAN move to e3 (along pin line, still blocking)"
        )
        self.assertTrue(
            is_move_truly_legal( # Pawn move, non-promotion
                board_pinned_pawn, ((6,4), (4,4), None), WHITE, self.has_moved_initial
            ), "Pinned WP e2 CAN move to e4 (double step, still blocking)"
        )

        board_escape_check = setup_board([((0,0), (KING, BLACK)), ((1,0), (ROOK, WHITE))])
        # King on a8 (0,0) is not its original square, so it's considered moved by default
        # if not explicitly set. For this test, we want to treat it as if its 'BK' status is True.
        has_moved_bk_on_a8 = {**copy.deepcopy(self.has_moved_initial), 'BK':True}
        legal_moves = get_all_legal_moves(board_escape_check, BLACK, has_moved_bk_on_a8)
        # Expected moves are now 3-part tuples
        expected_escape_moves = [
            (((0,0),(0,1), None)), # Kb8
            (((0,0),(1,0), None))  # Kxa7
        ]
        self.assertCountEqual(
            legal_moves,
            expected_escape_moves,
            "BK a8 has two escape moves: Kb8 or Kxa7"
        )

        board2 = setup_board([
            ((7,4), (KING, WHITE)), ((7,3), (QUEEN, WHITE)),
            ((0,4), (KING, BLACK)), ((6,4), (ROOK, BLACK)),
        ])
        self.assertTrue(is_in_check(board2, WHITE, self.has_moved_initial),
                        "WK e1 is in check by BR e2")
        self.assertFalse(
            is_move_truly_legal(board2, ((7,3), (7,2), None), WHITE, self.has_moved_initial),
            "WQd1-c1 is illegal (king remains in check)"
        )
        self.assertTrue(
            is_move_truly_legal(board2, ((7,3), (6,4), None), WHITE, self.has_moved_initial),
            "WQd1xRe2 is legal (captures checker)"
        )

class TestEndConditionRules(unittest.TestCase):
    """Tests for game end conditions: checkmate and stalemate."""
    def setUp(self):
        """Initializes a fresh `has_moved_initial` for each test."""
        self.has_moved_initial = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_checkmate_back_rank(self):
        """Tests a classic back-rank checkmate scenario."""
        board = setup_board([
            ((0,7), (KING, BLACK)), ((1,5), (PAWN, BLACK)), ((1,6), (PAWN, BLACK)),
            ((1,7), (PAWN, BLACK)), ((7,4), (KING, WHITE)), ((7,0), (ROOK, WHITE))
        ])
        current_has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)
        # make_move expects a 3-part tuple
        make_move(board, ((7,0), (0,0), None), current_has_moved)
        self.assertTrue(is_in_check(board, BLACK, current_has_moved),
                        "Back-rank: Black King should be in check")
        self.assertEqual(len(get_all_legal_moves(board, BLACK, current_has_moved)), 0,
                         "Back-rank: Black King should have no legal moves")
        self.assertTrue(is_checkmate(board, BLACK, current_has_moved),
                        "Back-rank: This should be checkmate for Black")

    def test_checkmate_fools_mate(self):
        """Tests the Fool's Mate checkmate scenario."""
        board = initialize_board()
        current_has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)

        # parse_move already returns 3-part tuples
        f2f3_move = parse_move("f2f3") # ((6,5),(5,5),None)
        e7e5_move = parse_move("e7e5") # ((1,4),(3,4),None)
        g2g4_move = parse_move("g2g4") # ((6,6),(4,6),None)
        d8h4_move = parse_move("d8h4") # ((0,3),(4,7),None)

        make_move(board, f2f3_move, current_has_moved)
        make_move(board, e7e5_move, current_has_moved)
        make_move(board, g2g4_move, current_has_moved)
        make_move(board, d8h4_move, current_has_moved)
        self.assertTrue(is_checkmate(board, WHITE, current_has_moved),
                        "Fool's Mate: White should be checkmated")

    def test_stalemate_classic(self):
        """Tests a classic stalemate position (king trapped, not in check, no legal moves)."""
        board = setup_board([
            ((0,7), (KING, BLACK)), ((2,6), (QUEEN, WHITE)), ((4,5), (KING, WHITE))
        ])
        self.assertFalse(is_in_check(board, BLACK, self.has_moved_initial),
                         "Stalemate: Black king should NOT be in check")
        self.assertTrue(is_stalemate(board, BLACK, self.has_moved_initial),
                        "Stalemate: This position should be a stalemate for Black")

class TestCastlingRules(unittest.TestCase):
    """Test cases specifically for castling logic and rules."""
    def setUp(self):
        """Initializes a fresh `has_moved_initial` for each test."""
        self.has_moved_initial = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_castling_kingside_white_successful(self):
        """Tests successful Kingside castling for White (O-O)."""
        board = setup_board([((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE))])
        local_has_moved = copy.deepcopy(DEFAULT_HAS_MOVED)
        # get_king_moves returns 3-part tuples
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertIn( ((7,4),(7,6), None), actual_king_moves) # Expected castling move
        move_tuple = ((7,4), (7,6), None) # Use 3-part tuple
        self.assertTrue(is_move_truly_legal(board, move_tuple, WHITE, local_has_moved))
        make_move(board, move_tuple, local_has_moved)
        self.assertEqual(board[7][6], (KING, WHITE))
        self.assertEqual(board[7][5], (ROOK, WHITE))
        self.assertTrue(local_has_moved['WK']) # Check string key
        self.assertTrue(local_has_moved['WR_h1']) # Check string key for h1 rook

    def test_castling_queenside_white_successful(self):
        """Tests successful Queenside castling for White (O-O-O)."""
        board = setup_board([((7,4), (KING, WHITE)), ((7,0), (ROOK, WHITE))])
        local_has_moved = copy.deepcopy(self.has_moved_initial) # Uses string keys from global DEFAULT_HAS_MOVED
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertIn( ((7,4),(7,2), None), actual_king_moves)
        move_tuple = ((7,4),(7,2), None)
        self.assertTrue(is_move_truly_legal(board, move_tuple, WHITE, local_has_moved))
        make_move(board, move_tuple, local_has_moved)
        self.assertEqual(board[7][2], (KING, WHITE))
        self.assertEqual(board[7][3], (ROOK, WHITE))
        self.assertTrue(local_has_moved['WK'])
        self.assertTrue(local_has_moved['WR_a1'])

    def test_castling_kingside_black_successful(self):
        """Tests successful Kingside castling for Black (O-O)."""
        board = setup_board([((0,4), (KING, BLACK)), ((0,7), (ROOK, BLACK))])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        actual_king_moves = get_king_moves(board, 0, 4, BLACK, local_has_moved, False)
        self.assertIn( ((0,4),(0,6), None), actual_king_moves)
        move_tuple = ((0,4),(0,6), None)
        make_move(board, move_tuple, local_has_moved) # is_move_truly_legal implicitly tested by get_king_moves
        self.assertEqual(board[0][6], (KING, BLACK))
        self.assertEqual(board[0][5], (ROOK, BLACK))
        self.assertTrue(local_has_moved['BK'])
        self.assertTrue(local_has_moved['BR_h8'])

    def test_castling_queenside_black_successful(self):
        """Tests successful Queenside castling for Black (O-O-O)."""
        board = setup_board([((0,4), (KING, BLACK)), ((0,0), (ROOK, BLACK))])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        actual_king_moves = get_king_moves(board, 0, 4, BLACK, local_has_moved, False)
        self.assertIn( ((0,4),(0,2), None), actual_king_moves)
        move_tuple = ((0,4),(0,2), None)
        make_move(board, move_tuple, local_has_moved)
        self.assertEqual(board[0][2], (KING, BLACK))
        self.assertEqual(board[0][3], (ROOK, BLACK))
        self.assertTrue(local_has_moved['BK'])
        self.assertTrue(local_has_moved['BR_a8'])

    def test_castling_illegal_king_moved(self):
        """Tests castling is illegal if the king has moved."""
        board = setup_board([((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE))])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        local_has_moved['WK'] = True # King has moved
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_rook_moved(self):
        """Tests castling is illegal if the relevant rook has moved."""
        board = setup_board([((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE))])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        local_has_moved['WR_h1'] = True # Kingside rook has moved
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_pieces_between_kingside(self):
        """Tests castling is illegal if pieces are between king and kingside rook."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE)), ((7,5), (BISHOP, WHITE)) # Bishop on f1
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_pieces_between_queenside(self):
        """Tests castling is illegal if pieces are between king and queenside rook."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,0), (ROOK, WHITE)), ((7,2), (KNIGHT, WHITE)) # Knight on c1
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,2), None), actual_king_moves)

    def test_castling_illegal_king_in_check(self):
        """Tests castling is illegal if the king is currently in check."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE)), ((6,4), (ROOK, BLACK)) # Black rook checks white king
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        self.assertTrue(is_in_check(board, WHITE, local_has_moved))
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_king_passes_through_attacked_square_kingside(self):
        """Tests castling is illegal if king passes through an attacked square (f1 for White O-O)."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE)), ((0,5), (ROOK, BLACK)) # Black rook attacks f1 (7,5)
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        self.assertTrue(is_square_attacked(board, 7, 5, BLACK, local_has_moved))
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_king_lands_on_attacked_square_kingside(self):
        """Tests castling is illegal if king lands on an attacked square (g1 for White O-O)."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,7), (ROOK, WHITE)), ((0,6), (ROOK, BLACK)) # Black rook attacks g1 (7,6)
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        self.assertTrue(is_square_attacked(board, 7, 6, BLACK, local_has_moved))
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,6), None), actual_king_moves)

    def test_castling_illegal_king_passes_through_attacked_square_queenside(self):
        """Tests castling is illegal if king passes through an attacked square (d1 for White O-O-O)."""
        board = setup_board([
            ((7,4), (KING, WHITE)), ((7,0), (ROOK, WHITE)), ((0,3), (ROOK, BLACK)) # Black rook attacks d1 (7,3)
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        self.assertTrue(is_square_attacked(board, 7, 3, BLACK, local_has_moved))
        actual_king_moves = get_king_moves(board, 7, 4, WHITE, local_has_moved, False)
        self.assertNotIn( ((7,4),(7,2), None), actual_king_moves)

class TestPromotionRules(unittest.TestCase):
    """Test cases specifically for pawn promotion logic."""
    def setUp(self):
        """Initializes a fresh `has_moved_initial` for each test."""
        self.has_moved_initial = copy.deepcopy(DEFAULT_HAS_MOVED)

    def test_pawn_promotion_white_to_queen(self):
        """Tests White pawn promoting to a Queen."""
        board = setup_board([
            ((1,4), (PAWN, WHITE)), ((7,0), (KING, WHITE)), ((0,0), (KING, BLACK))
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        legal_moves = get_all_legal_moves(board, WHITE, local_has_moved)
        expected_promo_move = ((1,4), (0,4), QUEEN)
        self.assertIn(expected_promo_move, legal_moves)
        make_move(board, expected_promo_move, local_has_moved)
        self.assertEqual(board[0][4], (QUEEN, WHITE))
        self.assertIsNone(board[1][4])

    def test_pawn_promotion_black_to_queen(self):
        """Tests Black pawn promoting to a Queen."""
        board = setup_board([
            ((6,3), (PAWN, BLACK)), ((0,7), (KING, BLACK)), ((7,7), (KING, WHITE))
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        legal_moves = get_all_legal_moves(board, BLACK, local_has_moved)
        expected_promo_move = ((6,3), (7,3), QUEEN)
        self.assertIn(expected_promo_move, legal_moves)
        make_move(board, expected_promo_move, local_has_moved)
        self.assertEqual(board[7][3], (QUEEN, BLACK))
        self.assertIsNone(board[6][3])

    def test_pawn_promotion_generates_all_options(self):
        """Tests that all four promotion options (Q, R, B, N) are generated by get_all_legal_moves."""
        board = setup_board([
            ((1,0), (PAWN, WHITE)), ((0,2), (KING, BLACK)), ((7,7), (KING, WHITE))
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        legal_moves = get_all_legal_moves(board, WHITE, local_has_moved)
        promotion_options_found = 0
        expected_promotions = [
            ((1,0), (0,0), QUEEN), ((1,0), (0,0), ROOK),
            ((1,0), (0,0), BISHOP), ((1,0), (0,0), KNIGHT)
        ]
        for move in legal_moves:
            if len(move) == 3 and move[0] == (1,0) and move[1] == (0,0):
                self.assertIn(move, expected_promotions)
                promotion_options_found +=1
        self.assertEqual(promotion_options_found, 4)

    def test_pawn_promotion_with_capture_white(self):
        """Tests White pawn promoting with a capture, ensuring all promotion options are generated."""
        board = setup_board([
            ((1,3), (PAWN, WHITE)), ((0,2), (ROOK, BLACK)),
            ((0,4), (KING, BLACK)), ((7,7), (KING, WHITE))
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        legal_moves = get_all_legal_moves(board, WHITE, local_has_moved)
        expected_promo_captures = [
            ((1,3), (0,2), QUEEN), ((1,3), (0,2), ROOK),
            ((1,3), (0,2), BISHOP), ((1,3), (0,2), KNIGHT)
        ]
        for promo_move in expected_promo_captures:
            self.assertIn(promo_move, legal_moves)
        # Test making one specific promotion move (e.g., to Queen)
        make_move(board, expected_promo_captures[0], local_has_moved)
        self.assertEqual(board[0][2], (QUEEN, WHITE))
        self.assertIsNone(board[1][3])

    def test_pawn_promotion_only_on_correct_rank(self):
        """Tests that pawn promotion options are ONLY generated when reaching the final rank."""
        board = setup_board([
            ((2,4), (PAWN, WHITE)), ((0,0), (KING, BLACK)), ((7,7), (KING, WHITE)) # White pawn at e6
        ])
        local_has_moved = copy.deepcopy(self.has_moved_initial)
        legal_moves = get_all_legal_moves(board, WHITE, local_has_moved)

        # Expected non-promoting move e6e7
        expected_simple_move_e6e7 = ((2,4), (1,4), None)

        # Check if this simple move is present
        self.assertIn(expected_simple_move_e6e7, legal_moves,
                      "Pawn move e6e7 should be a legal 3-part tuple.")

        # Verify that for this specific start/end, no promotion piece is offered (it shouldn't be)
        # This means only the tuple with None as the 3rd element should exist for ( (2,4), (1,4) )
        found_promotion_for_e6e7 = False
        for move in legal_moves:
            if move[0] == (2,4) and move[1] == (1,4) and move[2] is not None:
                found_promotion_for_e6e7 = True
                break
        self.assertFalse(found_promotion_for_e6e7,
                         "Move e6e7 should not generate promotion options (Q,R,B,N).")

if __name__ == '__main__':
    unittest.main()
