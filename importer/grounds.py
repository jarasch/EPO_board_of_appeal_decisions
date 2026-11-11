"""Normalise the EPO's own headword layer into typed ground dispositions.

`:Keyword` is the boards' own indexing of what each decision decided, and it is
97.3% populated across canonical decisions -- far better coverage than anything
extraction could produce. But it is unusable as stored: 53,233 distinct surface
forms over 49,062 decisions. "Inventive step" alone appears as

    Inventive step (yes)            2,822    Inventive step - yes        520
    Inventive step - (yes)          2,078    Inventive step - no         347
    Inventive step (no)             1,602    inventive step              398
    Inventive step - (no)           1,528    Inventive step              550
    Erfinderische Taetigkeit (ja)     937    Activite inventive (oui)    420
    Erfinderische Taetigkeit (bejaht) 537    ... and so on in 3 languages

Three things are packed into one string: the ground, the board's finding on it,
and sometimes which request it applied to ("Inventive step - main request (no)").
This module splits them.

The polarity trap
-----------------
"(yes)" does not mean the same thing for every ground, and this is the one thing
that will silently invert an analysis:

    Inventive step (yes)               requirement MET      -> for the patentee
    Sufficiency of disclosure (yes)    requirement MET      -> for the patentee
    Amendments - added subject-matter (yes)
                                       defect FOUND         -> AGAINST
    Substantial procedural violation (yes)
                                       violation FOUND      -> against the
                                                              first instance

So each ground declares its polarity, and the parsed result carries
`requirementMet` alongside the raw `finding`. Anything that aggregates across
grounds must use `requirementMet`; `finding` alone is only safe within one ground.
"""

import re

# polarity: "met" -> (yes) means the requirement is satisfied
#           "defect" -> (yes) means a defect or violation was found
GROUNDS = [
    # --- substantive patentability -----------------------------------------
    ("Art_54_novelty", "Novelty", "EPC_Art_054", "met", (
        "novelty and inventive step", "novelty", "neuheit", "nouveauté", "nouveaute",
        "grounds for opposition - lack of novelty",
    )),
    ("Art_56_inventive_step", "Inventive step", "EPC_Art_056", "met", (
        "inventive step", "erfinderische tätigkeit", "erfinderische taetigkeit",
        "activité inventive", "activite inventive",
        "grounds for opposition - lack of inventive step",
    )),
    ("Art_83_sufficiency", "Sufficiency of disclosure", "EPC_Art_083", "met", (
        "sufficiency of disclosure", "ausreichende offenbarung",
        "suffisance de l'exposé", "suffisance de l'expose",
        "grounds for opposition - insufficiency of disclosure",
        "insufficiency of disclosure",
    )),
    ("Art_84_clarity", "Claims - clarity", "EPC_Art_084", "met", (
        "claims - clarity", "clarity", "patentansprüche - klarheit",
        "patentansprueche - klarheit", "klarheit", "clarté", "clarte",
        "revendications - clarté",
    )),
    ("Art_53_exclusions", "Exceptions to patentability", "EPC_Art_053", "defect", (
        "exceptions to patentability", "patentierbarkeitsausnahmen",
        "exceptions à la brevetabilité",
    )),
    ("Art_52_patentability", "Patentable inventions", "EPC_Art_052", "met", (
        "patentable invention", "patentability", "technical character",
        "patentierbare erfindung", "technischer charakter",
    )),
    ("Art_87_priority", "Priority", "EPC_Art_087", "met", (
        "priority", "priorität", "prioritaet", "priorité", "priorite",
        "partial priority", "validity of priority",
    )),

    # --- amendments ---------------------------------------------------------
    # Split deliberately: "added subject-matter (yes)" is a defect while
    # "amendments - allowable (yes)" is compliance. Collapsing them into one
    # "amendments" ground would make the polarity undefinable.
    ("Art_123_2_added_matter", "Amendments - added subject-matter",
     "EPC_Art_123", "defect", (
        "amendments - added subject-matter", "added subject-matter",
        "amendments - extension beyond the content of the application as filed",
        "extension beyond the content of the application as filed",
        "änderungen - unzulässige erweiterung",
        "aenderungen - unzulaessige erweiterung",
        "änderungen - erweiterung über den inhalt der anmeldung in der eingereichten fassung hinaus",
        "unzulässige erweiterung", "erweiterung über den inhalt",
        "grounds for opposition - added subject-matter",
        "modifications - extension de l'objet",
        "divisional application - subject-matter extends beyond content of earlier application",
        "divisional application - subject-matter extends beyond content",
    )),
    ("Art_123_allowable", "Amendments - allowable", "EPC_Art_123", "met", (
        "amendments - allowable", "änderungen - zulässig", "aenderungen - zulaessig",
        "amendments", "änderungen", "aenderungen", "modifications",
    )),
    ("Art_123_3_extension", "Amendments - extension of protection",
     "EPC_Art_123", "defect", (
        "extension of protection", "amendments - extension of protection",
        "schutzbereichserweiterung", "erweiterung des schutzbereichs",
    )),

    # --- procedure ----------------------------------------------------------
    ("Proc_substantial_violation", "Substantial procedural violation",
     "EPC_R_103", "defect", (
        "substantial procedural violation", "wesentlicher verfahrensmangel",
        "vice substantiel de procédure", "procedural violation",
    )),
    ("Proc_right_to_be_heard", "Right to be heard", "EPC_Art_113", "met", (
        "right to be heard", "rechtliches gehör", "rechtliches gehoer",
        "droit d'être entendu", "oral proceedings",
    )),
    ("Proc_admissibility", "Admissibility of appeal", "EPC_Art_108", "met", (
        "admissibility of appeal", "missing statement of grounds",
        "admissibility of appeal - missing statement of grounds",
        "zulässigkeit der beschwerde", "zulaessigkeit der beschwerde",
        "fehlende beschwerdebegründung", "fehlende beschwerdebegruendung",
        "recevabilité du recours", "admissibility",
    )),
    ("Proc_remittal", "Remittal", "RPBA_2020_Art_011", "met", (
        "remittal", "remittal to the department of first instance",
        "appeal decision - remittal to the department of first instance",
        "zurückverweisung", "zurueckverweisung",
        "zurückverweisung an die erste instanz", "renvoi",
    )),
    ("Proc_fee_reimbursement", "Reimbursement of appeal fee", "EPC_R_103", "met", (
        "reimbursement of appeal fee", "reimbursement of the appeal fee",
        "rückzahlung der beschwerdegebühr", "rueckzahlung der beschwerdegebuehr",
        "remboursement de la taxe de recours",
    )),
    ("Proc_late_filed", "Late-filed submissions", "RPBA_2020_Art_013", "met", (
        "late-filed request - admitted", "late-filed auxiliary requests - admitted",
        "late-filed evidence - admitted", "late-filed document - admitted",
        "late-filed request", "late-filed evidence", "late submission",
        "amendment after summons - exceptional circumstances",
        "amendment after summons - taken into account",
        "verspätet eingereichte", "verspaetet eingereichte",
        "änderung nach ladung", "aenderung nach ladung",
        "amendment after notification of art. 15(1) rpba communication",
    )),
    ("Proc_costs", "Apportionment of costs", "EPC_Art_104", "met", (
        "apportionment of costs", "kostenverteilung", "répartition des frais",
    )),
    ("Proc_referral", "Referral to the Enlarged Board", "EPC_Art_112", "met", (
        "referral to the enlarged board of appeal", "referral to the enlarged board",
        "vorlage an die grosse beschwerdekammer",
        "saisine de la grande chambre de recours",
    )),
]

