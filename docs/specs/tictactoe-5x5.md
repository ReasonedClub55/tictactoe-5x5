# Spec: 5x5 Tic-Tac-Toe (four in a row)

Status: ready to build. Run: `python -m tictactoe5`. Python 3.12+, stdlib only.

## Goal

A terminal game: human vs computer on a 5x5 board, first to place **four in a row** (horizontal, vertical or diagonal) wins. Four difficulty levels (easy / medium / hard / expert). The original wish "impossible to beat" was dropped in favour of levels; expert is a strong search, **not** a proven solve and must never be described as unbeatable.

Product intent: a draw against a strong level should feel earned (the game says when the computer blocks your threat, and frames a draw as a good result); weaker levels should feel like a mind with habits, not a random mover.

## User stories

1. As a player I pick a difficulty and who moves first, so the game fits my mood.
2. As a player I enter moves like `b3` (columns a-e, rows 1-5) and see a clear board after every move.
3. As a player, bad input gets a short, specific message and another try; it never crashes or costs my turn.
4. As a player I am told when the computer blocks my threat, so I understand why the game is tight.
5. As a player I see a result message, a running session score (Wins / Losses / Draws), and can play again or quit.
6. As a player I can quit anytime with `q`, Ctrl-C or Ctrl-D without a traceback.

## Flow and states

```
START_MENU -> (difficulty, first mover) -> TURN_LOOP -> RESULT -> PLAY_AGAIN? -> START_MENU | EXIT
```

- **Start menu** (each game): prompt `Difficulty [e]asy [m]edium [h]ard e[x]pert (default m):`, then `Who goes first? [y]ou [c]omputer [r]andom (default y):`. Accept full word or first letter, case-insensitive, empty = default. Invalid -> one-line message, re-ask. First menu shows a one-line how-to (`Four in a row wins. Enter moves like b3. q quits.`) and the current score once any game is played. Session score lives in memory only.
- **Turn loop**: human is `X`, computer is `O` (X always shown the same way regardless of who starts). Human turn: show board, prompt `Your move (e.g. b3, q to quit):`. Computer turn: print `Computer is thinking...` (expert only), apply move, print `Computer plays c3.` plus a note if the move blocked a threat (see AC-9).
- **Invalid input** (not a coordinate, out of range, occupied cell, empty line): print one reason (`Not a move. Use a letter a-e and a number 1-5, like b3.` / `c3 is taken.`), re-prompt, no state change. No limit on retries.
- **Win / loss / draw**: board redrawn with the winning four marked (e.g. lowercase-bracketed or `*`), message: win `You win! Four in a row.`, loss `Computer wins this one.`, draw (board full, no four) framed positively: `A draw - well held.` (on hard/expert: `A draw against <level> - that is a real result.`). Score updated once.
- **Play again**: `Play again? [Y/n]`. Yes -> START_MENU (difficulty/first-mover re-asked with previous choices as defaults); no -> print final score, exit 0.
- **Quit**: `q`/`quit` at any prompt, Ctrl-C (`KeyboardInterrupt`) or EOF (`EOFError`) -> print `Bye.` plus session score if any games were finished, exit code 0. A game in progress is abandoned and not scored.

## Acceptance criteria (testable)

Rules
- AC-1: Board is 5x5; there are exactly 28 winning lines of length 4 (10 horizontal, 10 vertical, 8 diagonal). Each line wins; any 4 of 5 in a row/column/diagonal-of-length-5 counts; 3 in a row does not; a non-contiguous four does not.
- AC-2: A full board with no four-in-a-row is a draw; a move that fills the board and makes four is a win, not a draw.
- AC-3: `parse_move` maps `a1`..`e5` (case-insensitive, surrounding whitespace ok) to a cell; rejects `""`, `f1`, `a6`, `a0`, `aa`, `1a`, `a10`, `a 1`, non-ASCII and over-long input with a reason, never raising.

AI (all levels)
- AC-4: AI returns only legal (empty) cells, for every reachable position, including a single empty cell; it never mutates the board passed in.
- AC-5: At every level, if an immediate winning move exists the AI plays it.
- AC-6: Medium, hard and expert: if the opponent has an immediate win and the AI has none, the AI blocks it (if two distinct opponent wins exist it blocks one, legally). Easy is not required to block (stated, tested as "may not").
- AC-7: With a seeded RNG and same position, an AI returns the same move (hard/expert also with a fixed budget/node limit). Easy over 200 seeded moves from the empty board is not uniform: chosen cells are weighted toward the centre/lines (measurable: centre 3x3 chosen more than 50% of the time) yet more than 5 distinct cells appear.
- AC-8: Expert returns within the time budget (default 1.5 s) plus a 0.5 s margin on a mid-game and an empty board; with an injected tiny budget or node limit it still returns a legal move (depth-1 result is always completed). Hard at its fixed depth finishes in under 1 s on those positions.

