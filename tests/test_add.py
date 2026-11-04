from pathlib import Path

from conftest import git

from git_worktree_navigator.cli import main
from git_worktree_navigator.worktrees import Worktree, default_location


def test_default_location_sits_next_to_main():
    main_wt = Worktree(path=Path("/code/shop"), is_main=True)
    assert default_location(main_wt, "fix/x") == Path("/code/shop.worktrees/fix/x")


def test_default_location_drops_git_suffix_of_bare_repo():
    bare = Worktree(path=Path("/srv/shop.git"), bare=True, is_main=True)
    assert default_location(bare, "main") == Path("/srv/shop.worktrees/main")


def test_add_existing_branch(repo, capsys):
    git(repo, "branch", "fix/login-bug")

    assert main(["add", "fix/login-bug"]) == 0
    out = capsys.readouterr().out
    expected = repo.parent / "shop.worktrees" / "fix" / "login-bug"
    assert out == f"{expected}\n"
    assert git(expected, "branch", "--show-current").strip() == "fix/login-bug"


def test_add_new_branch_from_base(repo, capsys):
    first = git(repo, "rev-parse", "HEAD").strip()
    (repo / "two").write_text("2\n")
    git(repo, "add", "two")
    git(repo, "commit", "-q", "-m", "second")

    assert main(["add", "-b", "spike/cache", "--base", first]) == 0
    path = Path(capsys.readouterr().out.strip())
    assert git(path, "rev-parse", "HEAD").strip() == first
    assert git(path, "branch", "--show-current").strip() == "spike/cache"


def test_add_from_linked_worktree_still_uses_main_location(repo, capsys, monkeypatch):
    main(["add", "-b", "one"])
    first = Path(capsys.readouterr().out.strip())
    monkeypatch.chdir(first)

    assert main(["add", "-b", "two"]) == 0
    assert Path(capsys.readouterr().out.strip()) == repo.parent / "shop.worktrees" / "two"


def test_add_custom_path(repo, tmp_path, capsys):
    target = tmp_path / "elsewhere"
    assert main(["add", "-b", "spike", "--path", str(target)]) == 0
    assert capsys.readouterr().out.strip() == str(target)
    assert (target / "README").exists()


def test_add_missing_branch_reports_git_error(repo, capsys):
    assert main(["add", "no-such-branch"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no-such-branch" in captured.err


def test_base_without_new_branch_is_usage_error(repo, capsys):
    assert main(["add", "x", "--base", "main"]) == 2
