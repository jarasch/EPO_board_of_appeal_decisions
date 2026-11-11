"""Q11 (PHARMA_GENERICS_PLAN.md) -- patentee-direction scoring and Wilson intervals.

Q11 is explicitly the riskiest question in either plan to get wrong in a way
that *looks* right: "a board-level 'favours patentees' number travels
further than its caveats do." Two structural rules make that mistake
impossible to fall into by accident here, not just by convention:

1. `resolve_direction` reads `appellant_role`, not just `outcome_type`.
   "Dismissed" has no direction on its own -- it is pro-patentee when the
   opponent appealed and anti-patentee when the proprietor did (either side
   may be the appellant in an opposition appeal). Scoring it without the
   role would silently average two opposite things.
2. Every rate this module produces is a `(board, appellantRole)` pair, never
   a board alone. `wilson_interval` and `MIN_SUPPORT` exist so a thin cell
   reads as "insufficient data", not as a number.
"""

from importer.outcomes import PATENTEE_DIRECTION
from importer.stats import MIN_SUPPORT, score_rate, wilson_interval  # noqa: F401 -- re-exported

# RPBA 2020 changed what "remitted" means (Art. 11 RPBA 2020: no remittal
# without special reasons) and is the regime-break robustness check the plan
# specifies -- split here, then check whether the board ranking holds.
REGIME_BREAK = "2020-01-01"


def resolve_direction(outcome_type, appellant_role):
    """One decision's patentee-direction score.

    Returns "pro_patentee" / "partial" / "anti_patentee" / "excluded".
    "Excluded" covers: remitted/terminated/inadmissible/unclassified/etc
    (no merits result to score), "dismissed" with `appellant_role` not
    resolved to a single side (unknown, or "both" -- a dismissal of a
    cross-appeal does not by itself say what happened to the patent), and
    any outcome not in `PATENTEE_DIRECTION`.
    """
    if outcome_type == "dismissed":
        if appellant_role == "opponent":
            return "pro_patentee"
        if appellant_role == "proprietor":
            return "anti_patentee"
        return "excluded"
    return PATENTEE_DIRECTION.get(outcome_type, "excluded")
