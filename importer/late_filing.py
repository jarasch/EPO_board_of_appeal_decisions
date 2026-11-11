"""Q7 (PHARMA_GENERICS_PLAN.md) -- late-filed evidence/request admission under
Art. 12(4)/13(2) RPBA 2020.

    "Post-RPBA-2020, how often is late-filed evidence or a late request
    admitted under Art. 12(4) and 13(2) RPBA -- and on what reasoning? ...
    an opponent's best prior-art document is frequently found late. If it is
    not admitted, the attack dies on procedure regardless of merit."

Patterns mined from real `ReasonsForDecision` text (not guessed), across all
three languages -- one real complication drove the design: **a single
decision routinely rules on several requests with different outcomes** --
e.g. "Der Hilfsantrag 1 wurde ... nicht zum Beschwerdeverfahren zugelassen,
während der Hilfsantrag 2 zum Beschwerdeverfahren zugelassen wurde" (auxiliary
request 1 not admitted, auxiliary request 2 admitted, same paragraph). Forcing
one label per decision would misrepresent that as a clean yes/no. Instead,
`classify` reports two independent booleans, and a decision with both true is
a real, honest category ("mixed"), not an edge case to resolve away.

The other real ambiguity: parties routinely *request* that something (not) be
admitted before the board rules -- "the opponent requested that ... not be
admitted into the proceedings" is the party's ask, not the ruling. Matches
immediately preceded by a request-framing phrase are dropped for exactly this
reason; this is a heuristic, not a parse, and is not claimed to be perfect.

A second, unresolved ambiguity found by spot-checking real matches: "decided
not to admit" also describes what the FIRST-INSTANCE opposition/examining
division decided, narrated within the Board's own reasoning while it reviews
that decision -- e.g. "... the opposition division decided not to admit this
request into the proceedings" is not the Board's own RPBA 2020 ruling on
appeal, which is specifically what Q7 asks about, even though the sentence
matches the same pattern. This module does not attempt to disambiguate
"whose decision" a matched sentence describes -- callers should read
`--samples` output rather than trust the aggregate counts as precise.
"""

import re

_REQUEST_FRAMING_RE = re.compile(
    r"(?:request(?:ed)?\s+that|beantragt,?\s*dass|a\s+demand[ée]\s+que)\s*$",
    re.IGNORECASE,
)

ADMITTED_PATTERNS = (
    re.compile(r"decided\s+to\s+admit\b", re.IGNORECASE),
    re.compile(r"\b(?:has|have|was|were|is|are)\s+(?:been\s+)?admitted\s+into\s+the"
               r"\s+(?:appeal\s+)?proceedings", re.IGNORECASE),
    # de -- "nicht" can sit several words before "zugelassen", so the
    # not-admitted check runs first (see `classify`); this pattern alone
    # over-matches on "nicht ... zugelassen" sentences, which is fine.
    re.compile(r"(?:zum|zur|in\s+das)\s+(?:Beschwerde)?[Vv]erfahren\s+zugelassen", re.IGNORECASE),
    re.compile(r"\bwird\b.{0,40}?\bzugelassen\b", re.IGNORECASE),
    re.compile(r"\bsont\s+(?:donc\s+)?recevables?\b", re.IGNORECASE),
)

NOT_ADMITTED_PATTERNS = (
    re.compile(r"decided\s+not\s+to\s+admit\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are|was|were)\s+not\s+(?:been\s+)?admitted\s+into\s+the"
               r"\s+(?:appeal\s+)?proceedings", re.IGNORECASE),
    re.compile(r"\b(?:is|are|shall)\s+not\s+(?:be\s+)?taken\s+into\s+account", re.IGNORECASE),
    re.compile(r"\bnot\s+admitted\s+into\s+the\s+(?:appeal\s+)?proceedings", re.IGNORECASE),
    # de -- "nicht" and "zugelassen" bounded within one clause, order-independent
    re.compile(r"nicht\b(?:(?!zugelassen|[.\n]).){0,60}\bzugelassen", re.IGNORECASE),
    re.compile(r"\birrecevables?\b", re.IGNORECASE),
)


def _drop_request_framing(text, patterns):
    """True if any pattern matches `text` at a point NOT immediately preceded
    by a party's request framing ("requested that ...")."""
    for pattern in patterns:
        for match in pattern.finditer(text):
            preceding = text[max(0, match.start() - 40):match.start()]
            if not _REQUEST_FRAMING_RE.search(preceding):
                return True
    return False


def match_context(text, window=200):
    """The text around the first admission/non-admission signal in `text`,
    for `--samples`-style spot-checking -- printing from char 0 routinely
    missed the actual matched phrase in a long chunk."""
    body = text or ""
    for patterns in (ADMITTED_PATTERNS, NOT_ADMITTED_PATTERNS):
        for pattern in patterns:
            match = pattern.search(body)
            if match:
                start = max(0, match.start() - window)
                end = min(len(body), match.end() + window)
                return body[start:end]
    return body[:window * 2]


def classify(text):
    """One chunk's admission signal.

    Returns (admitted, not_admitted) -- both booleans, independently. Both
    true means the decision ruled on multiple requests with different
    outcomes ("mixed"); both false means no ruling-level admission language
    was found in this chunk (it may be discussed elsewhere, or in a way this
    heuristic does not catch).
    """
    body = text or ""
    return (
        _drop_request_framing(body, ADMITTED_PATTERNS),
        _drop_request_framing(body, NOT_ADMITTED_PATTERNS),
    )
