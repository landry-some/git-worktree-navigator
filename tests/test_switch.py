import io
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import git

from git_worktree_navigator import picker
from git_worktree_navigator.cli import main
from git_worktree_navigator.worktrees import Worktree


class TTYInput(io.StringIO):
    def isatty(self):
        return True


def wt(branch, folder=None):
    return Worktree(path=Path("/code/shop.worktrees") / (folder or branch), branch=branch)


TREES = [wt("main", "shop"), wt("fix/login-bug"), wt("feature/login-page"), wt("review/pr-212")]


def test_single_match_is_chosen():
    assert picker.choose("pr", TREES, str).branch == "review/pr-212"


def test_exact_name_wins_over_close_scores():
    trees = [wt("main"), wt("maint")]
    assert picker.choose("main", trees, str).branch == "main"


def test_close_matches_ask_and_read_number():
    stderr = io.StringIO()
    chosen = picker.choose("login", TREES, lambda w: w.label, stdin=TTYInput("2\n"), stderr=stderr)
    shown = stderr.getvalue()
    assert "1) fix/login-bug" in shown and "2) feature/login-page" in shown
    assert chosen.branch == "feature/login-page"


def test_picker_retries_on_bad_input():
    stderr = io.StringIO()
    chosen = picker.choose("", TREES, str, stdin=TTYInput("9\nx\n1\n"), stderr=stderr)
    assert chosen.branch == "main"
    assert stderr.getvalue().count("Not a number between 1 and 4") == 2


def test_picker_cancel_on_empty_line():
    with pytest.raises(picker.NothingPicked):
        picker.choose("", TREES, str, stdin=TTYInput("\n"), stderr=io.StringIO())


def test_ambiguous_without_terminal_lists_matches():
    with pytest.raises(picker.NothingPicked) as exc:
        picker.choose("login", TREES, lambda w: w.label, stdin=io.StringIO(""), stderr=io.StringIO())
    assert "fix/login-bug" in str(exc.value) and "feature/login-page" in str(exc.value)


def test_no_match_raises():
    with pytest.raises(picker.NothingPicked, match="no worktree matches"):
        picker.choose("zzz", TREES, str)


@pytest.fixture
def repo_with_worktrees(repo):
    base = repo.parent / "shop.worktrees"
    git(repo, "worktree", "add", "-q", "-b", "fix/login-bug", str(base / "fix" / "login-bug"))
    git(repo, "worktree", "add", "-q", "-b", "review/pr-212", str(base / "review" / "pr-212"))
    return repo


def test_switch_prints_only_the_path(repo_with_worktrees, capsys):
    assert main(["switch", "lgbug"]) == 0
    out = capsys.readouterr().out
    assert out == str(repo_with_worktrees.parent / "shop.worktrees" / "fix" / "login-bug") + "\n"


def test_switch_joins_query_words(repo_with_worktrees, capsys):
    assert main(["switch", "pr", "212"]) == 0
    assert capsys.readouterr().out.strip().endswith("review/pr-212")


def test_switch_no_match_exits_1(repo_with_worktrees, capsys):
    assert main(["switch", "qqq"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no worktree matches 'qqq'" in captured.err


def test_shell_init_outputs_function(capsys):
    assert main(["shell-init", "bash"]) == 0
    assert capsys.readouterr().out.startswith("gwn() {")


def test_gwn_function_changes_directory_in_bash(repo_with_worktrees, monkeypatch):
    bin_dir = Path(sys.executable).parent
    if not (bin_dir / "git-worktree-navigator").exists():
        pytest.skip("git-worktree-navigator is not installed next to this Python")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    script = 'eval "$(git-worktree-navigator shell-init bash)"; gwn pr212 && pwd; gwn qqq; echo "rc=$?"; pwd'
    result = subprocess.run(
        ["bash", "-c", script], cwd=repo_with_worktrees, capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    target = str(repo_with_worktrees.parent / "shop.worktrees" / "review" / "pr-212")
    assert lines == [target, "rc=1", target], result.stderr
