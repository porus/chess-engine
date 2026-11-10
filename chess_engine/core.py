# pylint: disable=too-many-lines, too-many-instance-attributes, too-many-arguments, too-many-locals, too-many-branches, too-many-statements
# Player constants
WHITE = "white"
BLACK = "black"

# Piece constants
PAWN = "P"
ROOK = "R"
KNIGHT = "N"
BISHOP = "B"
QUEEN = "Q"
KING = "K"

PIECE_VALUES = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 0}
VALID_PROMOTION_CHOICES = [QUEEN, ROOK, BISHOP, KNIGHT]


def get_position_hash(board, current_player, has_moved_dict, en_passant_target=None):
    """
    Generate a hash of the current position for repetition detection.
    Includes board state, current player, castling rights, and en passant target.
    
    Args:
        board (list): The 8x8 board.
        current_player (str): Current player's color.
        has_moved_dict (dict): Castling rights tracking.
        en_passant_target (tuple|None): En passant target square (row, col) or None.
    
    Returns:
        str: A string representing the position.
    """
    # Board representation
    board_str = ""
    for row in board:
        for square in row:
            if square is None:
                board_str += "."
            else:
                piece_type, color = square
                # Use uppercase for white, lowercase for black
                piece_char = piece_type if color == WHITE else piece_type.lower()
                board_str += piece_char
    
    # Castling rights
    castling = ""
    if not has_moved_dict.get('WK', True) and not has_moved_dict.get('WR_h1', True):
        castling += "K"
    if not has_moved_dict.get('WK', True) and not has_moved_dict.get('WR_a1', True):
        castling += "Q"
    if not has_moved_dict.get('BK', True) and not has_moved_dict.get('BR_h8', True):
        castling += "k"
    if not has_moved_dict.get('BK', True) and not has_moved_dict.get('BR_a8', True):
        castling += "q"
    if not castling:
        castling = "-"
    
    # En passant target
    ep_str = "-"
    if en_passant_target:
        ep_col = chr(ord('a') + en_passant_target[1])
        ep_row = str(8 - en_passant_target[0])
        ep_str = ep_col + ep_row
    
    return f"{board_str}|{current_player}|{castling}|{ep_str}"


def is_insufficient_material(board):
    """
    Check if the position has insufficient material for checkmate.
    Returns True for:
    - King vs King
    - King + Bishop vs King
    - King + Knight vs King
    - King + Bishop vs King + Bishop (same color squares)
    
    Args:
        board (list): The 8x8 board.
    
    Returns:
        bool: True if insufficient material, False otherwise.
    """
    pieces = []
    for row in board:
        for square in row:
            if square and square[0] != KING:
                pieces.append(square)
    
    # King vs King
    if len(pieces) == 0:
        return True
    
    # King + minor piece vs King
    if len(pieces) == 1:
        piece_type = pieces[0][0]
        if piece_type in [BISHOP, KNIGHT]:
            return True
    
    # King + Bishop vs King + Bishop (same color)
    if len(pieces) == 2:
        if all(p[0] == BISHOP for p in pieces):
            # Find bishop positions to check square colors
            bishop_positions = []
            for r, row in enumerate(board):
                for c, square in enumerate(row):
                    if square and square[0] == BISHOP:
                        bishop_positions.append((r, c))
            if len(bishop_positions) == 2:
                # Bishops on same color squares if (r+c) has same parity
                color1 = (bishop_positions[0][0] + bishop_positions[0][1]) % 2
                color2 = (bishop_positions[1][0] + bishop_positions[1][1]) % 2
                if color1 == color2:
                    return True
    
    return False


def is_fifty_move_draw(halfmove_clock):
    """
    Check if the game is a draw due to the 50-move rule.
    A draw can be claimed if 50 moves (100 half-moves) have been made
    without a pawn move or capture.
    
    Args:
        halfmove_clock (int): Number of half-moves since last pawn move or capture.
    
    Returns:
        bool: True if 50 moves without pawn move/capture, False otherwise.
    """
    return halfmove_clock >= 100


def is_threefold_repetition(position_history):
    """
    Check if the current position has occurred three times (threefold repetition).
    
    Args:
        position_history (list): List of position hashes from the game.
    
    Returns:
        bool: True if current position occurred 3+ times, False otherwise.
    """
    if not position_history or len(position_history) < 3:
        return False
    
    current_position = position_history[-1]
    count = position_history.count(current_position)
    return count >= 3


def initialize_board():
    """
    Initializes the chess board with pieces in their starting positions.

    Returns:
        list: An 8x8 list of lists representing the board.
              Each inner list is a rank (row).
              Each element is either None (empty) or a tuple (PIECE_TYPE, PLAYER_COLOR).
    """
    board = [[None for _ in range(8)] for _ in range(8)]

    # Place pawns
    for i in range(8):
        board[1][i] = (PAWN, BLACK)
        board[6][i] = (PAWN, WHITE)

    # Place rooks, knights, bishops, queen, king for black
    board[0] = [
        (ROOK, BLACK), (KNIGHT, BLACK), (BISHOP, BLACK), (QUEEN, BLACK),
        (KING, BLACK), (BISHOP, BLACK), (KNIGHT, BLACK), (ROOK, BLACK)
    ]
    # Place rooks, knights, bishops, queen, king for white
    board[7] = [
        (ROOK, WHITE), (KNIGHT, WHITE), (BISHOP, WHITE), (QUEEN, WHITE),
        (KING, WHITE), (BISHOP, WHITE), (KNIGHT, WHITE), (ROOK, WHITE)
    ]
    return board


