"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .worktrees import GitError, NotARepository, Worktree, current_toplevel, find_current, list_worktrees


def display_path(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + str(path.relative_to(home))
    except ValueError:
        return str(path)


def format_list(worktrees: list[Worktree], current: Worktree | None) -> list[str]:
    label_width = max(len(wt.label) for wt in worktrees)
    lines = []
    for wt in worktrees:
        marker = "*" if wt is current else " "
        parts = [f"{marker} {wt.label:<{label_width}}", f"{wt.head[:7]:<7}", display_path(wt.path)]
        line = "  ".join(parts)
        if wt.flags:
            line += "  " + " ".join(wt.flags)
        lines.append(line.rstrip())
    return lines


def cmd_list(args: argparse.Namespace) -> int:
    worktrees = list_worktrees()
    current = find_current(worktrees, current_toplevel())
    for line in format_list(worktrees, current):
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-worktree-navigator",
        description="List, add, remove and fuzzy-switch between git worktrees.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="show all worktrees")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except NotARepository as exc:
        print(f"git-worktree-navigator: {exc}", file=sys.stderr)
        return 2
    except GitError as exc:
        print(f"git-worktree-navigator: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
