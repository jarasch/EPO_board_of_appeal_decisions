"""Classify the operative order of a decision into a typed outcome.

Rule-based, not LLM, and deliberately so: the outcome is the join key for every
base rate in PHARMA_GENERICS_PLAN.md and EXAMINER_PLAN.md, so it has to be
auditable, deterministic and reproducible. A few percent of LLM error here would
silently poison every statistic computed downstream, and no count would reveal it.

Rules are viable because the orders are formulaic. Mined over 50,387 canonical
decisions, the top templates per language are:

    en  "the appeal is dismissed."                                   10,144
        "the decision under appeal is set aside. 2. the patent is revoked."  3,135
    de  "die beschwerde wird zurueckgewiesen."                         4,087
        "... wird aufgehoben. 2. das patent wird widerrufen."          1,236
    fr  "le recours est rejete."                                        879
        "... est annulee. 2. le brevet est revoque."                    236

All three official languages are handled. 35% of the corpus is DE/FR, and a
German-language decision is equally authoritative practice -- an EN-only
classifier would leave a third of every base rate in `unclassified`.

Phrases are matched anywhere in the order rather than as whole templates,
because an order routinely combines several operative acts: set aside, plus a
remittal, plus fee reimbursement, plus an apportionment of costs.
"""

import re

# --- operative phrase groups, en / de / fr ---------------------------------

# Matched on the verb alone rather than on a fixed subject phrase. The subject
# varies more than it first appears -- "the decision **of the Examination Board**
# under appeal is set aside", "la décision **de la division d'opposition** est
# annulée" -- and pinning the whole phrase left the entire D series and a large
# part of the French corpus unclassified.
SET_ASIDE = (
    "set aside",
    "aufgehoben",
    "annulée", "annulee", "annulé", "annule",
    "abgeändert", "abgeaendert",
)

# Regex for the same reason as SET_ASIDE and DISMISSED_RE: the patent is often
# named in the order -- "the patent **no. 0 820 265** is revoked" (T 1637/09) --
# and a fixed "patent is revoked" silently drops those into set_aside_other.
REVOKED_RE = re.compile(
    r"(?:patent[^.]{0,45}?(?:is|be)(?: hereby)? revoked"
    r"|patent[^.]{0,45}?wird widerrufen"
    r"|brevet[^.]{0,45}?est r[eé]voqu)",
    re.IGNORECASE,
)

# German writes the participle both solid and split ("aufrechterhalten" /
# "aufrecht erhalten"), and expresses "as granted" three ways: "in unveraenderter
# Form", "in der erteilten Fassung", "wie erteilt".
MAINTAINED_AS_GRANTED_RE = re.compile(
    r"(?:maintained (?:as granted|unamended|as it stands)"
    r"|(?:in unver[aä]nderter form|in der erteilten fassung|wie erteilt)"
    r"[^.]{0,30}?aufrecht ?erhalten"
    r"|maintenu tel que d[eé]livr)",
    re.IGNORECASE,
)

MAINTAINED_RE = re.compile(
    r"(?:patent[^.]{0,60}?(?:is|be) maintained|maintain the patent"
    r"|maintained (?:in amended form|on the basis of)"
    r"|patent[^.]{0,60}?(?:wird|werden) aufrecht ?erhalten"
    r"|aufrechtzuerhalten"
    r"|brevet[^.]{0,60}?est maintenu|maintenir le brevet)",
    re.IGNORECASE,
)

REMITTED = (
    "remitted to", "remitted for", "remitted with the order",
    "zurückverwiesen", "zurueckverwiesen",
    "an die erste instanz", "an die einspruchsabteilung", "an die prüfungsabteilung",
    "an die pruefungsabteilung", "zur weiteren entscheidung",
    "affaire est renvoyée", "affaire est renvoyee", "est renvoyée", "est renvoyee",
)

# Regex rather than fixed phrases, for the same reason as SET_ASIDE: the subject
# takes modifiers. "Die Beschwerden **der Beschwerdeführer 1 und 2** werden
# zurückgewiesen" is a dismissal, and a fixed "beschwerden werden zurückgewiesen"
# misses it. Anchored on the appeal noun so that a dismissed *request*
# ("Antrag wird zurückgewiesen") is not scored as a dismissed appeal.
DISMISSED_RE = re.compile(
    r"(?:appeals?[^.]{0,60}?(?:is|are|be) (?:dismissed|rejected|refused)"
    r"|beschwerden?[^.]{0,60}?(?:wird|werden) zurückgewiesen"
    r"|beschwerden?[^.]{0,60}?(?:wird|werden) zurueckgewiesen"
    r"|recours[^.]{0,60}?(?:est|sont) rejet)",
    re.IGNORECASE,
)

