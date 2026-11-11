"""Q5 (EXAMINER_PLAN.md) / Q2 (PHARMA_GENERICS_PLAN.md) -- which ground actually
kills a patent on appeal?

`Ground.polarity` (`scripts/classify_grounds.py`) means the same
`requirementMetAll` boolean points in *opposite* directions depending on the
ground: for a `met`-polarity ground (inventive step, novelty, sufficiency,
clarity, priority, patentability), the patent is hurt when the requirement
was NOT met; for a `defect`-polarity ground (added subject-matter, extension
of protection, substantial procedural violation), the patent is hurt when
the defect WAS found. Scoring every ground the same way ("requirementMetAll
== false means bad") would silently invert half the grounds.
"""


def ground_against_patent(polarity, requirement_met_all):
    """True if this ground's finding worked against the patent surviving.

    None if there is no finding to score (`requirementMetAll` is null --
    the ground was addressed with mixed per-request findings, see
    `scripts/classify_grounds.py`'s `requirementMetAll` vs `requirementMetAny`)
    or the polarity is unrecognised.
    """
    if requirement_met_all is None:
        return None
    if polarity == "met":
        return not requirement_met_all
    if polarity == "defect":
        return requirement_met_all
    return None
