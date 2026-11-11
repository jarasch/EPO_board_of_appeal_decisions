"""Phase 3 -- question understanding.

One LLM call, structured output via the existing `QueryIntent` model
(`retrieval/intent.py`) and the existing `db.chat(response_format=...)` helper, which
already knows how to call `.parse()` and hand back the parsed pydantic object.

Falls back to `intent.from_question` (no LLM, semantic-only) on any failure --
network error, malformed output, missing API key -- matching the "detection
failure is non-fatal, proceed with original values" pattern already used
elsewhere in this codebase (mcp-neo4j-lexical-graph's auto-fallback detection).
A parse failure should degrade retrieval quality, not take the app down.
"""

from retrieval import db
from retrieval.intent import QueryIntent, from_question

SYSTEM_PROMPT = """You turn a patent-law question about EPO Board of Appeal decisions into a
structured retrieval intent. Extract only what is actually in the question -- do not invent
dates, articles or case numbers that were not mentioned.

legal_issues: grounds in dispute, using EPO terminology (inventive step, novelty, added
    subject-matter, sufficiency of disclosure, clarity, admissibility, priority)
legal_tests: named doctrines/tests if the question names one (COMVIK, problem-solution approach,
    closest prior art, could-would, gold standard, technical effect, plausibility)
named_cases: decisions referenced by number, e.g. "T 641/00", "G 2/21" -- normalise to
    "<letter> <number>/<2-digit year>"
technical_terms: subject-matter terms worth an exact-phrase lexical search
articles: canonical EPC article codes if a provision is named, formatted "EPC_Art_<3-digit>",
    e.g. Article 56 EPC -> "EPC_Art_056", Article 123(2) EPC -> "EPC_Art_123"
date_from / date_to: ISO dates, only if the question states a bound ("since 2018" ->
    date_from="2018-01-01"; "before 2020" -> date_to="2019-12-31")
ipc_prefixes: IPC class prefixes, only if the question names a technical field directly
    (e.g. "computer-implemented inventions" -> ["G06F", "G06Q"]; "pharmaceutical compositions"
    -> ["A61K"]) -- leave empty rather than guessing
outcome_types: only if the question asks about a specific result, using these exact values:
    dismissed, set_aside_revoked, set_aside_maintained_as_amended,
    set_aside_maintained_as_granted, remitted, terminated, inadmissible
    (e.g. "patents that were revoked" -> ["set_aside_revoked"])
grounds: only if the question names a specific ground of opposition/refusal, using these exact
    values: Art_56_inventive_step, Art_54_novelty, Art_123_2_added_matter, Art_123_3_extension,
    Art_83_sufficiency, Art_84_clarity, Art_87_priority, Art_52_patentability, Art_53_exclusions,
    Proc_admissibility, Proc_fee_reimbursement, Proc_late_filed, Proc_referral, Proc_remittal,
    Proc_right_to_be_heard, Proc_substantial_violation, Proc_costs
grounds_met: only if the question asks specifically for grounds that succeeded (true) or failed
    (false) -- leave null if it just names the ground without saying which way
appellant_role: "opponent" | "proprietor" | "both", only if the question specifies who appealed
party_names: opponent/proprietor/applicant names if the question names a specific company
min_opponent_count: only if the question asks about multi-opponent cases specifically
semantic_query: the question rewritten as a clean statement of the subject matter, for vector
    search -- drop case numbers and article codes already captured above, keep the substance
"""


def parse_question(question):
    """Question text -> QueryIntent. Never raises; falls back to the no-LLM path."""
    try:
        parsed = db.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            response_format=QueryIntent,
        )
        if not parsed.semantic_query:
            parsed.semantic_query = question.strip()
        return parsed
    except Exception:
        return from_question(question)