# --- proceedings that are not appeals against a decision -------------------
#
# 1,265 canonical decisions (2.5%) are G referrals, R petitions for review and
# W protests under Rule 40.2(c) PCT. They have no decision to set aside and no
# appeal to dismiss, so folding them into `dismissed` would quietly inflate the
# "board upholds the first instance" rate that PHARMA_GENERICS_PLAN.md Q2 and
# EXAMINER_PLAN.md Q5 are built on. Typed separately so they can be excluded.

REFERRAL_ANSWERED = (
    "question of law", "questions of law", "question referred", "questions referred",
    "rechtsfrage", "rechtsfragen", "vorgelegte frage",
    "question de droit", "questions de droit",
)

PETITION_REJECTED = (
    "petition for review", "antrag auf überprüfung", "antrag auf ueberpruefung",
    "requête en révision", "requete en revision",
)

PROTEST_DECIDED = (
    "protest under rule", "protest is", "widerspruch",
    "réserve est", "reserve est",
)

REQUEST_REFUSED = (
    "request is refused", "request is dismissed", "request is rejected",
    "requests are refused", "requests are dismissed",
    "antrag wird zurückgewiesen", "antrag wird abgelehnt",
    "requête est rejetée", "requete est rejetee", "demande est rejetée",
)

INADMISSIBLE = (
    "as inadmissible", "is inadmissible", "are inadmissible",
    "deemed not to have been filed", "deemed not todhave been filed",
    "als unzulässig", "als unzuläßig", "als unzulaessig", "unzulässig verworfen",
    "ist unzulässig", "sind unzulässig", "ist unzuläßig",
    "gilt als nicht eingelegt",
    "comme irrecevable", "est irrecevable", "réputé non formé", "repute non forme",
)

TERMINATED = (
    "proceedings are terminated", "proceedings are closed",
    "appeal proceedings are terminated",
    "beschwerdeverfahren ist beendet", "verfahren wird eingestellt",
    "verfahren ist beendet",
    "procédure de recours est close", "procedure de recours est close",
    "procédure est closes", "est clôturée", "est cloturee",
)

# Reimbursement has to be split into ordered and refused. A bare substring match
# on "reimbursement of the appeal fee" scores "the request for reimbursement of
# the appeal fee is refused" as a reimbursement -- inverting the very signal
# EXAMINER_PLAN.md Q6 uses to find substantial procedural violations.
#
# The refusals are independently valuable there: they are the near-miss cases
# where the board found no violation and said why.
FEE_REIMBURSED_RE = re.compile(
    r"(?:reimbursement of the (?:appeal )?fee[^.]{0,40}?is ordered"
    r"|appeal fees? (?:of [^.]{0,40}?)?(?:is|are)(?: to be)? reimbursed"
    r"|reimbursement[^.]{0,40}?of the appeal fee is ordered"
    r"|rückzahlung der beschwerdegebühr[^.]{0,40}?(?:wird|ist) angeordnet"
    r"|beschwerdegebühr(?:en)? (?:wird|werden) zurückgezahlt"
    r"|remboursement de la taxe de recours est ordonné)",
    re.IGNORECASE,
)

FEE_REFUSED_RE = re.compile(
    r"(?:requests? for reimbursement[^.]{0,60}?(?:is|are) (?:refused|rejected|dismissed)"
    r"|reimbursement[^.]{0,40}?(?:is|are) (?:refused|rejected)"
    r"|antrag auf rückzahlung[^.]{0,60}?(?:wird|werden) (?:zurückgewiesen|abgelehnt)"
    r"|requête en remboursement[^.]{0,60}?est rejetée)",
    re.IGNORECASE,
)

COSTS_APPORTIONED = (
    "apportionment of costs", "apportionment of the costs",
    "kostenverteilung", "verteilung der kosten",
    "répartition des frais", "repartition des frais",
)

# The instruction attached to a remittal. "Remitted with the order to maintain
# the patent" is a remittal in form and a win for the proprietor in substance --
# recorded as both rather than collapsed into one, since Q11's patentee-outcome
# scale needs the substance and the procedural statistics need the form.
REMITTAL_MAINTAIN = (
    "order to maintain", "order to maintain the patent",
    "mit der auflage", "mit der anordnung", "aufrechtzuerhalten",
    "ordre de maintenir",
)
REMITTAL_FURTHER = (
    "for further prosecution", "zur weiteren", "pour poursuite",
    "poursuite de la procédure", "poursuite de la procedure",
)

# The surviving request, e.g. "auxiliary request 6" -- what actually survived is
# as commercially relevant as whether anything did.
_REQUEST_RE = re.compile(
    r"(auxiliary request(?:s)?\s+(?:no\.?\s*)?\d+|main request"
    r"|hilfsantrag(?:s)?\s+\d+|hauptantrag"
    r"|requête subsidiaire\s+\d+|requête principale)",
    re.IGNORECASE,
)

