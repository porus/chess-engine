"""Command-line interface for managing a local round-robin event."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from .service import TournamentService
from .store import TournamentError


def _format_report(report: dict) -> str:
    event = report["event"]
    lines = [f"{event['name']} ({event['id']})", f"Status: {event['status']}", "", "Pairings"]
    if not report["pairings"]:
        lines.append("  No pairings yet. Register at least two players, then start the event.")
    for pairing in report["pairings"]:
        opponent = pairing["black_name"] or "BYE"
        lines.append(
            f"  Round {pairing['round_number']}, board {pairing['board_number']}: "
            f"{pairing['white_name']} – {opponent} [{pairing['result']}] "
            f"game={pairing['id']}"
        )
    lines.extend(["", "Standings", "Rank  Pts  Buchholz  SB   W-D-L  Player"])
    for player in report["standings"]:
        lines.append(
            f"{player['rank']:>4}  {player['points']:>3.1f}  {player['buchholz']:>8.1f}  "
            f"{player['sonneborn_berger']:>3.1f}  "
            f"{player['wins']}-{player['draws']}-{player['losses']}  {player['name']}"
        )
    lines.extend(["", "Tie-break order: points, Buchholz, Sonneborn–Berger, wins, name."])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="club-tournament",
        description="Manage a local chess-club round-robin event and its results.",
    )
    parser.add_argument("--db", default="club-tournament.sqlite3", help="SQLite file (default: %(default)s)")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Create an event in registration state")
    create.add_argument("name", help="Event name")

    register = commands.add_parser("register", help="Register a player before the event starts")
    register.add_argument("event_id")
    register.add_argument("name")

    start = commands.add_parser("start", help="Generate the complete round-robin schedule")
    start.add_argument("event_id")

    report = commands.add_parser("report", help="Show pairings and current standings")
    report.add_argument("event_id")
    report.add_argument("--json", action="store_true", help="Print the report as JSON")

    result = commands.add_parser("result", help="Record a result once for a paired game")
    result.add_argument("game_id")
    result.add_argument("outcome", choices=("white_win", "black_win", "draw"))

    correction = commands.add_parser("correct-result", help="Correct a result with a required audit reason")
    correction.add_argument("game_id")
    correction.add_argument("outcome", choices=("white_win", "black_win", "draw"))
    correction.add_argument("--reason", required=True, help="Why the result is being corrected")

    complete = commands.add_parser("complete", help="Complete an event when every game has a result")
    complete.add_argument("event_id")

    audit = commands.add_parser("audit", help="Show the ordered change history for an event")
    audit.add_argument("event_id")

    commands.add_parser("events", help="List events stored in the selected database")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        service = TournamentService(args.db)
        if args.command == "create":
            event_id = service.create_event(args.name)
            print(f"Created event {event_id}: {args.name}")
        elif args.command == "register":
            player_id = service.register_player(args.event_id, args.name)
            print(f"Registered player {player_id}: {args.name}")
        elif args.command == "start":
            pairings = service.start_event(args.event_id)
            print(f"Generated {len(pairings)} board assignments")
        elif args.command == "report":
            report_data = service.report(args.event_id)
            print(json.dumps(report_data, indent=2) if args.json else _format_report(report_data))
        elif args.command == "result":
            service.record_result(args.game_id, args.outcome)
            print(f"Recorded {args.outcome} for game {args.game_id}")
        elif args.command == "correct-result":
            service.correct_result(args.game_id, args.outcome, args.reason)
            print(f"Corrected result to {args.outcome} for game {args.game_id}")
        elif args.command == "complete":
            service.complete_event(args.event_id)
            print(f"Completed event {args.event_id}")
        elif args.command == "audit":
            print(json.dumps(service.audit_log(args.event_id), indent=2))
        elif args.command == "events":
            print(json.dumps(service.list_events(), indent=2))
        return 0
    except (TournamentError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


__all__ = ["build_parser", "main"]
