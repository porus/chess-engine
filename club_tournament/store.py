"""SQLite setup and transaction helpers for the local tournament ledger."""

from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Iterator, Union

DatabasePath = Union[str, Path]
SCHEMA_VERSION = 1


class TournamentError(Exception):
    """Base class for expected tournament workflow errors."""


class NotFound(TournamentError):
    """A requested event, player, or game does not exist."""


class Conflict(TournamentError):
    """An operation conflicts with the current saved state."""


class InvalidTransition(TournamentError):
    """An operation is not valid in the event's current state."""


def connect(database: DatabasePath) -> sqlite3.Connection:
    """Open a configured connection. Connections are short-lived per action."""
    if str(database) == ":memory:":
        raise ValueError("Use a SQLite file path; each operation opens its own connection")
    Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(database), timeout=5.0, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def transaction(database: DatabasePath, *, write: bool = False) -> Iterator[sqlite3.Connection]:
    """Open a connection and commit or roll back one atomic operation."""
    connection = connect(database)
    try:
        connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(database: DatabasePath) -> None:
    """Create or validate the versioned schema without deleting existing data."""
    with transaction(database, write=True) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise Conflict(
                f"Database schema {version} is newer than supported schema {SCHEMA_VERSION}"
            )
        if version == SCHEMA_VERSION:
            return
        if version != 0:
            raise Conflict(f"No migration is available from database schema {version}")

        statements = (
            """CREATE TABLE events (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
                status TEXT NOT NULL CHECK(status IN ('registration', 'active', 'complete')),
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )""",

            """CREATE TABLE players (
                id INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                display_name TEXT NOT NULL CHECK(length(display_name) BETWEEN 1 AND 80),
                normalized_name TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                UNIQUE(event_id, normalized_name),
                UNIQUE(event_id, id)
            )""",

            """CREATE TABLE rounds (
                event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                number INTEGER NOT NULL CHECK(number > 0),
                status TEXT NOT NULL CHECK(status IN ('scheduled', 'complete')),
                completed_at TEXT,
                PRIMARY KEY(event_id, number)
            )""",

            """CREATE TABLE games (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                board_number INTEGER NOT NULL CHECK(board_number > 0),
                white_id INTEGER NOT NULL,
                black_id INTEGER,
                result TEXT NOT NULL CHECK(result IN ('pending', 'white_win', 'black_win', 'draw', 'bye')),
                recorded_at TEXT,
                FOREIGN KEY(event_id, round_number) REFERENCES rounds(event_id, number),
                FOREIGN KEY(event_id, white_id) REFERENCES players(event_id, id),
                FOREIGN KEY(event_id, black_id) REFERENCES players(event_id, id),
                CHECK(white_id != black_id OR black_id IS NULL),
                CHECK((black_id IS NULL AND result = 'bye') OR
                      (black_id IS NOT NULL AND result != 'bye')),
                UNIQUE(event_id, round_number, board_number),
                UNIQUE(event_id, round_number, white_id),
                UNIQUE(event_id, round_number, black_id)
            )""",

            "CREATE INDEX games_event_round ON games(event_id, round_number, board_number)",
            "CREATE INDEX players_event_registration ON players(event_id, registered_at, id)",

            """CREATE TABLE audit_log (
                sequence INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                occurred_at TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                before_value TEXT,
                after_value TEXT NOT NULL
            )""",
        )
        for statement in statements:
            connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