_PREAMBLE = re.compile(
    r"^\s*(order|entscheidungsformel|dispositif|tenor)\b[:.]?\s*", re.IGNORECASE)


def _normalise(text):
    return re.sub(r"\s+", " ", _PREAMBLE.sub("", text or "")).strip().lower()


def _any(text, phrases):
    return any(phrase in text for phrase in phrases)


def classify_order(text):
    """Classify one AppealOrder body.

    Returns a dict with `type`, the booleans `setAside` / `feeReimbursed` /
    `costsApportioned`, `remittalInstruction` and `survivingRequest`.

    `type` is one of: inadmissible, terminated, remitted, set_aside_revoked,
    set_aside_maintained_as_granted, set_aside_maintained_as_amended,
    set_aside_other, dismissed, revoked, maintained, unclassified.

    `unclassified` is a real answer, not a fallback to guess around: every base
    rate built on this has to publish how much of its denominator was unreadable.
    """
    body = _normalise(text)
    if not body:
        return {"type": "unclassified", "setAside": False, "feeReimbursed": False,
                "feeReimbursementRefused": False,
                "costsApportioned": False, "remittalInstruction": None,
                "survivingRequest": None}

    set_aside = _any(body, SET_ASIDE)
    remitted = _any(body, REMITTED)
    revoked = bool(REVOKED_RE.search(body))
    as_granted = bool(MAINTAINED_AS_GRANTED_RE.search(body))
    maintained = as_granted or bool(MAINTAINED_RE.search(body))

    # Inadmissibility and termination are dispositive of the whole appeal and
    # outrank everything else: an appeal dismissed *as inadmissible* was never
    # decided on the merits, and pooling it with merits dismissals would
    # overstate how often boards uphold the decision under appeal.
    if _any(body, PETITION_REJECTED):
        # R series. Checked first: a petition for review is "rejected as clearly
        # unallowable", which would otherwise read as an inadmissible appeal.
        outcome = "petition_decided"
    elif _any(body, REFERRAL_ANSWERED):
        outcome = "referral_answered"
    elif _any(body, PROTEST_DECIDED):
        outcome = "protest_decided"
    elif _any(body, INADMISSIBLE):
        outcome = "inadmissible"
    elif _any(body, TERMINATED):
        outcome = "terminated"
    elif remitted:
        # Checked before maintenance: the operative act is the remittal, and the
        # maintenance it may direct is captured in `remittalInstruction`.
        outcome = "remitted"
    elif set_aside and revoked:
        outcome = "set_aside_revoked"
    elif set_aside and as_granted:
        outcome = "set_aside_maintained_as_granted"
    elif set_aside and maintained:
        outcome = "set_aside_maintained_as_amended"
    elif set_aside:
        outcome = "set_aside_other"
    elif DISMISSED_RE.search(body):
        outcome = "dismissed"
    elif revoked:
        outcome = "revoked"
    elif maintained:
        outcome = "maintained"
    elif _any(body, REQUEST_REFUSED) or FEE_REFUSED_RE.search(body):
        # An ancillary order that disposes of a request without touching the
        # decision under appeal. Not a merits outcome, and not `unclassified`
        # either -- it was read correctly, it simply is not an appeal outcome.
        outcome = "request_decided"
    else:
        outcome = "unclassified"

    instruction = None
    if outcome == "remitted":
        if _any(body, REMITTAL_MAINTAIN):
            instruction = "maintain"
        elif _any(body, REMITTAL_FURTHER):
            instruction = "further_prosecution"

    request = _REQUEST_RE.search(body)

    return {
        "type": outcome,
        "setAside": set_aside,
        "feeReimbursed": bool(FEE_REIMBURSED_RE.search(body)),
        "feeReimbursementRefused": bool(FEE_REFUSED_RE.search(body)),
        "costsApportioned": _any(body, COSTS_APPORTIONED),
        "remittalInstruction": instruction,
        "survivingRequest": request.group(1) if request else None,
    }


# --- the patentee-outcome scale used by PHARMA_GENERICS_PLAN.md Q11 ---------
#
# Only meaningful together with the appellant's role: where only the proprietor
# appealed the board cannot revoke (reformatio in peius, G 9/92 / G 4/93), so the
# available outcomes differ by stratum and the rates are not comparable across
# them. This maps the operative result alone; the stratification is the caller's
# job and is enforced in the analytical queries.
PATENTEE_DIRECTION = {
    "set_aside_maintained_as_granted": "pro_patentee",
    "maintained": "pro_patentee",
    "set_aside_maintained_as_amended": "partial",
    "set_aside_revoked": "anti_patentee",
    "revoked": "anti_patentee",
    # dismissed is directional only once you know who appealed -- left out
    # on purpose so it cannot be scored by accident.
}
