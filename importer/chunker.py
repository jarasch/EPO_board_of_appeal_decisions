"""Chunking of Section text into :Chunk rows.

Two strategies:

`chunk_section` -- token windows. Mirrors the token_window strategy used by this
workspace's neo4j-lexical-graph MCP server (cl100k_base encoding, token-count
window + overlap) so the resulting :Chunk nodes are compatible with its generic
embed_chunks tool (node_label="Chunk", defaults otherwise).

`chunk_section_paragraphs` -- legal paragraph boundaries. Token windows split EPO
reasoning mid-sentence, which both degrades extraction and destroys the citable
unit: attorneys cite "T 1234/15, Reasons 2.3", not "chunk 7". This strategy splits
on blank lines, recognises the leading legal numbering (`1.`, `2.1`, `III.`),
keeps unnumbered continuation paragraphs with the paragraph they belong to, and
packs whole paragraphs up to a token budget without ever splitting one -- unless a
single paragraph exceeds the budget on its own, in which case it is split on
sentence boundaries.
"""

import re

import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50

# Section type -> human-readable label prepended as embedding context.
SECTION_CONTEXT = {
    "HeadNote": "Headnote",
    "Catchword": "Catchword",
    "SummaryOfFacts": "Summary of Facts and Submissions",
    "ReasonsForDecision": "Reasons for the Decision",
    "AppealOrder": "Order",
    "Abstract": "Abstract",
}


def _token_windows(text, chunk_size, chunk_overlap):
    tokens = _ENCODING.encode(text)
    total = len(tokens)
    if total == 0:
        return
    step = chunk_size - chunk_overlap
    start = 0
    while start < total:
        end = min(start + chunk_size, total)
        yield tokens[start:end]
        next_start = start + step
        if next_start >= total or next_start <= start:
            break
        start = next_start


def chunk_section(section, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    """Split a Section's text into chunk rows ready for UNWIND.

    `section` is a dict with keys: id, type, text, documentName. Returns a list
    of dicts: id, text, index, tokenCount, type, documentName, sectionContext,
    sectionId -- in section order, so consecutive rows are NEXT-chain neighbors.
    """
    text = section.get("text")
    if not text:
        return []

    rows = []
    for i, chunk_tokens in enumerate(_token_windows(text, chunk_size, chunk_overlap)):
        rows.append({
            "id": f"{section['id']}_{i:04d}",
            "text": _ENCODING.decode(chunk_tokens),
            "index": i,
            "tokenCount": len(chunk_tokens),
            "type": section["type"],
            "documentName": section["documentName"],
            "sectionContext": SECTION_CONTEXT.get(section["type"], section["type"]),
            "sectionId": section["id"],
        })
    return rows


# --- paragraph-aware strategy ------------------------------------------------

PARAGRAPH_GENERATION = "para-v1"

DEFAULT_MAX_TOKENS = 600

# Chunks below this are merged into a neighbour: an 8-token fragment (a stray line
# from a list of amicus curiae parties, say) is noise in a vector index.
DEFAULT_MIN_TOKENS = 40

# Decimal legal numbering: `1.`, `2.3`, `4.1.2`, optionally with a trailing dot or
# bracket, and followed by whitespace or end of block.
_DECIMAL_REF_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3})*)[.)]?(?=\s|$)")
# Roman numbering as used in the older summaries: `I.`, `III.`, `IV)`.
_ROMAN_REF_RE = re.compile(r"^([IVXLC]{1,5})[.)](?=\s|$)")

_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")

# The corpus carries raw cp1252 bytes decoded as Latin-1, so the typographic
# quotes and dashes land in the C1 control range. Left as-is they are noise in
# both embeddings and printed citations.
_CP1252_REPAIRS = {
    "\x91": "‘", "\x92": "’",   # single quotes
    "\x93": "“", "\x94": "”",   # double quotes
    "\x95": "•", "\x96": "–",   # bullet, en dash
    "\x97": "—", "\x85": "…",   # em dash, ellipsis
}

# A block short enough, and unpunctuated enough, to be an inline heading
# ("Fresh case on appeal", "Interlocutory revision") rather than prose.
_MAX_HEADING_CHARS = 100

