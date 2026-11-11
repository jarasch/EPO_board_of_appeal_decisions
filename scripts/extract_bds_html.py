#!/usr/bin/env python3
"""Extract a business distribution scheme from the OJ EPO HTML into the load CSVs.

The OJ article pages (e.g. https://www.epo.org/en/legal/official-journal/2026/01/a12)
are server-rendered, so the scheme can be lifted deterministically rather than
transcribed by hand or read by a model. Both matter here: this is a legal
reference table, and a silently mis-read exclusion would misallocate a whole IPC
class.

Two source documents per year:

    a11  Legal Board of Appeal   -- Article 1 lists the chair and members.
                                    No IPC allocation: the Legal Board takes
                                    J cases regardless of classification.
    a12  Technical Boards        -- Article 1 is the IPC allocation,
                                    Article 2 the composition per board.

Structure relied on: each board's block starts with a bold
"Board of Appeal <code>" heading, and articles start with a bold "Article <n>".
Both are stable across the years spot-checked (2014, 2017, 2018, 2020, 2021, 2026).

Download the sources first, then run this:

    curl -sSL -o data/bds/raw/oj2026_01_a12.html \\
        https://www.epo.org/en/legal/official-journal/2026/01/a12
    python3 scripts/extract_bds_html.py --year 2026

Writes data/bds/bds_<year>_allocation.csv and bds_<year>_members.csv, which
scripts/load_bds.py then loads.
"""

import argparse
import csv
import html
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data", "bds")
RAW_DIR = os.path.join(DATA_DIR, "raw")

BOARD_RE = re.compile(r"^Board of Appeal (\d\.\d\.\d\d)$")
ARTICLE_RE = re.compile(r"^Article\s+(\d+)$")
# "Ch: Name", "TM: Name", "LM: Name", and the combined "Ch + LM: Name".
MEMBER_RE = re.compile(r"^(Ch \+ LM|Ch|TM|LM):\s*(.+)$")
# A trailing validity qualifier: "(until 31.05.2026)", "(as from 01.06.2026)".
VALIDITY_RE = re.compile(r"\((?:\*?\s*)(until|as from)\s+([\d.]+)\)", re.IGNORECASE)

ROLE_MAP = {"Ch": "chair", "TM": "technical", "LM": "legal", "Ch + LM": "chair"}

# The Legal Board is board 3.1.01 -- verified against the corpus, where 3.1.01
# decides 1,278 J cases and nothing else.
LEGAL_BOARD_CODE = "3.1.01"

# An em/en dash alone means "no allocation this year" (vacant or wound down).
NO_ALLOCATION = {"-", "–", "—"}

# Corrections to the published text, keyed by (year, board). Applied to the
# extracted rule string, with the reasoning recorded in `source_note` so the
# change is visible in the graph rather than buried here. The raw HTML stays in
# data/bds/raw/ as provenance.
SOURCE_FIXUPS = {
    (2026, "3.4.03"): (
        ("G09B, F ; G", "G09B, F, G"),
        "published text reads 'G09B, F ; G' -- semicolon read as a comma, i.e. "
        "G09B/G09F/G09G, because board 3.4.01 takes 'G09 (exc. B, F, G)' and a "
        "bare section allocation 'G' would duplicate most of section G",
    ),
}


def body_lines(path):
    """Flatten the article body to text lines, marking bold runs with \\x01."""
    with open(path, encoding="utf-8") as handle:
        src = handle.read()

    start = src.find("oj-publication-content-container")
    if start > 0:
        src = src[start:]
    # Footnote markers sit inside the text and would corrupt IPC tokens.
    src = re.sub(r'<a class="FootnoteRef".*?</a>', "", src, flags=re.S)
    src = re.sub(r"<sup.*?</sup>", "", src, flags=re.S)
    src = src.replace("<strong>", "\x01").replace("</strong>", "")
    src = re.sub(r"<br\s*/?>", "\n", src)
    src = re.sub(r"<[^>]+>", "\n", src)

    lines = []
    for line in html.unescape(src).split("\n"):
        line = line.replace("\xa0", " ").strip()
        if line:
            lines.append(line)
    return lines


