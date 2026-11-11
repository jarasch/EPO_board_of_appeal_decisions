"""Graph-grounded RAG.

Multi-channel retrieval (question_parser -> seed_retrieval, corpus-wide) -> one
batched Cypher call expanding each hit to its Board / Outcome / Ground / cited
Case / cited Article / covering Paragraph -> an LLM answer that must cite with
`[n]` against a closed, numbered source list -> a provenance graph built from
exactly the sources the answer actually cited, not the full candidate pool.

That last point is deliberate, not an oversight: the graph view is meant to
show what backs the visible answer, so a user can go back to nodes and
relationships that were *used* -- not a dump of everything that was looked at.
"""

import re
import time

from retrieval import db
from retrieval.question_parser import parse_question
from retrieval.seed_retrieval import retrieve_seeds
from app.pipelines.common import unverified_case_numbers

TOP_N = 8
CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")

# One batched call over the top-N decisions. Each `CALL (d) { ... }` is an
# independent scoped subquery -- OPTIONAL MATCH + collect inside its own block
# rather than chained through one WITH, so five different one-to-many
# expansions off the same `d` don't multiply into a Cartesian product.
EXPAND_QUERY = """
UNWIND $items AS item
MATCH (d:Decision {reference: item.reference})
CALL (d) {
  OPTIONAL MATCH (d)-[:DECIDED_BY]->(b:Board)
  RETURN b.code AS boardCode LIMIT 1
}
CALL (d) {
  OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
  RETURN o.type AS outcomeNodeType LIMIT 1
}
CALL (d) {
  OPTIONAL MATCH (d)-[dg:DECIDED_GROUND]->(g:Ground)
  RETURN collect(DISTINCT {code: g.code, label: g.label, met: dg.requirementMetAll})[0..3]
         AS grounds
}
CALL (d) {
  OPTIONAL MATCH (d)-[:CITES]->(cited:Case)
  RETURN collect(DISTINCT cited.caseRef)[0..3] AS citedCases
}
CALL (d) {
  OPTIONAL MATCH (d)-[:CITES_ARTICLE]->(art:Article)
  RETURN collect(DISTINCT {code: art.code, label: art.label})[0..3] AS articles
}
CALL (item) {
  OPTIONAL MATCH (chunk:Chunk {id: item.chunkId})
  OPTIONAL MATCH (chunk)-[:COVERS]->(para:Paragraph)
  RETURN chunk,
         collect(DISTINCT {id: para.id, ref: para.ref, citation: para.citation,
                           text: para.text})[0..8] AS paragraphs
}
RETURN d.reference AS reference, d.caseNumber AS caseNumber,
       toString(d.decisionDate) AS decisionDate, d.outcomeType AS outcomeType,
       d.isInterPartes AS isInterPartes, d.authorityTier AS authorityTier,
       d.authorityWeight AS authorityWeight, d.authorityReason AS authorityReason,
       d.timesCited AS timesCited, boardCode, outcomeNodeType, grounds,
       citedCases, articles, chunk.id AS chunkId, chunk.text AS chunkText,
       chunk.citation AS chunkCitation, paragraphs
"""

# Anchor for a seed found only by the entity/structured channels, which operate
# at decision level and carry no chunk id: prefer the Headnote/Catchword (the
# EPO's own summary of the decision) over an arbitrary Reasons paragraph.
FALLBACK_CHUNK_QUERY = """
UNWIND $references AS reference
MATCH (d:Decision {reference: reference})-[:HAS_SECTION]->(s:Section)<-[:PART_OF]-(c:Chunk)
WHERE s:HeadNote OR s:Catchword OR s:ReasonsForDecision
WITH d, c, CASE WHEN s:HeadNote THEN 0 WHEN s:Catchword THEN 1 ELSE 2 END AS priority
ORDER BY priority, c.index
WITH d, collect(c)[0] AS chunk
RETURN d.reference AS reference, chunk.id AS chunkId
"""

