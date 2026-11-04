"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .picker import NothingPicked, choose
from .shell import SHELLS, init_script
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


def describe(wt: Worktree) -> str:
    return f"{wt.label}  {display_path(wt.path)}"


def cmd_switch(args: argparse.Namespace) -> int:
    query = "".join(args.query)
    worktrees = [wt for wt in list_worktrees() if not wt.bare]
    if not worktrees:
        raise NothingPicked("this repository has no checked-out worktrees")
    wt = choose(query, worktrees, describe)
    print(wt.path)
    return 0


def cmd_shell_init(args: argparse.Namespace) -> int:
    print(init_script(args.shell), end="")
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

    p_switch = sub.add_parser(
        "switch",
        help="print the path of the worktree matching a fuzzy query",
        description="Print the path of the best-matching worktree. With no query, "
        "or when matches are close, ask with a numbered list on stderr.",
    )
    p_switch.add_argument("query", nargs="*", help="characters to match, in order")
    p_switch.set_defaults(func=cmd_switch)

    p_init = sub.add_parser("shell-init", help="print the gwn shell function")
    p_init.add_argument("shell", choices=SHELLS)
    p_init.set_defaults(func=cmd_shell_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except NotARepository as exc:
        print(f"git-worktree-navigator: {exc}", file=sys.stderr)
        return 2
    except NothingPicked as exc:
        print(f"git-worktree-navigator: {exc}", file=sys.stderr)
        return 1
    except GitError as exc:
        print(f"git-worktree-navigator: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
