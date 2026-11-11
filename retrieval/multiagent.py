"""Multi-agent GraphRAG -- an opt-in, slower, more expensive path than
`app/pipelines/graphrag.py`'s single retrieve-then-generate pass.

Three agent roles, each a genuine LLM task the flat pipeline does not do:

    iterative retrieval  -- assesses whether the retrieved seed set actually
                             covers the question (e.g. contrary authority,
                             enough decisions) and can issue follow-up
                             searches, instead of trusting one fixed pass
    topic summarizer      -- one agent per Leiden-detected community (map),
                             so the final answer is organised by legal
                             topic instead of a flat citation list --
                             DEMO_IMPLEMENTATION_PLAN.md Phase 6, completed
                             here for the first time
    faithfulness critic   -- checks each citation in the drafted answer
                             against its actual source text and forces one
                             redraft if unsupported, closing the gap
                             `scripts/run_gold_set.py --with-synthesis`
                             deliberately left to a human grader

Runs over the full corpus (`decision_label="Decision"`), not the demo slice
-- `retrieval/subgraph.py` and `retrieval/communities.py` were generalised
for this (see their module comments). Corpus-scale Leiden exit criteria are
close to but not guaranteed to pass on the first attempt (measured: 15
communities, largest holding exactly 25.2% against a 25% limit on a real
question) -- `_detect_communities_with_retry` below bumps gamma once and
retries, per the plan's own stated approach to a failed exit criterion,
rather than hand-tuning a fixed gamma for corpus scope.

This is a real, ongoing cost per question (a dozen-plus LLM calls, not the
flat pipeline's two) -- by design an opt-in "deep" mode, not a replacement.
"""

import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from pydantic import BaseModel

from retrieval import db
from retrieval import subgraph as sub
from retrieval import communities as com
from retrieval.question_parser import parse_question
from retrieval.seed_retrieval import retrieve_seeds, run_channels, fuse

DECISION_LABEL = "Decision"
SCOPE = "corpus"

MAX_RETRIEVAL_ITERATIONS = 2
MAX_TOPICS = 8
MIN_COMMUNITY_SIZE = 5
MAX_REDRAFTS = 1

CASE_NUMBER_RE = re.compile(r"\b([GTJDRW])\s?(\d{1,4})/(\d{2})\b")


def _normalise_case(text):
    match = CASE_NUMBER_RE.search(text or "")
    return f"{match.group(1)} {int(match.group(2))}/{match.group(3)}" if match else None


# --- (1) iterative retrieval agent -------------------------------------------

class RetrievalAssessment(BaseModel):
    sufficient: bool
    reason: str
    additional_legal_tests: List[str] = []
    additional_technical_terms: List[str] = []
    broadened_semantic_query: Optional[str] = None


ASSESS_PROMPT = """You judge whether a set of retrieved EPO Board of Appeal decisions is
sufficient to answer a patent-law question well -- specifically, whether it plausibly covers
BOTH sides of the doctrine (including any contrary/distinguishing authority, not just the first
line of cases that agree with an obvious reading) and enough decisions to synthesise from.

If insufficient, propose concrete refinements: additional named legal tests/doctrines to search
for, additional technical terms, or a broadened semantic query. Do not propose a refinement that
narrows the question -- only ones that would surface MORE of what a thorough answer needs."""


def _seed_summary(seeds, session):
    """A compact description of the current seed set for the assessment prompt --
    not the full text, just enough to judge coverage: board/outcome/citation
    spread, not chunk content."""
    refs = [s["reference"] for s in seeds[:30]]
    if not refs:
        return "No decisions retrieved."
    rows = session.run(
        """UNWIND $refs AS ref
           MATCH (d:Decision {reference: ref})
           OPTIONAL MATCH (d)-[:DECIDED_BY]->(b:Board)
           OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
           RETURN d.caseNumber AS caseNumber, b.code AS board, o.type AS outcome""",
        refs=refs,
    ).data()
    lines = [f"{len(seeds)} decisions retrieved. Sample of {len(rows)}:"]
    lines += [f"  {r['caseNumber']} (Board {r['board'] or '?'}, {r['outcome'] or '?'})"
              for r in rows]
    return "\n".join(lines)