def display_board(board):
    """
    Displays the chess board in a human-readable format.
    Uppercase char for white pieces, lowercase char for black pieces.
    'W' or 'b' prefix before piece type.
    Ranks are 1-8 (chess notation), files are a-h.

    Args:
        board (list): The 8x8 board.
    """
    files_label = "  a  b  c  d  e  f  g  h"
    separator_line = " +" + "---"*8 + "-+"

    print(files_label)
    print(separator_line)
    for i, rank_data in enumerate(board):
        display_rank_number = 8 - i
        row_str = f"{display_rank_number}| "
        for square_content in rank_data:
            if square_content is None:
                row_str += ".  "
            else:
                piece_type, piece_color = square_content
                if piece_color == WHITE:
                    row_str += f"W{piece_type} "
                else:  # BLACK
                    row_str += f"b{piece_type} "
        print(row_str + f"|{display_rank_number}")
    print(separator_line)
    print(files_label)


def parse_move(move_str):
    """
    Parses a move string (e.g., "e2e4", "e7e8q") into start and end positions,
    and an optional promotion piece.

    Args:
        move_str (str): The move string.

    Returns:
        tuple | None: A tuple ((start_row, start_col), (end_row, end_col), promotion_piece)
                      or None if the format is invalid.
                      promotion_piece is None if not specified or not applicable.
    """
    if not isinstance(move_str, str) or not (4 <= len(move_str) <= 5):
        return None

    try:
        start_col_char = move_str[0]
        start_row_char = move_str[1]
        end_col_char = move_str[2]
        end_row_char = move_str[3]

        promotion_piece_char = None
        if len(move_str) == 5:
            promotion_piece_char = move_str[4].upper()
            if promotion_piece_char not in VALID_PROMOTION_CHOICES:
                return None # Invalid promotion piece

        start_col = ord(start_col_char) - ord('a')
        start_row = 8 - int(start_row_char)
        end_col = ord(end_col_char) - ord('a')
        end_row = 8 - int(end_row_char)

        if not (0 <= start_col <= 7 and 0 <= start_row <= 7 and \
                0 <= end_col <= 7 and 0 <= end_row <= 7):
            return None # Coordinates out of bounds

        return ((start_row, start_col), (end_row, end_col), promotion_piece_char)
    except (ValueError, IndexError):
        return None


def is_on_board(row, col):
    """
    Checks if a given row and column are within the board boundaries.

    Args:
        row (int): The row index.
        col (int): The column index.

    Returns:
        bool: True if (row, col) is on the board, False otherwise.
    """
    return 0 <= row <= 7 and 0 <= col <= 7


def _get_sliding_piece_moves(board, row, col, directions, current_player_color):
    """
    Helper function to get moves for sliding pieces (Rook, Bishop, Queen).

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the piece.
        col (int): The starting column of the piece.
        directions (list): A list of (dr, dc) tuples for movement.
        current_player_color (str): The color of the current player.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    moves = []
    for dr, dc in directions:
        for i in range(1, 8):
            end_row, end_col = row + dr * i, col + dc * i
            if not is_on_board(end_row, end_col):
                break
            target_square = board[end_row][end_col]
            if target_square is None:
                moves.append( ((row, col), (end_row, end_col), None) )
            else:
                if target_square[1] != current_player_color:
                    moves.append( ((row, col), (end_row, end_col), None) ) # Capture
                break # Blocked by a piece
    return moves


def get_pawn_moves(board, row, col, player_color, for_attacking_check=False, en_passant_target=None):
    """
    Gets all pseudo-legal pawn moves. Does not consider checks.
    Handles single/double forward moves, diagonal captures, and en passant.
    Does NOT handle promotion move generation directly here,
    promotion variants are handled in get_all_legal_moves.

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the pawn.
        col (int): The starting column of the pawn.
        player_color (str): The color of the pawn.
        for_attacking_check (bool): If True, only generates attacking moves.
                                    This is used for is_square_attacked.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    moves = []
    direction = -1 if player_color == WHITE else 1
    start_rank = 6 if player_color == WHITE else 1

    # Forward moves (only if not for_attacking_check)
    if not for_attacking_check:
        # Single square forward
        if is_on_board(row + direction, col) and \
           board[row + direction][col] is None:
            moves.append( ((row, col), (row + direction, col), None) )
            # Double square forward from starting rank
            if row == start_rank and \
               is_on_board(row + 2 * direction, col) and \
               board[row + 2 * direction][col] is None:
                moves.append( ((row, col), (row + 2 * direction, col), None) )

    # Diagonal captures
    for dc in [-1, 1]:
        end_row, end_col = row + direction, col + dc
        if is_on_board(end_row, end_col):
            target_square = board[end_row][end_col]
            if for_attacking_check: # For is_square_attacked, any piece can be "targeted"
                 # When checking for attacks, a pawn "attacks" the square regardless of occupation
                moves.append( ((row, col), (end_row, end_col), None) )
            elif target_square is not None and target_square[1] != player_color:
                moves.append( ((row, col), (end_row, end_col), None) ) # Capture
            # En passant capture - only valid from rank 5 for white (row 3) or rank 4 for black (row 4)
            elif en_passant_target and (end_row, end_col) == en_passant_target:
                en_passant_rank = 3 if player_color == WHITE else 4
                if row == en_passant_rank:
                    moves.append( ((row, col), (end_row, end_col), None) ) # En passant
    return moves


