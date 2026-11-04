"""Subsequence fuzzy matching with bonuses for word starts and runs."""

from __future__ import annotations

SEPARATORS = "/-_. "

MATCH = 1
WORD_START_BONUS = 8
CONSECUTIVE_BONUS = WORD_START_BONUS  # a run must not lose to s-c-a-t-t-e-r-e-d word starts
GAP_PENALTY = 1

# A top score must beat the runner-up by this much to be picked without asking.
CLEAR_MARGIN = WORD_START_BONUS


def score(query: str, text: str) -> int | None:
    """Score how well query matches text, or None if it does not match.

    Every query character must appear in text in order, ignoring case.
    The best-scoring placement is found with a small dynamic program over
    (query position, text position).
    """
    q = query.lower()
    t = text.lower()
    if not q:
        return 0
    if len(q) > len(t):
        return None

    def bonus(j: int) -> int:
        return WORD_START_BONUS if j == 0 or t[j - 1] in SEPARATORS else 0

    neg = None
    # best[j]: best score with the current query char matched exactly at t[j]
    best: list[int | None] = [
        MATCH + bonus(j) if t[j] == q[0] else neg for j in range(len(t))
    ]
    for i in range(1, len(q)):
        nxt: list[int | None] = [neg] * len(t)
        # running best over earlier positions, already reduced by the gap
        carry: int | None = neg
        for j in range(1, len(t)):
            prev = best[j - 1]
            if prev is not None:
                carry = prev if carry is None else max(carry, prev)
            if t[j] != q[i]:
                if carry is not None:
                    carry -= GAP_PENALTY
                continue
            candidates = []
            if prev is not None:
                candidates.append(prev + CONSECUTIVE_BONUS)
            if carry is not None:
                candidates.append(carry)
            if candidates:
                nxt[j] = max(candidates) + MATCH + bonus(j)
            if carry is not None:
                carry -= GAP_PENALTY
        best = nxt
    found = [s for s in best if s is not None]
    return max(found) if found else None


def rank(query: str, items: list[tuple[object, list[str]]]) -> list[tuple[int, object]]:
    """Rank items by their best-matching key. Non-matching items are dropped.

    Each item is (value, keys). Ties keep the input order.
    """
    ranked = []
    for index, (value, keys) in enumerate(items):
        scores = [s for s in (score(query, k) for k in keys) if s is not None]
        if scores:
            ranked.append((max(scores), index, value))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    return [(s, value) for s, _, value in ranked]
