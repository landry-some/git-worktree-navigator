"""Shell function that turns a printed path into a directory change."""

SHELLS = ("bash", "zsh")

# The same POSIX-style function works in bash and zsh.
FUNCTION = r"""
gwn() {
    local out
    case "$1" in
        list|remove|run|shell-init|-h|--help|--version)
            command git-worktree-navigator "$@"
            return
            ;;
        add)
            out="$(command git-worktree-navigator "$@")" || return
            ;;
        switch)
            shift
            out="$(command git-worktree-navigator switch "$@")" || return
            ;;
        *)
            out="$(command git-worktree-navigator switch "$@")" || return
            ;;
    esac
    if [ -d "$out" ]; then
        cd -- "$out"
    elif [ -n "$out" ]; then
        printf '%s\n' "$out"
    fi
}
""".lstrip()


def init_script(shell: str) -> str:
    if shell not in SHELLS:
        raise ValueError(f"unsupported shell {shell!r}")
    return FUNCTION
