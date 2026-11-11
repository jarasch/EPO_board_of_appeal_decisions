"""Streaming parser for the EPO Board of Appeal decisions XML export.

Turns each <ep-appeal-decision> element into a plain dict via extract_decision().
Uses only the stdlib (xml.etree.ElementTree) so the ~1.2GB source file is read
incrementally rather than loaded into memory as a DOM.
"""

import xml.etree.ElementTree as ET

# (Section label, source element tag) for the six long-text blocks that get
# their own (:Section) nodes instead of living as properties on (:Decision).
SECTION_DEFS = [
    ("HeadNote", "ep-headnote"),
    ("Catchword", "ep-catchword"),
    ("SummaryOfFacts", "ep-summary-of-facts"),
    ("ReasonsForDecision", "ep-reasons-for-decision"),
    ("AppealOrder", "ep-appeal-order"),
    ("Abstract", "abstract"),
]

# Public decision page on epo.org; the slug is the bib-data `reference`
# attribute lowercased (e.g. D000011EU1 -> .../decisions/d000011eu1).
DECISION_URL_TEMPLATE = "https://www.epo.org/en/boards-of-appeal/decisions/{}"


def _text(el):
    if el is None:
        return None
    t = "".join(el.itertext()).strip()
    return t or None


def _section_text(el):
    """Flatten a (heading*, p+)+ style block into readable paragraphs."""
    if el is None:
        return None
    parts = []
    for child in el:
        t = "".join(child.itertext()).strip()
        if t:
            parts.append(t)
    if not parts:
        return _text(el)
    return "\n\n".join(parts)


def _iso_date(raw):
    """EPO dates are 'YYYYMMDD'. Returns 'YYYY-MM-DD' or None if unparseable."""
    if not raw or len(raw) != 8 or not raw.isdigit():
        return None
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def _document_id(el):
    if el is None:
        return None
    country = _text(el.find("country"))
    number = _text(el.find("doc-number"))
    kind = _text(el.find("kind"))
    date = _iso_date(_text(el.find("date")))
    if not number:
        return None
    return {
        "key": f"{country or ''}-{number}-{kind or ''}",
        "country": country,
        "number": number,
        "kind": kind,
        "date": date,
    }


def _ipc_symbol(cl):
    section = _text(cl.find("section")) or ""
    cls = _text(cl.find("class")) or ""
    subclass = _text(cl.find("subclass")) or ""
    main_group = _text(cl.find("main-group"))
    subgroup = _text(cl.find("subgroup"))
    symbol = f"{section}{cls}{subclass}".strip()
    if main_group:
        symbol += f" {main_group}"
        if subgroup:
            symbol += f"/{subgroup}"
    return symbol or None


def _party_names(container_el, addr_tag):
    if container_el is None:
        return []
    names = []
    for addr in container_el.findall(addr_tag):
        book = addr.find("addressbook")
        name = _text(book.find("name")) if book is not None else None
        if name:
            names.append(name)
    return names


def _legal_refs(el):
    refs = []
    if el is None:
        return refs
    for ref in el.findall("ep-legal-ref"):
        raw = _text(ref)
        if raw:
            refs.append({"code": raw, "document": None, "documentPart": None})
    for citation in el.findall("ep-legal-citation"):
        presentation = _text(citation.find("ep-legal-ref-presentation"))
        text_el = citation.find("ep-legal-text")
        document = _text(text_el.find("ep-legal-document")) if text_el is not None else None
        part = _text(text_el.find("ep-legal-document-part")) if text_el is not None else None
        code = presentation or (f"{document}_{part}" if document else None)
        if code:
            refs.append({"code": code, "document": document, "documentPart": part})
    return refs


def _cited_cases(el):
    cited = []
    if el is None:
        return cited
    for c in el.findall("ep-cited-decision"):
        code = c.get("code")
        country = c.get("country")
        appeal_num = _text(c.find("ep-appeal-num"))
        year = _text(c.find("ep-year"))
        if appeal_num and year:
            key = f"{code or ''}-{country or ''}-{appeal_num}-{year}"
            cited.append({
                "key": key, "code": code, "country": country,
                "appealNum": appeal_num, "year": year, "raw": None,
            })
        else:
            raw = _text(c)
            if raw:
                cited.append({
                    "key": f"raw-{raw}", "code": code, "country": country,
                    "appealNum": None, "year": None, "raw": raw,
                })
    return cited


