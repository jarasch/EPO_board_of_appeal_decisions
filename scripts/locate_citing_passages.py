#!/usr/bin/env python3
"""Locate citing passages -- EXAMINER_PLAN.md Phase E5, non-LLM half.

Bounded to citations of the ~500 most-cited decisions (per the plan: "covers
the large majority of edges for a small fraction of the cost") -- measured
on this corpus, that is 35,486 of the 74,069 `CITES` edges, from 15,478
distinct citing decisions.

For each `(:Decision)-[:CITES]->(:Case)` edge into that top set, finds which
of the citing decision's own chunks actually name the cited case (case
numbers are distinctive strings, so this is exact matching, not search) and
writes the result onto the edge:

    (:Decision)-[:CITES {passageChunkIds, passageCount, passageLocated}]->(:Case)

`passageChunkIds = []` (with `passageLocated = true`) is a real, recorded
outcome -- the citation exists in the graph (from bibliographic metadata)
but no chunk text names the case, e.g. it was only in a citation list this
extraction pass didn't chunk, or the corpus's own citation extraction over-
or under-matched. That is useful information for the classification pass
that follows, not a failure to hide.

Fetches each citing decision's chunks once and checks it against every top
case it cites, rather than once per (case, decision) pair -- 15,478 decision
fetches, not 35,486.

This is deliberately NOT the classification step (followed / distinguished /
declined_to_follow / ...) -- that needs an LLM call per located passage and
is a separate, later script.

Usage:
    python3 scripts/locate_citing_passages.py [--top-n 500] [--dry-run]
"""

import argparse
import os
import sys
import time
from collections import Counter, defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.citator import find_case_mentions  # noqa: E402

TOP_CASE_EDGES = """
MATCH (top:Case)<-[:CITES]-(:Decision)
WITH top, count(*) AS citedBy
ORDER BY citedBy DESC LIMIT $topN
WITH collect(DISTINCT top) AS topCases
UNWIND topCases AS top
MATCH (d:Decision {isCanonical: true})-[:CITES]->(top)
RETURN d.reference AS reference, top.caseKey AS caseKey, top.code AS code,
       top.appealNum AS appealNum, top.year AS year
"""

FETCH_CHUNKS = """
UNWIND $references AS reference
MATCH (d:Decision {reference: reference})-[:HAS_SECTION]->(s)<-[:PART_OF]-(ch:Chunk)
RETURN reference, ch.id AS chunkId, ch.text AS text
"""

WRITE_RESULT = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})-[r:CITES]->(c:Case {caseKey: row.caseKey})
SET r.passageChunkIds = row.chunkIds, r.passageCount = size(row.chunkIds),
    r.passageLocated = true
"""

VERIFY = """
MATCH ()-[r:CITES]->() WHERE r.passageLocated = true
RETURN count(r) AS located,
       sum(CASE WHEN r.passageCount > 0 THEN 1 ELSE 0 END) AS withPassage,
       sum(CASE WHEN r.passageCount = 0 THEN 1 ELSE 0 END) AS withoutPassage
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--top-n", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=300,
                        help="citing decisions fetched per round-trip")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    stats = Counter()
    started = time.time()

    try:
        with driver.session(database=database) as session:
            edges = [dict(r) for r in session.run(TOP_CASE_EDGES, topN=args.top_n)]
            stats["edges"] = len(edges)

            targets_by_decision = defaultdict(list)
            for edge in edges:
                targets_by_decision[edge["reference"]].append(edge)
            references = list(targets_by_decision.keys())
            print(f"{len(edges):,} edges across {len(references):,} citing decisions "
                  f"(top {args.top_n} most-cited cases)")

            if args.dry_run:
                print("-- dry run, nothing written --")
                return

            for start in range(0, len(references), args.batch_size):
                batch_refs = references[start:start + args.batch_size]
                chunks_by_decision = defaultdict(list)
                for record in session.run(FETCH_CHUNKS, references=batch_refs):
                    chunks_by_decision[record["reference"]].append(record)

                batch_rows = []
                for reference in batch_refs:
                    chunks = chunks_by_decision.get(reference, [])
                    for target in targets_by_decision[reference]:
                        matched = [c["chunkId"] for c in chunks
                                   if find_case_mentions(c["text"], target["code"],
                                                          target["appealNum"], target["year"])]
                        batch_rows.append({"reference": reference, "caseKey": target["caseKey"],
                                            "chunkIds": matched})
                        stats["withPassage" if matched else "withoutPassage"] += 1

                session.execute_write(
                    lambda tx, r=batch_rows: tx.run(WRITE_RESULT, rows=r).consume())
                print(f"  {min(start+args.batch_size, len(references)):,} / "
                      f"{len(references):,} citing decisions", end="\r", flush=True)

            print(f"\ndone in {time.time()-started:.0f}s")
            print(f"  {stats['withPassage']:,} edges with a located passage")
            print(f"  {stats['withoutPassage']:,} edges with no matching chunk text "
                  "(recorded, not guessed)")

            print("\nverify (from the graph):")
            record = session.run(VERIFY).single()
            print(f"  {record['located']:,} CITES edges marked passageLocated "
                  f"({record['withPassage']:,} with passage, "
                  f"{record['withoutPassage']:,} without)")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
