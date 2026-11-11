"""Shared statistics for the analytical (non-LLM) report scripts.

Split out of `importer/patentee_analytics.py` once a second script
(`analyze_opponent_track_record.py`, Q6) needed the same interval and the
same "do not report a thin cell" discipline -- every base-rate report in
PHARMA_GENERICS_PLAN.md and EXAMINER_PLAN.md carries the same risk (a
plausible-looking percentage off a handful of decisions), so the guard
belongs in one place, not re-implemented per script.
"""

import math

# Below this many scored outcomes, a rate is not reported: an examiner/
# generics-counsel reader would otherwise get "62%" beside a cell of 3.
MIN_SUPPORT = 20


def wilson_interval(successes, total, z=1.96):
    """95% Wilson score interval for a binomial proportion.

    Preferred over the normal-approximation interval here because several
    reported cells are small (the support gate itself is 20), where the
    normal approximation can produce bounds outside [0, 1].
    """
    if total == 0:
        return (0.0, 0.0)
    phat = successes / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = (z / denom) * math.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total))
    return (max(0.0, center - margin), min(1.0, center + margin))


def score_rate(successes, total, min_support=MIN_SUPPORT):
    """(rate, wilson_lo, wilson_hi), or (None, None, None) below `min_support`.

    Callers must check for None and print "insufficient data" rather than a
    suppressed-but-silent zero row.
    """
    if total < min_support:
        return (None, None, None)
    lo, hi = wilson_interval(successes, total)
    return (successes / total, lo, hi)
