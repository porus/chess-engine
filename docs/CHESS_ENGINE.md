# Chess engine notes

The tournament manager does not need an opponent engine to create schedules or calculate results. The repository keeps a separate pure-Python chess module for local play and rule-focused examples.

## State representation

The board is an 8 × 8 list indexed from row 0 at Black's back rank to row 7 at White's back rank. Each occupied square is a `(piece, color)` tuple; empty squares are `None`. A move is `((start_row, start_col), (end_row, end_col), promotion_piece_or_none)`. Coordinates are zero-based internally; the terminal interface accepts coordinates such as `e2e4`.

Castling rights, en-passant state, halfmove count, and position history are supplied explicitly by callers. This keeps rule evaluation deterministic and avoids hidden global game state. `get_all_legal_moves` filters pseudo-legal moves by simulating each move and checking whether the active side's king remains safe.

## Implemented rules

The module handles piece movement, captures, check, checkmate, stalemate, castling, promotion, en passant, position repetition, the fifty-move draw counter, and insufficient material. State updates are covered by the regression suite in `tests/engine/`.

This implementation has not been certified against a complete external chess rules conformance suite. It does not read or write FEN/PGN, include an opening book or tablebases, run a search engine, or implement tournament pairing. The terminal opponent evaluates immediate material only and is intentionally a baseline demo.

## Change guidance

For a rule change, add a small position-based test that demonstrates the relevant legal and illegal moves, then run `python scripts/reviewer_checks.py`. Tournament operation tests live beside the engine tests but exercise the separate `club_tournament` package and temporary SQLite databases.