def _merge_intent(intent, assessment):
    """A new QueryIntent with the assessment's refinements folded in."""
    merged = intent.model_copy(deep=True)
    merged.legal_tests = list(dict.fromkeys(merged.legal_tests + assessment.additional_legal_tests))
    merged.technical_terms = list(
        dict.fromkeys(merged.technical_terms + assessment.additional_technical_terms))
    if assessment.broadened_semantic_query:
        merged.semantic_query = assessment.broadened_semantic_query
    return merged


def iterative_retrieve(session, question, seed_limit, log=None):
    """Runs retrieval, assesses sufficiency, and issues bounded follow-up
    searches. Returns (seeds, channels, iterations) where `iterations` is a
    list of {assessment, channelsFound} for --explain-style transparency.
    """
    log = log or (lambda msg: None)
    intent = parse_question(question)
    all_seeds_by_ref = {}
    iterations = []

    for i in range(MAX_RETRIEVAL_ITERATIONS):
        channels, best_chunks = run_channels(session, intent, scope=SCOPE)
        seeds = fuse(channels, seed_limit=seed_limit, best_chunks=best_chunks)
        for seed in seeds:
            all_seeds_by_ref.setdefault(seed["reference"], seed)
        merged_seeds = list(all_seeds_by_ref.values())

        summary = _seed_summary(merged_seeds, session)
        assessment = db.chat(
            [{"role": "system", "content": ASSESS_PROMPT},
             {"role": "user", "content": f"Question: {question}\n\n{summary}"}],
            response_format=RetrievalAssessment,
        )
        iterations.append({"round": i + 1, "seedCount": len(merged_seeds),
                            "assessment": assessment.model_dump()})
        log(f"retrieval round {i+1}: {len(merged_seeds)} seeds, "
            f"sufficient={assessment.sufficient} ({assessment.reason[:100]})")

        if assessment.sufficient or i == MAX_RETRIEVAL_ITERATIONS - 1:
            break
        intent = _merge_intent(intent, assessment)

    return list(all_seeds_by_ref.values()), channels, iterations


# --- (2) topic summarizer agents (map) + synthesis (reduce) -----------------

class TopicCard(BaseModel):
    topic_label: str
    doctrine_summary: str  # prose, citing decisions by case number inline


TOPIC_SYSTEM_PROMPT = """You summarise one legal topic (a cluster of related EPO Board of
Appeal decisions) for a patent attorney. Read the decisions below -- each is labelled with its
case number, board, outcome, and a representative passage from its Reasons.

Write:
1. topic_label: a short name for what this cluster of decisions is actually about (the shared
   doctrine/issue, not "topic N")
2. doctrine_summary: 3-6 sentences on what these decisions collectively establish, citing
   specific case numbers for specific propositions. Every substantive claim must cite a case
   number from the list below -- never a case number that is not in the list.

Stay close to what each excerpt actually says. Do not infer a general legal rule and then
attribute it to a specific decision whose excerpt only illustrates a narrower point -- if an
excerpt shows the board applying a test to specific facts, say that, not the abstract test
stated as if that decision were the source of the general rule. When in doubt, describe what
the decision DID rather than what it "established"."""

FETCH_TOPIC_MEMBERS = """
UNWIND $refs AS ref
MATCH (d:Decision {reference: ref})
CALL (d) {
  OPTIONAL MATCH (d)-[:DECIDED_BY]->(b:Board)
  RETURN b.code AS boardCode LIMIT 1
}
CALL (d) {
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
  RETURN o.type AS outcomeType LIMIT 1
}
CALL (d) {
  // Fallback only -- the *first* Reasons paragraph is background/facts far
  // more often than legal analysis (confirmed: a live run fed this to a
  // topic agent, which then made doctrinal claims the critic correctly
  // refused because the excerpt was just case background). Used only for
  // community members that were not themselves a retrieval seed and so
  // have no chunkId already proven relevant to the question -- see
  // `fetch_topic_members`, which prefers that chunk when available.
  MATCH (d)-[:HAS_SECTION]->(:ReasonsForDecision)<-[:PART_OF]-(c:Chunk)
  RETURN c.text AS fallbackText, c.citation AS fallbackCitation
  ORDER BY c.index LIMIT 1
}
RETURN d.reference AS reference, d.caseNumber AS caseNumber, boardCode, outcomeType,
       fallbackText, fallbackCitation
"""