# Outline numbering used for the major divisions of a decision, as opposed to the
# citable paragraph numbering: `I. THE REFERRED QUESTIONS`, `C. ADMISSIBILITY`.
# A short unpunctuated block carrying one of these is a heading, not a paragraph.
_OUTLINE_NUMBER_RE = re.compile(r"^(?:[IVXLC]{1,5}|[A-Z])[.)]\s+")

# Tabular rows look exactly like headings to the length/punctuation test: short,
# no terminal punctuation, no paragraph number. Measured corpus-wide, ~0.3M
# tokens of table content was being discarded this way --
# "|  Alloy  |  Mn  |  Cu  |  Si  |" reads as navigation and is dropped.
#
# That matters out of proportion to the volume: in the chemistry and pharma
# series a table *is* the evidence -- comparative examples, dissolution data,
# dosage ranges -- and it is exactly what an inventive-step argument turns on.
_TABLE_DELIMITER_RE = re.compile(r"\|")
# Column alignment without pipes, counted rather than matched as a pattern: cells
# may themselves contain single spaces ("Example 1  Example 2  Example 3"), so
# any regex anchored on `\S+` between the gaps breaks on the first multi-word
# cell and the row reads as a heading again. Counting the gaps sidesteps that.
_TABLE_GAP_RE = re.compile(r" {2,}")
_MIN_TABLE_GAPS = 3


def _is_table_row(block):
    """True for a block that is tabular data rather than prose or a heading."""
    if _TABLE_DELIMITER_RE.search(block):
        return True
    return len(_TABLE_GAP_RE.findall(block)) >= _MIN_TABLE_GAPS


# Lettered enumeration, as used for the features of a claim:
#   a) wasserloeslichen nichtionischen Polymeren aus der Gruppe der
#   a1) Polyvinylpyrrolidone,
#   b4) Alkylacrylamid/Acrylsaeure-Copolymere
# `_paragraph_ref` only recognises decimal and Roman numbering, so these carry no
# ref; they are short and end mid-clause rather than in a full stop, which is
# exactly the heading signature. They were being discarded -- and in a chemistry
# or pharma case the claim features *are* the subject matter under assessment,
# so this cost more than the table rows did.
#
# Lowercase only, and deliberately case-sensitive: `I. THE REFERRED QUESTIONS`
# and `C. ADMISSIBILITY` are outline headings owned by `_OUTLINE_NUMBER_RE`, and
# matching case-insensitively swallows them. Claim features are conventionally
# lettered in lowercase, outline divisions in uppercase.
_ENUMERATION_RE = re.compile(r"^\(?[a-z]\d*[.)]\s")

# A block ending mid-clause is a continuation, never a heading: a trailing comma
# or a hyphenated word broken across lines.
_CONTINUATION_SUFFIXES = (",", "-", "–", "—", "/", "+")


def repair_text(text):
    for bad, good in _CP1252_REPAIRS.items():
        if bad in text:
            text = text.replace(bad, good)
    return text


def _paragraph_ref(block):
    """Leading legal numbering of a block, or None if it has none."""
    match = _DECIMAL_REF_RE.match(block)
    if match:
        return match.group(1)
    match = _ROMAN_REF_RE.match(block)
    if match:
        return match.group(1)
    return None


def _is_heading(block):
    """True for a division heading, numbered with an outline letter/numeral or not.

    Roman numerals are ambiguous: `I. THE REFERRED QUESTIONS` is a heading, while
    `I. The appellant lodged an appeal against...` is a numbered paragraph. Length
    and terminal punctuation separate the two.
    """
    if len(block) > _MAX_HEADING_CHARS or block.endswith((".", ":", ";", "?", "!")):
        return False
    # All three checked before the numbering tests, because a table row, an
    # enumerated claim feature and a mid-clause continuation each satisfy every
    # one of them while being content rather than navigation.
    if _is_table_row(block):
        return False
    if block.endswith(_CONTINUATION_SUFFIXES):
        return False
    if _ENUMERATION_RE.match(block):
        return False
    # Decimal numbering is always a citable paragraph, even when short
    # (`2.1 Admissibility` heads the paragraph that follows it).
    return _OUTLINE_NUMBER_RE.match(block) is not None or _paragraph_ref(block) is None


