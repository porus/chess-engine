"""
Unit tests for individual piece movement logic in chess_engine.core.
This file focuses on verifying the correctness of move generation for each
piece type (Pawn, Rook, Knight, Bishop, Queen, King) under various
board conditions, such as empty boards, blocked paths, and captures.
It does not test for "truly legal" moves (i.e., moves that would put the
king in check), as that is covered in test_game_rules.py.
Castling moves for the King are also primarily tested in test_game_rules.py.
"""
import unittest
import copy
from chess_engine import (
    initialize_board,
    get_pawn_moves, get_rook_moves, get_knight_moves, get_bishop_moves, get_queen_moves,
    get_king_moves,
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

# Default has_moved state for get_king_moves tests where castling is not the focus.
# Using string keys for consistency with chess_engine.core's has_moved_dict
DEFAULT_HAS_MOVED_FALSE = {
    'WK': False, 'WR_a1': False, 'WR_h1': False,
    'BK': False, 'BR_a8': False, 'BR_h8': False
}
# King is assumed to have moved to prevent castling unless testing castling.
DEFAULT_KING_MOVED_STATE = {
    'WK': True, 'WR_a1': False, 'WR_h1': False,
    'BK': True, 'BR_a8': False, 'BR_h8': False
}
# A state where specific rooks might have moved, but kings haven't (useful for some tests)
SPECIFIC_ROOKS_MOVED_STATE = { # Kept for potential future use, not directly used in current fixes
    'WK': False, 'WR_a1': True, 'WR_h1': False,
    'BK': False, 'BR_a8': False, 'BR_h8': True
}


class TestPieceMovement(unittest.TestCase):
    """Tests pseudo-legal move generation for each piece type."""

    def test_get_pawn_moves(self):
        """
        Tests pawn movement: initial double step, single step, captures (left/right),
        blocked scenarios (by own/opponent piece), and invalid moves (backward, sideways).
        """
        board_init = initialize_board()
        # All get_<piece>_moves now return 3-part tuples.
        # Expected moves for pawns are ( (start_r,start_c), (end_r,end_c), None )
        wp_e2_moves = get_pawn_moves(board_init, 6, 4, WHITE)
        self.assertCountEqual(wp_e2_moves, [((6,4),(5,4),None), ((6,4),(4,4),None)],
                              "WP e2 initial moves: e3, e4")
        bp_d7_moves = get_pawn_moves(board_init, 1, 3, BLACK)
        self.assertCountEqual(bp_d7_moves, [((1,3),(2,3),None), ((1,3),(3,3),None)],
                              "BP d7 initial moves: d6, d5")

        board_wp_capture = setup_board([
            ((3,4), (PAWN, WHITE)), ((2,3), (PAWN, BLACK)), ((2,5), (PAWN, BLACK))
        ]) # WP e5, BP d6, BP f6
        wp_e5_captures = get_pawn_moves(board_wp_capture, 3, 4, WHITE)
        expected_wp_e5_captures = [((3,4),(2,4),None)] # Forward move e6
        if board_wp_capture[2][3] and board_wp_capture[2][3][1] == BLACK:
            expected_wp_e5_captures.append(((3,4),(2,3),None)) # Capture d6
        if board_wp_capture[2][5] and board_wp_capture[2][5][1] == BLACK:
            expected_wp_e5_captures.append(((3,4),(2,5),None)) # Capture f6
        self.assertCountEqual(wp_e5_captures, expected_wp_e5_captures,
                              "WP e5 should move to e6 and capture d6, f6")

        board_bp_capture = setup_board([
            ((4,4), (PAWN, BLACK)), ((5,3), (PAWN, WHITE)), ((5,5), (PAWN, WHITE))
        ]) # BP e4, WP d3, WP f3
        bp_e4_captures = get_pawn_moves(board_bp_capture, 4, 4, BLACK)
        expected_bp_e4_captures = [((4,4),(5,4),None)] # Forward move e3
        if board_bp_capture[5][3] and board_bp_capture[5][3][1] == WHITE:
            expected_bp_e4_captures.append(((4,4),(5,3),None)) # Capture d3
        if board_bp_capture[5][5] and board_bp_capture[5][5][1] == WHITE:
            expected_bp_e4_captures.append(((4,4),(5,5),None)) # Capture f3
        self.assertCountEqual(bp_e4_captures, expected_bp_e4_captures,
                              "BP e4 should move to e3 and capture d3, f3")

        board_wp_blocked_own = setup_board([((6,0), (PAWN, WHITE)), ((5,0), (PAWN, WHITE))])
        self.assertEqual(get_pawn_moves(board_wp_blocked_own, 6,0, WHITE), [],
                         "WP a2 blocked by own pawn at a3 should have no moves")
        board_wp_blocked_opp = setup_board([((6,0), (PAWN, WHITE)), ((5,0), (PAWN, BLACK))])
        # Pawn cannot move forward one square if blocked, so no double step either.
        self.assertEqual(get_pawn_moves(board_wp_blocked_opp, 6,0, WHITE), [],
                         "WP a2 blocked by opponent at a3 should have no moves (no double)")

        board_wp_backward = setup_board([((3,4), (PAWN, WHITE))]) # WP e5
        # Extract just end_pos for NotIn check if get_pawn_moves returns 3-tuples
        actual_moves_tuples = get_pawn_moves(board_wp_backward, 3,4, WHITE)
        actual_end_positions = [m[1] for m in actual_moves_tuples]
        self.assertNotIn((4,4), actual_end_positions,
                         "WP e5 should not be able to move backward to e4")
        self.assertNotIn((3,3), actual_end_positions,
                         "WP e5 should not be able to move sideways to d5 without capture")
        self.assertNotIn((3,5), actual_end_positions,
                         "WP e5 should not be able to move sideways to f5 without capture")

    def test_get_rook_moves(self):
        """
        Tests rook movement: initially blocked, max range on empty board,
        multiple captures, blocking by own pieces, and ensures no jumping.
        """
        board_init = initialize_board()
        self.assertEqual(get_rook_moves(board_init, 7, 7, WHITE), [],
                         "WR h1 should be initially blocked by h2 pawn")
        self.assertEqual(get_rook_moves(board_init, 0, 0, BLACK), [],
                         "BR a8 should be initially blocked by a7 pawn")

        empty_board = [[None for _ in range(8)] for _ in range(8)]
        empty_board[3][3] = (ROOK, WHITE) # Rook at d5
        moves = get_rook_moves(empty_board, 3, 3, WHITE)
        self.assertEqual(len(moves), 14, "Rook at d5 on empty board should have 14 moves")
        # Check one move to ensure 3-part tuple format
        self.assertIn( ((3,3),(3,0),None), moves, "Example rook move format incorrect")


        board_multi_capture = setup_board([
            ((3,3), (ROOK, WHITE)), ((3,0), (PAWN, BLACK)), ((5,3), (PAWN, BLACK)),
            ((0,3), (PAWN, BLACK)), ((3,6), (KNIGHT, WHITE)) # Own knight blocks
        ])
        moves_rook_multi = get_rook_moves(board_multi_capture, 3, 3, WHITE)
        # Expected moves are now 3-part tuples
        expected_rook_moves_tuples = [
            ((3,3),m,None) for m in [
                (3,2),(3,1),(3,0), # Left capture BP at a5
                (2,3),(1,3),(0,3), # Up capture BP at d8
                (4,3),(5,3),       # Down capture BP at d3
                (3,4),(3,5)        # Right, path to g5 blocked by own WN at g5
            ]
        ]
        self.assertCountEqual(moves_rook_multi, expected_rook_moves_tuples,
                              "Rook should capture available pieces and be blocked by own")

        board_jump = setup_board([
            ((0,0), (ROOK, WHITE)), ((0,1), (PAWN, BLACK)), ((0,2), (PAWN, BLACK))
        ]) # WR a8, BP b8, BP c8
        actual_jump_moves = [m[1] for m in get_rook_moves(board_jump, 0,0, WHITE)]
        self.assertNotIn((0,2), actual_jump_moves,
                         "Rook at a8 should not jump over BP at b8 to reach c8")

    def test_get_knight_moves(self):
        """
        Tests knight movement: initial moves, max range from center and corner,
        captures, and blocking by own pieces.
        """
        board_init = initialize_board()
        # Expected moves are 3-part tuples
        expected_g1_knight_moves = [((7,6),m,None) for m in [(5,5), (5,7)]]
        self.assertCountEqual(get_knight_moves(board_init, 7, 6, WHITE),
                              expected_g1_knight_moves, "WN g1 initial moves should be to f3, h3")

        empty_board = [[None for _ in range(8)] for _ in range(8)]
        empty_board[3][3] = (KNIGHT, WHITE) # Knight at d5
        moves_d5 = get_knight_moves(empty_board, 3, 3, WHITE)
        self.assertEqual(len(moves_d5), 8,
                         "Knight at d5 on empty board should have 8 moves")
        self.assertIn( ((3,3),(1,2),None), moves_d5, "Example knight move format incorrect")


        empty_board_corner = [[None for _ in range(8)] for _ in range(8)]
        empty_board_corner[0][0] = (KNIGHT, WHITE) # Knight at a8
        self.assertEqual(len(get_knight_moves(empty_board_corner, 0, 0, WHITE)), 2,
                         "Knight at a8 on empty board should have 2 moves")

        board_captures = setup_board([
            ((3,3), (KNIGHT, WHITE)), ((1,2), (PAWN, BLACK)), ((1,4), (PAWN, WHITE)),
            ((2,1), (ROOK, BLACK)), ((2,5), (BISHOP, WHITE))
        ]) # WN d5; BP c7, WP e7; BR b6, WB f6
        moves = get_knight_moves(board_captures, 3,3, WHITE)
        expected_tuples = [((3,3),m,None) for m in [(1,2), (2,1), (4,1), (5,2), (5,4), (4,5)]]
        self.assertCountEqual(moves, expected_tuples,
                              "Knight should capture opponent pieces and move to empty squares, not own")

    def test_get_bishop_moves(self):
        """
        Tests bishop movement: initially blocked, max range from center and corner,
        multiple captures, blocking by own pieces, and ensures no jumping.
        """
        board_init = initialize_board()
        self.assertEqual(get_bishop_moves(board_init, 7, 5, WHITE), [],
                         "WB f1 should be initially blocked")

        empty_board_center = [[None for _ in range(8)] for _ in range(8)]
        empty_board_center[3][3] = (BISHOP, WHITE) # Bishop at d5
        moves_d5 = get_bishop_moves(empty_board_center, 3, 3, WHITE)
        self.assertEqual(len(moves_d5), 13,
                         "Bishop at d5 on empty board should have 13 moves")
        self.assertIn( ((3,3),(0,0),None), moves_d5, "Example bishop move format incorrect")


        empty_board_corner = [[None for _ in range(8)] for _ in range(8)]
        empty_board_corner[0][0] = (BISHOP, WHITE) # Bishop at a8
        self.assertEqual(len(get_bishop_moves(empty_board_corner, 0, 0, WHITE)), 7,
                         "Bishop at a8 on empty board should have 7 moves")

        board_captures = setup_board([
            ((3,3), (BISHOP, WHITE)), ((1,1), (PAWN, BLACK)), ((1,5), (PAWN, WHITE)),
            ((5,1), (ROOK, BLACK)), ((5,5), (KNIGHT, WHITE))
        ]) # WB d5; BP b7, WP f7; BR b3, WN f3
        moves = get_bishop_moves(board_captures, 3,3, WHITE)
        expected_tuples = [((3,3),m,None) for m in [(2,2),(1,1), (2,4), (4,2),(5,1), (4,4)]]
        self.assertCountEqual(moves, expected_tuples,
                              "Bishop should capture available pieces and be blocked by own")

        board_jump = setup_board([
            ((0,2), (BISHOP, WHITE)), ((1,3), (PAWN, BLACK)), ((2,4), (PAWN, BLACK))
        ]) # WB c8, BP d7, BP e6
        actual_jump_moves = [m[1] for m in get_bishop_moves(board_jump,0,2, WHITE)]
        self.assertNotIn((2,4), actual_jump_moves,
                         "Bishop at c8 should not jump over BP at d7 to reach e6")

    def test_get_queen_moves(self):
        """
        Tests queen movement: initially blocked, max range, captures (rook & bishop like),
        blocking by own pieces, and ensures no jumping.
        """
        board_init = initialize_board()
        self.assertEqual(get_queen_moves(board_init, 7, 3, WHITE), [],
                         "WQ d1 should be initially blocked")

        empty_board = [[None for _ in range(8)] for _ in range(8)]
        empty_board[3][3] = (QUEEN, WHITE) # Queen at d5
        moves_d5 = get_queen_moves(empty_board, 3, 3, WHITE)
        self.assertEqual(len(moves_d5), 27,
                         "Queen at d5 on empty board should have 27 moves (13 diag + 14 straight)")
        self.assertIn( ((3,3),(3,7),None), moves_d5, "Example queen rook-like move format incorrect")
        self.assertIn( ((3,3),(7,7),None), moves_d5, "Example queen bishop-like move format incorrect")


        board_captures = setup_board([
            ((3,3), (QUEEN, WHITE)), ((3,0), (PAWN, BLACK)), ((0,3), (PAWN, WHITE)), # WQ d5; BP a5, WP d8
            ((1,1), (PAWN, BLACK)), ((5,5), (KNIGHT, WHITE)) # BP b7, WN f3
        ])
        moves = get_queen_moves(board_captures, 3,3, WHITE)
        expected_rook_part_ends = [
            (3,2),(3,1),(3,0),       # Left (capture a5)
            (3,4),(3,5),(3,6),(3,7), # Right
            (2,3),(1,3),             # Up (d8 blocked)
            (4,3),(5,3),(6,3),(7,3)  # Down
        ]
        expected_bishop_part_ends = [
            (2,2),(1,1),             # Up-Left (capture b7)
            (2,4),(1,5),(0,6),       # Up-Right
            (4,2),(5,1),(6,0),       # Down-Left
            (4,4)                    # Down-Right (f3 blocked)
        ]
        expected_ends = list(set(expected_rook_part_ends + expected_bishop_part_ends))
        expected_tuples = [((3,3),m,None) for m in expected_ends]
        self.assertCountEqual(moves, expected_tuples,
                              "Queen should combine rook/bishop captures and be blocked by own")

        board_jump_rook = setup_board([
            ((0,0), (QUEEN, WHITE)), ((0,1), (PAWN, BLACK)), ((0,2), (PAWN, BLACK))
        ])
        actual_jump_rook_moves = [m[1] for m in get_queen_moves(board_jump_rook, 0,0, WHITE)]
        self.assertNotIn((0,2), actual_jump_rook_moves,
                         "Queen should not jump (rook-like)")
        board_jump_bishop = setup_board([
            ((0,2), (QUEEN, WHITE)), ((1,3), (PAWN, BLACK)), ((2,4), (PAWN, BLACK))
        ])
        actual_jump_bishop_moves = [m[1] for m in get_queen_moves(board_jump_bishop,0,2, WHITE)]
        self.assertNotIn((2,4), actual_jump_bishop_moves,
                         "Queen should not jump (bishop-like)")

    def test_get_king_moves(self):
        """
        Tests king movement: initially blocked, max range from center and corner
        (excluding castling), captures, and blocking by own pieces.
        Castling itself is tested in TestGameRules.
        """
        board_init = initialize_board()
        self.assertEqual(
            get_king_moves(board_init, 7,4, WHITE, DEFAULT_HAS_MOVED_FALSE, False), [],
            "WK e1 should be initially blocked by own pieces for standard moves"
        )
        self.assertEqual(
            get_king_moves(board_init, 7,4, WHITE, DEFAULT_HAS_MOVED_FALSE, True), [],
            "WK e1 initially blocked (attack check, no castling)"
        )

        empty_board = [[None for _ in range(8)] for _ in range(8)]
        empty_board[3][3] = (KING, WHITE)
        # For a king at (3,3) not on its starting square, its 'has_moved' status for 'WK' should be True.
        king_has_moved_custom_d5 = {**copy.deepcopy(DEFAULT_HAS_MOVED_FALSE), 'WK': True}
        king_moves_d5 = get_king_moves(empty_board, 3, 3, WHITE, king_has_moved_custom_d5, False)
        self.assertEqual(
            len(king_moves_d5),
            8, "King at d5 on empty board should have 8 standard moves"
        )
        self.assertIn( ((3,3),(2,2),None), king_moves_d5, "Example king move format incorrect")

        empty_board_corner = [[None for _ in range(8)] for _ in range(8)]
        empty_board_corner[0][0] = (KING, WHITE)
        king_has_moved_custom_a8 = {**copy.deepcopy(DEFAULT_HAS_MOVED_FALSE), 'WK': True} # Not its home square
        self.assertEqual(
            len(get_king_moves(empty_board_corner, 0, 0, WHITE, king_has_moved_custom_a8, False)),
            3, "King at a8 on empty board should have 3 standard moves"
        )

        board_captures_valid = setup_board([
            ((3,3), (KING, WHITE)), ((2,2), (PAWN, BLACK)), ((2,3), (PAWN, WHITE)),
            ((2,4), (ROOK, BLACK)), ((3,2), (BISHOP, WHITE)), ((3,4), (KNIGHT, BLACK)),
            ((4,2), (QUEEN, BLACK)), ((4,4), (PAWN, BLACK))
        ])
        # Use a state where the White King is considered to have moved (e.g., 'WK': True)
        # DEFAULT_KING_MOVED_STATE already has 'WK':True.
        moves = get_king_moves(board_captures_valid, 3,3, WHITE,
                               DEFAULT_KING_MOVED_STATE, False)
        expected = [
            ((3,3), (2,2), None), ((3,3), (2,4), None), ((3,3), (3,4), None),
            ((3,3), (4,2), None), ((3,3), (4,4), None), ((3,3), (4,3), None)
        ]
        self.assertCountEqual(moves, expected,
                              "King should capture available pieces and move to empty squares")

if __name__ == '__main__':
    unittest.main()
