"""Tournament workflows, invariants, standings, and audit entries."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import sqlite3
import uuid
from typing import Any, Optional

from .pairings import round_robin
from .store import (
    Conflict,
    DatabasePath,
    InvalidTransition,
    NotFound,
    TournamentError,
    initialize,
    transaction,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_label(value: str, field: str, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{field} cannot be blank")
    if len(cleaned) > limit:
        raise ValueError(f"{field} cannot exceed {limit} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in cleaned):
        raise ValueError(f"{field} cannot contain control characters")
    return cleaned


def _audit(
    connection: sqlite3.Connection,
    event_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: Optional[dict[str, Any]],
    after: dict[str, Any],
) -> None:
    connection.execute(
        """INSERT INTO audit_log
           (event_id, occurred_at, action, entity_type, entity_id, before_value, after_value)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            event_id,
            _now(),
            action,
            entity_type,
            entity_id,
            json.dumps(before, sort_keys=True) if before is not None else None,
            json.dumps(after, sort_keys=True),
        ),
    )


class TournamentService:
    """Application service for a single SQLite database file.

    A tournament moves from registration to active to complete. Pairings are
    generated once at start and results are write-once, so a recorded result
    cannot be silently replaced through the normal command path.
    """

    def __init__(self, database: DatabasePath):
        self.database = database
        initialize(database)

    def create_event(self, name: str) -> str:
        name = _clean_label(name, "Event name", 100)
        event_id = str(uuid.uuid4())
        timestamp = _now()
        with transaction(self.database, write=True) as connection:
            connection.execute(
                "INSERT INTO events(id, name, status, created_at) VALUES (?, ?, 'registration', ?)",
                (event_id, name, timestamp),
            )
            _audit(connection, event_id, "event_created", "event", event_id, None, {
                "name": name, "status": "registration"
            })
        return event_id

    def register_player(self, event_id: str, display_name: str) -> int:
        display_name = _clean_label(display_name, "Player name", 80)
        normalized_name = display_name.casefold()
        with transaction(self.database, write=True) as connection:
            event = self._event(connection, event_id)
            if event["status"] != "registration":
                raise InvalidTransition("Players can only be registered before the event starts")
            try:
                cursor = connection.execute(
                    """INSERT INTO players(event_id, display_name, normalized_name, registered_at)
                       VALUES (?, ?, ?, ?)""",
                    (event_id, display_name, normalized_name, _now()),
                )
            except sqlite3.IntegrityError as exc:
                raise Conflict("A player with that name is already registered") from exc
            player_id = int(cursor.lastrowid)
            _audit(connection, event_id, "player_registered", "player", str(player_id), None, {
                "display_name": display_name
            })
        return player_id

    def start_event(self, event_id: str) -> list[dict[str, Any]]:
        with transaction(self.database, write=True) as connection:
            event = self._event(connection, event_id)
            if event["status"] != "registration":
                raise InvalidTransition("Only an event in registration can be started")
            player_ids = [row[0] for row in connection.execute(
                "SELECT id FROM players WHERE event_id = ? ORDER BY registered_at, id", (event_id,)
            )]
            try:
                schedule = round_robin(player_ids)
            except ValueError as exc:
                raise InvalidTransition(str(exc)) from exc

            rounds = sorted({pairing.round_number for pairing in schedule})
            connection.executemany(
                "INSERT INTO rounds(event_id, number, status) VALUES (?, ?, 'scheduled')",
                [(event_id, number) for number in rounds],
            )
            for pairing in schedule:
                connection.execute(
                    """INSERT INTO games
                       (id, event_id, round_number, board_number, white_id, black_id, result, recorded_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()), event_id, pairing.round_number, pairing.board_number,
                        pairing.white_id, pairing.black_id,
                        "bye" if pairing.is_bye else "pending",
                        _now() if pairing.is_bye else None,
                    ),
                )
            started_at = _now()
            connection.execute(
                "UPDATE events SET status = 'active', started_at = ? WHERE id = ?",
                (started_at, event_id),
            )
            _audit(connection, event_id, "event_started", "event", event_id,
                   {"status": "registration"}, {
                       "status": "active", "player_count": len(player_ids),
                       "round_count": len(rounds), "pairing_count": len(schedule),
                   })
        return self.pairings(event_id)

    def record_result(self, game_id: str, result: str) -> None:
        if result not in {"white_win", "black_win", "draw"}:
            raise ValueError("Result must be white_win, black_win, or draw")
        with transaction(self.database, write=True) as connection:
            game = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
            if game is None:
                raise NotFound(f"Game {game_id} was not found")
            event = self._event(connection, game["event_id"])
            if event["status"] != "active":
                raise InvalidTransition("Results can only be entered while the event is active")
            if game["result"] != "pending":
                raise Conflict("This game already has a recorded result")
            recorded_at = _now()
            updated = connection.execute(
                """UPDATE games SET result = ?, recorded_at = ?
                   WHERE id = ? AND result = 'pending'""",
                (result, recorded_at, game_id),
            )
            if updated.rowcount != 1:
                raise Conflict("The game result changed during this operation")
            _audit(connection, game["event_id"], "result_recorded", "game", game_id,
                   {"result": "pending"}, {"result": result})

            remaining = connection.execute(
                """SELECT COUNT(*) FROM games
                   WHERE event_id = ? AND round_number = ? AND result = 'pending'""",
                (game["event_id"], game["round_number"]),
            ).fetchone()[0]
            if remaining == 0:
                connection.execute(
                    """UPDATE rounds SET status = 'complete', completed_at = ?
                       WHERE event_id = ? AND number = ?""",
                    (recorded_at, game["event_id"], game["round_number"]),
                )

    def correct_result(self, game_id: str, result: str, reason: str) -> None:
        """Correct a previously recorded result while preserving its audit trail."""
        if result not in {"white_win", "black_win", "draw"}:
            raise ValueError("Result must be white_win, black_win, or draw")
        reason = _clean_label(reason, "Correction reason", 240)
        with transaction(self.database, write=True) as connection:
            game = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
            if game is None:
                raise NotFound(f"Game {game_id} was not found")
            self._event(connection, game["event_id"])
            if game["result"] in {"pending", "bye"}:
                raise InvalidTransition("Only a played game with a recorded result can be corrected")
            if game["result"] == result:
                raise Conflict("The corrected result is identical to the saved result")
            connection.execute(
                "UPDATE games SET result = ?, recorded_at = ? WHERE id = ?",
                (result, _now(), game_id),
            )
            _audit(connection, game["event_id"], "result_corrected", "game", game_id,
                   {"result": game["result"]}, {"result": result, "reason": reason})

    def complete_event(self, event_id: str) -> None:
        with transaction(self.database, write=True) as connection:
            event = self._event(connection, event_id)
            if event["status"] != "active":
                raise InvalidTransition("Only an active event can be completed")
            pending = connection.execute(
                "SELECT COUNT(*) FROM games WHERE event_id = ? AND result = 'pending'",
                (event_id,),
            ).fetchone()[0]
            if pending:
                raise InvalidTransition(f"Cannot complete the event while {pending} game(s) are pending")
            completed_at = _now()
            connection.execute(
                "UPDATE events SET status = 'complete', completed_at = ? WHERE id = ?",
                (completed_at, event_id),
            )
            _audit(connection, event_id, "event_completed", "event", event_id,
                   {"status": "active"}, {"status": "complete"})

    def list_events(self) -> list[dict[str, Any]]:
        with transaction(self.database) as connection:
            rows = connection.execute(
            "SELECT id, name, status, created_at FROM events ORDER BY created_at, id"
            ).fetchall()
            return [dict(row) for row in rows]

    def pairings(self, event_id: str, round_number: Optional[int] = None) -> list[dict[str, Any]]:
        with transaction(self.database) as connection:
            self._event(connection, event_id)
            query = """SELECT g.id, g.round_number, g.board_number, g.white_id, wp.display_name AS white_name,
                              g.black_id, bp.display_name AS black_name, g.result
                       FROM games g JOIN players wp ON wp.id = g.white_id
                       LEFT JOIN players bp ON bp.id = g.black_id
                       WHERE g.event_id = ?"""
            params: tuple[Any, ...] = (event_id,)
            if round_number is not None:
                query += " AND g.round_number = ?"
                params = (event_id, round_number)
            query += " ORDER BY g.round_number, g.board_number"
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def standings(self, event_id: str) -> list[dict[str, Any]]:
        with transaction(self.database) as connection:
            self._event(connection, event_id)
            player_rows = connection.execute(
                "SELECT id, display_name FROM players WHERE event_id = ? ORDER BY id", (event_id,)
            ).fetchall()
            stats = {row["id"]: {
                "player_id": row["id"], "name": row["display_name"], "points": 0.0,
                "wins": 0, "draws": 0, "losses": 0, "byes": 0,
                "opponents": [], "progressive": 0.0, "buchholz": 0.0,
                "sonneborn_berger": 0.0,
            } for row in player_rows}
            games = connection.execute(
                """SELECT round_number, white_id, black_id, result FROM games
                   WHERE event_id = ? ORDER BY round_number, board_number""", (event_id,)
            ).fetchall()
            for game in games:
                white = stats[game["white_id"]]
                black_id = game["black_id"]
                result = game["result"]
                if result == "bye":
                    white["points"] += 1.0
                    white["byes"] += 1
                elif result == "white_win":
                    white["points"] += 1.0
                    white["wins"] += 1
                    stats[black_id]["losses"] += 1
                elif result == "black_win":
                    stats[black_id]["points"] += 1.0
                    stats[black_id]["wins"] += 1
                    white["losses"] += 1
                elif result == "draw":
                    white["points"] += 0.5
                    stats[black_id]["points"] += 0.5
                    white["draws"] += 1
                    stats[black_id]["draws"] += 1

                if black_id is not None:
                    white["opponents"].append((black_id, result == "white_win", result == "draw"))
                    stats[black_id]["opponents"].append((game["white_id"], result == "black_win", result == "draw"))

            round_awards: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))
            for game in games:
                white_id, black_id, result = game["white_id"], game["black_id"], game["result"]
                if result == "bye":
                    round_awards[game["round_number"]][white_id] += 1.0
                elif result == "white_win":
                    round_awards[game["round_number"]][white_id] += 1.0
                elif result == "black_win":
                    round_awards[game["round_number"]][black_id] += 1.0
                elif result == "draw":
                    round_awards[game["round_number"]][white_id] += 0.5
                    round_awards[game["round_number"]][black_id] += 0.5
            cumulative = defaultdict(float)
            for number in sorted(round_awards):
                for player_id, points in round_awards[number].items():
                    cumulative[player_id] += points
                for player_id in stats:
                    stats[player_id]["progressive"] += cumulative[player_id]
            for player_id, player in stats.items():
                for opponent_id, won, drawn in player["opponents"]:
                    opponent_score = stats[opponent_id]["points"]
                    player["buchholz"] += opponent_score
                    player["sonneborn_berger"] += opponent_score * (1.0 if won else 0.5 if drawn else 0.0)
                player.pop("opponents")

            ordered = sorted(
                stats.values(),
                key=lambda player: (
                    -player["points"], -player["buchholz"],
                    -player["sonneborn_berger"], -player["wins"], player["name"].casefold(),
                ),
            )
            for rank, player in enumerate(ordered, 1):
                player["rank"] = rank
            return ordered

    def audit_log(self, event_id: str) -> list[dict[str, Any]]:
        with transaction(self.database) as connection:
            self._event(connection, event_id)
            rows = connection.execute(
                """SELECT sequence, occurred_at, action, entity_type, entity_id,
                          before_value, after_value FROM audit_log
                   WHERE event_id = ? ORDER BY sequence""", (event_id,)
            ).fetchall()
            records = []
            for row in rows:
                record = dict(row)
                record["before_value"] = json.loads(record["before_value"]) if record["before_value"] else None
                record["after_value"] = json.loads(record["after_value"])
                records.append(record)
            return records

    def report(self, event_id: str) -> dict[str, Any]:
        with transaction(self.database) as connection:
            event = self._event(connection, event_id)
            event_data = dict(event)
        return {
            "event": event_data,
            "rounds": self._rounds(event_id),
            "pairings": self.pairings(event_id),
            "standings": self.standings(event_id),
        }

    def _rounds(self, event_id: str) -> list[dict[str, Any]]:
        with transaction(self.database) as connection:
            return [dict(row) for row in connection.execute(
                "SELECT number, status, completed_at FROM rounds WHERE event_id = ? ORDER BY number",
                (event_id,),
            ).fetchall()]

    @staticmethod
    def _event(connection: sqlite3.Connection, event_id: str) -> sqlite3.Row:
        event = connection.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            raise NotFound(f"Event {event_id} was not found")
        return event


__all__ = ["TournamentService", "TournamentError", "NotFound", "Conflict", "InvalidTransition"]
