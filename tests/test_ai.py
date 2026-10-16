"""Tests for easy/medium/hard AI (AC-4 to AC-7, hard timing of AC-8)."""

import random
import time
import unittest
from collections import Counter

from tictactoe5 import ai, rules
from tictactoe5.rules import Board, O, X

LEVELS = ("easy", "medium", "hard")  # expert is covered in test_expert.py


def board(*rows: str) -> Board:
    return Board.from_rows(rows)


def random_position(rng: random.Random, plies: int) -> Board:
    """A reachable non-terminal position after ``plies`` random moves."""
    while True:
        b = Board()
        player = X
        for _ in range(plies):
            b.play(rng.choice(rules.legal_moves(b)), player)
            if rules.status(b) != "ongoing":
                break
            player = rules.opponent(player)
        else:
            return b


class LegalityTest(unittest.TestCase):
    def test_legal_and_no_mutation(self) -> None:
        rng = random.Random(1)
        for level in LEVELS:
            for plies in (0, 1, 4, 9, 14, 20):
                for _ in range(3):
                    b = random_position(rng, plies)
                    player = X if plies % 2 == 0 else O
                    before = b.key()
                    m = ai.choose_move(b, player, level, rng=random.Random(5))
                    self.assertEqual(b.key(), before)
                    self.assertIn(m, rules.legal_moves(b), (level, plies))

    def test_single_empty_cell(self) -> None:
        b = board("XXOOX", "OOXXO", "XXOOX", "OOXXO", "XXOO.")
        for level in LEVELS:
            self.assertEqual(ai.choose_move(b, X, level), 24)

    def test_full_board_and_bad_level(self) -> None:
        full = board("XXOOX", "OOXXO", "XXOOX", "OOXXO", "XXOOX")
        with self.assertRaises(ValueError):
            ai.choose_move(full, X, "easy")
        with self.assertRaises(ValueError):
            ai.choose_move(Board(), X, "nope")


class TacticsTest(unittest.TestCase):
    def test_takes_immediate_win_all_levels(self) -> None:
        # O wins at d2 (index 8); X also threatens a win at d1.
        b = board("XXX..", "OOO..", ".....", ".X...", ".....")
        for level in LEVELS:
            for seed in range(5):
                m = ai.choose_move(b, O, level, rng=random.Random(seed))
                self.assertEqual(m, 8, level)

    def test_win_beats_block(self) -> None:
        b = board("XXX..", "OOO..", ".....", ".....", ".....")
        for level in LEVELS:
            self.assertEqual(ai.choose_move(b, O, level, rng=random.Random(1)), 8)

    def test_blocks_immediate_loss(self) -> None:
        b = board("XXX..", "O.O..", ".....", ".....", ".....")
        for level in ("medium", "hard"):
            for seed in range(10):
                m = ai.choose_move(b, O, level, rng=random.Random(seed))
                self.assertEqual(m, 3, level)

    def test_blocks_vertical_and_diagonal(self) -> None:
        b = board("X....", ".X...", "..X..", ".....", "O.O.O")
        for level in ("medium", "hard"):
            self.assertEqual(ai.choose_move(b, O, level, rng=random.Random(2)), 18)

    def test_two_threats_blocks_one_legally(self) -> None:
        b = board("XXX..", ".....", "X....", "X....", "O.O..")
        # X wins at d1 (3) and at a2 (5).
        threats = set(rules.immediate_wins(b, X))
        self.assertEqual(len(threats), 2)
        for level in ("medium", "hard"):
            m = ai.choose_move(b, O, level, rng=random.Random(3))
            self.assertIn(m, threats)

    def test_easy_may_not_block(self) -> None:
        b = board("XXX..", ".....", ".....", ".....", "O...O")
        seen = {ai.choose_move(b, O, "easy", rng=random.Random(s)) for s in range(60)}
        self.assertNotEqual(seen, {3})  # stated: easy is not required to block

    def test_hard_avoids_loss_in_two(self) -> None:
        # X has b1 c1 with a1/d1/e1 open: O must stop an open three.
        b = board(".XX..", ".....", ".....", ".....", "O...O")
        m = ai.choose_move(b, O, "hard", rng=random.Random(1))
        self.assertIn(m, (0, 3, 4))
        after = b.copy()
        after.play(m, O)
        # After O's reply X cannot make an unstoppable double (two wins).
        for x in rules.legal_moves(after):
            t = after.copy()
            t.play(x, X)
            self.assertLess(len(rules.immediate_wins(t, X)), 2, (m, x))

    def test_medium_creates_double_threat(self) -> None:
        # O has two lines each needing one more to be a three-with-gap.
        b = board(".....", ".OO..", ".O...", ".....", "X.X.X")
        for seed in range(8):
            m = ai.choose_move(b, O, "medium", rng=random.Random(seed))
            t = b.copy()
            t.play(m, O)
            self.assertGreaterEqual(len(rules.immediate_wins(t, O)), 2, m)

    def test_empty_board_centre(self) -> None:
        for level in ("medium", "hard"):
            self.assertEqual(ai.choose_move(Board(), X, level, rng=random.Random(1)), 12)


class DeterminismTest(unittest.TestCase):
    def test_same_seed_same_move(self) -> None:
        b = random_position(random.Random(11), 8)
        for level in LEVELS:
            a = ai.choose_move(b, X, level, rng=random.Random(42))
            c = ai.choose_move(b, X, level, rng=random.Random(42))
            self.assertEqual(a, c)

    def test_easy_is_weighted_not_uniform_not_fixed(self) -> None:
        rng = random.Random(7)
        picks = [ai.choose_move(Board(), X, "easy", rng=rng) for _ in range(200)]
        inner = {6, 7, 8, 11, 12, 13, 16, 17, 18}
        share = sum(1 for p in picks if p in inner) / len(picks)
        self.assertGreater(share, 0.5)
        self.assertGreater(len(Counter(picks)), 5)


class HardTimingTest(unittest.TestCase):
    def test_hard_under_one_second(self) -> None:
        positions = [Board(), random_position(random.Random(3), 10),
                     random_position(random.Random(4), 6),
                     random_position(random.Random(9), 14)]
        for b in positions:
            player = X if b.cells.count(X) == b.cells.count(O) else O
            start = time.monotonic()
            ai.choose_move(b, player, "hard", rng=random.Random(1))
            self.assertLess(time.monotonic() - start, 1.0)


if __name__ == "__main__":
    unittest.main()
