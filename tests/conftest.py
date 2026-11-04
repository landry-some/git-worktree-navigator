import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch, tmp_path):
    """Keep the user's git config out of the tests and give commits an identity."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test Author")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Test Author")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "test@example.invalid")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository with one commit on main, and cwd set to it."""
    path = tmp_path / "shop"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    (path / "README").write_text("shop\n")
    git(path, "add", "README")
    git(path, "commit", "-q", "-m", "first")
    monkeypatch.chdir(path)
    return path