# Longest alias first, so "novelty and inventive step" is not shadowed by
# "novelty", and "amendments - added subject-matter" beats "amendments".
_ALIAS_INDEX = sorted(
    ((alias, code, polarity) for code, _, _, polarity, aliases in GROUNDS
     for alias in aliases),
    key=lambda row: -len(row[0]),
)

GROUND_META = {code: {"label": label, "article": article, "polarity": polarity}
               for code, label, article, polarity, _ in GROUNDS}

# `[^)]*` so a qualified finding is still read: the boards write
# "Inventive step (yes, after amendment)" and "Claims - clarity (no, after
# amendment)", which a strictly-anchored pattern drops entirely.
_FINDING_RE = re.compile(
    r"[\s\-–]*\(?\s*(yes|no|ja|nein|bejaht|verneint|oui|non)\b[^)]*\)?\s*$",
    re.IGNORECASE)

_POSITIVE = {"yes", "ja", "bejaht", "oui"}

_QUALIFIER_RE = re.compile(
    r"\s*[-–]\s*(main request|auxiliary requests?\s*\d*|all requests"
    r"|hauptantrag|hilfsantrag\s*\d*"
    r"|requête principale|requête subsidiaire\s*\d*)\s*$",
    re.IGNORECASE)


def parse_keyword(text):
    """Split one headword into ground, finding, requirementMet and qualifier.

    Returns None when the headword maps to no known ground -- the long tail of
    47,330 stems is mostly one-off descriptive phrases, and guessing at them
    would be worse than leaving them out of the denominator.
    """
    if not text:
        return None
    body = re.sub(r"\s+", " ", text).strip()

    finding = None
    qualifier = None
    # Repeat: forms like "Inventive step - main request (no)" carry both, and the
    # finding sits outside the qualifier.
    for _ in range(3):
        match = _FINDING_RE.search(body)
        if match and finding is None:
            finding = match.group(1).lower()
            body = body[: match.start()].strip()
            continue
        match = _QUALIFIER_RE.search(body)
        if match and qualifier is None:
            qualifier = match.group(1).lower()
            body = body[: match.start()].strip()
            continue
        break

    stem = body.strip(" -–").lower()
    if not stem:
        return None

    # Segments as well as the whole stem, because the ground is not always
    # leftmost: "Decision re appeals - remittal" carries the ground in the
    # second segment, and "Claims - clarity after amendment" suffixes it.
    # _ALIAS_INDEX is longest-first, so a specific alias always wins over a
    # shorter one it contains.
    segments = [seg.strip() for seg in stem.split(" - ")]
    for alias, code, polarity in _ALIAS_INDEX:
        if (stem == alias or stem.startswith(alias)
                or any(seg == alias or seg.startswith(alias) for seg in segments)):
            met = None
            if finding is not None:
                positive = finding in _POSITIVE
                # The polarity flip: for a defect ground, "yes" means the defect
                # was found, so the requirement was NOT met.
                met = positive if polarity == "met" else not positive
            return {
                "code": code,
                "finding": finding,
                "requirementMet": met,
                "qualifier": qualifier,
                "matchedAlias": alias,
            }
    return None
