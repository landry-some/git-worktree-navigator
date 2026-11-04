"""Command-line entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import __version__
from .picker import NothingPicked, choose
from .shell import SHELLS, init_script
from .worktrees import (
    GitError,
    NotARepository,
    Worktree,
    add_worktree,
    current_toplevel,
    default_location,
    find_current,
    is_dirty,
    list_worktrees,
    remove_worktree,
    worktree_status,
)


def display_path(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + str(path.relative_to(home))
    except ValueError:
        return str(path)


def format_list(
    worktrees: list[Worktree], current: Worktree | None, statuses: list[str]
) -> list[str]:
    label_width = max(len(wt.label) for wt in worktrees)
    status_width = max(len(s) for s in statuses)
    lines = []
    for wt, status in zip(worktrees, statuses):
        marker = "*" if wt is current else " "
        parts = [f"{marker} {wt.label:<{label_width}}", f"{wt.head[:7]:<7}"]
        if status_width:
            parts.append(f"{status:<{status_width}}")
        parts.append(display_path(wt.path))
        line = "  ".join(parts)
        if wt.flags:
            line += "  " + " ".join(wt.flags)
        lines.append(line.rstrip())
    return lines


def cmd_list(args: argparse.Namespace) -> int:
    worktrees = list_worktrees()
    current = find_current(worktrees, current_toplevel())
    statuses = [worktree_status(wt).summary for wt in worktrees]
    for line in format_list(worktrees, current, statuses):
        print(line)
    return 0


def describe(wt: Worktree) -> str:
    return f"{wt.label}  {display_path(wt.path)}"


def pick_checkout(query: str) -> Worktree:
    """Choose a worktree that has a folder to work in."""
    # A prunable worktree's folder is gone, so there is nothing to cd into.
    worktrees = [wt for wt in list_worktrees() if not wt.bare and not wt.prunable]
    if not worktrees:
        raise NothingPicked("this repository has no checked-out worktrees")
    return choose(query, worktrees, describe)


def cmd_switch(args: argparse.Namespace) -> int:
    print(pick_checkout("".join(args.query)).path)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if "--" not in args.words:
        print("git-worktree-navigator: usage: run [query ...] -- command [args ...]", file=sys.stderr)
        return 2
    split = args.words.index("--")
    query, command = args.words[:split], args.words[split + 1 :]
    if not command:
        print("git-worktree-navigator: run needs a command after --", file=sys.stderr)
        return 2
    wt = pick_checkout("".join(query))
    try:
        return subprocess.run(command, cwd=wt.path).returncode
    except FileNotFoundError:
        print(f"git-worktree-navigator: command not found: {command[0]}", file=sys.stderr)
        return 127


def cmd_add(args: argparse.Namespace) -> int:
    if args.base and not args.new:
        print("git-worktree-navigator: --base only makes sense with -b", file=sys.stderr)
        return 2
    main_wt = list_worktrees()[0]
    path = Path(args.path).resolve() if args.path else default_location(main_wt, args.branch)
    add_worktree(path, args.branch, new_branch=args.new, base=args.base)
    print(f"Created worktree for {args.branch} at {display_path(path)}", file=sys.stderr)
    print(path)
    return 0


def refusal(wt: Worktree, current: Worktree | None) -> str | None:
    """Why remove must not touch this worktree, or None if it may."""
    if wt.is_main:
        return "it is the main worktree"
    if wt is current:
        return "you are in it"
    return None


def cmd_remove(args: argparse.Namespace) -> int:
    query = "".join(args.query)
    worktrees = [wt for wt in list_worktrees() if not wt.bare]
    current = find_current(worktrees, current_toplevel())
    if not query:
        # Without a query, only offer worktrees that can actually be removed.
        worktrees = [wt for wt in worktrees if refusal(wt, current) is None]
        if not worktrees:
            raise NothingPicked("no worktree can be removed")
    wt = choose(query, worktrees, describe)
    reason = refusal(wt, current)
    if reason:
        raise NothingPicked(f"refusing to remove {wt.label}: {reason}")
    # A prunable worktree's folder is gone, so there are no changes to lose.
    if not args.force and not wt.prunable and is_dirty(wt):
        print(
            f"git-worktree-navigator: {wt.label} has uncommitted or untracked "
            "changes, use --force to remove it anyway",
            file=sys.stderr,
        )
        return 1
    remove_worktree(wt, force=args.force)
    print(f"Removed worktree {wt.label} at {display_path(wt.path)}")
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

    p_list = sub.add_parser(
        "list",
        help="show all worktrees",
        description="Show every worktree with branch, short HEAD, status and path. "
        "Status: ! for uncommitted or untracked changes, ↑n and ↓n for commits "
        "ahead of and behind the upstream branch.",
    )
    p_list.set_defaults(func=cmd_list)

    p_switch = sub.add_parser(
        "switch",
        help="print the path of the worktree matching a fuzzy query",
        description="Print the path of the best-matching worktree. With no query, "
        "or when matches are close, ask with a numbered list on stderr.",
    )
    p_switch.add_argument("query", nargs="*", help="characters to match, in order")
    p_switch.set_defaults(func=cmd_switch)

    p_run = sub.add_parser(
        "run",
        help="run a command inside the worktree matching a fuzzy query",
        usage="%(prog)s [query ...] -- command [args ...]",
        description="Run a command inside the best-matching worktree without "
        "switching to it, and exit with the command's exit code.",
        epilog="example: git-worktree-navigator run login -- git log -3",
    )
    p_run.add_argument(
        "words",
        nargs=argparse.REMAINDER,
        metavar="[query ...] -- command",
        help="characters to match, then -- and the command to run",
    )
    p_run.set_defaults(func=cmd_run)

    p_add = sub.add_parser(
        "add",
        help="create a worktree for a branch",
        description="Create a worktree in <repo>.worktrees/<branch> next to the "
        "main checkout and print its path.",
    )
    p_add.add_argument("branch", help="branch to check out")
    p_add.add_argument("-b", dest="new", action="store_true", help="create the branch")
    p_add.add_argument("--base", help="start point for a new branch (default: HEAD)")
    p_add.add_argument("--path", help="put the worktree here instead")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser(
        "remove",
        help="remove the worktree matching a fuzzy query",
        description="Remove a worktree. The main worktree and the one you are in "
        "are never removed. The branch itself is kept.",
    )
    p_remove.add_argument("query", nargs="*", help="characters to match, in order")
    p_remove.add_argument(
        "--force", action="store_true", help="remove even with uncommitted changes"
    )
    p_remove.set_defaults(func=cmd_remove)

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
