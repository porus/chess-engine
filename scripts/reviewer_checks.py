#!/usr/bin/env python3
"""Dependency-light repository audit and deterministic chess-engine checks."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_ENTRIES = {
    ".github", ".gitignore", "LICENSE", "README.md", "SECURITY.md", "THIRD_PARTY_NOTICES.md",
    "chess_engine", "club_tournament", "docs", "main.py", "pyproject.toml", "scripts", "tests",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit_repository() -> None:
    generated = {"__pycache__", ".pytest_cache", ".coverage", "htmlcov"}
    entries = {path.name for path in ROOT.iterdir() if path.name not in generated}
    unexpected = entries - ALLOWED_ROOT_ENTRIES - {".git"}
    missing = ALLOWED_ROOT_ENTRIES - entries
    require(not unexpected and not missing,
            f"Unexpected root entries: {sorted(unexpected)}; missing: {sorted(missing)}")
    git_metadata = ROOT / ".git"
    if git_metadata.exists():
        valid_git_directory = git_metadata.is_dir() and (git_metadata / "HEAD").is_file()
        valid_worktree_pointer = git_metadata.is_file() and git_metadata.read_text(
            encoding="utf-8", errors="replace"
        ).startswith("gitdir: ")
        require(valid_git_directory or valid_worktree_pointer,
                "The .git entry is not a valid repository metadata marker")
    require((ROOT / ".gitignore").is_file(), "Required .gitignore is missing")
    require("MIT License" in (ROOT / "LICENSE").read_text(encoding="utf-8"),
            "MIT license text is missing or malformed")
    require("*.db" in (ROOT / ".gitignore").read_text(encoding="utf-8"),
            "Local database files are not ignored")

    require(not (ROOT / "requirements.txt").exists() and not (ROOT / "requirements-dev.txt").exists(),
            "A requirements file exists; document and audit any future dependencies")
    project_metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    require("dependencies =" not in project_metadata and "optional-dependencies" not in project_metadata,
            "Third-party dependencies are declared; review and document them before adding")

    blocked_suffixes = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".so", ".dll", ".dylib", ".exe", ".bin", ".nnue", ".wasm", ".onnx", ".pt", ".pth", ".zip", ".tar", ".gz"}
    blocked_names = {".env", ".env.test", ".env.docker", ".env.production"}
    forbidden_engine_names = {"stockfish", "stockfish.exe", "stockfish.nnue"}
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        require(path.name not in blocked_names and not path.name.startswith(".env."),
                f"Environment file found at {relative}")
        require(path.name.lower() not in forbidden_engine_names, f"External engine artifact found at {relative}")
        require(path.suffix.lower() not in blocked_suffixes, f"Local data or key file found at {relative}")
        if path.name.endswith(".pyc"):
            continue

    text_extensions = {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".gitignore"}
    source_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in ROOT.rglob("*")
        if path.is_file() and (path.suffix.lower() in text_extensions or path.name == "LICENSE")
    ).lower()
    for marker in ("sk_" + "test_", "wh" + "sec_", "-----begin " + "private key-----"):
        require(marker not in source_text, f"Credential-like marker found: {marker}")


def smoke_checks() -> int:
    sys.path.insert(0, str(ROOT))
    from chess_engine import BLACK, WHITE, get_all_legal_moves, initialize_board, make_move

    board = initialize_board()
    moved = {
        "WK": False, "WR_a1": False, "WR_h1": False,
        "BK": False, "BR_a8": False, "BR_h8": False,
    }
    white_moves = get_all_legal_moves(board, WHITE, moved)
    require(len(board) == 8 and all(len(rank) == 8 for rank in board),
            "Initial board is not an 8 by 8 position")
    require(len(white_moves) == 20, f"Expected 20 opening moves for White, got {len(white_moves)}")
    require(len(set(white_moves)) == len(white_moves), "Move generation returned duplicate legal moves")

    e4 = ((6, 4), (4, 4), None)
    require(e4 in white_moves, "Expected e2-e4 to be legal from the initial position")
    outcome = make_move(board, e4, moved, halfmove_clock=0, position_history=[], current_player=WHITE)
    require(board[4][4] == ("P", WHITE) and board[6][4] is None,
            "Applying e2-e4 did not update the board correctly")
    require(outcome["en_passant_target"] == (5, 4), "Double pawn move did not set en-passant target")
    black_moves = get_all_legal_moves(board, BLACK, moved, outcome["en_passant_target"])
    require(len(black_moves) == 20, f"Expected 20 replies for Black, got {len(black_moves)}")
    require(all(move[0] != (4, 4) for move in black_moves), "Black move list contains a White pawn move")
    return 8


def tournament_smoke_checks() -> int:
    import tempfile
    from pathlib import Path
    from club_tournament import TournamentService

    with tempfile.TemporaryDirectory() as directory:
        service = TournamentService(Path(directory) / "review.sqlite3")
        event_id = service.create_event("Reviewer smoke event")
        service.register_player(event_id, "Player One")
        service.register_player(event_id, "Player Two")
        pairings = service.start_event(event_id)
        require(len(pairings) == 1, "Two registered players must produce one pairing")
        service.record_result(pairings[0]["id"], "draw")
        standings = service.standings(event_id)
        require([row["points"] for row in standings] == [0.5, 0.5],
                "A drawn game must award half a point to each player")
        require(all(row["draws"] == 1 for row in standings),
                "A drawn game must increment both draw totals")
        service.complete_event(event_id)
        require(service.report(event_id)["event"]["status"] == "complete",
                "A fully scored event must be completable")
    return 6


def main() -> int:
    try:
        audit_repository()
        print("PASS repository hygiene, required license, ignore rules, and dependency policy")
        python_files = (
            list((ROOT / "chess_engine").rglob("*.py"))
            + list((ROOT / "club_tournament").rglob("*.py"))
            + list((ROOT / "tests").rglob("*.py"))
            + [ROOT / "main.py", ROOT / "scripts/reviewer_checks.py"]
        )
        for source in python_files:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        print("PASS Python compilation")
        checks = smoke_checks()
        print(f"PASS {checks} deterministic chess-engine smoke assertions")
        tournament_checks = tournament_smoke_checks()
        print(f"PASS {tournament_checks} tournament workflow assertions")

        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests/engine",
             "-p", "test_*.py"], cwd=ROOT, check=False,
        )
        if result.returncode:
            return result.returncode
        print("PASS standard-library unit suite")
        return 0
    except (AssertionError, OSError, UnicodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
