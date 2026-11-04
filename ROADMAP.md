# Roadmap

What comes after v0.1. Estimates are rough, in hours, at 8 hours per working day.

## v0.1 (done)

- [x] `list`: show every worktree with branch, short HEAD, path and flags
- [x] `switch [query]`: fuzzy match on branch and path, numbered picker when ambiguous,
      `shell-init bash|zsh` for a `gwn` function that changes directory
- [x] `add <branch>`: create a worktree in `<repo>.worktrees/<branch>` next to the repo
- [x] `remove [query]`: fuzzy-select and remove, with guards for main, current and dirty
      worktrees

## Features

- [ ] Live-filtering full-screen picker with curses, arrow keys and type-to-filter (6 h)
- [ ] Preview pane in the picker: last commits and `git status --short` of the
      highlighted worktree (3 h)
- [ ] Status columns in `list`: dirty marker, ahead/behind upstream (3 h)
- [ ] Frecency ordering: remember recent switches and rank them first on ties (3 h)
- [ ] `fish` support in `shell-init`, plus bash/zsh/fish tab completion of worktree
      names (4 h)
- [ ] Config file (`~/.config/git-worktree-navigator/config.toml`) with a path
      template for new worktrees and a default base branch for `add -b` (3 h)
- [ ] `clean`: list worktrees whose branch is merged or gone upstream and offer to
      remove them, dry run first (3 h)
- [ ] `run <query> -- <cmd>`: run a command inside a worktree without switching (2 h)

## Bugs and edge cases

- [ ] Bare-repository layouts (`repo.git` with all checkouts as worktrees) (3 h)
- [ ] Branch names with slashes, spaces and unicode in worktree paths (2 h)
- [ ] Worktrees whose folder was deleted by hand (prunable) in `switch` and `remove` (1 h)
- [ ] Running from inside a nested worktree or a subfolder of one (1 h)

## Refactors

- [ ] Split the git runner from parsing so commands can be batched for speed on repos
      with many worktrees (2 h)
- [ ] Move picker rendering behind a small interface so the numbered and curses
      pickers share filtering code (2 h)

## Tests

- [ ] Scoring tests on a fixed corpus of branch names to lock ranking behaviour (2 h)
- [ ] Shell integration tests that source the generated function in bash and zsh (2 h)
- [ ] CI on GitHub Actions for Linux and macOS, Python 3.11 to 3.14 (1 h)

## Docs

- [ ] Recorded terminal demo in the README (1 h)
- [ ] Man page style `--help` text for every command, with examples (1 h)
- [ ] Notes on the worktree folder layout and how to change it (1 h)

## Total

46 hours, about 5.75 working days.
