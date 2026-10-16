"""Scripted-session tests for the CLI (AC-9 to AC-13)."""

import ast
import os
import pathlib
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tictactoe5 import cli, rules
from tictactoe5.rules import Board, format_move

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_EMPTY = """\
   a  b  c  d  e
1  .  .  .  .  .
2  .  .  .  .  .
3  .  .  .  .  .
4  .  .  .  .  .
5  .  .  .  .  ."""
GOLDEN_MID = """\
   a  b  c  d  e
1  X  .  .  .  .
2  .  O  O  .  .
3  .  X  .  .  .
4  .  .  .  .  .
5  .  .  .  .  ."""


def cell(name: str) -> int:
    res = rules.parse_move(name)
    assert res.move is not None
    return res.move


class Script:
    """Fake input/print plus a scripted computer."""

    def __init__(self, inputs: list, computer: list[str] | None = None) -> None:
        self.inputs = list(inputs)
        self.computer = [cell(c) for c in (computer or [])]
        self.out: list[str] = []
        self.levels: list[str] = []
        self.prompts: list[str] = []

    def input(self, prompt: str = "") -> str:
        self.prompts.append(prompt)
        if not self.inputs:
            raise EOFError
        item = self.inputs.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def choose(self, board, player, level, **kwargs):
        self.levels.append(level)
        return self.computer.pop(0)

    def run(self) -> int:
        with mock.patch("tictactoe5.cli.ai.choose_move", self.choose):
            return cli.run(self.input, self.out.append, rng=random.Random(1))

    @property
    def text(self) -> str:
        return "\n".join(self.out)

    def assert_clean(self, tc: unittest.TestCase) -> None:
        tc.assertNotIn("Traceback", self.text)


def draw_moves() -> tuple[list[str], list[str]]:
    final = ["XXOOX", "OOXXO", "XXOOX", "OOXXO", "XXOOX"]
    xs, os_ = [], []
    for r, row in enumerate(final):
        for c, ch in enumerate(row):
            (xs if ch == "X" else os_).append("abcde"[c] + str(r + 1))
    return xs, os_


class RenderTest(unittest.TestCase):
    def test_empty_golden(self) -> None:
        self.assertEqual(cli.render(Board()), GOLDEN_EMPTY)

    def test_midgame_golden(self) -> None:
        b = Board()
        b.play(cell("a1"), "X")
        b.play(cell("b2"), "O")
        b.play(cell("c2"), "O")
        b.play(cell("b3"), "X")
        self.assertEqual(cli.render(b), GOLDEN_MID)

    def test_ascii_and_width(self) -> None:
        b = Board.from_rows(["XXXX.", "OOO..", ".....", ".....", "....."])
        text = cli.render(b, rules.winning_line(b))
        self.assertTrue(text.isascii())
        self.assertLessEqual(max(len(line) for line in text.splitlines()), 80)
        self.assertIn("[X][X][X][X]", text)


class GameFlowTest(unittest.TestCase):
    def test_full_win(self) -> None:
        s = Script(["e", "y", "a1", "b1", "c1", "d1", "n"], ["a3", "b3", "c3"])
        self.assertEqual(s.run(), 0)
        self.assertIn("You win! Four in a row.", s.text)
        self.assertIn("[X][X][X][X]", s.text)
        self.assertIn("Score - You 1  Computer 0  Draws 0", s.text)
        s.assert_clean(self)

    def test_loss(self) -> None:
        s = Script(["e", "y", "a3", "b3", "c3", "a5", "n"], ["a1", "b1", "c1", "d1"])
        self.assertEqual(s.run(), 0)
        self.assertIn("Computer wins this one.", s.text)
        self.assertIn("Score - You 0  Computer 1  Draws 0", s.text)

    def test_draw_positive_framing(self) -> None:
        xs, os_ = draw_moves()
        inputs = ["e", "y"] + xs + ["n"]
        s = Script(inputs, os_)
        self.assertEqual(s.run(), 0)
        self.assertIn("A draw - well held.", s.text)
        self.assertIn("Draws 1", s.text)

    def test_draw_hard_wording(self) -> None:
        xs, os_ = draw_moves()
        s = Script(["h", "y"] + xs + ["n"], os_)
        s.run()
        self.assertIn("A draw against hard - that is a real result.", s.text)

    def test_computer_first(self) -> None:
        s = Script(["m", "c", "a1", "b1", "c1", "n"], ["a3", "b3", "c3", "d3"])
        s.run()
        self.assertEqual(s.out[1], "Computer plays a3.")  # before any board
        self.assertIn("Computer wins this one.", s.text)

    def test_score_series_win_loss_draw(self) -> None:
        xs, os_ = draw_moves()
        inputs = (["e", "y", "a1", "b1", "c1", "d1", "y"]
                  + ["", "", "a3", "b3", "c3", "a5", "y"]
                  + ["", ""] + xs + ["n"])
        comp = ["a3", "b3", "c3"] + ["a1", "b1", "c1", "d1"] + os_
        s = Script(inputs, comp)
        self.assertEqual(s.run(), 0)
        lines = [ln for ln in s.out if ln.startswith("Score -")]
        self.assertIn("Score - You 1  Computer 1  Draws 1", lines)
        self.assertEqual(lines[0], "Score - You 1  Computer 0  Draws 0")
        s.assert_clean(self)

    def test_invalid_then_valid_costs_no_turn(self) -> None:
        s = Script(["e", "y", "", "zz", "a1\x1b[A", "f9", "b3", "b3", "q"], ["c3"])
        self.assertEqual(s.run(), 0)
        self.assertEqual(s.text.count("Not a move."), 4)
        self.assertIn("b3 is taken.", s.text)
        self.assertNotIn("\x1b", s.text)
        self.assertNotIn("zz", s.text)
        self.assertEqual(s.levels, ["easy"])  # only one computer move happened

    def test_play_again_changes_difficulty_and_defaults(self) -> None:
        s = Script(["e", "y", "a1", "b1", "c1", "d1", "y", "h", "", "q"], ["a3", "b3", "c3"])
        s.computer.append(cell("c3"))  # unused spare
        self.assertEqual(s.run(), 0)
        menu_prompts = [p for p in s.prompts if p.startswith("Difficulty")]
        self.assertTrue(menu_prompts[0].endswith("(default m): "))
        self.assertTrue(menu_prompts[1].endswith("(default e): "))
        first_prompts = [p for p in s.prompts if p.startswith("Who goes first")]
        self.assertTrue(first_prompts[1].endswith("(default y): "))
        self.assertIn("Bye.", s.text)

    def test_second_game_uses_new_level(self) -> None:
        s = Script(["e", "y", "a1", "b1", "c1", "d1", "y", "hard", "y", "a1", "q"],
                   ["a3", "b3", "c3", "c3"])
        s.run()
        self.assertEqual(s.levels, ["easy", "easy", "easy", "hard"])

    def test_menu_words_and_invalid(self) -> None:
        s = Script(["EXPERT", "zzz", "Computer", "q"])
        s.computer = [cell("c3")]
        s.run()
        self.assertIn("Please answer one of", s.text)
        self.assertEqual(s.levels, ["expert"])
        self.assertIn("Computer is thinking...", s.text)