Product/CLI
- AC-9: When the computer's move occupies the cell where the human had an immediate winning move, output contains `blocks your threat`; it does not appear otherwise. Never printed at easy level.
- AC-10: Scripted sessions (fake `input`/`print` callables) cover: full win, loss, draw, invalid input then valid, play again with changed difficulty, `q` mid-game, EOF at menu, EOF mid-turn, Ctrl-C. Exit code 0 and no traceback in each.
- AC-11: Score line after each game is correct for a scripted win+loss+draw series (`Score - You 1  Computer 1  Draws 1`).
- AC-12: Board render is 5 columns labelled `a b c d e`, rows labelled 1-5, ASCII only, at most 80 columns, readable without colour. Golden-string test for the empty board and one mid-game board.
- AC-13: No files are created or read at runtime; no import outside the stdlib (a test scans package imports); `python -m tictactoe5` starts and exits cleanly on piped `q`.

## Technical approach

Package `tictactoe5/`, tests in `tests/` (stdlib `unittest`; also pytest-compatible).

| Module | Responsibility |
|---|---|
| `rules.py` | Single source of truth. `Board` (immutable-ish tuple of 25 cells, or list with `play`/`undo` for search), `WIN_LINES` (28 precomputed index tuples), `legal_moves`, `winner`, `is_full`, `status` (`ongoing/X/O/draw`), `winning_line`, `parse_move`, `format_move`. No I/O. |
| `ai.py` | `choose_move(board, player, level, *, rng=None, budget=1.5, node_limit=None) -> Move`. Pure; no printing, no sleeping. Contains shared helpers (`immediate_wins`, line scoring) and per-level strategies. |
| `cli.py` | I/O only. `run(input_fn=input, print_fn=print, rng=None, budget=...) -> int`. Menu, turn loop, rendering, score, messages. Takes injected callables so tests need no subprocess. |
| `__main__.py` | `sys.exit(cli.run())` with Ctrl-C/EOF safety net. |

Win detection and threat detection live only in `rules.py`/shared helpers in `ai.py` that call `rules`; the CLI calls `rules.winner` and never re-implements it.

### Per-difficulty AI

All levels first take an immediate win (AC-5).

