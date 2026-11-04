"""Choose one worktree, by fuzzy query or from a numbered list."""

from __future__ import annotations

import sys
from typing import TextIO

from .fuzzy import CLEAR_MARGIN, rank
from .worktrees import Worktree


class NothingPicked(Exception):
    """No worktree matched, or the user did not pick one."""


def match_keys(wt: Worktree) -> list[str]:
    return [wt.label, wt.path.name]


def candidates(query: str, worktrees: list[Worktree]) -> list[tuple[int, Worktree]]:
    return rank(query, [(wt, match_keys(wt)) for wt in worktrees])


def clear_winner(query: str, ranked: list[tuple[int, Worktree]]) -> Worktree | None:
    """The top match if it needs no confirmation, else None."""
    if not ranked:
        return None
    if len(ranked) == 1:
        return ranked[0][1]
    lowered = query.lower()
    exact = [wt for _, wt in ranked if lowered in (k.lower() for k in match_keys(wt))]
    if len(exact) == 1:
        return exact[0]
    (top, wt), (second, _) = ranked[0], ranked[1]
    if top - second >= CLEAR_MARGIN:
        return wt
    return None


def ask(
    options: list[Worktree],
    describe,
    stdin: TextIO | None = None,
    stderr: TextIO | None = None,
) -> Worktree:
    """Show a numbered list on stderr and read the choice from stdin."""
    stdin = stdin or sys.stdin
    stderr = stderr or sys.stderr
    if not stdin.isatty():
        lines = "\n".join(f"  {describe(wt)}" for wt in options)
        raise NothingPicked(f"more than one worktree matches:\n{lines}")
    width = len(str(len(options)))
    for number, wt in enumerate(options, 1):
        print(f"{number:>{width}}) {describe(wt)}", file=stderr)
    while True:
        print("Pick a number (empty to cancel): ", end="", file=stderr, flush=True)
        answer = stdin.readline()
        if not answer or not answer.strip():
            raise NothingPicked("nothing picked")
        answer = answer.strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print(f"Not a number between 1 and {len(options)}.", file=stderr)


def choose(query: str, worktrees: list[Worktree], describe, **streams) -> Worktree:
    if not query:
        if len(worktrees) == 1:
            return worktrees[0]
        return ask(worktrees, describe, **streams)
    ranked = candidates(query, worktrees)
    if not ranked:
        raise NothingPicked(f"no worktree matches {query!r}")
    winner = clear_winner(query, ranked)
    if winner is not None:
        return winner
    return ask([wt for _, wt in ranked], describe, **streams)