class ThreatMessageTest(unittest.TestCase):
    def run_block(self, level_key: str, reply: str) -> Script:
        s = Script([level_key, "y", "a1", "b1", "c1", "q"], ["a3", "b3", reply])
        s.run()
        return s

    def test_blocks_message_at_medium(self) -> None:
        s = self.run_block("m", "d1")
        self.assertIn("Computer plays d1. It blocks your threat.", s.text)
        self.assertEqual(s.text.count("blocks your threat"), 1)

    def test_not_shown_when_not_blocking(self) -> None:
        s = self.run_block("m", "e5")
        self.assertNotIn("blocks your threat", s.text)

    def test_never_at_easy(self) -> None:
        s = self.run_block("e", "d1")
        self.assertNotIn("blocks your threat", s.text)

    def test_real_ai_blocks_and_says_so(self) -> None:
        # Real medium AI, no mocks: it must block a1 b1 c1 with d1.
        board = Board.from_rows(["XXX..", "O.O..", ".....", ".....", "....."])
        sess = cli._Session(lambda _p: "", lambda _t: None, random.Random(3), 1.5, None)
        sess.level = "medium"
        out: list[str] = []
        sess.print = out.append
        sess.computer_move(board)
        self.assertIn("It blocks your threat.", out[-1])
        self.assertEqual(board.cells[3], "O")


class QuitTest(unittest.TestCase):
    def check(self, inputs: list, in_game: bool = False) -> Script:
        s = Script(inputs, ["c3", "c3"])
        self.assertEqual(s.run(), 0)
        s.assert_clean(self)
        self.assertIn("Bye.", s.text)
        return s

    def test_q_at_menu(self) -> None:
        s = self.check(["q"])
        self.assertNotIn("Score", s.text)

    def test_quit_word_mid_game(self) -> None:
        s = self.check(["e", "y", "a1", "QUIT"])
        self.assertNotIn("Score", s.text)  # abandoned game is not scored

    def test_eof_at_menu(self) -> None:
        self.check([])

    def test_eof_mid_turn(self) -> None:
        self.check(["e", "y", "a1"])

    def test_ctrl_c_at_menu_and_mid_game(self) -> None:
        self.check([KeyboardInterrupt()])
        self.check(["e", "y", KeyboardInterrupt()])

    def test_quit_after_game_shows_score(self) -> None:
        s = Script(["e", "y", "a1", "b1", "c1", "d1", "q"], ["a3", "b3", "c3"])
        self.assertEqual(s.run(), 0)
        self.assertEqual(s.text.count("Score - You 1  Computer 0  Draws 0"), 2)

    def test_play_again_invalid_then_no(self) -> None:
        s = Script(["e", "y", "a1", "b1", "c1", "d1", "maybe", "no"], ["a3", "b3", "c3"])
        self.assertEqual(s.run(), 0)
        self.assertIn("Please answer y or n.", s.text)


class ProcessTest(unittest.TestCase):
    def run_main(self, stdin: str) -> tuple[subprocess.CompletedProcess, list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
            proc = subprocess.run(
                [sys.executable, "-m", "tictactoe5"], input=stdin, text=True,
                capture_output=True, cwd=tmp, env=env, timeout=20,
            )
            return proc, os.listdir(tmp)

    def test_piped_q(self) -> None:
        proc, files = self.run_main("q\n")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, "")
        self.assertIn("Bye.", proc.stdout)
        self.assertEqual(files, [])

    def test_piped_eof_mid_game(self) -> None:
        proc, files = self.run_main("m\ny\na1\n")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        self.assertEqual(files, [])


class ImportScanTest(unittest.TestCase):
    def test_only_stdlib_imports(self) -> None:
        for path in (ROOT / "tictactoe5").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:  # relative import inside the package
                        continue
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    self.assertIn(name.split(".")[0], sys.stdlib_module_names, (path, name))

    def test_no_file_io_in_package(self) -> None:
        for path in (ROOT / "tictactoe5").glob("*.py"):
            text = path.read_text()
            self.assertNotIn("open(", text, path)

    def test_format_move_roundtrip(self) -> None:
        self.assertEqual(format_move(cell("c3")), "c3")


if __name__ == "__main__":
    unittest.main()