def _keywords(decision_el):
    words = []
    for container in ("ep-keywords", "ep-keywords-documentation"):
        for kw in decision_el.findall(f"{container}/keyword"):
            t = _text(kw)
            if t:
                words.append(t)
    return words


def _sections(decision_el):
    sections = []
    for label, tag in SECTION_DEFS:
        text = _section_text(decision_el.find(tag))
        if text:
            sections.append({"type": label, "text": text})
    return sections


def extract_decision(elem):
    """Extract a single <ep-appeal-decision> element into a flat dict of lists."""
    bib = elem.find("ep-appeal-bib-data")
    if bib is None:
        return None

    case_num_el = bib.find("ep-case-num")
    code = case_num_el.get("code") if case_num_el is not None else None
    appeal_num = _text(case_num_el.find("ep-appeal-num")) if case_num_el is not None else None
    year = _text(case_num_el.find("ep-year")) if case_num_el is not None else None
    case_number = None
    if code and appeal_num and year:
        case_number = f"{code} {appeal_num}/{year[-2:]}"

    reference = bib.get("reference")
    if not reference:
        return None

    board_code = _text(bib.find("ep-board-of-appeal-code"))
    decision_date = _iso_date(_text(bib.find("ep-date-of-decision/date")))
    ecli = _text(bib.find("ep-ecli"))

    oj = bib.find("ep-official-journal")
    official_journal_ref = None
    if oj is not None:
        oj_num = _text(oj.find("ep-official-journal-num"))
        oj_year = _text(oj.find("ep-year"))
        oj_ppf = _text(oj.find("ppf"))
        official_journal_ref = ", ".join(x for x in (oj_num, oj_year, oj_ppf) if x) or None

    appeal_board = bib.find("ep-appeal-board")
    chairman = None
    board_members = []
    if appeal_board is not None:
        chairman_el = appeal_board.find("ep-board-chairman")
        chairman = _text(chairman_el.find("name")) if chairman_el is not None else None
        for m in appeal_board.findall("ep-board-member"):
            n = _text(m.find("name"))
            if n:
                board_members.append(n)

    registrar = _text(bib.find("ep-registrar/name"))

    decision = {
        "reference": reference,
        "url": DECISION_URL_TEMPLATE.format(reference.lower()),
        "ecli": ecli,
        "caseNumber": case_number,
        "code": code,
        "appealNum": appeal_num,
        "year": year,
        "lang": elem.get("lang"),
        "procedureLang": elem.get("procedure-lang"),
        "appealType": elem.get("appeal-type"),
        "dtdVersion": elem.get("dtd-version"),
        "volume": bib.get("volume"),
        "distributionCode": _text(bib.find("ep-distribution-code")),
        "decisionDate": decision_date,
        "boardCode": board_code,
        "headword": _text(elem.find("ep-headword")),
        "inventionTitle": _text(bib.find("invention-title")),
        "yearOfCaseLaw": _text(bib.find("ep-year-of-case-law")),
        "officialJournalRef": official_journal_ref,
    }

    related = {
        "application": _document_id(bib.find("application-reference/document-id")),
        "publication": _document_id(bib.find("publication-reference/document-id")),
        "ipcSymbols": [
            s for s in (
                _ipc_symbol(cl)
                for cl in bib.findall("classifications-ipcr/classification-ipcr")
            ) if s
        ],
        "applicants": _party_names(bib.find("ep-applicant-addresses"), "ep-applicant-address"),
        "opponents": _party_names(bib.find("ep-opponent-addresses"), "ep-opponent-address"),
        "representatives": _party_names(bib.find("ep-representative-addresses"), "ep-representative-address"),
        "chairman": chairman,
        "boardMembers": board_members,
        "registrar": registrar,
        "keywords": _keywords(elem),
        "legalRefs": _legal_refs(elem.find("ep-legal-refs")),
        "citedCases": _cited_cases(elem.find("ep-cited-decisions")),
        "sections": _sections(elem),
    }

    return decision, related


def iter_decisions(xml_path, limit=None):
    """Stream <ep-appeal-decision> elements from the source file, yielding
    (decision, related) tuples. Frees each element's subtree after use so
    memory stays bounded regardless of file size.
    """
    count = 0
    context = ET.iterparse(xml_path, events=("end",))
    for _, elem in context:
        if elem.tag != "ep-appeal-decision":
            continue
        try:
            result = extract_decision(elem)
            if result is not None:
                yield result
                count += 1
        finally:
            elem.clear()
        if limit is not None and count >= limit:
            break
