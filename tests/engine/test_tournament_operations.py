"""Persistence and workflow tests for the club tournament application."""

from pathlib import Path
import tempfile
import unittest

from club_tournament import Conflict, InvalidTransition, NotFound, TournamentService
from club_tournament.pairings import round_robin


class RoundRobinPairingTests(unittest.TestCase):
    def test_even_field_pairs_every_player_once_per_round(self):
        schedule = round_robin([1, 2, 3, 4, 5, 6])
        self.assertEqual(len(schedule), 15)
        self.assertEqual({pair.round_number for pair in schedule}, {1, 2, 3, 4, 5})
        for round_number in range(1, 6):
            round_games = [pair for pair in schedule if pair.round_number == round_number]
            players = [player for pair in round_games for player in (pair.white_id, pair.black_id)]
            self.assertEqual(sorted(players), [1, 2, 3, 4, 5, 6])
        opponents = {
            frozenset((pair.white_id, pair.black_id))
            for pair in schedule
        }
        self.assertEqual(len(opponents), 15)

    def test_odd_field_gives_each_player_exactly_one_bye(self):
        schedule = round_robin([11, 12, 13, 14, 15])
        byes = [pair.white_id for pair in schedule if pair.is_bye]
        self.assertEqual(len(schedule), 15)
        self.assertEqual(set(byes), {11, 12, 13, 14, 15})
        for round_number in range(1, 6):
            games = [pair for pair in schedule if pair.round_number == round_number]
            played = [player for pair in games if not pair.is_bye
                      for player in (pair.white_id, pair.black_id) if player]
            self.assertEqual(len(played), 4)
            self.assertEqual(len({pair.board_number for pair in games}), 3)

    def test_schedule_is_reproducible_and_rejects_bad_fields(self):
        self.assertEqual(round_robin([8, 3, 5]), round_robin([8, 3, 5]))
        for field in ([1], [1, 1]):
            with self.subTest(field=field), self.assertRaises(ValueError):
                round_robin(field)


class TournamentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "club.sqlite3"
        self.service = TournamentService(self.database)
        self.event_id = self.service.create_event("Wednesday Club Night")

    def tearDown(self):
        self.temporary.cleanup()

    def _register(self, *names):
        return [self.service.register_player(self.event_id, name) for name in names]

    def test_registration_is_normalized_and_closed_when_started(self):
        self.service.register_player(self.event_id, "  Alex   Lee ")
        with self.assertRaises(Conflict):
            self.service.register_player(self.event_id, "alex lee")
        self.service.register_player(self.event_id, "Morgan")
        self.service.start_event(self.event_id)
        with self.assertRaises(InvalidTransition):
            self.service.register_player(self.event_id, "Late Arrival")

    def test_event_cannot_start_with_fewer_than_two_players(self):
        self.service.register_player(self.event_id, "Only Player")
        with self.assertRaises(InvalidTransition):
            self.service.start_event(self.event_id)
        self.assertEqual(self.service.report(self.event_id)["event"]["status"], "registration")

    def test_round_robin_results_standings_and_completion(self):
        self._register("Ari", "Bex", "Casey", "Devin")
        pairings = self.service.start_event(self.event_id)
        self.assertEqual(len(pairings), 6)
        with self.assertRaises(InvalidTransition):
            self.service.complete_event(self.event_id)

        for pairing in pairings:
            if pairing["result"] == "pending":
                self.service.record_result(pairing["id"], "draw")
        standings = self.service.standings(self.event_id)
        self.assertEqual({row["points"] for row in standings}, {1.5})
        self.assertEqual({row["draws"] for row in standings}, {3})
        self.assertEqual({row["rank"] for row in standings}, {1, 2, 3, 4})
        self.service.complete_event(self.event_id)
        self.assertEqual(self.service.report(self.event_id)["event"]["status"], "complete")

    def test_odd_field_bye_is_awarded_one_point_and_excluded_from_games_played(self):
        self._register("Ari", "Bex", "Casey")
        pairings = self.service.start_event(self.event_id)
        bye = next(pairing for pairing in pairings if pairing["result"] == "bye")
        player = next(row for row in self.service.standings(self.event_id)
                      if row["player_id"] == bye["white_id"])
        self.assertEqual(player["points"], 1.0)
        self.assertEqual(player["byes"], 1)
        self.assertEqual(player["wins"], 0)

    def test_progressive_score_sums_each_rounds_cumulative_points(self):
        player_ids = self._register("Ari", "Bex", "Casey")
        pairings = self.service.start_event(self.event_id)
        for pairing in pairings:
            if pairing["result"] == "pending":
                self.service.record_result(pairing["id"], "draw")
        progressive_by_player = {
            row["player_id"]: row["progressive"] for row in self.service.standings(self.event_id)
        }
        self.assertEqual(progressive_by_player, {
            player_ids[0]: 4.5,
            player_ids[1]: 4.0,
            player_ids[2]: 3.5,
        })

    def test_results_are_write_once_and_audited(self):
        self._register("Ari", "Bex")
        pairing = self.service.start_event(self.event_id)[0]
        self.service.record_result(pairing["id"], "white_win")
        with self.assertRaises(Conflict):
            self.service.record_result(pairing["id"], "draw")
        actions = [row["action"] for row in self.service.audit_log(self.event_id)]
        self.assertEqual(actions, ["event_created", "player_registered", "player_registered",
                                   "event_started", "result_recorded"])

    def test_correction_requires_reason_and_preserves_old_and_new_values(self):
        self._register("Ari", "Bex")
        pairing = self.service.start_event(self.event_id)[0]
        self.service.record_result(pairing["id"], "white_win")
        with self.assertRaises(ValueError):
            self.service.correct_result(pairing["id"], "draw", "  ")
        self.service.correct_result(pairing["id"], "draw", "Score sheet was entered incorrectly")
        audit = self.service.audit_log(self.event_id)[-1]
        self.assertEqual(audit["before_value"], {"result": "white_win"})
        self.assertEqual(audit["after_value"]["result"], "draw")
        self.assertEqual(audit["after_value"]["reason"], "Score sheet was entered incorrectly")
        self.assertEqual({row["points"] for row in self.service.standings(self.event_id)}, {0.5})

    def test_database_reopens_without_losing_event_state(self):
        self._register("Ari", "Bex")
        pairings = self.service.start_event(self.event_id)
        self.service.record_result(pairings[0]["id"], "black_win")
        reopened = TournamentService(self.database)
        self.assertEqual(reopened.report(self.event_id)["event"]["status"], "active")
        self.assertEqual(reopened.pairings(self.event_id)[0]["result"], "black_win")

    def test_unknown_event_and_game_return_clear_errors(self):
        with self.assertRaises(NotFound):
            self.service.report("missing-event")
        with self.assertRaises(NotFound):
            self.service.record_result("missing-game", "draw")

    def test_name_validation_rejects_empty_and_oversized_values(self):
        with self.assertRaises(ValueError):
            self.service.create_event(" \t ")
        with self.assertRaises(ValueError):
            self.service.create_event("x" * 101)


if __name__ == "__main__":
    unittest.main()
