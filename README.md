# git-worktree-navigator

A command-line tool for moving between git worktrees by typing part of the branch
name, and for adding and removing worktrees without thinking about where their
folders go.

`git worktree` is handy for keeping a hotfix or a review checkout next to your main
work without stashing, but switching between them means remembering folder names,
and `git worktree list` only prints paths. `git-worktree-navigator` lists worktrees
by branch, fuzzy-matches a query against them and prints the path of the match. A
small shell function turns that into a `cd`.

## Who it's for

Developers who keep a few worktrees per repository and jump between them during
the day.

## Built with

Python 3.11+ and the standard library only. Every action runs the `git`
command-line tool (`git worktree list --porcelain`, `git worktree add`,
`git worktree remove`), so git's own checks still apply. Tests use pytest and build
real throwaway repositories.

## Install

Needs Python 3.11 or newer and git 2.31 or newer.

```bash
git clone https://github.com/landry-some/git-worktree-navigator.git
cd git-worktree-navigator
python3 -m venv .venv
.venv/bin/pip install -e .
```

This puts the `git-worktree-navigator` command in `.venv/bin/`. Activate the venv
(`source .venv/bin/activate`) or put that folder on your `PATH`. Because the name
starts with `git-`, it also works as `git worktree-navigator`.

### Shell function

A program can't change the directory of the shell that started it, so switching
needs a small function. Add this to `~/.bashrc` or `~/.zshrc`:

```bash
eval "$(git-worktree-navigator shell-init bash)"   # or: shell-init zsh
```

That defines `gwn`. `gwn <query>` jumps to the matching worktree, and any other
`gwn` arguments are passed through, so `gwn list`, `gwn add` and `gwn remove` work
too. `gwn add` also moves you into the new worktree.

## Usage

Run it anywhere inside a git repository or one of its worktrees.

```bash
git-worktree-navigator list                 # all worktrees with branch, HEAD, path
git-worktree-navigator switch login         # print the path of the best match
git-worktree-navigator switch               # pick from a numbered list
git-worktree-navigator add fix/login-bug    # worktree for an existing branch
git-worktree-navigator add -b spike/cache   # new branch from HEAD
git-worktree-navigator add -b spike/cache --base main
git-worktree-navigator remove login         # remove the matching worktree
git-worktree-navigator remove login --force # even with uncommitted changes
```

Example `list` output:

```
* main            3f2a9c1  ~/code/shop
  fix/login-bug   8b01d4e  ~/code/shop.worktrees/fix/login-bug
  review/pr-212   c45e7aa  ~/code/shop.worktrees/review/pr-212  locked
```

### Matching

A query matches a worktree when its characters appear in order in the branch name
or the path, ignoring case (`lgbug` matches `fix/login-bug`). Matches at the start
of a word, right after `/`, `-`, `_` or `.`, and runs of consecutive characters
score higher. If one worktree clearly wins, its path is printed straight away.
When the top scores are close, or no query is given, a numbered list is shown on
stderr and you type the number. The picker never writes to stdout, so
`cd "$(git-worktree-navigator switch x)"` stays safe.

### Where new worktrees go

`add` puts new worktrees in a folder next to the main checkout, named after it:
`~/code/shop` gets `~/code/shop.worktrees/<branch>`. Use `--path` to choose
another location.

### What `remove` refuses

- the main worktree
- the worktree you are currently in
- a worktree with uncommitted or untracked changes, unless `--force` is given

## Exit codes

- `0` success
- `1` no match, nothing picked, or git refused the operation
- `2` usage error or not inside a git repository

## Development

```bash
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

See [ROADMAP.md](ROADMAP.md) for planned work.

## License

MIT, see [LICENSE](LICENSE).
