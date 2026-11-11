#!/usr/bin/env python3
"""Classify citation treatment -- EXAMINER_PLAN.md Phase E5, LLM half.

For each `(:Decision)-[:CITES]->(:Case)` edge already passage-located
(`scripts/locate_citing_passages.py`), classifies the citing passage's
treatment of the cited case (`importer/citator_classify.py`) and writes it
onto the edge:

    (:Decision)-[:CITES {treatment, treatmentClassifiedAt}]->(:Case)

This costs real LLM tokens -- the full 34,730 located edges is a genuine
spend, not a bounded/free pass like everything else built so far. Defaults
to a small `--limit` for exactly that reason: validate quality on a slice
before committing to the full run, the same discipline
DEMO_IMPLEMENTATION_PLAN.md's D1 applies to entity extraction. Pass
`--limit 0` for no limit (the full backlog).

Resumable: only fetches edges where `r.treatment IS NULL`, so re-running
after a partial run (or after raising `--limit`) continues rather than
re-classifying and re-spending on what is already done.

Usage:
    python3 scripts/classify_citations.py [--limit 40] [--batch-size 8]
                                           [--case-keys T-0641-2000 ...] [--dry-run]
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import db  # noqa: E402
from importer.citator_classify import classify_batch  # noqa: E402

FETCH_EDGES = """
MATCH (top:Case)<-[r:CITES]-(d:Decision)
WHERE r.passageCount > 0 AND r.treatment IS NULL
  AND ($caseKeys = [] OR top.caseKey IN $caseKeys)
RETURN d.reference AS citingRef, top.caseKey AS caseKey, top.caseRef AS caseRef,
       r.passageChunkIds AS chunkIds
ORDER BY top.caseKey
LIMIT $limit
"""

FETCH_CHUNK_TEXT = """
UNWIND $chunkIds AS chunkId
MATCH (c:Chunk {id: chunkId})
RETURN c.id AS chunkId, c.text AS text
"""

WRITE_TREATMENT = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.citingRef})-[r:CITES]->(c:Case {caseKey: row.caseKey})
SET r.treatment = row.treatment, r.treatmentClassifiedAt = date()
"""

VERIFY = """
MATCH ()-[r:CITES]->() WHERE r.treatment IS NOT NULL
RETURN r.treatment AS treatment, count(*) AS n ORDER BY n DESC
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--limit", type=int, default=40,
                        help="edges to classify this run; 0 = no limit")
    parser.add_argument("--batch-size", type=int, default=8,
                        help="passages per LLM call")
    parser.add_argument("--case-keys", nargs="*", default=[],
                        help="restrict to specific Case.caseKey values, e.g. for a pilot")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be classified, call the LLM on nothing")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    fetch_limit = args.limit if args.limit > 0 else 1_000_000

    try:
        with driver.session(database=database) as session:
            edges = session.run(FETCH_EDGES, caseKeys=args.case_keys, limit=fetch_limit).data()
            print(f"{len(edges):,} unclassified edges fetched"
                  + (f" (limit {args.limit})" if args.limit else " (no limit)"))
            if not edges:
                return

            all_chunk_ids = sorted({cid for e in edges for cid in e["chunkIds"]})
            texts_by_chunk = {r["chunkId"]: r["text"]
                               for r in session.run(FETCH_CHUNK_TEXT, chunkIds=all_chunk_ids)}

            items = []
            for i, edge in enumerate(edges, start=1):
                passage = " [...] ".join(
                    texts_by_chunk.get(cid, "") for cid in edge["chunkIds"] if texts_by_chunk.get(cid))
                items.append({"item": i, "caseRef": edge["caseRef"], "citingRef": edge["citingRef"],
                              "passageText": passage, "caseKey": edge["caseKey"]})

            if args.dry_run:
                print("-- dry run -- sample of what would be sent:")
                for entry in items[:3]:
                    print(f"  item {entry['item']}: {entry['citingRef']} citing "
                          f"{entry['caseRef']}: {entry['passageText'][:150]!r}")
                return

            started = time.time()
            written, missing = 0, 0
            for start in range(0, len(items), args.batch_size):
                batch = items[start:start + args.batch_size]
                result = classify_batch(db.chat, batch)

                rows = []
                for entry in batch:
                    treatment = result.get(entry["item"])
                    if treatment is None:
                        missing += 1
                        continue
                    rows.append({"citingRef": entry["citingRef"], "caseKey": entry["caseKey"],
                                 "treatment": treatment})
                if rows:
                    session.run(WRITE_TREATMENT, rows=rows).consume()
                    written += len(rows)

                print(f"  {min(start+args.batch_size, len(items)):,} / {len(items):,} "
                      f"({written:,} written, {missing:,} missing/unparsed)", end="\r", flush=True)

            print(f"\ndone in {time.time()-started:.0f}s: {written:,} written, "
                  f"{missing:,} the model dropped or mislabelled (not retried -- "
                  "still passageLocated, still treatment IS NULL, will be picked up "
                  "on the next run)")

            print("\nverify (from the graph, all-time, not just this run):")
            for record in session.run(VERIFY):
                print(f"  {record['treatment']:20s} {record['n']:6,}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
