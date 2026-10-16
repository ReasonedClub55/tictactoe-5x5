"""Tests for the expert AI (AC-4 to AC-8). Search is bounded by node limits."""

import random
import time
import unittest

from tictactoe5 import ai, rules
from tictactoe5.rules import Board, O, X

LIMIT = 3000  # nodes: deterministic and fast


def board(*rows: str) -> Board:
    return Board.from_rows(rows)


def expert(b: Board, player: str, seed: int = 1, **kw) -> int:
    kw.setdefault("node_limit", LIMIT)
    kw.setdefault("budget", 30.0)
    return ai.choose_move(b, player, "expert", rng=random.Random(seed), **kw)


def random_position(rng: random.Random, plies: int) -> Board:
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


class ExpertLegalityTest(unittest.TestCase):
    def test_legal_and_no_mutation(self) -> None:
        rng = random.Random(21)
        for plies in (0, 1, 4, 9, 14, 20, 23):
            for _ in range(3):
                b = random_position(rng, plies)
                player = X if plies % 2 == 0 else O
                before = b.key()
                m = expert(b, player, node_limit=800)
                self.assertEqual(b.key(), before)
                self.assertIn(m, rules.legal_moves(b), plies)

    def test_single_empty_cell(self) -> None:
        b = board("XXOOX", "OOXXO", "XXOOX", "OOXXO", "XXOO.")
        self.assertEqual(expert(b, X), 24)

    def test_tiny_limit_still_legal(self) -> None:
        b = random_position(random.Random(5), 8)
        for limit in (1, 2, 10):
            self.assertIn(expert(b, X, node_limit=limit), rules.legal_moves(b))
        self.assertIn(expert(b, X, budget=0.0, node_limit=None), rules.legal_moves(b))


class ExpertTacticsTest(unittest.TestCase):
    def test_takes_win(self) -> None:
        b = board("XXX..", "OOO..", ".....", ".X...", ".....")
        self.assertEqual(expert(b, O), 8)

    def test_blocks(self) -> None:
        b = board("XXX..", "O.O..", ".....", ".....", ".....")
        for seed in range(5):
            self.assertEqual(expert(b, O, seed), 3)

    def test_two_threats_blocks_one(self) -> None:
        b = board("XXX..", ".....", "X....", "X....", "O.O..")
        self.assertIn(expert(b, O), set(rules.immediate_wins(b, X)))

    def test_empty_board_centre(self) -> None:
        self.assertEqual(expert(Board(), X), 12)

    def test_avoids_loss_in_two(self) -> None:
        b = board(".XX..", ".....", ".....", ".....", "O...O")
        m = expert(b, O)
        after = b.copy()
        after.play(m, O)
        for x in rules.legal_moves(after):
            t = after.copy()
            t.play(x, X)
            self.assertLess(len(rules.immediate_wins(t, X)), 2, (m, x))

    def test_finds_forced_win_in_two(self) -> None:
        # O (to move) can make two simultaneous threes-with-gap: a double
        # threat wins by force; expert should find a winning move.
        b = board(".....", ".OO..", ".O...", ".....", "X.X.X")
        m = expert(b, O)
        t = b.copy()
        t.play(m, O)
        self.assertGreaterEqual(len(rules.immediate_wins(t, O)), 2)

    def test_plays_out_game_vs_hard_without_illegal_moves(self) -> None:
        rng = random.Random(8)
        b = Board()
        player = X
        while rules.status(b) == "ongoing":
            if player == X:
                m = expert(b, X, node_limit=400)
            else:
                m = ai.choose_move(b, O, "hard", rng=rng)
            self.assertIn(m, rules.legal_moves(b))
            b.play(m, player)
            player = rules.opponent(player)


class ExpertDeterminismTest(unittest.TestCase):
    def test_same_seed_and_limit_same_move(self) -> None:
        b = random_position(random.Random(12), 9)
        a = expert(b, O, seed=4, node_limit=2000)
        c = expert(b, O, seed=4, node_limit=2000)
        self.assertEqual(a, c)


class ExpertTimingTest(unittest.TestCase):
    def test_within_budget_plus_margin(self) -> None:
        for b in (Board(), random_position(random.Random(3), 8)):
            player = X if b.cells.count(X) == b.cells.count(O) else O
            start = time.monotonic()
            m = ai.choose_move(b, player, "expert", rng=random.Random(1), budget=0.4)
            self.assertLess(time.monotonic() - start, 0.4 + 0.5)
            self.assertIn(m, rules.legal_moves(b))

    def test_default_budget_midgame(self) -> None:
        b = random_position(random.Random(3), 8)
        player = X if b.cells.count(X) == b.cells.count(O) else O
        start = time.monotonic()
        ai.choose_move(b, player, "expert", rng=random.Random(1))
        self.assertLess(time.monotonic() - start, 1.5 + 0.5)


if __name__ == "__main__":
    unittest.main()