SYSTEM_PROMPT = """You are answering a patent-law question about EPO Board of Appeal decisions.
Use ONLY the numbered sources below. Cite every substantive claim with the matching [n] --
never cite a source number that is not listed below. If the sources do not support an answer,
say so plainly rather than guessing. Be concise."""


def _source_block(n, row):
    lines = [
        f"[{n}] {row['chunkCitation'] or row['caseNumber']} "
        f"(Board {row['boardCode'] or 'unknown'}, decided {row['decisionDate'] or 'unknown'}, "
        f"outcome: {row['outcomeType'] or 'unknown'}, authority: {row['authorityTier']}, "
        f"cited {row['timesCited'] or 0}x in this corpus)"
    ]
    grounds = [
        f"{g['label']} - {'met' if g['met'] else 'not met' if g['met'] is False else 'undetermined'}"
        for g in (row["grounds"] or []) if g.get("label")
    ]
    if grounds:
        lines.append("Grounds: " + "; ".join(grounds))
    authorities = [c for c in (row["citedCases"] or []) if c] + \
        [a["label"] or a["code"] for a in (row["articles"] or []) if a.get("code")]
    if authorities:
        lines.append("Cites: " + " · ".join(authorities))
    lines.append(f'"{(row["chunkText"] or "")[:1200]}"')
    return "\n".join(lines)


def _graph_payload(cited_rows):
    """Nodes/edges for exactly the sources cited in the final answer."""
    nodes, edges, seen = [], [], set()

    def add_node(node_id, label, node_type, **props):
        if node_id not in seen:
            seen.add(node_id)
            nodes.append({"id": node_id, "label": label, "type": node_type, **props})

    def add_edge(source, target, rel_type):
        edges.append({"source": source, "target": target, "type": rel_type})

    for row in cited_rows:
        d_id = f"decision:{row['reference']}"
        add_node(d_id, row["caseNumber"], "Decision", outcomeType=row["outcomeType"],
                 authorityTier=row["authorityTier"], decisionDate=row["decisionDate"],
                 authorityWeight=row["authorityWeight"])

        for para in row["paragraphs"] or []:
            if not para.get("id"):
                continue
            p_id = f"paragraph:{para['id']}"
            add_node(p_id, para.get("citation") or para.get("ref") or "paragraph",
                     "Paragraph", text=para.get("text"))
            add_edge(d_id, p_id, "HAS_PARAGRAPH")

        if row["boardCode"]:
            b_id = f"board:{row['boardCode']}"
            add_node(b_id, row["boardCode"], "Board")
            add_edge(d_id, b_id, "DECIDED_BY")

        if row["outcomeNodeType"]:
            o_id = f"outcome:{row['outcomeNodeType']}"
            add_node(o_id, row["outcomeNodeType"], "Outcome")
            add_edge(d_id, o_id, "HAS_OUTCOME")

        for g in row["grounds"] or []:
            if not g.get("code"):
                continue
            g_id = f"ground:{g['code']}"
            add_node(g_id, g["label"], "Ground")
            add_edge(d_id, g_id, "DECIDED_GROUND")

        for case_ref in (row["citedCases"] or [])[:3]:
            if not case_ref:
                continue
            c_id = f"case:{case_ref}"
            add_node(c_id, case_ref, "Case")
            add_edge(d_id, c_id, "CITES")

        for art in (row["articles"] or [])[:3]:
            if not art.get("code"):
                continue
            a_id = f"article:{art['code']}"
            add_node(a_id, art.get("label") or art["code"], "Article")
            add_edge(d_id, a_id, "CITES_ARTICLE")

    return {"nodes": nodes, "edges": edges}


def _empty_result(started, channels=None):
    return {
        "answer": "No relevant decisions were retrieved for this question.",
        "rawAnswer": None,
        "sources": [],
        "graph": {"nodes": [], "edges": []},
        "retrievalExplain": {name: len(refs) for name, refs in (channels or {}).items()},
        "validation": {"citationsInRange": True, "citationsFound": 0,
                       "unverifiedCaseNumbers": [], "refused": False},
        "elapsedMs": round((time.time() - started) * 1000),
    }


