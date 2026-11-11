"""Rule-based appellant-role classifier -- PHARMA_GENERICS_PLAN.md Phase P2b.

In an inter partes appeal, an operative result only has a direction once you
know who appealed: "appeal dismissed" is pro-patentee when the opponent
appealed and anti-patentee when the proprietor did, and where only the
proprietor appealed the board cannot revoke at all (reformatio in peius,
G 9/92 / G 4/93). Q11 in the plan has no usable denominator without this.

Rules, not an LLM, for the same reason as `importer/outcomes.py`: this is a
join key for every stratified base rate downstream, so it needs to be
auditable and reproducible rather than a few-percent-wrong LLM call repeated
30,000 times.

Patterns below were mined by grep over real `SummaryOfFacts` text, not
guessed, and revised twice after checking real false positives/negatives
against the reformatio-in-peius invariant (see `violates_reformatio_in_peius`
below) -- see the forms EPO decisions actually use:

    en  parenthetical, both orders, party sometimes numbered:
            "The appellant (opponent) lodged an appeal ..."
            "The appellant (opponent 01) filed an appeal ..."
            "The patent proprietor (appellant) appealed against ..."
        prose, "the" is not reliable -- a numbered party label
        ("Opponent O2 lodged an appeal") is written without it:
            "... appeal ... lodged by the opponent ..."
            "Opponent O2 lodged an appeal on ..."
    de  prose, plus a parenthetical form with the ROLE first and
        "(Beschwerdeführer/in)" second -- the reverse of the EN order, and
        not the "Beschwerdeführerin (Einsprechende)" order the plan sketch
        guessed, which was not found in a corpus sample of inter partes DE
        decisions:
            "legte die Einsprechende Beschwerde ein"
            "Die Beschwerden der Einsprechenden richten sich gegen ..."
            "Die Einsprechende 03 (Beschwerdeführerin) legte Beschwerde ..."
    fr  parenthetical, same order as EN:
            "la requérante (opposante) a formé un recours"
            "la requérante (titulaire du brevet) a formé un recours"

A real, unresolved residual: `SummaryOfFacts` narrates case *history*, and a
decision that references an earlier appeal in the same proceedings (a prior
remittal, e.g.) can carry a role phrase for that earlier appeal, not the
current one. That is exactly the failure mode `violates_reformatio_in_peius`
exists to catch -- see the module docstring note there.

`classify` returns "both" when both sides' patterns match (a genuine cross
-appeal, not a fallback) and "unknown" -- a real answer, not a guess -- when
neither matches. Coverage is expected to be well under 100% on the first
pass; PHARMA_GENERICS_PLAN.md scopes the remainder to a bounded LLM pass over
`SummaryOfFacts` openings as a separate, later step, not attempted here.
"""

import re

# A party label is routinely numbered ("Opponent 01", "opponent O2") --
# every "opponent"/"proprietor" reference below tolerates an optional
# "01" / "O2" / "1" style suffix rather than requiring the bare word.
_NUM = r"\s*(?:O?\d+)?"

OPPONENT_APPELLANT_PATTERNS = (
    # en -- parenthetical, both orders, either side optionally numbered
    # ("Appellant II (opponent I)")
    re.compile(rf"appellant{_NUM}\s*\(\s*opponent{_NUM}\s*\)", re.IGNORECASE),
    re.compile(rf"opponent{_NUM}\s*\(\s*appellant{_NUM}\s*\)", re.IGNORECASE),
    re.compile(r"proprietor\s*\(\s*respondent\s*\)", re.IGNORECASE),
    # en -- prose. No "the" required: a numbered party label ("Opponent O2
    # lodged an appeal") is routinely written without it.
    re.compile(rf"\b(?:the\s+)?opponent{_NUM}\b[^.]{{0,40}}?(?:has\s+)?(?:lodged|filed)\s+an?\s+appeal",
               re.IGNORECASE),
    re.compile(r"appeal[^.]{0,40}?(?:lodged|filed)\s+by\s+(?:the\s+)?opponent", re.IGNORECASE),
    # en -- plural/possessive subject form: "The opponents' appeal(s) [is/
    # are] directed against ..." rather than a lodged/filed verb.
    re.compile(r"opponents?['’]\s+appeals?\s+(?:is|are)\s+directed\s+against",
               re.IGNORECASE),
    # de -- prose, plus the "role (Beschwerdeführer/in)" parenthetical order
    re.compile(r"legte\s+(?:die\s+)?Einsprechende[nr]?\s+Beschwerde\s+ein", re.IGNORECASE),
    re.compile(r"Einsprechende[nr]?\s+legte\s+Beschwerde\s+ein", re.IGNORECASE),
    re.compile(r"Beschwerden?\s+der\s+Einsprechenden\s+richt(?:et|en)\s+sich", re.IGNORECASE),
    re.compile(rf"Einsprechende[nr]?{_NUM}\s*\(\s*Beschwerdef[uü]hrer(?:in)?\s*\)",
               re.IGNORECASE),
    # fr -- parenthetical + prose
    re.compile(r"requ[ée]rante\s*\(\s*opposante\s*\)", re.IGNORECASE),
    re.compile(r"l['’]opposante\s+a\s+form[ée]\s+un\s+recours", re.IGNORECASE),
)

