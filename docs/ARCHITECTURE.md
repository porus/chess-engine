# Architecture

Club Tournament Desk is a local application with three boundaries: a command-line adapter, tournament application services, and a SQLite persistence layer. The chess rules engine is a separate module used by the terminal game and rules tests; tournament scheduling and scoring do not depend on engine evaluation.

## Request path

```text
CLI arguments
    ↓
TournamentService: validates lifecycle and business rules
    ↓
pairings.py (schedule) / store.py (SQLite transactions)
    ↓
SQLite event, player, round, game, and audit tables
```

The CLI is intentionally thin. It parses a command, calls one service operation, and prints a human-readable or JSON response. The service owns state transitions and the rules for recording or correcting a result. The store opens short-lived SQLite connections, enables foreign-key checks, and wraps each mutation in a transaction.

## Event lifecycle

```text
registration → active → complete
```

- `registration`: organizers can add participants. A name is unique within an event after whitespace normalization and case folding.
- `active`: the round-robin schedule is fixed. New registration is rejected; results can be recorded; a saved result can be corrected with a reason.
- `complete`: all games have results. The event can be reported and a correction remains possible, with the change captured in the audit log.

Each write is atomic. A result uses a conditional update from `pending`, so repeated or racing submissions cannot silently replace the first result. A correction is a separate operation that records before and after values.

## Storage model

| Table | Purpose | Important constraints |
| --- | --- | --- |
| `events` | Name, lifecycle status, and timestamps | Status is constrained to the supported lifecycle values |
| `players` | Display names registered to an event | Unique normalized name per event; event-scoped foreign key |
| `rounds` | Generated round status | One row per event and round number |
| `games` | Board assignment and result | One board per round; one appearance per player per round; valid bye/result combinations |
| `audit_log` | Ordered record of event operations | Captures action, entity, timestamp, and before/after data |

The database schema is versioned with SQLite's `user_version`. The current schema is version 1. The application refuses a database created by a newer version instead of opening it as if it understood that schema.

## Pairing and standings

The schedule uses a deterministic circle-method round robin. For an odd field, a placeholder is added to the rotating list and the paired participant receives a bye. Pairings are generated once when an event starts; there is no automatic rescheduling after a withdrawal.

Standings award one point for a win or bye and half a point for a draw. Ranking is by total points, Buchholz, Sonneborn–Berger, win count, and name. Progressive score is displayed as a report value but is not used as a ranking tie-break. These are explicit local conventions, not a federation-rule implementation.

## Deliberate boundaries

- No web server, hosted database, authentication, or external chess engine.
- Participant records contain display names only; there is no contact or demographic profile.
- SQLite and standard-library modules are used so the project can be run in an isolated review sandbox.
- The terminal opponent is a simple one-ply material selector.

This separation keeps event administration testable without starting the chess game, and keeps the chess rules module usable without creating an event database.
