# Tournament operations

This guide describes the local event workflow and the records the application creates. It is written for a club organizer reviewing the tool before using it for an event.

## Before the event

Choose a database path and create an event:

```bash
python -m club_tournament --db ./club-night.sqlite3 create "Wednesday Club Night"
```

The command prints a UUID. Use it for registration and later event operations. Add each participant before starting:

```bash
python -m club_tournament --db ./club-night.sqlite3 register EVENT_ID "Ari Patel"
```

Duplicate names are checked within the event after trimming and collapsing whitespace and ignoring capitalization. Two different people with the same normalized display name cannot currently be represented in one event; use a distinguishing suffix such as a club or team label.

## Start and run rounds

Start locks registration and generates the full round-robin schedule:

```bash
python -m club_tournament --db ./club-night.sqlite3 start EVENT_ID
python -m club_tournament --db ./club-night.sqlite3 report EVENT_ID
```

The report lists rounds, boards, player display names, game IDs, and current results. A JSON form is available for downstream processing:

```bash
python -m club_tournament --db ./club-night.sqlite3 report EVENT_ID --json
```

Record outcomes by game ID:

```bash
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID white_win
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID black_win
python -m club_tournament --db ./club-night.sqlite3 result GAME_ID draw
```

The result names are from the pairing's color perspective. A game can only receive its first result once through this command. To fix a clerical error, use `correct-result` and include an explanation:

```bash
python -m club_tournament --db ./club-night.sqlite3 correct-result GAME_ID draw \
  --reason "The signed score sheet showed a draw"
```

Every event creation, registration, start, result, correction, and completion is recorded in the audit table. Corrections retain the old result, new result, and supplied reason.

Review the ordered audit trail from the command line:

```bash
python -m club_tournament --db ./club-night.sqlite3 audit EVENT_ID
```

## Close and retain records

The event can be completed only after every paired game has a recorded result. A bye is generated as a completed pairing and does not need result entry.

```bash
python -m club_tournament --db ./club-night.sqlite3 complete EVENT_ID
python -m club_tournament --db ./club-night.sqlite3 report EVENT_ID
```

Keep the SQLite file as the event record and make a backup through the operating system's normal file-copy process. This application does not encrypt the database or protect it from someone with filesystem access. It does not transmit the file over a network.

## Data recorded

- Event: generated identifier, event name, lifecycle status, and timestamps.
- Participant: generated integer identifier, display name, normalized name used for duplicate detection, and registration timestamp.
- Pairing: event, round, board, White and Black participant identifiers, result, and result timestamp.
- Audit entry: monotonically increasing sequence, event, timestamp, action, entity identifier, and before/after JSON values.

No contact details or online account identifiers are collected.

## Pairing, bye, and ranking policy

The schedule is a complete round robin and cannot be edited through the CLI after the event starts. For an odd participant count, one player receives a bye in each round and every participant receives exactly one bye over the full event. Each bye awards one point.

The standings sort by:

1. Points (win/bye = 1; draw = 0.5; loss = 0).
2. Buchholz (sum of opponents' final points).
3. Sonneborn–Berger (opponents' final points weighted by game score).
4. Number of wins.
5. Display name, case-insensitively.

Progressive score is also calculated and shown. Organizers should verify that this policy is appropriate for their event before treating standings as official. The software does not implement Swiss pairings, federation reporting, title norms, arbitration, time controls, or rating submission.