FETCH_CHUNK_TEXT = """
UNWIND $chunkIds AS chunkId
MATCH (c:Chunk {id: chunkId})
RETURN c.id AS chunkId, c.text AS text, c.citation AS citation
"""


def _topic_block(rows):
    blocks = []
    for row in rows:
        blocks.append(
            f"{row['citation'] or row['caseNumber']} (Board {row['boardCode'] or '?'}, "
            f"outcome: {row['outcomeType'] or '?'})\n"
            # 900 chars was cutting the average chunk (~1400-1800 chars) off
            # before its conclusion -- confirmed live: the critic correctly
            # flagged a claim as unsupported because the excerpt "cuts off
            # before showing the board's conclusion." 2200 covers the large
            # majority of chunks whole (avg 358 tokens ~= 1400-1800 chars).
            f'"{(row["text"] or "")[:2200]}"'
        )
    return "\n\n".join(blocks)


def fetch_topic_members(session, community, chunk_id_by_ref=None):
    """Sequential DB fetch for one community -- kept separate from
    `summarize_topic_from_rows` (the LLM call) specifically so callers can
    run every community's fetch on one session first, THEN parallelize only
    the LLM calls: a Neo4j session is not safe to share across threads, and
    the fetch is fast enough that it does not need parallelising anyway.

    `chunk_id_by_ref`: {decisionReference: chunkId} from the original
    retrieval seeds (`fuse()`'s `best_chunks`) -- that chunk was already
    matched as relevant to the actual question by the semantic/lexical
    channel, so it is used in preference to an arbitrary first-paragraph
    fallback wherever a member has one (every original seed does; decisions
    pulled in only by subgraph expansion do not, and fall back).
    """
    chunk_id_by_ref = chunk_id_by_ref or {}
    refs = [m["reference"] for m in community["members"][:20]]  # cap per-topic cost
    rows = session.run(FETCH_TOPIC_MEMBERS, refs=refs).data()

    chunk_ids = [chunk_id_by_ref[r] for r in refs if chunk_id_by_ref.get(r)]
    preferred = {}
    if chunk_ids:
        preferred = {row["chunkId"]: row
                     for row in session.run(FETCH_CHUNK_TEXT, chunkIds=chunk_ids).data()}

    for row in rows:
        best = preferred.get(chunk_id_by_ref.get(row["reference"]))
        row["text"] = best["text"] if best else row["fallbackText"]
        row["citation"] = best["citation"] if best else row["fallbackCitation"]
    return rows


def summarize_topic_from_rows(rows, identity=None):
    """One topic-summarizer agent call for one Leiden community's already-
    fetched member rows (see `fetch_topic_members`) -- no DB access, safe to
    run from a thread pool.

    Returns (card, rows): `rows` is what the faithfulness critic later
    checks citations against -- kept as the actual source text, not just a
    case number string, so "is this case real" and "does the text support
    this specific claim" stay genuinely separate checks.
    """
    hint = ""
    if identity:
        top_bridges = ", ".join(i["name"] for i in identity[:5] if i.get("name"))
        hint = f"\n\nBridges most distinctive of this cluster: {top_bridges}"
    user_prompt = (f"{len(rows)} decisions in this cluster:{hint}\n\n" + _topic_block(rows))
    card = db.chat(
        [{"role": "system", "content": TOPIC_SYSTEM_PROMPT},
         {"role": "user", "content": user_prompt}],
        response_format=TopicCard,
    )
    return card, rows


SYNTHESIS_SYSTEM_PROMPT = """You are answering a patent-law question about EPO Board of Appeal
decisions, given topic cards -- each already a grounded summary of one cluster of decisions.
Write one answer organised BY TOPIC (use the topic labels as headers), synthesising across the
cards. Every substantive claim must carry a case-number citation that already appears in the
topic cards below -- never invent one, and never sharpen or generalise a claim beyond what the
topic card actually says next to that citation. If a topic card describes what one decision did
on its specific facts, report that -- do not upgrade it into a general rule the citation cannot
support on its own. If asked to fix specific unsupported claims, remove or correct exactly
those, keep everything else."""