def _group_blocks(text):
    """Blocks -> paragraph groups [{ref, heading, blocks}].

    A group starts at each numbered block; unnumbered prose is appended to the
    open group (or opens a ref-less group if the section starts with prose).
    Headings are not part of any group -- they become the `heading` context of the
    groups that follow them.
    """
    groups = []
    heading = None
    headings_seen = []
    for raw_block in re.split(r"\n\s*\n", text):
        block = raw_block.strip()
        if not block:
            continue

        if _is_heading(block):
            heading = block
            headings_seen.append(block)
            continue

        ref = _paragraph_ref(block)
        if ref is not None or not groups or groups[-1]["heading"] != heading:
            groups.append({"ref": ref, "heading": heading, "blocks": [block]})
        else:
            groups[-1]["blocks"].append(block)

    if not groups and headings_seen:
        # A section made up entirely of heading-shaped blocks is content, not
        # navigation. 682 sections corpus-wide are exactly this -- 498 Catchwords
        # and 28 HeadNotes whose whole body is one short unpunctuated phrase
        # ("Erfinderische Tatigkeit") with no paragraph after it. A heading is
        # normally preserved as the `headingContext` of the paragraphs it
        # introduces, but with nothing following it there is no carrier and the
        # legally indexed topic would be dropped from the graph altogether.
        #
        # Deliberately only when no group was produced: firing this in a section
        # that already has groups could append a chunk that `_coalesce_small`
        # merges backwards, rewriting the text of an already-embedded chunk.
        groups.append({"ref": None, "heading": None, "blocks": headings_seen})
    return groups


def _split_oversized(text, max_tokens):
    """Split a single over-budget paragraph on sentence boundaries."""
    sentences = _SENTENCE_BOUNDARY_RE.split(text)
    parts, current, current_tokens = [], [], 0
    for sentence in sentences:
        tokens = len(_ENCODING.encode(sentence))
        if current and current_tokens + tokens > max_tokens:
            parts.append(" ".join(current))
            current, current_tokens = [], 0
        current.append(sentence)
        current_tokens += tokens
    if current:
        parts.append(" ".join(current))
    return parts


def _coalesce_small(packed, min_tokens, max_tokens):
    """Merge sub-`min_tokens` chunks into a neighbour, preferring the one before."""
    merged = []
    for chunk in packed:
        if (merged and chunk["tokenCount"] < min_tokens
                and merged[-1]["tokenCount"] + chunk["tokenCount"] <= max_tokens):
            merged[-1]["text"] += "\n\n" + chunk["text"]
            merged[-1]["tokenCount"] += chunk["tokenCount"]
            merged[-1]["refs"].extend(chunk["refs"])
            merged[-1]["groups"].extend(chunk["groups"])
            continue
        if (merged and merged[-1]["tokenCount"] < min_tokens
                and merged[-1]["tokenCount"] + chunk["tokenCount"] <= max_tokens):
            chunk = dict(chunk,
                         text=merged[-1]["text"] + "\n\n" + chunk["text"],
                         tokenCount=merged[-1]["tokenCount"] + chunk["tokenCount"],
                         refs=merged[-1]["refs"] + chunk["refs"],
                         groups=merged[-1]["groups"] + chunk["groups"],
                         heading=merged[-1]["heading"] or chunk["heading"])
            merged.pop()
        merged.append(chunk)
    return merged


def _primary_ref(refs):
    """The citable paragraph number for a chunk.

    Prefers decimal numbering -- an attorney cites "Reasons 7", not "Reasons III".
    """
    for ref in refs:
        if ref[0].isdigit():
            return ref
    return refs[0] if refs else None


