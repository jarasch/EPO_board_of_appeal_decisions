"""Shared helpers for the baseline and graphrag pipelines."""

import re

# EPO case numbers: a series letter, a number (unpadded, as attorneys write it),
# a 2-digit year. Matches both "T 914/12" and the less common no-space "T914/12".
CASE_NUMBER_RE = re.compile(r"\b([GTJDRW])\s?(\d{1,4})/(\d{2})\b")


def extract_case_numbers(text):
    """Case numbers mentioned in `text`, normalised to 'X 123/45'."""
    return sorted({
        f"{m.group(1)} {int(m.group(2))}/{m.group(3)}"
        for m in CASE_NUMBER_RE.finditer(text or "")
    })


def unverified_case_numbers(answer_text, known_refs):
    """Case numbers named in `answer_text` that are not among `known_refs`.

    `known_refs` should be citation strings or case refs from the retrieved set
    for THIS answer, not the whole corpus -- the corpus obviously contains
    almost any real case number, so that check would always pass and prove
    nothing. This asks the narrower, useful question: did the model's answer
    stay inside what was actually retrieved for it.

    Applying the same regex to `known_refs` as to the answer (rather than
    comparing raw strings) is what makes the two sides comparable: a citation
    string like "T 914/12, Order" and a bare case ref "T 914/12" both reduce to
    the same normalised form.
    """
    known = set()
    for ref in known_refs:
        known.update(extract_case_numbers(ref))
    return [case for case in extract_case_numbers(answer_text) if case not in known]
