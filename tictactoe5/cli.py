"""Terminal interface: menu, turn loop, rendering and session score.

All I/O goes through injected callables so tests need no subprocess. Win and
threat detection is delegated to ``rules``; nothing is re-implemented here.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from . import ai, rules
from .rules import Board, Move

HUMAN = rules.X
COMPUTER = rules.O
HOWTO = "Four in a row wins. Enter moves like b3. q quits."
DIFFICULTY_PROMPT = "Difficulty [e]asy [m]edium [h]ard e[x]pert (default {}): "
FIRST_PROMPT = "Who goes first? [y]ou [c]omputer [r]andom (default {}): "
MOVE_PROMPT = "Your move (e.g. b3, q to quit): "
AGAIN_PROMPT = "Play again? [Y/n] "

LEVEL_KEYS = {"e": "easy", "m": "medium", "h": "hard", "x": "expert"}
FIRST_KEYS = {"y": "you", "c": "computer", "r": "random"}

InputFn = Callable[[str], str]
PrintFn = Callable[[str], None]


class _Quit(Exception):
    """Raised when the player quits (q, Ctrl-C or end of input)."""


class _Score:
    """Session score, kept in memory only."""

    def __init__(self) -> None:
        self.wins = 0
        self.losses = 0
        self.draws = 0

    @property
    def played(self) -> int:
        """Number of finished games."""
        return self.wins + self.losses + self.draws

    def line(self) -> str:
        """Return the score summary line."""
        return f"Score - You {self.wins}  Computer {self.losses}  Draws {self.draws}"


def render(board: Board, win_line: rules.Line | None = None) -> str:
    """Return the board as ASCII; cells of a winning four are [bracketed]."""
    marked = set(win_line or ())
    rows = ["  " + "".join(f" {c} " for c in "abcde")]
    for r in range(rules.SIZE):
        cells = ""
        for c in range(rules.SIZE):
            i = r * rules.SIZE + c
            ch = board.cells[i]
            cells += f"[{ch}]" if i in marked else f" {ch} "
        rows.append(f"{r + 1} {cells}")
    return "\n".join(row.rstrip() for row in rows)


def _pick(text: str, keys: dict[str, str]) -> str | None:
    """Map a full word or first letter (any case) to a value, else None."""
    s = text.strip().lower()
    if len(s) > 16 or not s:
        return None
    for key, word in keys.items():
        if s == key or s == word:
            return word
    return None


class _Session:
    """One run of the program: holds the I/O callables, score and defaults."""

    def __init__(
        self,
        input_fn: InputFn,
        print_fn: PrintFn,
        rng: random.Random,
        budget: float,
        node_limit: int | None,
    ) -> None:
        self.input_fn = input_fn
        self.print = print_fn
        self.rng = rng
        self.budget = budget
        self.node_limit = node_limit
        self.score = _Score()
        self.level = "medium"
        self.first = "you"

    def read(self, prompt: str) -> str:
        """Read a line; q/quit raises _Quit (EOF/Ctrl-C are handled in run)."""
        text = self.input_fn(prompt)
        if text.strip().lower() in ("q", "quit"):
            raise _Quit
        return text

    def ask_choice(self, prompt: str, keys: dict[str, str], default: str) -> str:
        """Ask until the answer is a valid choice; empty means default."""
        while True:
            text = self.read(prompt.format(default[0]))
            if not text.strip():
                return default
            choice = _pick(text, keys)
            if choice:
                return choice
            letters = ", ".join(keys)
            self.print(f"Please answer one of: {letters}.")

    def menu(self) -> str:
        """Ask difficulty and first mover; return who moves first."""
        self.level = self.ask_choice(DIFFICULTY_PROMPT, LEVEL_KEYS, self.level)
        self.first = self.ask_choice(FIRST_PROMPT, FIRST_KEYS, self.first)
        if self.first == "random":
            return self.rng.choice(["you", "computer"])
        return self.first

    def human_move(self, board: Board) -> Move:
        """Prompt until the human enters a legal move."""
        while True:
            parsed = rules.parse_move(self.read(MOVE_PROMPT))
            if parsed.move is None:
                self.print(parsed.error or "Not a move.")
            elif board.cells[parsed.move] != rules.EMPTY:
                self.print(f"{rules.format_move(parsed.move)} is taken.")
            else:
                return parsed.move

    def computer_move(self, board: Board) -> None:
        """Let the AI play, announcing it (and any block of a human threat)."""
        threats = rules.immediate_wins(board, HUMAN)
        if self.level == "expert":
            self.print("Computer is thinking...")
        move = ai.choose_move(
            board,
            COMPUTER,
            self.level,
            rng=self.rng,
            budget=self.budget,
            node_limit=self.node_limit,
        )
        board.play(move, COMPUTER)
        note = " It blocks your threat." if self.level != "easy" and move in threats else ""
        self.print(f"Computer plays {rules.format_move(move)}.{note}")

    def play_game(self, first: str) -> None:
        """Run one game to its end and update the score."""
        board = Board()
        turn = HUMAN if first == "you" else COMPUTER
        while rules.status(board) == "ongoing":
            if turn == HUMAN:
                self.print(render(board))
                board.play(self.human_move(board), HUMAN)
            else:
                self.computer_move(board)
            turn = rules.opponent(turn)
        self.print(render(board, rules.winning_line(board)))
        result = rules.status(board)
        if result == HUMAN:
            self.score.wins += 1
            self.print("You win! Four in a row.")
        elif result == COMPUTER:
            self.score.losses += 1
            self.print("Computer wins this one.")
        else:
            self.score.draws += 1
            if self.level in ("hard", "expert"):
                self.print(f"A draw against {self.level} - that is a real result.")
            else:
                self.print("A draw - well held.")
        self.print(self.score.line())

    def play_again(self) -> bool:
        """Ask whether to play another game."""
        while True:
            text = self.read(AGAIN_PROMPT).strip().lower()
            if text in ("", "y", "yes"):
                return True
            if text in ("n", "no"):
                return False
            self.print("Please answer y or n.")

    def farewell(self) -> None:
        """Say goodbye, with the score if any game finished."""
        self.print("Bye.")
        if self.score.played:
            self.print(self.score.line())

    def loop(self) -> None:
        """Menu -> game -> play again, until the player stops."""
        self.print(HOWTO)
        while True:
            if self.score.played:
                self.print(self.score.line())
            self.play_game(self.menu())
            if not self.play_again():
                return


def run(
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
    rng: random.Random | None = None,
    budget: float = 1.5,
    node_limit: int | None = None,
) -> int:
    """Run the game; always returns 0 (quit, Ctrl-C and EOF are normal exits)."""
    session = _Session(input_fn, print_fn, rng or random.Random(), budget, node_limit)
    try:
        session.loop()
    except (_Quit, KeyboardInterrupt, EOFError):
        print_fn("")  # leave the prompt line
    session.farewell()
    return 0
