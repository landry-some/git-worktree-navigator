import io

import pytest
from conftest import git

from git_worktree_navigator import picker
from git_worktree_navigator.cli import main


@pytest.fixture
def trees(repo):
    base = repo.parent / "shop.worktrees"
    paths = {
        "login": base / "fix" / "login-bug",
        "maint": base / "maintenance",
    }
    git(repo, "worktree", "add", "-q", "-b", "fix/login-bug", str(paths["login"]))
    git(repo, "worktree", "add", "-q", "-b", "maintenance", str(paths["maint"]))
    return paths


def branches_with_worktrees(repo):
    out = git(repo, "worktree", "list", "--porcelain")
    return [line.split("refs/heads/")[1] for line in out.splitlines() if line.startswith("branch ")]


def test_remove_clean_worktree_keeps_branch(repo, trees, capsys):
    assert main(["remove", "login"]) == 0
    assert "Removed worktree fix/login-bug" in capsys.readouterr().out
    assert not trees["login"].exists()
    assert branches_with_worktrees(repo) == ["main", "maintenance"]
    assert "fix/login-bug" in git(repo, "branch", "--list", "fix/login-bug")


def test_remove_refuses_main_even_when_another_name_contains_it(repo, trees, capsys):
    assert main(["remove", "main"]) == 1
    assert "refusing to remove main: it is the main worktree" in capsys.readouterr().err
    assert trees["maint"].exists()


def test_remove_refuses_current_worktree(repo, trees, capsys, monkeypatch):
    monkeypatch.chdir(trees["login"])
    assert main(["remove", "login"]) == 1
    assert "you are in it" in capsys.readouterr().err
    assert trees["login"].exists()


def test_remove_refuses_dirty_without_force(repo, trees, capsys):
    (trees["login"] / "notes.txt").write_text("untracked\n")

    assert main(["remove", "login"]) == 1
    assert "use --force" in capsys.readouterr().err
    assert trees["login"].exists()

    assert main(["remove", "login", "--force"]) == 0
    assert not trees["login"].exists()


def test_remove_without_query_offers_only_removable(repo, trees, monkeypatch):
    class TTY(io.StringIO):
        def isatty(self):
            return True

    stderr = io.StringIO()
    monkeypatch.setattr(picker.sys, "stdin", TTY("2\n"))
    monkeypatch.setattr(picker.sys, "stderr", stderr)

    assert main(["remove"]) == 0
    shown = stderr.getvalue()
    assert "main  " not in shown and "1) fix/login-bug" in shown
    assert not trees["maint"].exists()


def test_remove_with_nothing_removable(repo, capsys):
    assert main(["remove"]) == 1
    assert "no worktree can be removed" in capsys.readouterr().err
