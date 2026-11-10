"""Deterministic round-robin scheduling for small club events.

This module deliberately implements a fixed round-robin schedule. It does not
claim to implement Swiss-system pairing regulations or arbitrate tournament
rules that vary by organizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class Pairing:
    round_number: int
    board_number: int
    white_id: int
    black_id: Optional[int]

    @property
    def is_bye(self) -> bool:
        return self.black_id is None


def round_robin(player_ids: Sequence[int]) -> list[Pairing]:
    """Build one complete schedule; odd fields receive one bye per round.

    The circle method keeps one entry fixed and rotates the remaining entries.
    Board order and colors are stable for the same input order, which makes
    generated schedules reproducible in tests and useful for printed sheets.
    """
    ids = list(player_ids)
    if len(ids) < 2:
        raise ValueError("A round-robin event needs at least two players")
    if len(set(ids)) != len(ids):
        raise ValueError("Player IDs must be unique")

    ring: list[Optional[int]] = ids[:]
    if len(ring) % 2:
        ring.append(None)

    schedule: list[Pairing] = []
    round_count = len(ring) - 1
    for round_index in range(round_count):
        board_number = 1
        for index in range(len(ring) // 2):
            first, second = ring[index], ring[-1 - index]
            if first is None or second is None:
                bye_player = second if first is None else first
                assert bye_player is not None
                schedule.append(Pairing(round_index + 1, board_number, bye_player, None))
                board_number += 1
                continue

            if (round_index + index) % 2:
                first, second = second, first
            schedule.append(Pairing(round_index + 1, board_number, first, second))
            board_number += 1

        # Keep the first player fixed; rotate all other slots by one position.
        ring = [ring[0], ring[-1], *ring[1:-1]]

    return schedule
