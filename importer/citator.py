"""Citing-passage location -- EXAMINER_PLAN.md Phase E5, non-LLM half.

E5 is a two-step build: (1) locate the passage in the citing decision that
actually names the cited case -- cheap, deterministic, since case numbers
are highly distinctive strings -- then (2) classify that passage's treatment
(followed / distinguished / declined_to_follow / ...), which is a genuine
LLM task. This module is step (1) only. Step (2) is deliberately not
attempted here: it costs tokens, and locating the evidence first means the
classification pass runs on exactly the passages that matter rather than
scanning whole decisions.

`find_case_mentions` reuses the same case-number pattern as
`app/pipelines/common.py`'s citation-integrity check (kept as a separate
copy, not an import, so `importer/` does not depend on `app/` -- retrieval
code depends on `importer`/`retrieval`, never the other way around).
"""

import re

CASE_NUMBER_RE = re.compile(r"\b([GTJDRW])\s?(\d{1,4})/(\d{2})\b")


def find_case_mentions(text, code, appeal_num, year):
    """True if `text` names the case (code, appealNum, year) -- e.g.
    (code='T', appeal_num=641, year='00') matches "T 641/00" and "T641/00"
    but not "T 641/01" or "G 641/00".
    """
    target_num = int(appeal_num)
    target_year = year[-2:]
    for match in CASE_NUMBER_RE.finditer(text or ""):
        if (match.group(1) == code and int(match.group(2)) == target_num
                and match.group(3) == target_year):
            return True
    return False
