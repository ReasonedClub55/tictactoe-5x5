"""Round-robin tournament between the AI levels (stdlib only).

Usage: python3 scripts/tournament.py [--games N] [--budget SECONDS] [--seed S]

Each pairing plays N games, alternating who moves first. Prints a
win/draw/loss table from the point of view of the first-named level.
"""

from __future__ import annotations

import argparse
import itertools
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tictactoe5 import ai, rules  # noqa: E402


def play_game(first: str, second: str, budget: float, rng: random.Random) -> str:
    """Play one game; return 'first', 'second' or 'draw'."""
    board = rules.Board()
    levels = {rules.X: first, rules.O: second}
    player = rules.X
    while True:
        move = ai.choose_move(board, player, levels[player], rng=rng, budget=budget)
        board.play(move, player)
        result = rules.status(board)
        if result == rules.X:
            return "first"
        if result == rules.O:
            return "second"
        if result == "draw":
            return "draw"
        player = rules.opponent(player)


def play_pairing(a: str, b: str, games: int, budget: float, rng: random.Random):
    """Return (a_wins, draws, a_losses); a and b alternate moving first."""
    wins = draws = losses = 0
    for g in range(games):
        if g % 2 == 0:
            outcome = play_game(a, b, budget, rng)
            a_won, b_won = outcome == "first", outcome == "second"
        else:
            outcome = play_game(b, a, budget, rng)
            a_won, b_won = outcome == "second", outcome == "first"
        if a_won:
            wins += 1
        elif b_won:
            losses += 1
        else:
            draws += 1
    return wins, draws, losses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=6, help="games per pairing (default 6)")
    parser.add_argument("--budget", type=float, default=0.2, help="expert seconds per move (default 0.2)")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    args = parser.parse_args()
    if args.games < 1 or args.budget <= 0:
        parser.error("--games must be >= 1 and --budget > 0")
    rng = random.Random(args.seed)
    print(f"games per pairing={args.games} expert budget={args.budget}s seed={args.seed}")
    print("(first level's perspective; first move alternates)\n")
    print(f"{'pairing':<20}{'W':>4}{'D':>4}{'L':>4}")
    for a, b in itertools.combinations(ai.LEVELS, 2):
        w, d, l = play_pairing(a, b, args.games, args.budget, rng)
        print(f"{a + ' vs ' + b:<20}{w:>4}{d:>4}{l:>4}", flush=True)


if __name__ == "__main__":
    main()
