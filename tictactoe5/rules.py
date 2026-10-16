"""Game rules: the single source of truth for lines, wins and draws.

No I/O lives here. Cells are indexed 0..24 as ``row * 5 + col``; ``a1`` is 0,
``e1`` is 4, ``a5`` is 20 and ``e5`` is 24.
"""

from __future__ import annotations

from typing import NamedTuple

SIZE = 5
WIN_LENGTH = 4
CELLS = SIZE * SIZE
EMPTY = "."
X = "X"
O = "O"  # noqa: E741 - the mark is called O
MAX_INPUT_LEN = 64

Move = int
Line = tuple[int, ...]


def _build_win_lines() -> tuple[Line, ...]:
    """Return every run of WIN_LENGTH cells in a row, column or diagonal."""
    lines: list[Line] = []
    for row in range(SIZE):
        for col in range(SIZE):
            # right, down, down-right, down-left
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r = row + dr * (WIN_LENGTH - 1)
                end_c = col + dc * (WIN_LENGTH - 1)
                if 0 <= end_r < SIZE and 0 <= end_c < SIZE:
                    lines.append(
                        tuple(
                            (row + dr * i) * SIZE + col + dc * i
                            for i in range(WIN_LENGTH)
                        )
                    )
    return tuple(lines)


WIN_LINES: tuple[Line, ...] = _build_win_lines()


def opponent(player: str) -> str:
    """Return the other player's mark."""
    return O if player == X else X


class Board:
    """A mutable 5x5 board supporting ``play``/``undo`` for search."""

    __slots__ = ("cells",)

    def __init__(self, cells: list[str] | tuple[str, ...] | None = None) -> None:
        """Create an empty board, or one from 25 cells of 'X', 'O' or '.'."""
        if cells is None:
            self.cells: list[str] = [EMPTY] * CELLS
        else:
            if len(cells) != CELLS:
                raise ValueError(f"a board needs {CELLS} cells")
            if any(c not in (X, O, EMPTY) for c in cells):
                raise ValueError("cells must be 'X', 'O' or '.'")
            self.cells = list(cells)

    @classmethod
    def from_rows(cls, rows: list[str] | tuple[str, ...]) -> Board:
        """Build a board from 5 strings of 5 characters (row 1 first)."""
        if len(rows) != SIZE or any(len(r) != SIZE for r in rows):
            raise ValueError("expected 5 rows of 5 characters")
        return cls(list("".join(rows)))

    def copy(self) -> Board:
        """Return an independent copy."""
        return Board(self.cells)

    def key(self) -> tuple[str, ...]:
        """Return a hashable snapshot of the position."""
        return tuple(self.cells)

    def play(self, move: Move, player: str) -> None:
        """Place ``player`` on an empty cell; raise ValueError if illegal."""
        if not 0 <= move < CELLS:
            raise ValueError(f"move {move} is off the board")
        if self.cells[move] != EMPTY:
            raise ValueError(f"cell {format_move(move)} is taken")
        self.cells[move] = player

    def undo(self, move: Move) -> None:
        """Clear a cell (the inverse of ``play``)."""
        self.cells[move] = EMPTY

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Board) and self.cells == other.cells

    def __hash__(self) -> int:
        return hash(self.key())

    def __repr__(self) -> str:
        return "Board(" + "".join(self.cells) + ")"


def legal_moves(board: Board) -> list[Move]:
    """Return all empty cells in index order."""
    return [i for i, c in enumerate(board.cells) if c == EMPTY]


def winning_line(board: Board) -> Line | None:
    """Return the first completed four, or None."""
    cells = board.cells
    for line in WIN_LINES:
        first = cells[line[0]]
        if first != EMPTY and all(cells[i] == first for i in line):
            return line
    return None


def winner(board: Board) -> str | None:
    """Return 'X' or 'O' if that player has four in a row, else None."""
    line = winning_line(board)
    return board.cells[line[0]] if line else None


def is_full(board: Board) -> bool:
    """Return True when no empty cell remains."""
    return EMPTY not in board.cells


def status(board: Board) -> str:
    """Return 'X' or 'O' (that side won), 'draw', or 'ongoing'.

    A win takes precedence over a full board (the last move may make four).
    """
    won = winner(board)
    if won:
        return won
    return "draw" if is_full(board) else "ongoing"


def immediate_wins(board: Board, player: str) -> list[Move]:
    """Return empty cells where ``player`` would complete four in a row."""
    cells = board.cells
    wins: list[Move] = []
    for line in WIN_LINES:
        mine = 0
        gap = -1
        for i in line:
            c = cells[i]
            if c == player:
                mine += 1
            elif c == EMPTY:
                gap = i
            else:
                break
        else:
            if mine == WIN_LENGTH - 1 and gap not in wins:
                wins.append(gap)
    return sorted(wins)


class ParseResult(NamedTuple):
    """Outcome of ``parse_move``: exactly one of the fields is set."""

    move: Move | None
    error: str | None


_BAD_FORMAT = "Not a move. Use a letter a-e and a number 1-5, like b3."
_COLS = "abcde"
_ROWS = "12345"


def parse_move(text: str) -> ParseResult:
    """Parse text like ``b3`` (case-insensitive, whitespace trimmed).

    Never raises and never echoes the input. Uses exact character lookup so
    Unicode digits and control characters are rejected.
    """
    if not isinstance(text, str) or len(text) > MAX_INPUT_LEN:
        return ParseResult(None, _BAD_FORMAT)
    s = text.strip().lower()
    if len(s) != 2 or s[0] not in _COLS or s[1] not in _ROWS:
        return ParseResult(None, _BAD_FORMAT)
    return ParseResult(_ROWS.index(s[1]) * SIZE + _COLS.index(s[0]), None)


def format_move(move: Move) -> str:
    """Return the coordinate name of a cell, e.g. 12 -> 'c3'."""
    return _COLS[move % SIZE] + _ROWS[move // SIZE]