def get_rook_moves(board, row, col, player_color):
    """
    Gets all pseudo-legal rook moves. Does not consider checks.

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the rook.
        col (int): The starting column of the rook.
        player_color (str): The color of the player whose rook is being moved.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    # _get_sliding_piece_moves uses current_player_color, which is player_color here
    return _get_sliding_piece_moves(board, row, col, directions, player_color)


def get_knight_moves(board, row, col, player_color):
    """
    Gets all pseudo-legal knight moves. Does not consider checks.

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the knight.
        col (int): The starting column of the knight.
        player_color (str): The color of the player whose knight is being moved.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    moves = []
    knight_hops = [
        (1, 2), (1, -2), (-1, 2), (-1, -2),
        (2, 1), (2, -1), (-2, 1), (-2, -1)
    ]
    for dr, dc in knight_hops:
        end_row, end_col = row + dr, col + dc
        if is_on_board(end_row, end_col):
            target_square = board[end_row][end_col]
            # A knight can move to an empty square or capture an opponent's piece.
            # It cannot move to a square occupied by its own piece.
            if target_square is None or target_square[1] != player_color:
                moves.append( ((row, col), (end_row, end_col), None) )
    return moves


def get_bishop_moves(board, row, col, player_color):
    """
    Gets all pseudo-legal bishop moves. Does not consider checks.

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the bishop.
        col (int): The starting column of the bishop.
        player_color (str): The color of the player whose bishop is being moved.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    return _get_sliding_piece_moves(board, row, col, directions, player_color)


def get_queen_moves(board, row, col, player_color):
    """
    Gets all pseudo-legal queen moves. Does not consider checks.

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the queen.
        col (int): The starting column of the queen.
        player_color (str): The color of the player whose queen is being moved.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    # Combines rook and bishop moves
    directions = [
        (0, 1), (0, -1), (1, 0), (-1, 0),  # Rook directions
        (1, 1), (1, -1), (-1, 1), (-1, -1) # Bishop directions
    ]
    return _get_sliding_piece_moves(board, row, col, directions, player_color)


