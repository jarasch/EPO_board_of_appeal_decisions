"""Canonicalisation of :Party surface forms onto :Organisation (PHARMA_GENERICS_PLAN.md P4).

The raw `:Party` layer is one node per distinct name *string*, and the corpus
writes the same legal entity a different way almost every time it appears:
numbering markers carried over from the decision's cover sheet
(`"01) BASF SE"`, `"(II) Siemens AG"`, `"Opponent 01: ..."`), a city qualifier
glued onto the legal form (`"BASF Aktiengesellschaft, Ludwigshafen"` vs
`"BASF Aktiengesellschaft"`), case variants (`"SIEMENS AKTIENGESELLSCHAFT"` vs
`"Siemens Aktiengesellschaft"`), and procedural annotations
(`"(opposition withdrawn)"`, `"(trading as Mylan)"`). BASF alone has >180
distinct Party strings for what is functionally one opponent history.

Two distinct problems, kept separate on purpose:

1. **Same legal entity, different spelling** -- `normalise` collapses these by
   stripping the markers/annotations above and folding legal-form spelling
   variants (`Aktiengesellschaft` == `AG`) for the *grouping key* only; the
   display name keeps the cleanest original spelling. Mechanical, and safe to
   apply corpus-wide.
2. **Different legal entities, same corporate family** -- Hexal AG and
   Novartis AG are two real, distinct legal persons; no amount of string
   normalisation makes them the same node, and pretending it does silently
   fabricates a merger. This is `CORPORATE_GROUPS`: a small, explicit,
   evidence-tagged table, extended by hand rather than inferred. Getting this
   wrong produces a *confidently wrong* opponent track record, which is worse
   than not answering, so entries with no solid evidence are marked
   `needs_review` (parent left unset) instead of guessed.
"""

import re
import unicodedata

# --- (1) same-entity string normalisation -----------------------------------

# Numbering carried over from the decision's opponent/applicant list --
# "01)", "(II)", "1.", "III:", "Opponent 01:". Stripped once, at the start of
# the string; a second marker later in the string ("1) BASF 2) AKZO N.V.")
# means the Party node actually holds *two* entities glued together by the
# upstream parser -- left alone rather than guessed apart, see `is_multi_party`.
_LEADING_MARKER_RE = re.compile(
    r"^\s*(?:opponent\s*)?(?:\(?\s*(?:\d{1,2}|[IVXLCM]{1,4})\s*\)?[.):]\s*)",
    re.IGNORECASE,
)

# A second numbering marker anywhere else in the string is the signature of
# the upstream-parser artefact above -- multiple opponents recorded as one
# Party node ("BASF, AKZO", "1)BASF 2)AKZO N.V.", "Behringwerke, Sandoz,
# Becton, Boehringer"). Not split here: the separators are ambiguous (", " is
# also used inside single names) and a wrong split fabricates parties that
# never existed as such. Flagged so downstream consumers can exclude them
# from a track-record count rather than silently mis-attribute it.
#
# The mid-string `\S\s+\d\s*\)` alternative was added after `resolve_group`
# (below) swept "Bayer AG 2) BASF AG" into the BASF rollup: it reads as one
# name at a glance, but the numbering marker sitting after "AG" and before
# "BASF" is the same second-opponent boundary as "1) BASF 2) AKZO N.V." --
# just missing the marker on the first name. The original pattern required
# *two* `\d)` markers and missed this.
_MULTI_PARTY_RE = re.compile(
    r"\d\s*\)\s*\S.*\d\s*\)|\S\s+\d\s*\)\s*\S|;|/|,\s*(?:AKZO|BASF|Bayer|Hoechst|Sandoz|Becton|"
    r"Boehringer|Siemens|CIBA|DSM|Imperial)",
    re.IGNORECASE,
)

# Trailing annotations this module understands well enough to strip safely.
# Each strips to a flag/value rather than being discarded silently.
_WITHDRAWN_RE = re.compile(
    r"\((?:opposition |appeal and opposition )?(?:withdrawn)"
    r"|zur[uü]ckgenommen|retir[eé]|beendet\)",
    re.IGNORECASE,
)
_FORMER_OPPONENT_RE = re.compile(r"\(former opponent\)", re.IGNORECASE)
_TRADING_AS_RE = re.compile(r"\(trading as ([^)]+)\)", re.IGNORECASE)
_ET_AL_RE = re.compile(r",?\s*et al\.?\s*$", re.IGNORECASE)
# Single-letter EPO document-language tag, "(d)" / "(e)" / "(f)" -- distinct
# from a genuine two-letter country/jurisdiction code like "(DE)", which is
# left untouched since it is not purely cosmetic.
_DOC_TAG_RE = re.compile(r"\(\s*[a-z]\s*\)\s*$")

