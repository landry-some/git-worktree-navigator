"""Read worktree information from git."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(Exception):
    """A git command failed. The message is git's own error output."""


class NotARepository(GitError):
    """The working directory is not inside a git repository."""


def run_git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or f"git {args[0]} failed"
        raise GitError(message)
    return result.stdout


@dataclass
class Worktree:
    path: Path
    head: str = ""
    branch: str | None = None
    is_main: bool = False
    bare: bool = False
    detached: bool = False
    locked: bool = False
    prunable: bool = False

    @property
    def label(self) -> str:
        """Branch name, or a placeholder when there is none."""
        if self.branch:
            return self.branch
        if self.bare:
            return "(bare)"
        return "(detached)"

    @property
    def flags(self) -> list[str]:
        names = []
        if self.locked:
            names.append("locked")
        if self.prunable:
            names.append("prunable")
        return names


def parse_porcelain(text: str) -> list[Worktree]:
    """Parse the output of `git worktree list --porcelain`.

    Records are separated by blank lines. The first record is always the
    main worktree.
    """
    worktrees: list[Worktree] = []
    current: Worktree | None = None
    for line in text.splitlines():
        if not line:
            current = None
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = Worktree(path=Path(value), is_main=not worktrees)
            worktrees.append(current)
        elif current is None:
            continue
        elif key == "HEAD":
            current.head = value
        elif key == "branch":
            current.branch = value.removeprefix("refs/heads/")
        elif key == "bare":
            current.bare = True
        elif key == "detached":
            current.detached = True
        elif key == "locked":
            current.locked = True
        elif key == "prunable":
            current.prunable = True
    return worktrees


def current_toplevel(cwd: Path | None = None) -> Path | None:
    """Top folder of the worktree containing cwd, or None inside a bare repo."""
    try:
        out = run_git("rev-parse", "--show-toplevel", cwd=cwd)
    except GitError as exc:
        if "not a git repository" in str(exc):
            raise NotARepository(str(exc)) from exc
        return None
    return Path(out.strip())


def list_worktrees(cwd: Path | None = None) -> list[Worktree]:
    try:
        out = run_git("worktree", "list", "--porcelain", cwd=cwd)
    except GitError as exc:
        if "not a git repository" in str(exc):
            raise NotARepository(str(exc)) from exc
        raise
    return parse_porcelain(out)


@dataclass
class Status:
    dirty: bool = False
    ahead: int = 0
    behind: int = 0

    @property
    def summary(self) -> str:
        """`!` when dirty, then `↑n` and `↓n` against the upstream, if any."""
        parts = []
        if self.dirty:
            parts.append("!")
        if self.ahead:
            parts.append(f"↑{self.ahead}")
        if self.behind:
            parts.append(f"↓{self.behind}")
        return " ".join(parts)


def parse_status(text: str) -> Status:
    """Parse the output of `git status --porcelain=v2 --branch`."""
    status = Status()
    for line in text.splitlines():
        if line.startswith("# branch.ab "):
            ahead, behind = line.split()[2:4]
            status.ahead = int(ahead.lstrip("+"))
            status.behind = int(behind.lstrip("-"))
        elif line and not line.startswith("#"):
            status.dirty = True
    return status


def worktree_status(wt: Worktree) -> Status:
    """Dirty flag and ahead/behind counts. Empty for bare or missing worktrees."""
    if wt.bare or wt.prunable:
        return Status()
    return parse_status(run_git("status", "--porcelain=v2", "--branch", cwd=wt.path))


def find_current(worktrees: list[Worktree], toplevel: Path | None) -> Worktree | None:
    if toplevel is None:
        return None
    resolved = toplevel.resolve()
    for wt in worktrees:
        if wt.path.resolve() == resolved:
            return wt
    return None


def default_location(main: Worktree, branch: str) -> Path:
    """`~/code/shop` + `fix/x` -> `~/code/shop.worktrees/fix/x`."""
    name = main.path.name.removesuffix(".git")
    return main.path.parent / f"{name}.worktrees" / branch


def add_worktree(
    path: Path, branch: str, new_branch: bool = False, base: str | None = None
) -> None:
    if new_branch:
        args = ["worktree", "add", "-b", branch, str(path)]
        if base:
            args.append(base)
    else:
        args = ["worktree", "add", str(path), branch]
    run_git(*args)


def is_dirty(wt: Worktree) -> bool:
    """True if the worktree has uncommitted or untracked changes."""
    return bool(run_git("status", "--porcelain", cwd=wt.path).strip())


def remove_worktree(wt: Worktree, force: bool = False) -> None:
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    run_git(*args, str(wt.path))