def synthesize(question, topic_cards, feedback=None):
    cards_text = "\n\n".join(
        f"## {card.topic_label}\n{card.doctrine_summary}" for card in topic_cards)
    user_prompt = f"Question: {question}\n\nTopic cards:\n\n{cards_text}"
    if feedback:
        user_prompt += f"\n\nFix required: {feedback}"
    return db.chat([
        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])


# --- (3) faithfulness critic agent -------------------------------------------

class FaithfulnessVerdict(BaseModel):
    case_number: str
    supported: bool
    reason: str


CRITIC_SYSTEM_PROMPT = """You check whether a drafted answer's citations are actually
supported by their source text. For each (claim, source) pair below, decide if the source text
genuinely supports the specific claim made next to that citation in the answer -- not just that
the case exists, but that it says what the answer claims it says. Default to unsupported if
unsure."""


def check_faithfulness(answer, source_by_case):
    """`source_by_case`: {caseNumber: sourceText}. Returns list[FaithfulnessVerdict]
    for every cited case number found in `answer` that has a known source."""
    cited = {m.group(0) for m in CASE_NUMBER_RE.finditer(answer)}
    pairs = []
    for raw in cited:
        norm = _normalise_case(raw)
        source = source_by_case.get(norm)
        if not source:
            continue
        # The sentence containing the citation -- the specific claim to check,
        # not the whole answer.
        idx = answer.find(raw)
        sentence = answer[max(0, idx - 200):idx + 200]
        pairs.append((norm, sentence, source))

    if not pairs:
        return []

    blocks = "\n\n".join(
        f"Claim (near citation to {case}): \"...{claim}...\"\nSource text for {case}: "
        # Same truncation length as the topic-summarizer's own view of this
        # text (_topic_block) -- the critic must see at least as much of the
        # source as the agent whose claim it is checking, or it will
        # correctly-but-wrongly flag a claim that a later, unseen sentence
        # actually does support.
        f"\"{source[:2200]}\""
        for case, claim, source in pairs
    )
    result = db.chat(
        [{"role": "system", "content": CRITIC_SYSTEM_PROMPT},
         {"role": "user", "content": blocks}],
        response_format=_VerdictList,
    )
    return result.verdicts


class _VerdictList(BaseModel):
    verdicts: List[FaithfulnessVerdict]


# --- top-level orchestrator ---------------------------------------------------