def split_articles(lines):
    """Group lines by article number, keyed on the 'Article <n>' headings.

    Bold is not the marker: the article headings sit in <h5> while the board
    headings inside them use <strong>. The anchored regex is what keeps prose
    references ("having regard to Article 1, paragraph 1") from starting a new
    article.
    """
    articles, current = {}, None
    for line in lines:
        plain = line.lstrip("\x01").strip()
        match = ARTICLE_RE.match(plain)
        if match:
            current = int(match.group(1))
            articles.setdefault(current, [])
            continue
        if current is not None:
            articles[current].append(line)
    return articles


def _blocks_by_board(lines):
    """Split one article's lines into {board_code: [lines]}."""
    blocks, current = {}, None
    for line in lines:
        plain = line.lstrip("\x01").strip()
        if line.startswith("\x01"):
            match = BOARD_RE.match(plain)
            if match:
                current = match.group(1)
                blocks[current] = []
                continue
            # Any other bold heading ends the current board's block.
            current = None
            continue
        if current is not None:
            blocks[current].append(plain)
    return blocks


def _iso(date_text):
    """'30.04.2026' -> '2026-04-30'."""
    day, month, year = date_text.strip(" .").split(".")
    return f"{year}-{month}-{day}"


def extract_allocation(articles, year):
    """Article 1 of a12: board -> allocation strings, split by validity window.

    The 2026 scheme is not uniform across the year: board 3.5.01 is wound down
    and its subject matter moves to 3.5.05/06/07 as from 01.05.2026. That is
    published as validity qualifiers, in two forms with opposite scope:

        "Until 30.04.2026:"     a prefix -- governs everything that FOLLOWS,
                                until the next prefix qualifier
        "(as from 01.05.2026)"  a parenthetical on its own line -- governs
                                everything ACCUMULATED since the last flush

    Flattening these away would silently merge two different allocations, so
    each window becomes its own row.
    """
    prefix_re = re.compile(r"^(Until|As from)\s+([\d.]+)\s*:$", re.IGNORECASE)
    paren_re = re.compile(r"^\(\s*(until|as from)\s+([\d.]+)\s*\)$", re.IGNORECASE)
    # A numbered sub-paragraph means the board list is over and the article's own
    # prose has started ("(2) If (a) because of the technical content ...").
    prose_re = re.compile(r"^\(([\da-z])\)")

    default = (f"{year}-01-01", f"{year}-12-31")
    rows = []

    for code, lines in _blocks_by_board(articles.get(1, [])).items():
        segments, window, emitted = [], default, 0

        def flush(win):
            nonlocal segments, emitted
            joined = re.sub(r"\s*;\s*", "; ", " ".join(segments)).strip("; ").strip()
            segments = []
            if not joined:
                return
            no_alloc = joined in NO_ALLOCATION
            note = "no allocation for this window" if no_alloc else ""

            fixup = SOURCE_FIXUPS.get((year, code))
            if fixup and not no_alloc:
                (before, after), reason = fixup
                if before in joined:
                    joined = joined.replace(before, after)
                    note = reason
                else:
                    note = f"EXPECTED FIXUP NOT APPLIED (source changed?): {reason}"

            rows.append({
                "board_code": code,
                "rule_raw": "" if no_alloc else joined,
                "valid_from": win[0],
                "valid_until": win[1],
                "source_note": note,
            })
            emitted += 1

        for line in lines:
            if prose_re.match(line):
                break

            match = prefix_re.match(line)
            if match:
                flush(window)
                keyword, date_text = match.group(1).lower(), _iso(match.group(2))
                window = (
                    (default[0], date_text) if keyword == "until" else (date_text, default[1])
                )
                continue

            match = paren_re.match(line)
            if match:
                keyword, date_text = match.group(1).lower(), _iso(match.group(2))
                flush(
                    (default[0], date_text) if keyword == "until" else (date_text, default[1])
                )
                continue

            segments.append(line)

        flush(window)

        if not emitted:
            rows.append({
                "board_code": code,
                "rule_raw": "",
                "valid_from": default[0],
                "valid_until": default[1],
                "source_note": "no allocation for this year",
            })
    return rows