def run(session_factory, question, top_n=TOP_N):
    started = time.time()
    intent = parse_question(question)

    with session_factory() as session:
        seeds, channels = retrieve_seeds(session, intent, scope="corpus")
        seeds = seeds[:top_n]
        if not seeds:
            return _empty_result(started, channels)

        missing = [s["reference"] for s in seeds if not s.get("chunkId")]
        fallback = {}
        if missing:
            fallback = {
                row["reference"]: row["chunkId"]
                for row in session.run(FALLBACK_CHUNK_QUERY, references=missing).data()
                if row["chunkId"]
            }

        items = [
            {"reference": s["reference"],
             "chunkId": s.get("chunkId") or fallback.get(s["reference"])}
            for s in seeds
        ]
        rows = session.run(EXPAND_QUERY, items=items).data()

    rows_by_ref = {row["reference"]: row for row in rows}
    ordered_rows = [rows_by_ref[s["reference"]] for s in seeds if s["reference"] in rows_by_ref]
    if not ordered_rows:
        return _empty_result(started, channels)

    source_blocks = [_source_block(n, row) for n, row in enumerate(ordered_rows, start=1)]
    user_prompt = f"Question: {question}\n\nSources:\n\n" + "\n\n".join(source_blocks)

    answer = db.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    cited_ns = sorted({int(n) for n in CITATION_MARKER_RE.findall(answer)})
    citations_in_range = all(1 <= n <= len(ordered_rows) for n in cited_ns)
    cited_rows = [ordered_rows[n - 1] for n in cited_ns if 1 <= n <= len(ordered_rows)]
    # An empty graph would read as a bug rather than "the model cited nothing" --
    # fall back to showing everything retrieved so the graph is never blank.
    display_rows = cited_rows or ordered_rows

    known_refs = ([row["chunkCitation"] for row in ordered_rows]
                  + [c for row in ordered_rows for c in (row["citedCases"] or [])])
    unverified = unverified_case_numbers(answer, known_refs)

    # E7.1 / P7.1 grounding discipline: "refuse to answer over silently
    # returning an ungrounded claim." GraphRAG is the pipeline making the
    # grounding promise -- baseline.py deliberately does not do this, since
    # showing its hallucinations uncorrected is the point of the comparison.
    # The raw model output is kept (not discarded) so the refusal is itself
    # inspectable rather than a black box.
    refused = bool(unverified)
    raw_answer = answer
    if refused:
        plural = "s" if len(unverified) > 1 else ""
        answer = (
            f"Refusing to present this answer as generated: it cites case "
            f"number{plural} {', '.join(unverified)} that do not appear "
            f"among the sources retrieved for this question. An answer "
            f"citing authority outside its own retrieved evidence is not "
            f"grounded, regardless of whether the citation happens to be "
            f"correct elsewhere in the corpus."
        )

    channel_lookup = {s["reference"]: s["channels"] for s in seeds}
    sources = [
        {
            "n": n,
            "reference": row["reference"],
            "caseNumber": row["caseNumber"],
            "citation": row["chunkCitation"],
            "text": row["chunkText"],
            "boardCode": row["boardCode"],
            "decisionDate": row["decisionDate"],
            "outcomeType": row["outcomeType"],
            "authorityTier": row["authorityTier"],
            "authorityWeight": row["authorityWeight"],
            "authorityReason": row["authorityReason"],
            "timesCited": row["timesCited"],
            "grounds": row["grounds"],
            "citedCases": row["citedCases"],
            "articles": row["articles"],
            "channels": channel_lookup.get(row["reference"], []),
            "cited": n in cited_ns,
        }
        for n, row in enumerate(ordered_rows, start=1)
    ]

    return {
        "answer": answer,
        "rawAnswer": raw_answer if refused else None,
        "sources": sources,
        "graph": _graph_payload(display_rows),
        "retrievalExplain": {name: len(refs) for name, refs in channels.items()},
        "validation": {
            "citationsInRange": citations_in_range,
            "citationsFound": len(cited_ns),
            "unverifiedCaseNumbers": unverified,
            "refused": refused,
        },
        "elapsedMs": round((time.time() - started) * 1000),
    }
