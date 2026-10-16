"""Computer players: heuristic, easy, medium and hard strategies.

Pure functions: no printing, no sleeping, and the board passed in is never
mutated. All win detection is delegated to ``rules``.
"""

from __future__ import annotations

import random

from . import rules
from .rules import CELLS, EMPTY, SIZE, WIN_LINES, Board, Move

LEVELS = ("easy", "medium", "hard")

WIN_SCORE = 10_000  # terminal win, minus ply so faster wins score higher
THREAT_BONUS = 5_000  # side to move has a winning cell / opponent has two
LINE_WEIGHTS = (0, 1, 10, 100)  # by number of marks on a one-sided line
HARD_DEPTH = 4
CENTRE = (SIZE * SIZE) // 2

_Rng = random.Random


def _centre_bonus(cell: Move) -> int:
    """Return 4 for the centre, 2 for the ring around it, else 0."""
    row, col = divmod(cell, SIZE)
    dist = max(abs(row - SIZE // 2), abs(col - SIZE // 2))
    return (4, 2, 0)[dist]


CENTRE_BONUS = tuple(_centre_bonus(c) for c in range(CELLS))

# Empty cells within 1 (king move) of each cell, used for candidate pruning.
NEIGHBOURS: tuple[tuple[Move, ...], ...] = tuple(
    tuple(
        (r + dr) * SIZE + c + dc
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr or dc) and 0 <= r + dr < SIZE and 0 <= c + dc < SIZE
    )
    for r, c in (divmod(cell, SIZE) for cell in range(CELLS))
)


def evaluate(board: Board, to_move: str) -> int:
    """Threat-based score of the position for the side to move.

    Every line holding only one side's marks scores 1/10/100 for 1/2/3
    marks; the score is own total minus opponent total plus a small centre
    bonus. A side to move that has a winning cell gets a large bonus, and one
    facing two distinct winning cells (it can block only one) a large penalty.
    """
    cells = board.cells
    other = rules.opponent(to_move)
    own_total = opp_total = 0
    own_wins: set[int] = set()
    opp_wins: set[int] = set()
    for line in WIN_LINES:
        mine = theirs = 0
        gap = -1
        for i in line:
            c = cells[i]
            if c == to_move:
                mine += 1
            elif c == other:
                theirs += 1
            else:
                gap = i
        if theirs == 0:
            own_total += LINE_WEIGHTS[mine]
            if mine == 3:
                own_wins.add(gap)
        elif mine == 0:
            opp_total += LINE_WEIGHTS[theirs]
            if theirs == 3:
                opp_wins.add(gap)
    score = own_total - opp_total
    if cells[CENTRE] == to_move:
        score += 3
    elif cells[CENTRE] == other:
        score -= 3
    if own_wins:
        score += THREAT_BONUS
    elif len(opp_wins) >= 2:
        score -= THREAT_BONUS
    return score


def cell_priority(board: Board, cell: Move, player: str) -> int:
    """Cheap static ordering score for playing ``cell`` (no lookahead).

    Sums, over lines through the cell, the weight of the player's own marks
    on open lines (building) plus the opponent's marks on lines the opponent
    could still use (blocking), plus the centre bonus.
    """
    cells = board.cells
    other = rules.opponent(player)
    total = CENTRE_BONUS[cell]
    for line in rules.LINES_BY_CELL[cell]:
        mine = theirs = 0
        for i in line:
            c = cells[i]
            if c == player:
                mine += 1
            elif c == other:
                theirs += 1
        if theirs == 0:
            total += LINE_WEIGHTS[mine]
        elif mine == 0:
            total += LINE_WEIGHTS[theirs]
    return total


def candidates(board: Board) -> list[Move]:
    """Empty cells within 1 of any mark (the centre on an empty board)."""
    cells = board.cells
    if all(c == EMPTY for c in cells):
        return [CENTRE]
    near: set[int] = set()
    for i, c in enumerate(cells):
        if c != EMPTY:
            near.update(n for n in NEIGHBOURS[i] if cells[n] == EMPTY)
    return sorted(near)


def _forced_move(board: Board, player: str, block: bool, rng: _Rng) -> Move | None:
    """Return an immediate win, else (if ``block``) a block, else None."""
    wins = rules.immediate_wins(board, player)
    if wins:
        return rng.choice(wins)
    if block:
        threats = rules.immediate_wins(board, rules.opponent(player))
        if threats:
            return rng.choice(threats)
    return None


def _easy_move(board: Board, player: str, rng: _Rng) -> Move:
    """Weighted-random mover that builds its own lines and misses threats."""
    other = rules.opponent(player)
    cells = board.cells
    moves = rules.legal_moves(board)
    weights: list[int] = []
    for m in moves:
        score = CENTRE_BONUS[m]
        for line in rules.LINES_BY_CELL[m]:
            if any(cells[i] == other for i in line):
                continue
            score += sum(1 for i in line if cells[i] == player)
        weights.append(score + 1)
    return rng.choices(moves, weights=weights)[0]


def _medium_move(board: Board, player: str, rng: _Rng) -> Move:
    """One-ply heuristic: best of the top three cells, forks taken outright."""
    other = rules.opponent(player)
    scored: list[tuple[int, Move]] = []
    work = board.copy()
    for m in rules.legal_moves(work):
        work.play(m, player)
        if rules.is_full(work):
            score = 0
        else:
            score = -evaluate(work, other)
        work.undo(m)
        scored.append((score, m))
    scored.sort(key=lambda t: (-t[0], t[1]))
    if scored[0][0] >= THREAT_BONUS // 2:  # creates a double threat: take it
        best = [m for s, m in scored if s == scored[0][0]]
        return rng.choice(best)
    return rng.choice([m for _, m in scored[:3]])


class _Search:
    """Fixed-depth negamax with alpha-beta and heuristic move ordering."""

    def __init__(self) -> None:
        self.nodes = 0

    def ordered(self, board: Board, player: str) -> list[Move]:
        """Candidate moves, most promising first (ties by cell index)."""
        moves = candidates(board)
        moves.sort(key=lambda m: (-cell_priority(board, m, player), m))
        return moves

    def negamax(
        self, board: Board, player: str, depth: int, alpha: int, beta: int, ply: int
    ) -> int:
        """Score of the position for ``player`` to move, searching ``depth``."""
        self.nodes += 1
        other = rules.opponent(player)
        best = -WIN_SCORE
        for m in self.ordered(board, player):
            board.play(m, player)
            if rules.completes_four(board, m, player):
                score = WIN_SCORE - (ply + 1)
            elif rules.is_full(board):
                score = 0
            elif depth <= 1:
                score = -evaluate(board, other)
            else:
                score = -self.negamax(board, other, depth - 1, -beta, -alpha, ply + 1)
            board.undo(m)
            if score > best:
                best = score
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        break
        return best

    def best_root_moves(self, board: Board, player: str, depth: int) -> list[Move]:
        """All root moves tied for the best value at ``depth`` plies."""
        other = rules.opponent(player)
        best = -WIN_SCORE - 1
        best_moves: list[Move] = []
        for m in self.ordered(board, player):
            board.play(m, player)
            if rules.completes_four(board, m, player):
                score = WIN_SCORE - 1
            elif rules.is_full(board):
                score = 0
            elif depth <= 1:
                score = -evaluate(board, other)
            else:
                # Window (best-1, inf) keeps ties with the best exact.
                score = -self.negamax(board, other, depth - 1, -WIN_SCORE - 1, -(best - 1), 1)
            board.undo(m)
            if score > best:
                best, best_moves = score, [m]
            elif score == best:
                best_moves.append(m)
        return best_moves


def _hard_move(board: Board, player: str, rng: _Rng) -> Move:
    """Depth-4 alpha-beta, random among equal best moves."""
    moves = _Search().best_root_moves(board.copy(), player, HARD_DEPTH)
    return rng.choice(moves)


def choose_move(
    board: Board,
    player: str,
    level: str,
    *,
    rng: random.Random | None = None,
    budget: float = 1.5,
    node_limit: int | None = None,
) -> Move:
    """Pick a legal move for ``player`` at the given difficulty.

    ``budget`` (seconds) and ``node_limit`` bound the expert search only.
    The board is never mutated. Raises ValueError for a full board or an
    unknown level.
    """
    if level not in LEVELS:
        raise ValueError(f"unknown level {level!r}")
    if rules.is_full(board):
        raise ValueError("no legal moves")
    rng = rng or random.Random()
    moves = rules.legal_moves(board)
    if len(moves) == 1:
        return moves[0]
    # Every level takes an immediate win; medium and up also block.
    forced = _forced_move(board, player, block=level != "easy", rng=rng)
    if forced is not None:
        return forced
    if level == "easy":
        return _easy_move(board, player, rng)
    if level == "medium":
        return _medium_move(board, player, rng)
    return _hard_move(board, player, rng)
