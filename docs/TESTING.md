# Running the checks

## Prerequisite

Python 3.11 or newer. The repository does not require an install step, package download, database server, or network access.

## Reviewer command

From the repository root, run:

```bash
python scripts/reviewer_checks.py
```

The command performs these checks in order:

1. Confirms the expected root files, MIT license, ignore rules, and absence of local databases, key files, engine binaries, and common credential markers. It accepts a valid `.git` marker when run from a GitHub checkout and skips scanning Git internals.
2. Compiles application, test, and validation-script sources without writing bytecode files.
3. Runs eight deterministic chess-engine smoke assertions covering the initial position, legal opening move count, and the `e2e4` state update.
4. Runs six tournament workflow assertions against a temporary SQLite database: event creation, registration, schedule generation, draw scoring, standings, and event completion.
5. Runs the full standard-library `unittest` suite.

At the current revision the suite contains **141 tests**. The final output should include `Ran 141 tests` and `OK`, along with `PASS` lines for repository hygiene, compilation, and both smoke-check groups. A non-zero exit status indicates a failure.

## Focused commands

Run only the tests:

```bash
python -m unittest discover -s tests/engine -p 'test_*.py' -v
```

Run just the tournament workflow tests:

```bash
python -m unittest discover -s tests/engine -p 'test_tournament_operations.py' -v
```

Run the interactive chess demo:

```bash
python main.py
```

The validation script uses a temporary database directory and removes it when done. The normal CLI writes to the database path supplied with `--db`; `.gitignore` excludes SQLite database files from version control.

## Scope

These checks cover the listed scenarios; they do not establish full rules certification, federation compliance, production security, or correctness for every possible tournament configuration. The round-robin generator is tested for schedule coverage and byes. Pairing conventions and scoring are documented in [TOURNAMENT_OPERATIONS.md](TOURNAMENT_OPERATIONS.md).