def get_king_moves(board, row, col, piece_player_color, has_moved_state, for_attacking_check=False):
    """
    Gets all pseudo-legal king moves, including castling if conditions are met.
    Does not consider if the king moves into check for regular moves,
    but does for castling path/landing squares.
    All returned moves are 3-part tuples: ((start_r, start_c), (end_r, end_c), None).

    Args:
        board (list): The 8x8 board.
        row (int): The starting row of the king.
        col (int): The starting column of the king.
        piece_player_color (str): The color of the king. (Changed from player_color for clarity)
        has_moved_state (dict): Tracks if king/rooks have moved.
        for_attacking_check (bool): If True, only standard king moves are returned
                                    (no castling), for use in is_square_attacked.

    Returns:
        list: A list of 3-part move tuples ((start_r, start_c), (end_r, end_c), None).
    """
    moves = []
    # Standard king moves
    king_hops = [
        (0, 1), (0, -1), (1, 0), (-1, 0),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    for dr, dc in king_hops:
        end_row, end_col = row + dr, col + dc
        if is_on_board(end_row, end_col):
            target_square = board[end_row][end_col]
            if target_square is None or target_square[1] != piece_player_color:
                moves.append(((row, col), (end_row, end_col), None))

    if for_attacking_check: # Castling moves are not attacking moves
        return moves

    # Castling logic
    king_initial_col = 4 # King's 'e' file
    king_initial_row = 7 if piece_player_color == WHITE else 0

    # 1. King must be on its starting square
    if row != king_initial_row or col != king_initial_col:
        return moves

    king_char = 'WK' if piece_player_color == WHITE else 'BK'
    opponent_color = BLACK if piece_player_color == WHITE else WHITE

    # 2. King must not have moved
    if has_moved_state.get(king_char, True): # Default to True (moved) if not in dict
        return moves

    # 3. King must not be in check
    if is_in_check(board, piece_player_color, has_moved_state):
        return moves

    # Kingside Castling (O-O)
    kingside_rook_char = 'WR_h1' if piece_player_color == WHITE else 'BR_h8'
    # 4. Kingside rook must not have moved
    # 5. Squares between king and kingside rook must be empty (f-file, g-file)
    # 6. Kingside rook must be present
    if not has_moved_state.get(kingside_rook_char, True) and \
       board[king_initial_row][5] is None and \
       board[king_initial_row][6] is None and \
       board[king_initial_row][7] == (ROOK, piece_player_color):
        # 7. King must not pass through an attacked square (f-file)
        # 8. King must not land on an attacked square (g-file)
        if not is_square_attacked(board, king_initial_row, 5, opponent_color, has_moved_state, True) and \
           not is_square_attacked(board, king_initial_row, 6, opponent_color, has_moved_state, True):
            moves.append(((king_initial_row, king_initial_col), (king_initial_row, 6), None))

    # Queenside Castling (O-O-O)
    queenside_rook_char = 'WR_a1' if piece_player_color == WHITE else 'BR_a8'
    # 4. Queenside rook must not have moved
    # 5. Squares between king and queenside rook must be empty (b-file, c-file, d-file)
    # 6. Queenside rook must be present
    if not has_moved_state.get(queenside_rook_char, True) and \
       board[king_initial_row][1] is None and \
       board[king_initial_row][2] is None and \
       board[king_initial_row][3] is None and \
       board[king_initial_row][0] == (ROOK, piece_player_color):
        # 7. King must not pass through an attacked square (d-file)
        # 8. King must not land on an attacked square (c-file)
        # (King's current square e-file already confirmed not attacked by is_in_check)
        if not is_square_attacked(board, king_initial_row, 3, opponent_color, has_moved_state, True) and \
           not is_square_attacked(board, king_initial_row, 2, opponent_color, has_moved_state, True):
            moves.append(((king_initial_row, king_initial_col), (king_initial_row, 2), None))

    return moves


PIECE_MOVE_FUNCTIONS = {
    PAWN: lambda b, r, c, pc, hms, fa, ept=None: get_pawn_moves(b, r, c, pc, for_attacking_check=fa, en_passant_target=ept),
    ROOK: lambda b, r, c, pc, hms, fa, ept=None: get_rook_moves(b, r, c, pc), # hms, fa, ept ignored
    KNIGHT: lambda b, r, c, pc, hms, fa, ept=None: get_knight_moves(b, r, c, pc), # hms, fa, ept ignored
    BISHOP: lambda b, r, c, pc, hms, fa, ept=None: get_bishop_moves(b, r, c, pc), # hms, fa, ept ignored
    QUEEN: lambda b, r, c, pc, hms, fa, ept=None: get_queen_moves(b, r, c, pc), # hms, fa, ept ignored
    KING: lambda b, r, c, pc, hms, fa, ept=None: get_king_moves(b, r, c, pc, hms, for_attacking_check=fa),
    # Note: For KING, 'pc' (player_color from the caller like is_move_pseudo_legal) is passed as
    # 'piece_player_color' to get_king_moves. ept parameter added for consistency.
}


def is_square_attacked(board, target_row, target_col, attacker_color,
                       has_moved_state_for_king_moves, for_castling_check=False): # pylint: disable=too-many-arguments,unused-argument
    """
    Checks if a given square is attacked by any of the attacker's pieces.
    All piece move functions now return 3-part tuples.

    Args:
        board (list): The 8x8 board.
        target_row (int): The row of the square to check.
        target_col (int): The column of the square to check.
        attacker_color (str): The color of the pieces that might be attacking.
        has_moved_state_for_king_moves (dict): State for king moves.
        for_castling_check (bool): If True, this is for castling safety. (unused by current direct logic but good for context)

    Returns:
        bool: True if the square is attacked, False otherwise.
    """
    # The for_castling_check parameter isn't directly used in this function's logic anymore
    # because get_king_moves itself now has a for_attacking_check parameter which
    # is set to True when called from here, preventing castling moves from being considered attacks.
    # However, keeping it in the signature can be useful if other parts of the code
    # make decisions based on whether this is a castling-related check.

    for r_start in range(8):
        for c_start in range(8):
            piece_data = board[r_start][c_start]
            if piece_data is not None and piece_data[1] == attacker_color:
                piece_type, _ = piece_data

                # Get the appropriate move function from the dictionary
                # The lambda includes the necessary for_attacking_check=True for pawn/king
                move_func = PIECE_MOVE_FUNCTIONS[piece_type]

                # Call the move function with for_attacking_check=True for pawn and king
                # Other pieces' lambdas ignore the 'fa' (for_attacking_check) argument or handle it internally
                # if their base functions were changed (they weren't for this example).
                # King moves need has_moved_state. Pawn needs for_attacking_check.
                # The lambdas handle passing the correct arguments or ignoring unused ones.
                # En passant is not relevant for attack checking (pawns attack diagonally regardless)
                possible_moves = move_func(board, r_start, c_start, attacker_color,
                                           hms=has_moved_state_for_king_moves,
                                           fa=True, ept=None) # fa=True for attack checks, ept=None

                for move in possible_moves:
                    # All move functions now return 3-part tuples
                    # ((start_r, start_c), (end_r, end_c), promo_or_None)
                    _s, end_pos, _p = move
                    if end_pos == (target_row, target_col):
                        return True
    return False


def find_king(board, player_color):
    """
    Finds the king of the specified color on the board.

    Args:
        board (list): The 8x8 board.
        player_color (str): The color of the king to find.

    Returns:
        tuple | None: (row, col) of the king, or None if not found.
    """
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == KING and piece[1] == player_color:
                return (r, c)
    return None # Should not happen in a valid game state


def is_in_check(board, player_color, has_moved_state):
    """
    Checks if the specified player is currently in check.

    Args:
        board (list): The 8x8 board.
        player_color (str): The color of the player to check.
        has_moved_state (dict): Tracks if king/rooks have moved.

    Returns:
        bool: True if the player is in check, False otherwise.
    """
    king_pos = find_king(board, player_color)
    if not king_pos:
        return False # Or raise error, king should always be on board
    opponent_color = BLACK if player_color == WHITE else WHITE
    return is_square_attacked(board, king_pos[0], king_pos[1], opponent_color, has_moved_state)


def make_move(board, move_tuple, has_moved_dict, en_passant_target=None, 
              halfmove_clock=0, position_history=None, current_player=None):
    """
    Makes a move on the board and updates the has_moved_dict.
    Handles regular moves, captures, castling, pawn promotion, and en passant.
    It now robustly handles move_tuple which must be a 3-part tuple.

    Args:
        board (list): The 8x8 board (will be modified).
        move_tuple (tuple): A 3-part tuple:
                            ((start_row, start_col), (end_row, end_col), promotion_piece_or_None).
                            For castling, end_col is the king's destination.
        has_moved_dict (dict): Tracks if king/rooks have moved (will be modified).
        en_passant_target (tuple|None): Current en passant target square (row, col) or None.
        halfmove_clock (int): Current halfmove clock for 50-move rule.
        position_history (list|None): List of position hashes for threefold repetition.
        current_player (str|None): Current player color (for position hashing).

    Returns:
        dict: Dictionary with keys:
            - 'en_passant_target': New en passant target or None
            - 'halfmove_clock': Updated halfmove clock
            - 'position_history': Updated position history (if provided)
    """
    if not (isinstance(move_tuple, tuple) and len(move_tuple) == 3 and
            isinstance(move_tuple[0], tuple) and len(move_tuple[0]) == 2 and
            isinstance(move_tuple[1], tuple) and len(move_tuple[1]) == 2):
        # This indicates an internal error if make_move is called with an invalid tuple format.
        # print(f"Critical Error: make_move called with invalid move_tuple: {move_tuple}")
        # Consider raising an error here. For now, try to proceed if tests expect graceful failure.
        return # Or raise ValueError("Invalid move_tuple format for make_move")

    start_pos, end_pos, promotion_choice = move_tuple
    start_row, start_col = start_pos
    end_row, end_col = end_pos

    moving_piece_data = board[start_row][start_col]

    if moving_piece_data is None:
        # This should ideally be caught by legality checks before calling make_move
        # print(f"Error: No piece at starting square {start_pos} for move {move_tuple}")
        return

    piece_type, piece_color = moving_piece_data

    # Check if this is a capture BEFORE modifying the board
    is_capture = (board[end_row][end_col] is not None)
    is_pawn_move = (piece_type == PAWN)

    # Update board
    board[end_row][end_col] = moving_piece_data
    board[start_row][start_col] = None

    # Track new en passant target (will be set below if pawn moves 2 squares)
    new_en_passant_target = None

    # Handle en passant capture (pawn moves diagonally to empty square)
    if piece_type == PAWN:
        if end_col != start_col and en_passant_target and (end_row, end_col) == en_passant_target:
            # En passant capture: remove the captured pawn (one rank behind destination)
            captured_pawn_row = start_row  # Captured pawn is on same row as moving pawn
            board[captured_pawn_row][end_col] = None
            is_capture = True  # En passant is a capture
        
        # Track 2-square pawn move for next turn's en passant opportunity
        if abs(end_row - start_row) == 2:
            # Pawn moved 2 squares, set en passant target to square it passed over
            new_en_passant_target = ((start_row + end_row) // 2, start_col)

    # Handle pawn promotion
    if piece_type == PAWN and promotion_choice:
        # Ensure promotion_choice is one of the valid types (Q, R, B, N)
        if promotion_choice in VALID_PROMOTION_CHOICES:
            board[end_row][end_col] = (promotion_choice, piece_color)
        # Else: if not valid, it's an issue, but make_move assumes valid input for now

    # Handle castling: move the rook as well
    if piece_type == KING:
        # King moved from e1/e8
        if start_col == 4 and abs(end_col - start_col) == 2:
            # Kingside castling (king moves to g-file, col 6)
            if end_col == 6:
                rook_start_col, rook_end_col = 7, 5
            # Queenside castling (king moves to c-file, col 2)
            else: # end_col == 2
                rook_start_col, rook_end_col = 0, 3
            rook = board[start_row][rook_start_col]
            board[start_row][rook_end_col] = rook
            board[start_row][rook_start_col] = None

    # Update has_moved_dict
    king_char = 'WK' if piece_color == WHITE else 'BK' # Covers king's own move for castling too

    if piece_type == KING:
        has_moved_dict[king_char] = True
        # If castling, also mark the corresponding rook as moved
        if start_col == 4 and abs(end_col - start_col) == 2: # King made a 2-square move (castling)
            if end_col == 6: # Kingside
                rook_char = 'WR_h1' if piece_color == WHITE else 'BR_h8'
                has_moved_dict[rook_char] = True
            elif end_col == 2: # Queenside
                rook_char = 'WR_a1' if piece_color == WHITE else 'BR_a8'
                has_moved_dict[rook_char] = True
    elif piece_type == ROOK:
        # Standard rook move updates (original squares only)
        if piece_color == WHITE:
            if start_pos == (7, 0): # a1
                has_moved_dict['WR_a1'] = True
            elif start_pos == (7, 7): # h1
                has_moved_dict['WR_h1'] = True
        else: # BLACK
            if start_pos == (0, 0): # a8
                has_moved_dict['BR_a8'] = True
            elif start_pos == (0, 7): # h8
                has_moved_dict['BR_h8'] = True
    
    # Update halfmove clock (50-move rule tracking)
    # Reset clock on pawn move or capture, otherwise increment
    if is_pawn_move or is_capture:
        new_halfmove_clock = 0
    else:
        new_halfmove_clock = halfmove_clock + 1
    
    # Update position history (threefold repetition tracking)
    new_position_history = position_history[:] if position_history else []
    if current_player:
        # Add new position hash after the move
        # Next player's turn, so switch player for hash
        next_player = BLACK if current_player == WHITE else WHITE
        position_hash = get_position_hash(board, next_player, has_moved_dict, new_en_passant_target)
        new_position_history.append(position_hash)
    
    # Return format depends on whether advanced tracking is enabled
    if position_history is not None or halfmove_clock != 0:
        # Return full dict for tournament rules tracking
        return {
            'en_passant_target': new_en_passant_target,
            'halfmove_clock': new_halfmove_clock,
            'position_history': new_position_history
        }
    # Backward compatibility: return just en_passant_target
    return new_en_passant_target


def is_move_pseudo_legal(board, move_tuple, current_player_color, has_moved_state, en_passant_target=None):
    """
    Checks if a move is pseudo-legal (follows piece movement rules,
    but doesn't check for leaving the king in check).
    Assumes move_tuple is a 3-part tuple as per standardization.

    Args:
        board (list): The 8x8 board.
        move_tuple (tuple): A 3-part tuple ((start_r, start_c), (end_r, end_c), promo_choice_or_None).
        current_player_color (str): The color of the player making the move.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        bool: True if the move is pseudo-legal, False otherwise.
    """
    start_pos, end_pos, _ = move_tuple # promo_choice not directly used for this check
    start_row, start_col = start_pos

    piece_data = board[start_row][start_col]
    if not piece_data or piece_data[1] != current_player_color:
        return False

    piece_type, piece_actual_color = piece_data
    if piece_actual_color != current_player_color: # Should be redundant due to above check
        return False

    move_func = PIECE_MOVE_FUNCTIONS.get(piece_type)
    if not move_func: # Should not happen
        return False

    # All piece_move_functions now expect player_color and return 3-part tuples.
    # The lambda in PIECE_MOVE_FUNCTIONS handles passing has_moved_state and for_attacking_check.
    # For pseudo-legality, for_attacking_check is False.
    generated_moves = move_func(board, start_row, start_col, current_player_color,
                                hms=has_moved_state, fa=False, ept=en_passant_target)

    for gen_move in generated_moves:
        # gen_move is ((s_r,s_c),(e_r,e_c),None)
        g_start_pos, g_end_pos, _g_promo = gen_move
        if g_start_pos == start_pos and g_end_pos == end_pos:
            # This check is sufficient for pseudo-legality.
            # Promotion piece specifics are handled by get_all_legal_moves / is_move_truly_legal.
            return True
    return False


def is_move_truly_legal(board, move_tuple, current_player_color, has_moved_state, en_passant_target=None):
    """
    Checks if a move is truly legal (i.e., it's pseudo-legal AND
    it does not leave the player's own king in check).
    Expects move_tuple to be a 3-part tuple.

    Args:
        board (list): The 8x8 board.
        move_tuple (tuple): A 3-part tuple ((start_r, start_c), (end_r, end_c), promo_choice_or_None).
        current_player_color (str): The color of the player making the move.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        bool: True if the move is truly legal, False otherwise.
    """
    if not is_move_pseudo_legal(board, move_tuple, current_player_color, has_moved_state, en_passant_target):
        return False

    # Simulate the move on a temporary board
    # Deep copy of the board
    # Need to copy inner lists as well
    temp_board = [rank[:] for rank in board]
    # Deep copy of has_moved_state (dicts are mutable)
    temp_has_moved_state = has_moved_state.copy()

    make_move(temp_board, move_tuple, temp_has_moved_state, en_passant_target)

    # Check if the current player's king is in check on the temp_board
    # The has_moved_state for is_in_check should be the one *after* the move.
    if is_in_check(temp_board, current_player_color, temp_has_moved_state):
        return False # Move is illegal because it leaves king in check

    return True


def get_all_legal_moves(board, player_color, has_moved_state, en_passant_target=None):
    """
    Gets all truly legal moves for the specified player.
    This includes handling pawn promotions by generating all 4 variants.

    Args:
        board (list): The 8x8 board.
        player_color (str): The color of the player whose moves to get.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        list: A list of 3-part truly legal move tuples
              ((start_r, start_c), (end_r, end_c), promo_choice_or_None).
    """
    legal_moves = []
    for r_start in range(8):
        for c_start in range(8):
            piece_data = board[r_start][c_start]
            if piece_data and piece_data[1] == player_color:
                piece_type, piece_actual_color = piece_data # piece_actual_color is player_color here

                move_func = PIECE_MOVE_FUNCTIONS[piece_type]

                # Generate base pseudo-legal moves. These are now all 3-part tuples.
                # The lambda in PIECE_MOVE_FUNCTIONS handles passing hms and fa.
                # For generating actual moves, for_attacking_check is False.
                base_moves = move_func(board, r_start, c_start, piece_actual_color,
                                       hms=has_moved_state, fa=False, ept=en_passant_target)

                for move_candidate in base_moves:
                    # move_candidate is ((s_r,s_c),(e_r,e_c), None from piece funcs)
                    # except for king's castling which is also ((s_r,s_c),(king_dest_r,king_dest_c), None)

                    start_pos, end_pos, _ = move_candidate # Original promo part is None

                    # Handle pawn promotion specifically
                    is_pawn = piece_type == PAWN
                    promotion_rank_reached = (player_color == WHITE and end_pos[0] == 0) or \
                                             (player_color == BLACK and end_pos[0] == 7)

                    if is_pawn and promotion_rank_reached:
                        for promo_choice in VALID_PROMOTION_CHOICES:
                            # Create a new 3-part tuple for each promotion variant
                            promotion_move_tuple = (start_pos, end_pos, promo_choice)
                            if is_move_truly_legal(board, promotion_move_tuple,
                                                   player_color, has_moved_state, en_passant_target):
                                legal_moves.append(promotion_move_tuple)
                    else:
                        # For non-promotion moves (including king's castling from get_king_moves)
                        # move_candidate is already the correct 3-part tuple with None as promo.
                        if is_move_truly_legal(board, move_candidate,
                                               player_color, has_moved_state, en_passant_target):
                            legal_moves.append(move_candidate)
    return legal_moves


def is_checkmate(board, player_color, has_moved_state, en_passant_target=None):
    """
    Checks if the specified player is in checkmate.

    Args:
        board (list): The 8x8 board.
        player_color (str): The color of the player to check for checkmate.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        bool: True if the player is in checkmate, False otherwise.
    """
    if not is_in_check(board, player_color, has_moved_state):
        return False # Not in check, so not checkmate
    # Player is in check, check if they have any legal moves
    return not get_all_legal_moves(board, player_color, has_moved_state, en_passant_target)


def is_stalemate(board, player_color, has_moved_state, en_passant_target=None):
    """
    Checks if the specified player is in stalemate.

    Args:
        board (list): The 8x8 board.
        player_color (str): The color of the player to check for stalemate.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        bool: True if the player is in stalemate, False otherwise.
    """
    if is_in_check(board, player_color, has_moved_state):
        return False # In check, so not stalemate (could be checkmate)
    # Player is not in check, check if they have any legal moves
    return not get_all_legal_moves(board, player_color, has_moved_state, en_passant_target)


def evaluate_board(board):
    """
    Evaluates the board from White's perspective.
    Positive score means White is ahead, negative means Black is ahead.

    Args:
        board (list): The 8x8 board.

    Returns:
        int: The material score of the board.
    """
    score = 0
    for r in range(8):
        for c in range(8):
            piece_data = board[r][c]
            if piece_data:
                piece_type, piece_color = piece_data
                value = PIECE_VALUES[piece_type]
                if piece_color == WHITE:
                    score += value
                else:
                    score -= value
    return score


def get_random_ai_move(board, ai_player_color, has_moved_state, en_passant_target=None):
    """
    Selects a random legal move for the AI.

    Args:
        board (list): The 8x8 board.
        ai_player_color (str): The color of the AI player.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        tuple | None: A legal move tuple ((start_r, start_c), (end_r, end_c), promo_choice)
                      or None if no legal moves exist.
    """
    import random # pylint: disable=import-outside-toplevel
    legal_moves = get_all_legal_moves(board, ai_player_color, has_moved_state, en_passant_target)
    return random.choice(legal_moves) if legal_moves else None


def get_greedy_ai_move(board, ai_player_color, has_moved_state, en_passant_target=None):
    """
    Selects a legal move that results in the best immediate material score for the AI.
    If multiple moves lead to the same best score, one is chosen randomly.

    Args:
        board (list): The 8x8 board.
        ai_player_color (str): The color of the AI player.
        has_moved_state (dict): Tracks if king/rooks have moved.
        en_passant_target (tuple|None): En passant target square (row, col) or None.

    Returns:
        tuple | None: The best legal move tuple or None if no legal moves.
    """
    import random # pylint: disable=import-outside-toplevel
    legal_moves = get_all_legal_moves(board, ai_player_color, has_moved_state, en_passant_target)
    if not legal_moves:
        return None

    best_score = -float('inf') if ai_player_color == WHITE else float('inf')
    best_moves = []

    for move in legal_moves:
        temp_board = [rank[:] for rank in board]
        temp_has_moved_state = has_moved_state.copy()
        make_move(temp_board, move, temp_has_moved_state, en_passant_target)
        score = evaluate_board(temp_board)

        if ai_player_color == WHITE:
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        else: # BLACK
            if score < best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

    return random.choice(best_moves) if best_moves else None


def _get_human_move(current_player, game_board, current_has_moved_state, en_passant_target):
    """Helper function to get and validate human player's move."""
    while True:
        move_str = input(
            f"{current_player}'s turn. Enter move (e.g., e2e4, e1g1 for castle, e7e8q for promo, or 'q' to quit): " # pylint: disable=line-too-long
        ).strip().lower()

        if move_str == 'q':
            return None # Signal to quit

        parsed_move_tuple = parse_move(move_str)
        if not parsed_move_tuple:
            print("Invalid move format. Try again.")
            continue

        start_pos, end_pos, promo_choice = parsed_move_tuple
        piece_at_start = game_board[start_pos[0]][start_pos[1]]

        # Handle pawn promotion choice if not specified in move_str
        if piece_at_start and piece_at_start[0] == PAWN and not promo_choice:
            is_white_promo = current_player == WHITE and start_pos[0] == 1 and end_pos[0] == 0
            is_black_promo = current_player == BLACK and start_pos[0] == 6 and end_pos[0] == 7
            if is_white_promo or is_black_promo:
                while True:
                    promo_input = input(
                        "Promote pawn to (Q, R, B, N): "
                    ).strip().upper()
                    if promo_input in VALID_PROMOTION_CHOICES:
                        promo_choice = promo_input
                        # Reconstruct move_tuple with promotion choice
                        parsed_move_tuple = (start_pos, end_pos, promo_choice)
                        break
                    print("Invalid promotion choice. Try again.")

        if is_move_truly_legal(game_board, parsed_move_tuple,
                               current_player, current_has_moved_state, en_passant_target):
            return parsed_move_tuple
        print("Invalid or illegal move. Try again.")


def _get_ai_move(ai_player_color, game_board, current_has_moved_state, difficulty, en_passant_target):
    """Helper function to get AI's move."""
    print(f"AI ({ai_player_color}, Difficulty: {difficulty}) is thinking...")
    if difficulty == "1": # Easy
        return get_random_ai_move(game_board, ai_player_color, current_has_moved_state, en_passant_target)
    # Default to Greedy for "2" or any other value
    return get_greedy_ai_move(game_board, ai_player_color, current_has_moved_state, en_passant_target)


def play_game():
    """
    Main game loop for the chess game.
    Allows human vs AI play with tournament rules (50-move, threefold repetition).
    """
    game_board = initialize_board()
    # Initialize has_moved state for castling
    # Keys: 'WK', 'WR_a1', 'WR_h1', 'BK', 'BR_a8', 'BR_h8'
    # Value: False if not moved, True if moved.
    current_has_moved_state = {
        'WK': False, 'WR_a1': False, 'WR_h1': False,
        'BK': False, 'BR_a8': False, 'BR_h8': False
    }
    current_player = WHITE
    current_en_passant_target = None  # Track en passant target square
    halfmove_clock = 0  # Track for 50-move rule
    position_history = []  # Track for threefold repetition
    
    # Add initial position
    initial_hash = get_position_hash(game_board, current_player, current_has_moved_state, 
                                     current_en_passant_target)
    position_history.append(initial_hash)
    
    human_player = None
    ai_player = None
    ai_difficulty = "1" # Default to Easy

    # Player color selection
    while human_player not in [WHITE, BLACK]:
        choice = input("Play as (w)hite or (b)lack? ").strip().lower()
        if choice == 'w':
            human_player = WHITE
            ai_player = BLACK
        elif choice == 'b':
            human_player = BLACK
            ai_player = WHITE
        else:
            print("Invalid choice. Enter 'w' or 'b'.")

    # AI difficulty selection
    while True:
        diff_choice = input("Choose AI difficulty: (1) Easy (Random) or (2) Hard (Greedy): ").strip()
        if diff_choice in ["1", "2"]:
            ai_difficulty = diff_choice
            break
        print("Invalid choice. Enter '1' or '2'.")


    while True:
        display_board(game_board)
        print("-" * 20)

        # Check draw conditions
        if is_fifty_move_draw(halfmove_clock):
            print("Draw by 50-move rule! No pawn move or capture in 50 moves.")
            break
        if is_threefold_repetition(position_history):
            print("Draw by threefold repetition! Same position occurred 3 times.")
            break
        if is_insufficient_material(game_board):
            print("Draw by insufficient material!")
            break

        # Check checkmate/stalemate
        if is_checkmate(game_board, current_player, current_has_moved_state):
            print(f"Checkmate! {current_player} loses.")
            break
        if is_stalemate(game_board, current_player, current_has_moved_state):
            print("Stalemate! It's a draw.")
            break
        if is_in_check(game_board, current_player, current_has_moved_state):
            print(f"{current_player} is in check!")

        move_tuple = None
        if current_player == human_player:
            move_tuple = _get_human_move(current_player, game_board, current_has_moved_state,
                                        current_en_passant_target)
            if move_tuple is None: # Human chose to quit
                print(f"{human_player} quit the game.")
                break
        else: # AI's turn
            move_tuple = _get_ai_move(ai_player, game_board, current_has_moved_state,
                                     ai_difficulty, current_en_passant_target)
            if move_tuple:
                start_sq = chr(ord('a')+move_tuple[0][1]) + str(8-move_tuple[0][0])
                end_sq = chr(ord('a')+move_tuple[1][1]) + str(8-move_tuple[1][0])
                promo_str = f" to {move_tuple[2]}" if move_tuple[2] else ""
                print(f"AI ({ai_player}) moves: {start_sq}{end_sq}{promo_str}")
            else: # Should only happen in checkmate/stalemate, already handled
                print(f"AI ({ai_player}) has no moves, but game not over? This is unexpected.")
                # This case should ideally not be reached if checkmate/stalemate works.
                break


        result = make_move(game_board, move_tuple, current_has_moved_state,
                          current_en_passant_target, halfmove_clock, position_history,
                          current_player)
        
        # Update game state from result
        if isinstance(result, dict):
            current_en_passant_target = result['en_passant_target']
            halfmove_clock = result['halfmove_clock']
            position_history = result['position_history']
        else:
            # Backward compatibility (should not happen with new parameters)
            current_en_passant_target = result
        
        current_player = BLACK if current_player == WHITE else WHITE

    print("\nGame Over. Final board:")
    display_board(game_board)
    print(f"Final score (White's perspective): {evaluate_board(game_board)}")
    print("Thanks for playing!")