def _member(code, raw, year):
    raw = raw.strip()
    validity = VALIDITY_RE.search(raw)
    name = VALIDITY_RE.sub("", raw).strip()
    is_deputy = "*" in name
    name = name.replace("*", "").strip(" ,;")
    if not name:
        return None
    return {
        "board_code": code,
        "name": name,
        "role": None,  # filled by caller
        "is_deputy": "true" if is_deputy else "false",
        "validity": f"{validity.group(1).lower()} {validity.group(2)}" if validity else "",
    }


def extract_members_technical(articles, year):
    """Article 2 of a12: board -> [chair, technical members, legal members]."""
    rows = []
    for code, lines in _blocks_by_board(articles.get(2, [])).items():
        for line in lines:
            if line in NO_ALLOCATION:
                continue
            match = MEMBER_RE.match(line)
            if not match:
                continue
            role_token, rest = match.groups()
            member = _member(code, rest, year)
            if not member:
                continue
            member["role"] = ROLE_MAP[role_token]
            rows.append(member)
            # "Ch + LM" is one person holding both roles; record the second too
            # so a legal-member query does not miss them.
            if role_token == "Ch + LM":
                extra = dict(member, role="legal")
                rows.append(extra)
    return rows


def extract_members_legal(lines, year):
    """Article 1 of a11: the Legal Board's chair and members.

    Every member of the Legal Board is legally qualified, so the published list
    carries no role tags and the role is implied.
    """
    rows, role = [], None
    for line in lines:
        plain = line.lstrip("\x01").strip()
        if line.startswith("\x01"):
            lowered = plain.lower().rstrip(":")
            if lowered.startswith("chair"):
                role = "chair"
            elif lowered.startswith("member"):
                role = "legal"
            continue
        if role is None or plain.startswith("The members"):
            continue
        member = _member(LEGAL_BOARD_CODE, plain, year)
        if member:
            member["role"] = role
            rows.append(member)
            role = "legal" if role == "chair" else role
    return rows


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {os.path.relpath(path, REPO)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--technical", help="path to the a12 HTML")
    parser.add_argument("--legal", help="path to the a11 HTML")
    args = parser.parse_args()

    technical = args.technical or os.path.join(RAW_DIR, f"oj{args.year}_01_a12.html")
    legal = args.legal or os.path.join(RAW_DIR, f"oj{args.year}_01_a11.html")

    if not os.path.exists(technical):
        raise SystemExit(f"missing {technical} -- download the OJ a12 page first (see docstring)")

    articles = split_articles(body_lines(technical))
    allocation = extract_allocation(articles, args.year)
    members = extract_members_technical(articles, args.year)
    print(f"a12: {len(allocation)} boards, {len(members)} member entries")

    if os.path.exists(legal):
        legal_articles = split_articles(body_lines(legal))
        legal_members = extract_members_legal(legal_articles.get(1, []), args.year)
        members.extend(legal_members)
        print(f"a11: {len(legal_members)} Legal Board member entries -> {LEGAL_BOARD_CODE}")
    else:
        print(f"a11 not found at {legal}, skipping the Legal Board")

    write_csv(
        os.path.join(DATA_DIR, f"bds_{args.year}_allocation.csv"),
        allocation,
        ["board_code", "rule_raw", "valid_from", "valid_until", "source_note"],
    )
    write_csv(
        os.path.join(DATA_DIR, f"bds_{args.year}_members.csv"),
        members,
        ["board_code", "name", "role", "is_deputy", "validity"],
    )


if __name__ == "__main__":
    main()
