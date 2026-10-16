"""Tests for tictactoe5.rules (AC-1, AC-2, AC-3)."""

import unittest

from tictactoe5 import rules
from tictactoe5.rules import Board, O, X


def board(*rows: str) -> Board:
    return Board.from_rows(rows)


class WinLinesTest(unittest.TestCase):
    def test_counts(self) -> None:
        self.assertEqual(len(rules.WIN_LINES), 28)
        self.assertEqual(len(set(rules.WIN_LINES)), 28)

    def test_every_line_wins(self) -> None:
        for line in rules.WIN_LINES:
            for p in (X, O):
                b = Board()
                for i in line:
                    b.play(i, p)
                self.assertEqual(rules.winner(b), p, line)
                self.assertEqual(rules.winning_line(b), line)
                self.assertEqual(rules.status(b), p)

    def test_four_of_five_anywhere(self) -> None:
        for cells in ([0, 1, 2, 3], [1, 2, 3, 4]):
            b = Board()
            for i in cells:
                b.play(i, X)
            self.assertEqual(rules.winner(b), X)
        b = Board()
        for i in (0, 6, 12, 18):  # diagonal
            b.play(i, O)
        self.assertEqual(rules.winner(b), O)

    def test_three_does_not_win(self) -> None:
        b = board("XXX..", ".....", ".....", ".....", ".....")
        self.assertIsNone(rules.winner(b))
        self.assertEqual(rules.status(b), "ongoing")

    def test_non_contiguous_four_does_not_win(self) -> None:
        b = board("XX.XX", ".....", ".....", ".....", ".....")
        self.assertIsNone(rules.winner(b))

    def test_wrap_around_is_not_a_line(self) -> None:
        b = board("...XX", "XX...", ".....", ".....", ".....")
        self.assertIsNone(rules.winner(b))

    def test_mixed_line_does_not_win(self) -> None:
        b = board("XXOX.", ".....", ".....", ".....", ".....")
        self.assertIsNone(rules.winner(b))


class StatusTest(unittest.TestCase):
    def test_empty_is_ongoing(self) -> None:
        self.assertEqual(rules.status(Board()), "ongoing")

    def test_full_board_without_four_is_draw(self) -> None:
        b = board("XXOOX", "OOXXO", "XXOOX", "OOXXO", "XXOOX")
        self.assertIsNone(rules.winner(b))
        self.assertTrue(rules.is_full(b))
        self.assertEqual(rules.status(b), "draw")

    def test_last_move_making_four_is_win_not_draw(self) -> None:
        b = board("OXXOO", "XOOOX", "XXXOX", "XOOXX", "OXXO.")
        self.assertEqual(rules.status(b), "ongoing")
        b.play(24, X)
        self.assertTrue(rules.is_full(b))
        self.assertEqual(rules.status(b), X)

    def test_play_undo_and_illegal(self) -> None:
        b = Board()
        b.play(12, X)
        with self.assertRaises(ValueError):
            b.play(12, O)
        with self.assertRaises(ValueError):
            b.play(25, O)
        b.undo(12)
        self.assertEqual(b, Board())
        self.assertEqual(rules.legal_moves(b), list(range(25)))

    def test_completes_four(self) -> None:
        b = board("XXX..", ".....", ".....", ".....", ".....")
        self.assertFalse(rules.completes_four(b, 2, X))
        b.play(3, X)
        self.assertTrue(rules.completes_four(b, 3, X))
        self.assertFalse(rules.completes_four(b, 3, O))

    def test_immediate_wins(self) -> None:
        b = board("XXX..", ".....", ".....", ".....", ".....")
        self.assertEqual(rules.immediate_wins(b, X), [3])
        self.assertEqual(rules.immediate_wins(b, O), [])
        b = board("XXX.X", ".....", ".....", ".....", ".....")
        self.assertEqual(rules.immediate_wins(b, X), [3])
        b = board("XXXX.", ".....", ".....", ".....", ".....")
        self.assertEqual(rules.immediate_wins(b, X), [4])


class ParseMoveTest(unittest.TestCase):
    def test_all_cells(self) -> None:
        for r in range(5):
            for c in range(5):
                name = "abcde"[c] + str(r + 1)
                for variant in (name, name.upper(), f"  {name}\n"):
                    res = rules.parse_move(variant)
                    self.assertEqual(res.move, r * 5 + c)
                    self.assertIsNone(res.error)
                self.assertEqual(rules.format_move(r * 5 + c), name)

    def test_rejects(self) -> None:
        bad = ["", " ", "f1", "a6", "a0", "aa", "1a", "a10", "a 1", "b33",
               "b-3", "3b", "b³", "b３", "\x1b[A", "b3\x00",
               "q" * 500, "١a", "b٣"]
        for text in bad:
            res = rules.parse_move(text)
            self.assertIsNone(res.move, repr(text))
            self.assertTrue(res.error)
            self.assertNotIn(text.strip() or "\0", res.error)

    def test_non_str_does_not_raise(self) -> None:
        res = rules.parse_move(None)  # type: ignore[arg-type]
        self.assertIsNone(res.move)


if __name__ == "__main__":
    unittest.main()
