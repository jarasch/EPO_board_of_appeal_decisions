#!/usr/bin/env python3
"""Gold-set evaluation harness -- E7.3/P7.2 (grounding discipline).

Runs `retrieval/gold_set.py`'s questions through three retrieval channels and
reports recall@k separately for each -- exactly the "semantic vs keyword A/B,
report recall@10 for both" both plans ask for, plus the actual fused pipeline
(`retrieval/seed_retrieval.py`) as a third point of comparison:

    semantic  -- vector_search only (chunk_text_embedding)
    keyword   -- fulltext_search only (chunk_text_fulltext)
    fused     -- the real multi-channel pipeline (semantic+lexical+entity+structured
                 -> reciprocal rank fusion), the same one app/pipelines/graphrag.py uses

Recall@k: did the retrieved top-k *decisions* include the case the question
names by doctrine (not by case number -- the question text never contains the
answer)? See `retrieval/gold_set.py` for why this is a narrower, honestly-
scoped proxy for "recall", not the attorney-graded gold standard the plans
describe.

Nearly free by default: embeddings + fulltext queries for the semantic/
keyword channels, plus one small `question_parser.parse_question` call per
question for the "fused" channel -- using the same LLM-based intent parser
`app/pipelines/graphrag.py` actually runs, rather than the no-LLM
`intent.from_question` fallback, which would leave the lexical/entity/
structured channels permanently empty and make "fused" a degenerate copy of
"semantic". 12 short question-parses, not a meaningful spend. No chat
completions for the answer/synthesis path unless `--with-synthesis` is set.
`--with-synthesis` additionally runs the full GraphRAG pipeline per question
and prints a faithfulness worksheet -- question, generated answer, and each
cited source's actual text, side by side, FOR A HUMAN TO GRADE. This module
deliberately does not auto-score faithfulness with a second LLM call: E7.1/
P7.1's citation-integrity check already verifies structural resolution
(a citation points at a real retrieved source); whether that source's text
actually supports the specific claim next to it is a judgment call, not a
string match, and putting a human in that loop is the point, not a
shortcut around it. This flag also spends real tokens (one chat completion
per question), unlike the recall measurement above.

Usage:
    python3 scripts/run_gold_set.py [--k 10] [--with-synthesis]
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import db  # noqa: E402
from retrieval.gold_set import GOLD_SET  # noqa: E402

# Mirrors app/pipelines/common.py's CASE_NUMBER_RE -- kept local rather than
# imported, same layering reason as importer/citator.py: app/ depends on
# retrieval/, never the reverse.
CASE_NUMBER_RE = re.compile(r"\b([GTJDRW])\s?(\d{1,4})/(\d{2})\b")


def normalise_case_ref(text):
    match = CASE_NUMBER_RE.search(text or "")
    if not match:
        return None
    return f"{match.group(1)} {int(match.group(2))}/{match.group(3)}"


VECTOR_QUERY = """
CALL db.index.vector.queryNodes('chunk_text_embedding', $fetch, $embedding)
YIELD node, score
MATCH (node)-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE d.isCanonical
WITH d, max(score) AS score
RETURN d.reference AS reference, d.caseNumber AS caseNumber, score
ORDER BY score DESC LIMIT $k
"""

FULLTEXT_QUERY = """
CALL db.index.fulltext.queryNodes('chunk_text_fulltext', $luceneQuery, {limit: $fetch})
YIELD node, score
MATCH (node)-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE d.isCanonical
WITH d, max(score) AS score
RETURN d.reference AS reference, d.caseNumber AS caseNumber, score
ORDER BY score DESC LIMIT $k
"""


def _lucene_escape(text):
    return re.sub(r'([+\-!(){}\[\]^"~*?:\\/])', r"\\\1", text)


def run_channel(session, query, params):
    rows = session.run(query, **params).data()
    return [normalise_case_ref(row["caseNumber"]) or row["caseNumber"] for row in rows]


def hit_at_k(retrieved_case_refs, expected_cases):
    expected = set(expected_cases)
    return any(ref in expected for ref in retrieved_case_refs)


def print_faithfulness_worksheet(gold, answer_result):
    print(f"\n  --- faithfulness worksheet: {gold.id} (grade by hand) ---")
    print(f"  Q: {gold.question}")
    print(f"  A: {answer_result['answer']}")
    cited = [s for s in answer_result["sources"] if s.get("cited")]
    if not cited:
        print("  (no sources marked cited -- nothing to grade)")
        return
    for s in cited:
        print(f"\n    [{s['n']}] {s['citation'] or s['caseNumber']}")
        print(f"    source text: {(s['text'] or '')[:400]}")
    print("\n    Grade: for each [n] above, does the source text actually support "
          "the claim the answer made next to it? (yes / no / partial)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--fetch", type=int, default=50,
                        help="over-fetch before dedup to decisions (chunks -> decisions "
                             "collapses many-to-one)")
    parser.add_argument("--with-synthesis", action="store_true",
                        help="also run the full GraphRAG pipeline and print a "
                             "faithfulness worksheet (costs one chat completion/question)")
    args = parser.parse_args()

    from retrieval.question_parser import parse_question
    from retrieval.seed_retrieval import retrieve_seeds

    hits = defaultdict(int)
    rows_for_print = []

    with db.session() as session:
        for gold in GOLD_SET:
            embedding = db.embed(gold.question)
            semantic = run_channel(session, VECTOR_QUERY,
                                    {"embedding": embedding, "fetch": args.fetch, "k": args.k})
            keyword = run_channel(session, FULLTEXT_QUERY,
                                   {"luceneQuery": _lucene_escape(gold.question),
                                    "fetch": args.fetch, "k": args.k})

            intent = parse_question(gold.question)
            seeds, _ = retrieve_seeds(session, intent, seed_limit=args.k, scope="corpus")
            # seed references aren't case numbers -- resolve via Decision.caseNumber
            fused_refs = [session.run(
                "MATCH (d:Decision {reference: $ref}) RETURN d.caseNumber AS caseNumber",
                ref=seed["reference"]).single()["caseNumber"] for seed in seeds[:args.k]]
            fused = [normalise_case_ref(c) or c for c in fused_refs]

            row = {"id": gold.id, "theme": gold.theme, "expected": gold.expected_cases}
            for channel, refs in (("semantic", semantic), ("keyword", keyword), ("fused", fused)):
                hit = hit_at_k(refs, gold.expected_cases)
                hits[channel] += int(hit)
                row[channel] = "HIT" if hit else "miss"
            rows_for_print.append(row)

        print(f"{len(GOLD_SET)} gold questions, recall@{args.k}\n")
        print(f"  {'id':32s} {'semantic':>9s} {'keyword':>9s} {'fused':>9s}  expected")
        for row in rows_for_print:
            print(f"  {row['id']:32s} {row['semantic']:>9s} {row['keyword']:>9s} "
                  f"{row['fused']:>9s}  {row['expected']}")

        n = len(GOLD_SET)
        print(f"\naggregate recall@{args.k}:")
        for channel in ("semantic", "keyword", "fused"):
            print(f"  {channel:10s} {hits[channel]}/{n} = {100.0*hits[channel]/n:.0f}%")

        if args.with_synthesis:
            from app.pipelines import graphrag
            print("\nRunning full GraphRAG synthesis per question (spends tokens)...")
            for gold in GOLD_SET:
                result = graphrag.run(db.session, gold.question, top_n=args.k)
                print_faithfulness_worksheet(gold, result)


if __name__ == "__main__":
    main()
