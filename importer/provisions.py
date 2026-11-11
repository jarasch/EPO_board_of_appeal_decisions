"""Canonicalisation of :LegalProvision codes onto a single :Article per provision.

The corpus records the same article once per EPC version -- `EPC1973_Art_056` and
`EPC2000_Art_056` are the same Article 56 to an attorney -- plus a tail of typos and
version suffixes (`EPC2000_Art_056_(2007)`, `blankEPC_Art_056`, `EpC2000_Art_056`).
`canonicalise` maps a raw code onto (instrument, kind, number), deliberately keeping
the instrument: Art. 56 EPC and Art. 56 PCT are different provisions.
"""

import re

# <instrument>_<Art|R>_<number><suffixes>, e.g. EPC1973_Art_056, RPBA2020_Art_013(2).
# The instrument itself may contain underscores (`RPBA_2020_Art_013(2)`,
# `Paris_Convention_Art_004`), so it matches greedily and `rest` must start with a
# digit -- that is what forces the split onto the right `_Art_` / `_R_`.
_CODE_RE = re.compile(r"^(?P<instrument>[A-Za-z][A-Za-z0-9 _]*)_(?P<kind>Art|R)_(?P<rest>\d.*)$")

# Leading article number, optionally with the a/b/c letter suffix the EPC uses
# for inserted articles (Art. 112a EPC, R. 23b EPC 1973).
_NUMBER_RE = re.compile(r"^(?P<digits>\d+)(?P<alpha>[a-z]?)")

# Version year glued to (or spaced from) the instrument: EPC1973, RPBA 2020.
_VERSION_SUFFIX_RE = re.compile(r"\s*(?:19|20)\d{2}$")

# Instruments whose article numbering is stable across versions, so the version
# can be dropped: EPC 1973 Art. 56 and EPC 2000 Art. 56 are the same article.
# NOT true of the RPBA -- the 2020 revision renumbered -- so RPBA2020_Art_013 and
# RPBA_Art_013 stay distinct Articles.
_STABLE_NUMBERING = {"EPC"}

# Spelling variants of the same instrument seen in the corpus.
_INSTRUMENT_ALIASES = {
    "PARISCONVENTION": "PARIS",
    "PRBA2020": "RPBA2020",  # transposition typo in the source data
}

_KIND_LABEL = {"Art": "Art.", "R": "R."}


def _normalise_instrument(raw):
    """`EPC1973` / `blankEPC 1973` / `EpC2000` -> `EPC`; `RPBA2020` -> `RPBA`."""
    instrument = re.sub(r"\s+", " ", raw).strip()
    instrument = re.sub(r"^blank", "", instrument, flags=re.IGNORECASE)
    instrument = instrument.upper().replace(" ", "").replace("_", "")
    unversioned = _VERSION_SUFFIX_RE.sub("", instrument)
    if unversioned in _STABLE_NUMBERING:
        instrument = unversioned
    return _INSTRUMENT_ALIASES.get(instrument, instrument)


def canonicalise(code):
    """Map a raw LegalProvision code to a canonical Article dict, or None.

    Returns keys: code, instrument, kind ('Art'|'R'), number, label.
    None means the code has no parseable article number -- free-text citations
    ("VCLT: Art 31", transitional-provisions prose) keep only their
    :LegalProvision node.
    """
    if not code:
        return None

    match = _CODE_RE.match(code)
    if not match:
        return None

    number_match = _NUMBER_RE.match(match.group("rest"))
    if not number_match:
        return None

    instrument = _normalise_instrument(match.group("instrument"))
    if not instrument:
        return None

    kind = match.group("kind")
    # Zero-pad so codes sort numerically as strings: Art_009 before Art_056.
    number = f"{int(number_match.group('digits')):03d}{number_match.group('alpha')}"
    display_number = f"{int(number_match.group('digits'))}{number_match.group('alpha')}"

    return {
        "code": f"{instrument}_{kind}_{number}",
        "instrument": instrument,
        "kind": kind,
        "number": number,
        "label": f"{_KIND_LABEL[kind]} {display_number} {instrument}",
    }