def run_deep(session_factory, question, seed_limit=200, log=None):
    started = time.time()
    log = log or (lambda msg: None)

    with session_factory() as session:
        seeds, channels, retrieval_iterations = iterative_retrieve(
            session, question, seed_limit, log=log)
        if not seeds:
            return _empty_result(started, retrieval_iterations)

        refs = [s["reference"] for s in seeds]
        chunk_id_by_ref = {s["reference"]: s["chunkId"] for s in seeds if s.get("chunkId")}
        induced = sub.induce(session, refs, decision_label=DECISION_LABEL)
        log(f"induced subgraph: {sub.describe(induced)}")

        # A unique GDS projection name per call -- com.detect()'s default
        # ("legalTopics") would collide if two requests ran this concurrently
        # (this endpoint is reachable by any live app user, unlike
        # scripts/probe_topics.py's single-user CLI use of the same default).
        graph_name = f"legalTopics_{uuid.uuid4().hex[:12]}"

        leiden_config = com.LeidenConfig()
        result = com.detect(session, induced, leiden_config, graph_name=graph_name,
                             decision_label=DECISION_LABEL)
        exit_check = com.check_exit_criteria(result, leiden_config)
        if not exit_check["ok"] and result["communities"]:
            # Bumped once, per the plan's own stated response to a failed exit
            # criterion ("raise gamma... and retry, bounded retry loop").
            log(f"Leiden exit criteria failed ({exit_check['reason']}); "
                "retrying with gamma raised")
            leiden_config.gamma += 0.5
            result = com.detect(session, induced, leiden_config, graph_name=graph_name,
                                 decision_label=DECISION_LABEL)
            exit_check = com.check_exit_criteria(result, leiden_config)
        log(f"Leiden: {exit_check}")

        communities = sorted(result["communities"], key=lambda c: -c["size"])[:MAX_TOPICS]
        identities = com.topic_identity(session, induced, communities,
                                         decision_label=DECISION_LABEL)

        if not communities:
            return _empty_result(started, retrieval_iterations, note="no usable topics")

        # Sequential: one session, one query per community. Fast (~8 short
        # queries) -- the LLM calls below are the slow part and the ones
        # worth parallelising.
        community_rows = [fetch_topic_members(session, c, chunk_id_by_ref)
                           for c in communities]

    # Session closed above; everything from here is pure LLM calls, safe to
    # run from a thread pool.
    with ThreadPoolExecutor(max_workers=min(8, len(communities))) as pool:
        topic_results = list(pool.map(
            lambda args: summarize_topic_from_rows(*args),
            [(rows, identities.get(c["id"])) for c, rows in zip(communities, community_rows)]))

    topic_cards = [card for card, _ in topic_results]
    source_text_by_case = {}
    for _, rows in topic_results:
        for row in rows:
            norm = _normalise_case(row["citation"] or row["caseNumber"])
            if norm and row["text"]:
                source_text_by_case.setdefault(norm, row["text"])

    log(f"{len(topic_cards)} topic cards produced")

    answer = synthesize(question, topic_cards)
    verdicts = check_faithfulness(answer, source_text_by_case)
    unsupported = [v for v in verdicts if not v.supported]

    redrafts = 0
    raw_answer = None
    while unsupported and redrafts < MAX_REDRAFTS:
        feedback = "; ".join(f"{v.case_number}: {v.reason}" for v in unsupported)
        raw_answer = answer
        answer = synthesize(question, topic_cards, feedback=feedback)
        verdicts = check_faithfulness(answer, source_text_by_case)
        unsupported = [v for v in verdicts if not v.supported]
        redrafts += 1

    refused = bool(unsupported)
    final_answer = answer
    if refused:
        raw_answer = raw_answer or answer
        reasons = "; ".join(f"{v.case_number} ({v.reason})" for v in unsupported)
        final_answer = (
            "Refusing to present this answer as generated: the faithfulness critic "
            f"could not confirm support for: {reasons}. This survived "
            f"{redrafts} redraft attempt(s)."
        )

    sources, graph = _build_sources_and_graph(topic_results)

    return {
        "answer": final_answer,
        "rawAnswer": raw_answer if refused else None,
        "topicCards": [c.model_dump() for c in topic_cards],
        "sources": sources,
        "graph": graph,
        "retrievalIterations": retrieval_iterations,
        "leidenStats": result["stats"],
        "exitCriteria": exit_check,
        "faithfulness": [v.model_dump() for v in verdicts],
        "redrafts": redrafts,
        "refused": refused,
        "elapsedMs": round((time.time() - started) * 1000),
    }


def _build_sources_and_graph(topic_results):
    """Flat source list + provenance graph, same shape as
    `app/pipelines/graphrag.py` -- one node per topic and per member
    decision, an edge from decision to the topic(s) it belongs to. Unlike
    the flat pipeline, this does not restrict to only-cited sources: a
    topic's full member list is part of what the topic-organisation is
    showing, not incidental detail.
    """
    sources, nodes, edges, seen = [], [], [], set()

    def add_node(node_id, **props):
        if node_id not in seen:
            seen.add(node_id)
            nodes.append({"id": node_id, **props})

    for card, rows in topic_results:
        topic_id = f"topic:{card.topic_label}"
        add_node(topic_id, label=card.topic_label, type="Topic")
        for row in rows:
            d_id = f"decision:{row['reference']}"
            add_node(d_id, label=row["caseNumber"], type="Decision",
                     boardCode=row["boardCode"], outcomeType=row["outcomeType"])
            edges.append({"source": d_id, "target": topic_id, "type": "IN_TOPIC"})
            sources.append({
                "reference": row["reference"], "caseNumber": row["caseNumber"],
                "citation": row["citation"], "text": row["text"],
                "boardCode": row["boardCode"], "outcomeType": row["outcomeType"],
                "topic": card.topic_label,
            })

    return sources, {"nodes": nodes, "edges": edges}


def _empty_result(started, retrieval_iterations, note="no decisions retrieved"):
    return {
        "answer": f"No relevant decisions were retrieved for this question ({note}).",
        "rawAnswer": None, "topicCards": [], "retrievalIterations": retrieval_iterations,
        "leidenStats": None, "exitCriteria": None, "faithfulness": [], "redrafts": 0,
        "refused": False, "elapsedMs": round((time.time() - started) * 1000),
    }