# Legal-form endings recognised for the city-qualifier strip below. Order
# does not matter; matched case-insensitively against the tail of the name.
_LEGAL_FORM_ENDINGS = (
    "aktiengesellschaft", "kgaa", "gmbh & co\\. kg", "gmbh", "ag", "se", "kg",
    "s\\.p\\.a\\.", "spa", "s\\.r\\.l\\.", "srl", "s\\.a\\.s\\.", "sas",
    "s\\.l\\.u\\.", "slu", "s\\.l\\.", "sl", "s\\.a\\.", "sa",
    "b\\.v\\.", "bv", "n\\.v\\.", "nv", "ltd", "limited", "plc",
    "inc\\.", "inc", "llc", "l\\.p\\.", "lp", "co\\.,? ltd\\.?", "oy",
    "a/s", "ab", "ehf", "hf",
)
# "<name ending in a legal form>, <city>" -- the German/Nordic convention of
# glueing the registered seat onto the legal form. Guarded to the legal-form
# anchor so it does not fire on "BASF, AKZO" (no legal form before the
# comma) or swallow a second entity in a comma-joined multi-party string.
_CITY_QUALIFIER_RE = re.compile(
    r"^(?P<base>.*\b(?:" + "|".join(_LEGAL_FORM_ENDINGS) + r"))\s*,\s*"
    r"(?P<city>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .\-]{1,40})$",
    re.IGNORECASE,
)

# Full-word -> abbreviation, applied to the *grouping key* only (never to the
# display name), so "Aktiengesellschaft" and "AG" fold to one key.
_LEGAL_FORM_KEY_MAP = {
    "aktiengesellschaft": "ag",
    "incorporated": "inc",
    "limited": "ltd",
    "corporation": "corp",
    "company": "co",
}


def _strip_diacritics(text):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def is_multi_party(raw_name):
    """True if a Party node looks like >1 entity glued into one string.

    A known upstream-parser artefact, not something this module fixes --
    surfaced so callers (e.g. a Q6 track-record query) can exclude these
    from per-organisation counts instead of silently attributing an
    opposition to whichever entity happens to sort first.
    """
    return bool(_MULTI_PARTY_RE.search(raw_name or ""))


def normalise(raw_name):
    """Resolve one raw :Party.name into a grouping key + cleaned attributes.

    Returns a dict: `key` (the grouping key -- same key means "treat as the
    same legal entity"), `cleanName` (annotations/markers stripped, original
    spelling and case kept, for use as a *display name candidate*),
    `tradingAs` (captured from a "(trading as X)" annotation, or None),
    `isWithdrawn`, `isFormerOpponent`, `isMultiParty`.
    """
    name = (raw_name or "").strip()
    is_multi = is_multi_party(name)

    name = _LEADING_MARKER_RE.sub("", name).strip()

    is_withdrawn = bool(_WITHDRAWN_RE.search(name))
    is_former = bool(_FORMER_OPPONENT_RE.search(name))
    trading_as_match = _TRADING_AS_RE.search(name)
    trading_as = trading_as_match.group(1).strip() if trading_as_match else None

    for pattern in (_WITHDRAWN_RE, _FORMER_OPPONENT_RE, _TRADING_AS_RE):
        name = pattern.sub("", name)
    name = _DOC_TAG_RE.sub("", name)
    name = _ET_AL_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(",").strip()

    city_match = _CITY_QUALIFIER_RE.match(name)
    if city_match:
        city = city_match.group("city")
        # Refuse the strip if the "city" itself carries a digit or another
        # legal-form token -- that is a second entity, not a place name.
        if not re.search(r"\d", city) and not any(
            re.search(rf"\b{ending}\b", city, re.IGNORECASE)
            for ending in _LEGAL_FORM_ENDINGS
        ):
            name = city_match.group("base").strip()

    clean_name = name

    key = _strip_diacritics(name).casefold()
    key = re.sub(r"[.,]", "", key)
    for full, short in _LEGAL_FORM_KEY_MAP.items():
        key = re.sub(rf"\b{full}\b", short, key)
    key = re.sub(r"\s+", " ", key).strip()

    return {
        "key": key,
        "cleanName": clean_name,
        "tradingAs": trading_as,
        "isWithdrawn": is_withdrawn,
        "isFormerOpponent": is_former,
        "isMultiParty": is_multi,
    }