PROPRIETOR_APPELLANT_PATTERNS = (
    # en -- parenthetical, both orders, either side optionally numbered
    re.compile(rf"appellant{_NUM}\s*\(\s*(?:patent\s+)?proprietor\s*\)", re.IGNORECASE),
    re.compile(rf"(?:patent\s+)?proprietor\s*\(\s*appellant{_NUM}\s*\)", re.IGNORECASE),
    re.compile(rf"opponent{_NUM}\s*\(\s*respondent\s*\)", re.IGNORECASE),
    # en -- prose
    re.compile(r"\bthe\s+(?:patent\s+)?proprietor\b[^.]{0,40}?(?:has\s+)?(?:lodged|filed)\s+an?\s+appeal",
               re.IGNORECASE),
    re.compile(r"appeal[^.]{0,40}?(?:lodged|filed)\s+by\s+the\s+(?:patent\s+)?proprietor",
               re.IGNORECASE),
    # en -- plural/possessive subject form
    re.compile(r"(?:patent\s+)?proprietor['’]s\s+appeal\s+(?:is|are)\s+directed\s+against",
               re.IGNORECASE),
    # de -- prose, plus the "role (Beschwerdeführer/in)" parenthetical order
    re.compile(r"legte\s+(?:die\s+)?Patentinhaberin\s+Beschwerde\s+ein", re.IGNORECASE),
    re.compile(r"Patentinhaberin\s+legte\s+Beschwerde\s+ein", re.IGNORECASE),
    re.compile(r"Beschwerden?\s+der\s+Patentinhaberin\s+richt(?:et|en)\s+sich", re.IGNORECASE),
    re.compile(r"Patentinhaberin?\s*\(\s*Beschwerdef[uü]hrer(?:in)?\s*\)", re.IGNORECASE),
    # fr -- parenthetical + prose
    re.compile(r"requ[ée]rante\s*\(\s*titulaire(?:\s+du\s+brevet)?\s*\)", re.IGNORECASE),
    re.compile(r"(?:le\s+)?titulaire(?:\s+du\s+brevet)?\s+a\s+form[ée]\s+un\s+recours",
               re.IGNORECASE),
)

# reformatio in peius (G 9/92 / G 4/93): on a proprietor-only appeal, the
# board cannot revoke -- there is no opponent appeal putting maintenance at
# risk. Any (proprietor, revoked) pair is therefore a labelling error in the
# role classifier, the outcome classifier, or both, not a real case.
REVOKED_OUTCOMES = frozenset({"set_aside_revoked", "revoked"})


def classify(text):
    """Classify one decision's `SummaryOfFacts` text.

    Returns "opponent", "proprietor", "both", or "unknown".
    """
    body = text or ""
    is_opponent = any(p.search(body) for p in OPPONENT_APPELLANT_PATTERNS)
    is_proprietor = any(p.search(body) for p in PROPRIETOR_APPELLANT_PATTERNS)
    if is_opponent and is_proprietor:
        return "both"
    if is_opponent:
        return "opponent"
    if is_proprietor:
        return "proprietor"
    return "unknown"


def violates_reformatio_in_peius(role, outcome_type):
    return role == "proprietor" and outcome_type in REVOKED_OUTCOMES
