"""Computer players: heuristic plus easy, medium, hard and expert strategies.

Pure functions: no printing, no sleeping, and the board passed in is never
mutated. All win detection is delegated to ``rules``.
"""

from __future__ import annotations

import random
import time

from . import rules
from .rules import CELLS, EMPTY, SIZE, WIN_LINES, Board, Move

LEVELS = ("easy", "medium", "hard", "expert")

WIN_SCORE = 10_000  # terminal win, minus ply so faster wins score higher
THREAT_BONUS = 5_000  # side to move has a winning cell / opponent has two
LINE_WEIGHTS = (0, 1, 10, 100)  # by number of marks on a one-sided line
HARD_DEPTH = 4
TT_MAX_ENTRIES = 300_000
CHECK_EVERY = 512  # nodes between clock / node-limit checks
MATE_BOUND = WIN_SCORE - 100  # |score| above this is a proven win or loss
EXACT, LOWER, UPPER = 0, 1, 2  # transposition table bound flags
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


class _Stop(Exception):
    """Raised inside the expert search when the budget runs out."""


class _Expert:
    """Iterative-deepening alpha-beta with a transposition table.

    Approach: search depth 1, 2, 3, ... and keep the best moves of the last
    depth that finished; an interrupted depth is discarded. Depth 1 always
    completes. The table is per call, so nothing leaks between moves.
    """

    def __init__(self, deadline: float, node_limit: int | None) -> None:
        self.deadline = deadline
        self.node_limit = node_limit
        self.nodes = 0
        self.can_stop = False  # False while depth 1 runs, so it always finishes
        self.tt: dict[tuple[tuple[str, ...], str], tuple[int, int, int, Move]] = {}
        self.killers: dict[int, list[Move]] = {}

    def _check_stop(self) -> None:
        if self.node_limit is not None and self.nodes >= self.node_limit:
            raise _Stop
        if time.monotonic() >= self.deadline:
            raise _Stop

    def _order(
        self, board: Board, player: str, moves: list[Move], first: Move, ply: int
    ) -> list[Move]:
        """Best-first: previous/table move, killers, then static priority."""
        killers = self.killers.get(ply, ())

        def key(m: Move) -> tuple[int, int]:
            bonus = 0
            if m == first:
                bonus = 1_000_000
            elif m in killers:
                bonus = 10_000
            return (-(bonus + cell_priority(board, m, player)), m)

        return sorted(moves, key=key)

    def negamax(
        self, board: Board, player: str, depth: int, alpha: int, beta: int, ply: int
    ) -> int:
        """Score for ``player`` to move; mate scores are ply-adjusted."""
        self.nodes += 1
        if self.can_stop and self.nodes % CHECK_EVERY == 0:
            self._check_stop()
        other = rules.opponent(player)
        if rules.immediate_wins(board, player):
            return WIN_SCORE - (ply + 1)
        threats = rules.immediate_wins(board, other)
        if len(threats) >= 2:  # can block only one
            return -(WIN_SCORE - (ply + 2))
        if depth <= 0:
            return evaluate(board, player)
        key = (board.key(), player)
        entry = self.tt.get(key)
        first = -1
        if entry is not None:
            e_depth, e_val, e_flag, first = entry
            if e_depth >= depth:
                value = _from_tt(e_val, ply)
                if e_flag == EXACT:
                    return value
                if e_flag == LOWER:
                    alpha = max(alpha, value)
                elif e_flag == UPPER:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value
        if threats:
            moves = threats  # forced block
        else:
            moves = self._order(board, player, candidates(board), first, ply)
        orig_alpha = alpha
        best = -WIN_SCORE
        best_move = moves[0]
        for m in moves:
            board.play(m, player)
            if rules.is_full(board):
                score = 0
            else:
                score = -self.negamax(board, other, depth - 1, -beta, -alpha, ply + 1)
            board.undo(m)
            if score > best:
                best, best_move = score, m
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        ks = self.killers.setdefault(ply, [])
                        if m not in ks:
                            ks.insert(0, m)
                            del ks[2:]
                        break
        flag = EXACT
        if best <= orig_alpha:
            flag = UPPER
        elif best >= beta:
            flag = LOWER
        if len(self.tt) >= TT_MAX_ENTRIES:
            self.tt.clear()
        self.tt[key] = (depth, _to_tt(best, ply), flag, best_move)
        return best

    def _root(self, board: Board, player: str, depth: int, first: Move) -> tuple[int, list[Move]]:
        """Best value and all root moves tied for it at this depth."""
        other = rules.opponent(player)
        best = -WIN_SCORE - 1
        tied: list[Move] = []
        for m in self._order(board, player, candidates(board), first, 0):
            board.play(m, player)
            if rules.is_full(board):
                score = 0
            else:
                # Window (best-1, inf) keeps moves tied with the best exact.
                score = -self.negamax(board, other, depth - 1, -WIN_SCORE - 1, -(best - 1), 1)
            board.undo(m)
            if score > best:
                best, tied = score, [m]
            elif score == best:
                tied.append(m)
        return best, tied

    def search(self, board: Board, player: str) -> list[Move]:
        """Return the tied best moves of the deepest completed iteration."""
        work = board.copy()
        empties = len(rules.legal_moves(work))
        best_moves: list[Move] = []
        first = -1
        for depth in range(1, empties + 1):
            self.can_stop = depth > 1
            try:
                value, tied = self._root(work, player, depth, first)
            except _Stop:
                break
            best_moves = tied
            first = tied[0]
            if abs(value) >= MATE_BOUND:  # proven win or loss: deeper adds nothing
                break
        return best_moves


def _to_tt(value: int, ply: int) -> int:
    """Make a mate score independent of the ply it was found at."""
    if value >= MATE_BOUND:
        return value + ply
    if value <= -MATE_BOUND:
        return value - ply
    return value


def _from_tt(value: int, ply: int) -> int:
    """Inverse of ``_to_tt``."""
    if value >= MATE_BOUND:
        return value - ply
    if value <= -MATE_BOUND:
        return value + ply
    return value


def _expert_move(
    board: Board, player: str, rng: _Rng, budget: float, node_limit: int | None
) -> Move:
    """Time-bounded iterative deepening, random among equal best moves."""
    cands = candidates(board)
    if len(cands) == 1:
        return cands[0]
    search = _Expert(time.monotonic() + budget, node_limit)
    return rng.choice(search.search(board, player))


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
    if level == "hard":
        return _hard_move(board, player, rng)
    return _expert_move(board, player, rng, budget, node_limit)