# --- (2) corporate-group roll-up ---------------------------------------------
#
# PHARMA_GENERICS_PLAN.md P4 asks for "the ~100 organisations that matter in
# pharma". This table covers ~38, in two batches: an initial pharma-specific
# set, and a general-industry expansion (below) built by cross-referencing
# this corpus's actual top-200 organisations by decision count against
# verified corporate history -- not memory alone. Several entries below were
# checked against a live search specifically because memory turned out to be
# wrong or incomplete on the details that matter here:
#
#   - Infineon's 1999 Siemens spin-off is not "independent since spin-off" --
#     Siemens held a 74% majority stake at least through Infineon's 2000 IPO.
#     Flagged needs_review rather than either assumption.
#   - BSH (Bosch/Siemens home appliances) was a 50/50 joint venture from 1967
#     to January 2015, when Bosch bought Siemens's half. The pre-2015 name
#     ("BSH Bosch und Siemens Hausgeräte GmbH") is flagged needs_review for
#     exactly the period it was jointly owned; only the post-2015 name
#     ("BSH Hausgeräte GmbH") rolls up to Bosch.
#
# Deliberately still short of "~100": most of the corpus's other top-200
# organisations are genuinely independent, with no group relationship to
# assert (Novozymes was spun off from, and is not owned by, Novo Nordisk;
# Sumitomo Chemical and Sumitomo Electric share a keiretsu heritage, not
# ownership) -- inventing a rollup where none exists is exactly the mistake
# this table exists to avoid, so those are simply left out rather than
# padded in. What is here is either read directly off the corpus text
# (`evidence: "corpus"`) or a documented corporate event (`evidence:
# "external"`); anything with a real chance of being wrong for a subset of
# decisions is marked `needs_review` with no parent asserted, rather than
# guessed. Extend this table with verified facts rather than
# plausible-sounding ones.

