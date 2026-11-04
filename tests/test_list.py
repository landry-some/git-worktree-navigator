from pathlib import Path

from conftest import git

from git_worktree_navigator.cli import main
from git_worktree_navigator.worktrees import Status, parse_porcelain, parse_status

PORCELAIN = """\
worktree /home/dev/shop
HEAD 3f2a9c1aa0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5
branch refs/heads/main

worktree /home/dev/shop.worktrees/fix/login-bug
HEAD 8b01d4e00000000000000000000000000000000
branch refs/heads/fix/login-bug
locked reason: on a usb disk

worktree /home/dev/shop.worktrees/old
HEAD c45e7aa00000000000000000000000000000000
detached
prunable gitdir file points to non-existent location

"""


def test_parse_porcelain_reads_every_record():
    main_wt, fix, old = parse_porcelain(PORCELAIN)

    assert main_wt.is_main and main_wt.branch == "main"
    assert main_wt.path == Path("/home/dev/shop")
    assert fix.branch == "fix/login-bug" and fix.locked and not fix.is_main
    assert old.branch is None and old.detached and old.prunable
    assert old.label == "(detached)"
    assert old.flags == ["prunable"]


def test_parse_porcelain_bare_main():
    (bare,) = parse_porcelain("worktree /srv/shop.git\nbare\n")
    assert bare.bare and bare.label == "(bare)"


def test_list_marks_current_worktree(repo, capsys):
    other = repo.parent / "shop.worktrees" / "feature"
    git(repo, "worktree", "add", "-q", "-b", "feature/search", str(other))

    assert main(["list"]) == 0
    lines = capsys.readouterr().out.splitlines()

    assert len(lines) == 2
    assert lines[0].startswith("* main")
    assert lines[1].startswith("  feature/search")
    assert lines[1].endswith("shop.worktrees/feature")


def test_list_from_inside_linked_worktree(repo, capsys, monkeypatch):
    other = repo.parent / "shop.worktrees" / "feature"
    git(repo, "worktree", "add", "-q", "-b", "feature/search", str(other))
    (other / "sub").mkdir()
    monkeypatch.chdir(other / "sub")

    assert main(["list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[1].startswith("* feature/search")


def test_list_outside_repo_exits_2(tmp_path, monkeypatch, capsys):
    outside = tmp_path / "plain"
    outside.mkdir()
    monkeypatch.chdir(outside)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    assert main(["list"]) == 2
    assert "not a git repository" in capsys.readouterr().err


def test_parse_status_reads_dirty_and_ahead_behind():
    text = "# branch.oid abc\n# branch.head main\n# branch.upstream origin/main\n# branch.ab +2 -1\n? notes.txt\n"
    status = parse_status(text)
    assert status == Status(dirty=True, ahead=2, behind=1)
    assert status.summary == "! ↑2 ↓1"


def test_parse_status_clean_without_upstream():
    status = parse_status("# branch.oid abc\n# branch.head main\n")
    assert status == Status() and status.summary == ""


def commit(path, name):
    (path / name).write_text(name + "\n")
    git(path, "add", name)
    git(path, "commit", "-q", "-m", name)


def test_list_shows_dirty_and_ahead_behind(repo, capsys):
    other = repo.parent / "shop.worktrees" / "feature"
    git(repo, "worktree", "add", "-q", "-b", "feature/search", str(other))
    git(other, "branch", "-q", "--set-upstream-to=main")
    commit(other, "one")
    commit(other, "two")
    commit(repo, "three")
    (repo / "scratch").write_text("untracked\n")

    assert main(["list"]) == 0
    lines = capsys.readouterr().out.splitlines()

    assert lines[0].split()[3] == "!"
    assert lines[1].split()[2:4] == ["↑2", "↓1"]
    # the path column stays aligned
    assert lines[0].rindex(" ") == lines[1].rindex(" ")
