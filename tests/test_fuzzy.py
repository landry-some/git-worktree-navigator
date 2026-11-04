from git_worktree_navigator.fuzzy import rank, score


def test_subsequence_required():
    assert score("lgbug", "fix/login-bug") is not None
    assert score("bugl", "fix/login-bug") is None
    assert score("toolongquery", "main") is None


def test_case_insensitive():
    assert score("LOGIN", "fix/login-bug") == score("login", "fix/login-bug")


def test_empty_query_matches_everything():
    assert score("", "anything") == 0


def test_word_start_beats_middle_of_word():
    # "log" at a word start vs. buried inside "catalog"
    assert score("log", "fix/login") > score("log", "catalogue")


def test_consecutive_beats_scattered():
    assert score("main", "main") > score("main", "m-a-i-n")


def test_picks_best_placement_not_first():
    # The first "b" is mid-word, the later one starts a word.
    assert score("bug", "abc/bug") > score("bug", "abxuxg")


def test_rank_orders_and_drops_non_matches():
    items = [
        ("catalog", ["feature/catalogue"]),
        ("login", ["fix/login-bug"]),
        ("main", ["main"]),
    ]
    ranked = [value for _, value in rank("log", items)]
    assert ranked == ["login", "catalog"]


def test_rank_uses_best_key():
    items = [("wt", ["(detached)", "login-bug"])]
    assert rank("login", items)[0][1] == "wt"
