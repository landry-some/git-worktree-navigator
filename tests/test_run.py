import sys

import pytest
from conftest import git

from git_worktree_navigator.cli import main

PRINT_CWD = [sys.executable, "-c", "import os; print(os.getcwd())"]


@pytest.fixture
def login(repo):
    path = repo.parent / "shop.worktrees" / "fix" / "login-bug"
    git(repo, "worktree", "add", "-q", "-b", "fix/login-bug", str(path))
    return path


def test_run_executes_in_matching_worktree(repo, login, capfd):
    assert main(["run", "login", "--", *PRINT_CWD]) == 0
    assert capfd.readouterr().out.strip() == str(login)


def test_run_joins_query_words_and_keeps_command_dashes(repo, login, capfd):
    script = "import sys; print(sys.argv[1:])"
    assert main(["run", "lg", "bug", "--", sys.executable, "-c", script, "--", "-x"]) == 0
    assert capfd.readouterr().out.strip() == "['--', '-x']"


def test_run_returns_command_exit_code(repo, login):
    assert main(["run", "login", "--", sys.executable, "-c", "raise SystemExit(3)"]) == 3


def test_run_without_separator_is_usage_error(repo, login, capsys):
    assert main(["run", "login", "ls"]) == 2
    assert "usage: run" in capsys.readouterr().err


def test_run_without_command_is_usage_error(repo, login, capsys):
    assert main(["run", "login", "--"]) == 2
    assert "needs a command" in capsys.readouterr().err


def test_run_unknown_command_exits_127(repo, login, capsys):
    assert main(["run", "login", "--", "no-such-command-gwn"]) == 127
    assert "command not found: no-such-command-gwn" in capsys.readouterr().err


def test_run_no_match_exits_1(repo, login, capsys):
    assert main(["run", "qqq", "--", "true"]) == 1
    assert "no worktree matches 'qqq'" in capsys.readouterr().err