CORPORATE_GROUPS = [
    {
        "match": re.compile(r"\bratiopharm\b", re.IGNORECASE),
        "parent": "Teva Pharmaceutical Industries Ltd.",
        "evidence": "external",
        "note": "Teva completed the acquisition of ratiopharm in 2010; ratiopharm "
                "ceased to trade independently. No known subsequent divestment.",
    },
    {
        "match": re.compile(r"\bhexal\b", re.IGNORECASE),
        "parent": "Novartis AG",
        "evidence": "external",
        "note": "Novartis (via its Sandoz division) acquired Hexal AG in 2005. "
                "CAVEAT: Novartis demerged Sandoz -- including Hexal -- into the "
                "independent Sandoz Group AG in Oct 2023. This edge is not "
                "date-filtered against Decision.decisionDate; check the date "
                "before using it for a decision after 2023-10-01.",
    },
    {
        "match": re.compile(r"\bsandoz\b", re.IGNORECASE),
        "parent": "Novartis AG",
        "evidence": "external",
        "note": "Same caveat as Hexal above -- Sandoz was demerged from Novartis "
                "in Oct 2023 and is independent (Sandoz Group AG) after that date.",
    },
    {
        # Matched on the tradingAs field captured by `normalise`, not on the
        # name text -- this is the one row backed by the corpus itself:
        # several "Generics [UK] Limited" records literally say
        # "(trading as Mylan)".
        "match_trading_as": "mylan",
        "parent": "Mylan",
        "evidence": "corpus",
        "note": "Party name annotated \"(trading as Mylan)\" in the decision text.",
    },
    {
        "match": re.compile(r"^mylan\b", re.IGNORECASE),
        "parent": "Viatris Inc.",
        "evidence": "external",
        "note": "Pfizer's Upjohn generics unit merged with Mylan N.V. to form "
                "Viatris Inc. in Nov 2020. Single, uncontested event.",
    },
    {
        "match": re.compile(r"\bactavis\b", re.IGNORECASE),
        "parent": None,
        "evidence": "needs_review",
        "note": "No parent asserted. Teva acquired most of Actavis Generics in "
                "2016, but EU competition remedies required divesting national "
                "businesses to third parties -- e.g. the UK generics business "
                "went to Accord Healthcare/Intas, not Teva. Which parent applies "
                "depends on the specific Actavis entity and decision date; "
                "assign per-entity by hand rather than as one rollup.",
    },

    # --- general-industry expansion, verified against this corpus's actual
    # top-200 organisations (see module docstring above) ---------------------

    {
        "match": re.compile(r"\bbasf\b", re.IGNORECASE),
        "parent": "BASF SE",
        "evidence": "external",
        "note": "BASF Aktiengesellschaft converted to a Societas Europaea (SE) "
                "in 2008 -- same continuing legal entity, legal-form change "
                "only. Matches broadly ('BASF Coatings GmbH', 'BASF Catalysts "
                "LLC', ...) because BASF-branded subsidiaries are, as far as "
                "verified, genuinely part of the BASF group.",
    },
    {
        "match": re.compile(r"\bhenkel\b", re.IGNORECASE),
        "parent": "Henkel AG & Co. KGaA",
        "evidence": "external",
        "note": "Collapses spelling/expansion variants of the same legal form "
                "('Henkel Kommanditgesellschaft auf Aktien' is German for "
                "'KGaA' written out in full) rather than a real corporate "
                "event -- the string-normalisation step (D1 above) did not "
                "catch this because it does not have 'KGaA' -> "
                "'Kommanditgesellschaft auf Aktien' in its legal-form map.",
    },
    {
        "match": re.compile(r"^daimlerchrysler ag$", re.IGNORECASE),
        "parent": "Daimler AG",
        "evidence": "external",
        "note": "DaimlerChrysler AG renamed itself Daimler AG on 4 Oct 2007 "
                "after divesting Chrysler to Cerberus Capital Management -- "
                "same continuing German entity. Verified via web search.",
    },
    {
        "match": re.compile(r"giesecke\s*[+&]\s*devrient currency technology",
                             re.IGNORECASE),
        "parent": "Giesecke & Devrient GmbH",
        "evidence": "external",
        "note": "Currency Technology GmbH is G+D's banknote/currency division, "
                "a subsidiary of the group holding company. Also collapses "
                "'Giesecke & Devrient' -> 'Giesecke+Devrient' (G+D restyled "
                "the ampersand as a plus sign in April 2018; same entity). "
                "Verified via web search.",
    },
    {
        "match": re.compile(r"^bayer$", re.IGNORECASE),
        "parent": "Bayer AG",
        "evidence": "external",
        "note": "Bare short form of the same entity, not a distinct company.",
    },
    {
        "match": re.compile(r"^ibm$", re.IGNORECASE),
        "parent": "International Business Machines Corporation",
        "evidence": "external",
        "note": "IBM is the standard abbreviation of the same entity.",
    },
    {
        "match": re.compile(r"^knorr-bremse$", re.IGNORECASE),
        "parent": "KNORR-BREMSE Systeme für Nutzfahrzeuge GmbH",
        "evidence": "external",
        "note": "Bare group name rolled up to the commercial-vehicle-systems "
                "subsidiary that files most of this group's EPO litigation.",
    },
    {
        "match": re.compile(r"^hoechst(\s+ag)?$", re.IGNORECASE),
        "parent": "Sanofi-Aventis Deutschland GmbH",
        "evidence": "external",
        "note": "Hoechst AG merged with Rhône-Poulenc to form Aventis in 1999; "
                "Aventis merged with Sanofi in 2004 (Sanofi-Aventis, later "
                "renamed Sanofi). Two mergers and two decades of history "
                "between the corpus entity and the parent named here -- "
                "flagged as a longer chain than the other entries in this "
                "table, but each link is well-documented and uncontested.",
    },
    {
        "match": re.compile(r"microsoft technology licensing", re.IGNORECASE),
        "parent": "MICROSOFT CORPORATION",
        "evidence": "external",
        "note": "Microsoft's patent-licensing subsidiary.",
    },
    {
        "match": re.compile(r"^rohm and haas company$", re.IGNORECASE),
        "parent": "THE DOW CHEMICAL COMPANY",
        "evidence": "external",
        "note": "Dow completed its acquisition of Rohm and Haas in 2009.",
    },
    {
        "match": re.compile(r"^union carbide corporation$", re.IGNORECASE),
        "parent": "THE DOW CHEMICAL COMPANY",
        "evidence": "external",
        "note": "Dow completed its acquisition of Union Carbide in 2001.",
    },
    {
        "match": re.compile(r"^dow global technologies llc$", re.IGNORECASE),
        "parent": "THE DOW CHEMICAL COMPANY",
        "evidence": "external",
        "note": "Dow's own patent-holding subsidiary.",
    },
    {
        "match": re.compile(r"^mobil oil corporation$", re.IGNORECASE),
        "parent": "ExxonMobil",
        "evidence": "external",
        "note": "Exxon and Mobil merged in 1999 to form ExxonMobil.",
    },
    {
        "match": re.compile(r"^exxonmobil chemical patents inc\.?$", re.IGNORECASE),
        "parent": "ExxonMobil",
        "evidence": "external",
        "note": "ExxonMobil's own patent-holding subsidiary.",
    },
    {
        "match": re.compile(r"^imperial chemical industries plc$", re.IGNORECASE),
        "parent": "Akzo Nobel N.V.",
        "evidence": "external",
        "note": "AkzoNobel completed its acquisition of ICI in Jan 2008.",
    },
    {
        "match": re.compile(r"^genencor international,? inc\.?$", re.IGNORECASE),
        "parent": "E.I. DU PONT DE NEMOURS AND COMPANY",
        "evidence": "external",
        "note": "Genencor was part of Danisco, which DuPont acquired in 2011 "
                "(became DuPont Industrial Biosciences).",
    },
    {
        "match": re.compile(r"^roche diagnostics gmbh$", re.IGNORECASE),
        "parent": "F. Hoffmann-La Roche AG",
        "evidence": "external",
        "note": "Roche's diagnostics subsidiary.",
    },
    {
        "match": re.compile(r"^genentech,? inc\.?$", re.IGNORECASE),
        "parent": "F. Hoffmann-La Roche AG",
        "evidence": "external",
        "note": "Roche held a majority stake in Genentech from 1990 and "
                "completed a full acquisition in 2009.",
    },
    {
        "match": re.compile(r"^glaxo group limited$", re.IGNORECASE),
        "parent": "GlaxoSmithKline",
        "evidence": "external",
        "note": "Glaxo Wellcome merged with SmithKline Beecham in 2000 to "
                "form GlaxoSmithKline; Glaxo Group Limited continues as a "
                "GSK subsidiary holding entity.",
    },
    {
        "match": re.compile(r"^glaxosmithkline biologicals sa$", re.IGNORECASE),
        "parent": "GlaxoSmithKline",
        "evidence": "external",
        "note": "GSK's vaccines subsidiary.",
    },
    {
        "match": re.compile(r"^unilever n\.?v\.?$", re.IGNORECASE),
        "parent": "Unilever PLC",
        "evidence": "external",
        "note": "Unilever unified its dual-listed PLC/N.V. structure into a "
                "single entity (Unilever PLC) in Nov 2020, verified via web "
                "search. CAVEAT: before that date the two were co-equal "
                "parallel-listed entities under a shared board, not parent "
                "and subsidiary -- this edge is not date-filtered against "
                "Decision.decisionDate; check the date before relying on it "
                "for a pre-2020 decision.",
    },
    {
        "match": re.compile(r"^bsh hausgeräte gmbh$", re.IGNORECASE),
        "parent": "Robert Bosch GmbH",
        "evidence": "external",
        "note": "Bosch bought out Siemens's 50% stake in the BSH home"
                "-appliances joint venture in Jan 2015 (~EUR 3bn), after which "
                "BSH was renamed from 'BSH Bosch und Siemens Hausgeräte GmbH' "
                "to 'BSH Hausgeräte GmbH'. Verified via web search. This row "
                "matches only the post-2015 name -- see the next row for the "
                "pre-2015 name, which is NOT rolled up here.",
    },
    {
        "match": re.compile(r"^bsh bosch und siemens hausgeräte gmbh$", re.IGNORECASE),
        "parent": None,
        "evidence": "needs_review",
        "note": "No parent asserted. This was the name used while BSH was a "
                "50/50 Bosch-Siemens joint venture (1967-2015) -- rolling it "
                "up to either Bosch or Siemens alone would misattribute the "
                "other's half-ownership for the entire period this name was "
                "in use. Verified via web search.",
    },
    {
        "match": re.compile(r"^infineon technologies ag$", re.IGNORECASE),
        "parent": None,
        "evidence": "needs_review",
        "note": "No parent asserted. Infineon was spun off from Siemens on "
                "1 Apr 1999, but Siemens retained a 74% majority stake at "
                "least through Infineon's IPO in March 2000 -- this is not "
                "the clean 'independent since spin-off' story it first "
                "appears to be, and the exact date Siemens fully divested is "
                "not confirmed. Verified via web search specifically because "
                "the initial assumption (no relationship) turned out to be "
                "incomplete.",
    },
    {
        "match": re.compile(r"^allergan,? inc\.?$", re.IGNORECASE),
        "parent": None,
        "evidence": "needs_review",
        "note": "No parent asserted. 'Allergan' names a chain of distinct "
                "entities over time -- the original California-based "
                "Allergan Inc. (this corpus entity), Actavis plc's 2015 "
                "rebrand to 'Allergan plc' after acquiring the original "
                "Allergan, and AbbVie's 2020 acquisition of Allergan plc. "
                "Same naming-collision risk as the Actavis entry above; "
                "assign per-decision by hand rather than as one rollup.",
    },
    {
        "match": re.compile(r"^fresenius medical care deutschland gmbh$", re.IGNORECASE),
        "parent": None,
        "evidence": "needs_review",
        "note": "No parent asserted. Fresenius Medical Care was historically "
                "majority-owned by Fresenius SE, but was reclassified in "
                "fiscal year 2023 as an 'Investment Company' with Fresenius "
                "SE holding only ~27.8% as of Dec 2025 -- no longer a "
                "controlled subsidiary in the traditional sense. Verified via "
                "web search; ownership percentage and classification changed "
                "recently enough that pre/post-2023 decisions may warrant "
                "different treatment.",
    },
    {
        "match": re.compile(r"^fresenius kabi deutschland gmbh$", re.IGNORECASE),
        "parent": "Fresenius AG",
        "evidence": "external",
        "note": "Fresenius Kabi is a wholly (100%) owned operating company of "
                "the Fresenius group. Verified via web search.",
    },
    {
        "match": re.compile(r"^ppg industries ohio,? inc\.?$", re.IGNORECASE),
        "parent": "PPG Industries, Inc.",
        "evidence": "external",
        "note": "Same PPG corporate family, US-state subsidiary naming.",
    },
    {
        "match": re.compile(r"^basell poliolefine italia s\.?r\.?l\.?$", re.IGNORECASE),
        "parent": "Basell Polyolefine GmbH",
        "evidence": "external",
        "note": "Same Basell/LyondellBasell corporate family (2007 Basell/"
                "Lyondell Chemical merger); grouped under the existing corpus "
                "entity rather than a synthetic 'LyondellBasell' node.",
    },
    {
        "match": re.compile(r"^nestec s\.?a\.?$", re.IGNORECASE),
        "parent": "Nestlé S.A.",
        "evidence": "external",
        "note": "Nestec S.A. (also styled Nestec Ltd/AG) is a Nestlé group "
                "subsidiary. Web search confirmed both this and 'Société des "
                "Produits Nestlé S.A.' are Nestlé subsidiaries but did not "
                "confirm the exact internal relationship between the two "
                "(successor vs. parallel entity) -- both are linked to the "
                "ultimate parent rather than to each other, deliberately not "
                "asserting a relationship that was not confirmed.",
    },
    {
        "match": re.compile(r"^société des produits nestlé s\.?a\.?$", re.IGNORECASE),
        "parent": "Nestlé S.A.",
        "evidence": "external",
        "note": "Nestlé's IP-holding subsidiary (Wikipedia). Same caveat as "
                "the Nestec row above.",
    },
]

_STRAWMAN_RE = re.compile(r"\bstraw\s*man\s+limited\b", re.IGNORECASE)


def is_strawman(clean_name):
    """Flag straw-man opponent filers identifiable by name alone.

    Deliberately narrow -- "Strawman Limited" is a name the corpus itself
    uses for this purpose (90 oppositions per PHARMA_GENERICS_PLAN.md).
    Detecting *unnamed* straw men (a shell company filing on someone else's
    behalf without saying so) is not a string-matching problem and is not
    attempted here.
    """
    return bool(_STRAWMAN_RE.search(clean_name or ""))


def resolve_group(clean_name, trading_as):
    """Look up `CORPORATE_GROUPS` for this organisation.

    Returns the matching row (with a `needs_review` flag baked in) or None
    if nothing matches. Trading-as rows are checked first since they are the
    corpus-evidenced ones.
    """
    if trading_as:
        for row in CORPORATE_GROUPS:
            if "match_trading_as" in row and row["match_trading_as"].lower() == trading_as.lower():
                return row
    for row in CORPORATE_GROUPS:
        if "match" in row and row["match"].search(clean_name or ""):
            return row
    return None
