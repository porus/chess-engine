"""
Chess Engine Module

A pure Python chess engine implementing standard chess rules, move validation,
check/checkmate detection, and AI opponents.

This module provides:
- Complete chess rule implementation (FIDE tournament rules)
- Move generation and validation
- Check, checkmate, and stalemate detection
- AI move selection (random and greedy algorithms)
- Position evaluation
- Game state management

Usage:
    from chess_engine import (
        initialize_board,
        play_game,
        make_move,
        is_move_truly_legal,
        get_all_legal_moves,
        # ... other functions
    )

Constants:
    WHITE, BLACK - Player colors
    PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING - Piece types
"""

# Re-export all public functions and constants from core module
from chess_engine.core import (
    # Constants
    WHITE,
    BLACK,
    PAWN,
    ROOK,
    KNIGHT,
    BISHOP,
    QUEEN,
    KING,
    PIECE_VALUES,
    VALID_PROMOTION_CHOICES,
    
    # Position hashing and analysis
    get_position_hash,
    is_insufficient_material,
    is_fifty_move_draw,
    is_threefold_repetition,
    
    # Board operations
    initialize_board,
    display_board,
    
    # Move parsing and validation
    parse_move,
    is_square_attacked,
    find_king,
    is_in_check,
    is_move_pseudo_legal,
    is_move_truly_legal,
    
    # Move generation
    get_pawn_moves,
    get_rook_moves,
    get_knight_moves,
    get_bishop_moves,
    get_queen_moves,
    get_king_moves,
    get_all_legal_moves,
    
    # Piece-specific move functions (internal)
    PIECE_MOVE_FUNCTIONS,
    
    # Move execution
    make_move,
    
    # Game state checking
    is_checkmate,
    is_stalemate,
    
    # AI and evaluation
    evaluate_board,
    get_random_ai_move,
    get_greedy_ai_move,
    
    # Game loop
    play_game,
)

__all__ = [
    # Constants
    "WHITE",
    "BLACK",
    "PAWN",
    "ROOK",
    "KNIGHT",
    "BISHOP",
    "QUEEN",
    "KING",
    "PIECE_VALUES",
    "VALID_PROMOTION_CHOICES",
    
    # Position hashing and analysis
    "get_position_hash",
    "is_insufficient_material",
    "is_fifty_move_draw",
    "is_threefold_repetition",
    
    # Board operations
    "initialize_board",
    "display_board",
    
    # Move parsing and validation
    "parse_move",
    "is_square_attacked",
    "find_king",
    "is_in_check",
    "is_move_pseudo_legal",
    "is_move_truly_legal",
    
    # Move generation
    "get_pawn_moves",
    "get_rook_moves",
    "get_knight_moves",
    "get_bishop_moves",
    "get_queen_moves",
    "get_king_moves",
    "get_all_legal_moves",
    "PIECE_MOVE_FUNCTIONS",
    
    # Move execution
    "make_move",
    
    # Game state checking
    "is_checkmate",
    "is_stalemate",
    
    # AI and evaluation
    "evaluate_board",
    "get_random_ai_move",
    "get_greedy_ai_move",
    
    # Game loop
    "play_game",
]

__version__ = "2.0.0"
__author__ = "Chess Engine Team"
