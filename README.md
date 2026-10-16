# tictactoe-5x5

A terminal game: tic-tac-toe on a 5x5 board where **four in a row** (horizontal, vertical or diagonal) wins. You play against the computer at one of four difficulty levels.

## Requirements

Python 3.12+. Standard library only: nothing to install, no network, no files written.

## Run

```
python3 -m tictactoe5
```

## How to play

- You are X, the computer is O. Columns are letters `a`-`e`, rows are numbers `1`-`5`.
- Enter a move as letter + number, for example `b3` (case does not matter).
- At the start of each game a menu asks for the difficulty (`e`asy, `m`edium, `h`ard, e`x`pert; default medium) and who goes first (`y`ou, `c`omputer, `r`andom). Press Enter to accept the default.
- The computer announces its move, and says when it blocks your threat (medium and up).
- Type `q` (or `quit`, Ctrl-C, or end of input) at any prompt to quit. A running score is shown across games, and you are asked whether to play again after each one.

## Difficulty levels

| Level | What it does |
|---|---|
| easy | Mostly random, leaning towards the centre and towards cells that extend its own lines. Takes a win if one is available, but does **not** block yours. |
| medium | Looks one move ahead with a threat-based score and picks among its top three moves. Takes wins, always blocks an immediate loss, and grabs a double threat when it sees one. |
| hard | Fixed-depth search, 4 plies (alpha-beta), choosing randomly among equally good moves. Takes wins and blocks. |
| expert | Iterative-deepening alpha-beta search with a transposition table and a time budget per move (default 1.5 s), keeping the result of the deepest search that finished. Takes wins and blocks. |

Expert is a strong search, not a solved game: it is **not** guaranteed to be unbeatable, and a slow machine means a shallower search. A draw against hard or expert is a real result.

## Tests

```
python3 -m unittest discover -s tests -v
```

## AI tournament

`scripts/tournament.py` plays the levels against each other (every pairing, alternating who moves first) and prints wins/draws/losses from the first-named level's point of view.

```
python3 scripts/tournament.py --games 4 --seed 1
```

Options: `--games` per pairing (default 6), `--budget` expert seconds per move (default 0.2), `--seed`.

Example, observed on one run with `--games 4 --budget 0.2 --seed 1` (about 12 s). With only four games per pairing this is a sanity check, not a strength measurement:

```
pairing                W   D   L
easy vs medium         0   0   4
easy vs hard           0   0   4
easy vs expert         0   0   4
medium vs hard         0   0   4
medium vs expert       0   1   3
hard vs expert         0   4   0
```

## How it was built

The idea was discussed in a Dream Team session (Eon, Joss), then planned and built with the engsys lite profile: Jody wrote the spec, Isabelle implemented, Patricia wrote the docs. The spec and plan are in `docs/specs/tictactoe-5x5.md`.