- **Easy (human-ish, forgiving):** no lookahead and no blocking. Scores each empty cell by the *open lines it extends* (own marks on lines that contain no opponent marks) plus a small centre bonus, then picks by weighted random from all legal cells (weights = score + 1, so every cell is possible). Result: plays near its own marks and the centre, builds lines, and misses your threats. Feels like a casual player, not a dice roll.
- **Medium (solid club player):** win -> block (AC-6) -> otherwise 1-ply heuristic (below), choosing randomly among the top 3 cells by score. Also creates simple double threats if the heuristic finds them (two lines each one move from complete). No search, so deeper traps beat it.
- **Hard (fixed-depth search):** negamax alpha-beta, fixed depth 4 plies (no clock, so deterministic and reproducible), root and inner move ordering by heuristic score, candidate pruning to empty cells within 1 of any occupied cell (all cells if board is empty -> centre). Leaf = heuristic. Win/block forced checks before searching. Random tie-break among equal best.
- **Expert (time-bounded):** iterative deepening alpha-beta (depth 1, 2, 3, ... until the budget, default 1.5 s via `time.monotonic`, deadline checked every ~512 nodes; an interrupted depth is discarded and the last completed depth's best move is used; depth 1 always completes). Features: move ordering = previous-iteration best move first, then killer/threat moves (wins, blocks, creating threes), then heuristic score; transposition table (dict keyed by board tuple + side to move, storing depth, value, bound flag, best move; capped at ~300k entries, cleared when full); threat-based heuristic; forced win/block detection before search; random tie-break among equal best at the final depth; also stops early on a proven forced win or when only one legal move remains. Hard cap depth at the number of empty cells.
- **Threat-based heuristic (shared):** for each of the 28 lines containing only one side's marks, add a weight by count: 1 mark = 1, 2 = 10, 3 = 100 (a three with an open fourth cell is one move from winning). Score = own total - opponent total (+ small centre bonus). A position where the side to move has a three on an open line, or two distinct such lines (double threat), gets a large bonus. Terminal win = +/- 10,000 minus ply (prefer faster wins, slower losses).

Strength is validated empirically, not claimed: expert vs hard and hard vs medium match results are reported in the README as observed, not promised.

### Threat-block message

In `cli.py`, before the computer moves: `threats = rules.immediate_wins(board, human)`. If the chosen move is in `threats` (and level != easy), append `It blocks your threat.` to the move line. Easy never blocks on purpose, so the message essentially never fires there; if it happens by chance it is still accurate to show it only when the condition holds, but the AC says not at easy to keep the "feels like a mind" promise honest.

## Edge cases

- Empty board, computer first: expert/hard/medium take centre (`c3`); easy weighted but may pick any.
- Last empty cell: AI plays it; result is win or draw correctly.
- Board full with a four formed by the final move counts as a win (AC-2).
- Two simultaneous opponent threats: AI blocks one and loses on correct play by opponent; tests accept any legal reply.
- Multiple winning lines made by one move: still one win, score +1.
- Input: `B3`, ` b3 `, `b3\n`; reject `b33`, `b-3`, `3b`, `bb`, Unicode digits (`b³`, full-width `３`), embedded control or escape characters; empty string; extremely long lines (cap read length considered at 64 chars before parsing).
- Windows consoles or terminals without Unicode: ASCII only.
- Terminal narrower than 80 columns: board is 13 columns wide, so safe.
- Clock changes: use `time.monotonic`, not `time.time`.
- Slow machine: expert budget is a wall-clock limit, so it degrades to shallower depth instead of stalling; depth-1 completion is O(25).
- Ctrl-C during expert search: handled by the same quit path.

## Risks and decisions (lens findings folded in)

Lenses applied inline: architecture, testing, product/UX, quick security.

Decisions
- D1: Human is always `X`, computer `O`; "first" only changes who moves first. Keeps rendering and tests simple.
- D2: Hard uses **fixed depth** and expert uses **time**: hard is reproducible and tests are not flaky; only expert has wall-clock behaviour, and it is test-injectable.
- D3: Session score only, in memory; no persistence file (keeps "no files at runtime" invariant).
- D4: No undo, no hints, no colour, no `curses`: minimum for a hobby game and portable on any terminal.
- D5: Expert is described as "strong" only. No "unbeatable"/"perfect" wording in UI, README, or docs. Whether 5x5/4-in-row is a forced draw is not asserted here.

Findings
- [medium] Testing: expert is time-dependent and could flake. Fix: `choose_move` accepts `budget` and `node_limit`; tests use `node_limit` for determinism and only one separate test asserts wall-clock (AC-8, generous 0.5 s margin). Seeded `rng` everywhere.
- [medium] Testing: "strong AI" has no pass/fail oracle. Fix: oracle tests are tactical positions (win-in-1, block-in-1, avoid-lose-in-2 for hard/expert, double-threat creation) plus a seeded tournament script (not in the unit suite) whose results go in the README.
- [medium] Architecture: transposition table could grow unbounded within 1.5 s. Fix: size cap ~300k entries, clear-on-full, TT is per-call (no state between moves), so no leak and no cross-game memory.
- [medium] Architecture: duplicate win logic would drift between AI and CLI. Fix: only `rules.py` knows lines; AI and CLI import from it (invariant in CLAUDE.md); a test checks `WIN_LINES` count (28).
- [medium] Product: a "blocks your threat" message that fires wrongly would undercut trust. Fix: message driven by the same `immediate_wins` helper, AC-9 asserts both presence and absence.
- [low] Product: a draw can read as a letdown. Fix: positive framing (win/draw/loss copy above), plus score line includes draws as a first-class count.
- [low] Product: expert freezes visually up to 1.5 s. Fix: `Computer is thinking...` printed first for expert (and hard if it exceeds ~0.3 s is not needed; hard is fast).
- [low] Security (quick): untrusted input is only keyboard text. Attack path 1: ANSI/escape sequences echoed back in error messages could garble the terminal. Fix: never echo raw input; messages are fixed strings (or `repr`-escaped at most). Path 2: huge pasted line causing slow parsing. Fix: truncate to 64 chars before parsing; parse via exact lookup, not `eval`/`int()` on arbitrary text (`int()` also accepts Unicode digits). Path 3: dependency/supply chain: none, stdlib only (AC-13 import scan). No secrets, network, files, or PII; nothing is logged.
- [low] Testing: first-mover randomness (`r`) is nondeterministic. Fix: inject `rng`.
- Open (no user input needed): board-mark style for the winning line and exact menu copy are left to the implementer within the ACs above.
- Needs user: none. Defaults chosen above are reversible later (e.g. a `--level` CLI flag, colour).

## Plan

Two phases, one PR each. One issue = one commit. Owner persona: Isabelle (implements), Patricia (docs).

| Phase | Issue | Size | Depends on | Owner | Acceptance (one line) |
|---|---|---|---|---|---|
| P0: Core + AI | 1. Rules and board (`rules.py`, `parse_move`, 28 lines) + unit tests | S | none | Isabelle | AC-1, AC-2, AC-3 pass; no I/O in module. |
| P0: Core + AI | 2. Shared heuristic + easy / medium / hard AI + tests | M | 1 | Isabelle | AC-4, AC-5, AC-6, AC-7 (easy part) pass for the three levels; hard under 1 s. |
| P0: Core + AI | 3. Expert iterative-deepening alpha-beta (TT, ordering, budget) + tests | M | 2 | Isabelle | AC-4 to AC-8 pass for expert; returns legal move at tiny budget; within 1.5 s + margin. |
| P1: CLI + docs | 4. CLI, `__main__`, rendering, score, threat-block message + scripted-session tests | M | 1, 2 (expert wired via 3) | Isabelle | AC-9 to AC-13 pass; piped `q` exits 0 with no traceback. |
| P1: CLI + docs | 5. README, run/test instructions, seeded tournament script + honest strength notes | S | 3, 4 | Patricia | README covers run/test/levels; no "unbeatable" wording; tournament results recorded as observed. |

Order: rules -> AI + tests -> CLI -> docs. Issue 4 may start against hard once issue 2 lands, but the phase PR merges after 3. New ideas (colour, `--level` flag, persistence, undo) become new issues, not bigger ones. Tracker: none for this project (user agreed to skip the board); this table is the plan of record.