def chunk_section_paragraphs(section, max_tokens=DEFAULT_MAX_TOKENS,
                             min_tokens=DEFAULT_MIN_TOKENS):
    """Split a Section's text into paragraph-aligned chunk rows ready for UNWIND.

    `section` is a dict with keys: id, type, text, documentName. Returns a list of
    dicts adding `paragraphRef` (the citable legal paragraph number the chunk
    starts at, e.g. "2.3"), `paragraphRefs` and `headingContext` to the fields
    `chunk_section` produces -- in section order, so consecutive rows are
    NEXT-chain neighbours.

    `paragraphRefs` is best-effort: enumerations inside a paragraph ("1. ... 2. ..."
    in a quoted claim) can add spurious entries. `paragraphRef` -- the field to
    cite from -- is the first decimal ref, which is the paragraph the chunk opens.
    """
    text = section.get("text")
    if not text:
        return []

    groups = _group_blocks(repair_text(text))
    section_context = SECTION_CONTEXT.get(section["type"], section["type"])

    # Pack whole groups up to the budget; never merge across a heading change.
    # `groups` carries the index of every paragraph group a chunk consumed. It is
    # bookkeeping only -- it never affects text, ids or refs -- and it is what the
    # :Paragraph layer links against, because `refs` is best-effort (an enumeration
    # inside a quoted claim can add spurious entries) while group indices are exact.
    packed = []
    for group_index, group in enumerate(groups):
        body = "\n\n".join(group["blocks"])
        tokens = len(_ENCODING.encode(body))

        if tokens > max_tokens:
            for part in _split_oversized(body, max_tokens):
                packed.append({
                    "text": part,
                    "tokenCount": len(_ENCODING.encode(part)),
                    "refs": [group["ref"]] if group["ref"] else [],
                    "groups": [group_index],
                    "heading": group["heading"],
                })
            continue

        open_chunk = packed[-1] if packed else None
        if (open_chunk
                and open_chunk["heading"] == group["heading"]
                and open_chunk["tokenCount"] + tokens <= max_tokens):
            open_chunk["text"] += "\n\n" + body
            open_chunk["tokenCount"] += tokens
            open_chunk["groups"].append(group_index)
            if group["ref"]:
                open_chunk["refs"].append(group["ref"])
        else:
            packed.append({
                "text": body,
                "tokenCount": tokens,
                "refs": [group["ref"]] if group["ref"] else [],
                "groups": [group_index],
                "heading": group["heading"],
            })

    rows = []
    for i, chunk in enumerate(_coalesce_small(packed, min_tokens, max_tokens)):
        rows.append({
            "id": f"{section['id']}_p{i:04d}",
            "text": chunk["text"],
            "index": i,
            "tokenCount": chunk["tokenCount"],
            "type": section["type"],
            "documentName": section["documentName"],
            "sectionContext": section_context,
            "sectionId": section["id"],
            "paragraphRef": _primary_ref(chunk["refs"]),
            "paragraphRefs": chunk["refs"],
            "paragraphIndexes": sorted(set(chunk["groups"])),
            "headingContext": chunk["heading"],
            "generation": PARAGRAPH_GENERATION,
        })
    return rows


def section_paragraphs(section):
    """The Section's paragraph groups as rows, one per citable legal paragraph.

    This is the structural layer that sits between `:Section` and `:Chunk`: exactly
    the groups `chunk_section_paragraphs` packs, in section order, so a chunk's
    `paragraphIndexes` index straight into this list.

    A group with `ref = None` is real structure, not a failure -- an appeal order
    is unnumbered by nature, and a Reasons section can open with unnumbered prose.
    Those paragraphs are kept so the layer is a faithful decomposition of the
    section rather than only its numbered parts.
    """
    text = section.get("text")
    if not text:
        return []

    rows = []
    for index, group in enumerate(_group_blocks(repair_text(text))):
        body = "\n\n".join(group["blocks"])
        rows.append({
            "id": f"{section['id']}_g{index:04d}",
            "sectionId": section["id"],
            "index": index,
            "ref": group["ref"],
            "text": body,
            "tokenCount": len(_ENCODING.encode(body)),
            "type": section["type"],
            "documentName": section["documentName"],
            "headingContext": group["heading"],
            "generation": PARAGRAPH_GENERATION,
        })
    return rows
