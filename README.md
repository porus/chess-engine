# Club Tournament Desk

Club Tournament Desk is an offline-first Python application for running a small chess-club round-robin event. It handles the operational work around a tournament: event setup, player registration, schedule generation, result entry and correction, standings, and a durable audit trail. The included chess rules engine remains available for a terminal game and for rule-focused regression tests.

The project is intended for organizers who need a lightweight local record of an event without setting up a hosted service, a database server, or third-party Python packages. It stores data in SQLite and runs with Python 3.10 or newer.

**Engine scope:** this is a chess rules implementation with a basic one-move material opponent, not a Stockfish-strength engine. It does not implement look-ahead search or timed games. The tournament commands manage round-robin schedules and results; games are played outside the application. The current interface is command-line only.

## What it does

- Creates named events with a registration, active, and complete lifecycle.
- Registers participants with duplicate-name checks that ignore capitalization and extra whitespace.
- Generates a deterministic round-robin schedule using the circle method. Even fields play every other participant once; odd fields receive one bye each.
- Records game results once. A later correction requires a reason and writes both the previous and corrected values to the event audit log.
- Calculates points, wins, draws, losses, byes, progressive score, Buchholz, and Sonneborn–Berger values.
- Produces a text or JSON event report, including game identifiers for result entry.
- Persists all event records in a local SQLite database with foreign keys, uniqueness constraints, schema versioning, and transactional updates.
- Includes a self-contained chess rules engine for legal move generation, special moves, end conditions, draw conditions, and a basic material-greedy opponent.

## Local setup

Use Python 3.10 or newer. Clone the repository and run commands from its root:

```bash
git clone https://github.com/porus/chess-engine.git
cd chess-engine
python --version
python scripts/reviewer_checks.py
```

The project needs no package installation, Docker, database server, or network connection to run. It uses only Python's standard library, including the built-in SQLite module. On macOS or Linux, use `python3` if `python` points to an older version; on Windows, use `py -3`.

## Quick start

From the repository root:

```bash
python -m club_tournament --db ./club-night.sqlite3 create "Wednesday Club Night"
```

Copy the event ID printed by the command, then register players:

```bash
python -m club_tournament --db ./club-night.sqlite3 register EVENT_ID "Ari Patel"
python -m club_tournament --db ./club-night.sqlite3 register EVENT_ID "Morgan Chen"
python -m club_tournament --db ./club-night.sqlite3 register EVENT_ID "Sam Rivera"
python -m club_tournament --db ./club-night.sqlite3 register EVENT_ID "Taylor Jones"
```

Start the event and print the schedule and standings:

```bash
python -m club_tournament --db ./club-night.sqlite3 start EVENT_ID
python -m club_tournament --db ./club-night.sqlite3 report EVENT_ID
```

Each pairing shows a game ID. Enter the outcome using that ID and the color-relative result value:

```bash
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID draw
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID white_win
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID black_win
```

When every game is scored, close the event and export a machine-readable report:

```bash
python -m club_tournament --db ./club-night.sqlite3 complete EVENT_ID
python -m club_tournament --db ./club-night.sqlite3 report EVENT_ID --json
python -m club_tournament --db ./club-night.sqlite3 audit EVENT_ID
```

To correct a mistakenly entered result, use the correction command. The reason is required and retained in the audit log:

```bash
python -m club_tournament --db ./club-night.sqlite3 correct-result GAME_ID draw \
  --reason "The signed score sheet showed a draw"
```

Other useful commands:

```bash
python -m club_tournament --help
python -m club_tournament --db ./club-night.sqlite3 events
```

The database path is optional; if omitted, the program uses `club-tournament.sqlite3` in the current directory. Back up that file to preserve event records. The application does not upload it anywhere.

## Scoring and pairing conventions

This tool generates a complete round-robin schedule before the first round. It is not a Swiss pairing program. A bye is stored as a distinct schedule entry and awards one point. Standings are ordered by points, Buchholz, Sonneborn–Berger, wins, then player name. Progressive score is reported but is not a ranking tie-break in this version. These are application conventions, not a claim of compliance with any federation's event regulations. An organizer should confirm that the scoring and tie-break order suit the event before using the report as an official result.

## Chess rules demo

The project also includes a terminal game, separate from the tournament workflow. Start it from the repository root:

```bash
python main.py
```

At the prompts, choose `w` or `b` for your color, then choose `1` for the random opponent or `2` for the greedy opponent. Enter moves in coordinate form, such as `e2e4`; enter `q` when prompted for a move to quit. The board is printed after each turn. The opponent uses a one-move score and does not search ahead, so it is a demonstration opponent rather than a competitive engine. The demo does not save game moves or positions.

## Reviewer validation

Run the complete offline validation from the repository root:

```bash
python scripts/reviewer_checks.py
```

The script checks required files and repository hygiene, compiles the Python sources, runs deterministic chess and tournament workflow smoke checks, and runs the `unittest` suite. It uses only the Python standard library, creates temporary databases outside the repository, and does not invoke Git, Docker, a web service, or an external chess engine. See [docs/TESTING.md](docs/TESTING.md) for the exact check sequence and expected output.

## Project layout

```text
club_tournament/   Tournament lifecycle, pairings, SQLite storage, CLI
chess_engine/      Chess rules and terminal-play support
tests/engine/      Rules, edge cases, persistence, and event workflow tests
scripts/           One-command reviewer validation
docs/              Architecture, operating conventions, testing, licensing
```

The responsibilities are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Event operations and the data model are covered in [docs/TOURNAMENT_OPERATIONS.md](docs/TOURNAMENT_OPERATIONS.md).

## Data and security boundaries

The SQLite database stores event names, lifecycle status and timestamps; participant display names and normalized names; rounds and pairings; manually entered results; and audit entries with before-and-after values for recorded changes. It does not store moves from the terminal chess demo, collect contact details, or connect to a network service. By default the database file is `club-tournament.sqlite3` in the current directory; pass `--db PATH` to choose another location. Keep event files private to the organizer and delete them when no longer needed. The repository's `.gitignore` excludes local databases, environment files, caches, and generated build output. For private vulnerability reporting, see [SECURITY.md](SECURITY.md).

This is a single-machine organizer tool, not a multi-user hosted service. It does not implement login, role management, server-side synchronization, or concurrent operator workflows. The audit log makes changes reviewable; it is not tamper-proof against someone who can edit the database file directly.

## Dependencies and licensing

The runtime and test suite use the Python standard library only. The GitHub Actions workflow references `actions/checkout` and `actions/setup-python`; neither project's code is copied into this repository. Their versions and license references are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No Stockfish binary, opening book, or third-party chess package is bundled.

Project files are distributed under the MIT License in [LICENSE](LICENSE). See [docs/LICENSING.md](docs/LICENSING.md) for the dependency and contribution boundary.
