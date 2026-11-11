#!/usr/bin/env python3
"""Build the ground-disposition layer from the EPO's own headwords.

    (:Decision)-[:DECIDED_GROUND {findings, requirementMetAll,
                                  requirementMetAny, qualifiers}]->(:Ground)
    (:Ground {code, label, polarity})-[:UNDER_ARTICLE]->(:Article)

Completes PHARMA_GENERICS_PLAN.md Q2 ("which ground actually kills pharma
patents") and feeds EXAMINER_PLAN.md Q5, replacing the Article-citation proxy --
citing Art. 56 says the board discussed inventive step, not how it decided it.

Source is `:Keyword`, the boards' own indexing, which covers 97.3% of canonical
decisions. Normalisation and the polarity handling live in `importer/grounds.py`;
65.6% of keyword links map to a known ground, giving 84.2% of decisions at least
one typed disposition. The rest is a long tail of one-off descriptive headwords,
deliberately left unmapped rather than guessed at.

Two findings per ground rather than one
---------------------------------------
A decision can decide the same ground differently per request -- "Inventive step
- main request (no)" together with "Inventive step - auxiliary request 2 (yes)".
Collapsing that to a single boolean would either report the ground as failed
(ignoring that the patent survived on the auxiliary request) or as met (ignoring
that the main request fell). Both are stored:

    requirementMetAll   every finding on this ground was met
    requirementMetAny   at least one finding was met

Use `All` for "was this ground a clean pass", `Any` for "did the patent survive
this ground on some request". The raw `findings` list is kept so neither has to
be trusted blindly.

Usage:
    python3 scripts/classify_grounds.py [--dry-run]
"""

import argparse
import os
import sys
import time
from collections import Counter, defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.grounds import GROUND_META, parse_keyword  # noqa: E402

SETUP = [
    "CREATE CONSTRAINT ground_code IF NOT EXISTS FOR (g:Ground) REQUIRE g.code IS UNIQUE",
]

WRITE_GROUNDS = """
UNWIND $rows AS row
MERGE (g:Ground {code: row.code})
SET g.label = row.label, g.polarity = row.polarity, g.articleCode = row.article
WITH g, row
OPTIONAL MATCH (a:Article {code: row.article})
FOREACH (_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END |
  MERGE (g)-[:UNDER_ARTICLE]->(a))
"""

FETCH = """
MATCH (d:Decision)-[:HAS_KEYWORD]->(k:Keyword)
WHERE d.isCanonical
RETURN d.reference AS reference, collect(k.text) AS keywords
ORDER BY d.reference
SKIP $skip LIMIT $limit
"""

WRITE_DISPOSITIONS = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MATCH (g:Ground {code: row.code})
MERGE (d)-[r:DECIDED_GROUND]->(g)
SET r.findings          = row.findings,
    r.qualifiers        = row.qualifiers,
    r.requirementMetAll = row.metAll,
    r.requirementMetAny = row.metAny
"""

VERIFY = """
MATCH (d:Decision)-[r:DECIDED_GROUND]->(g:Ground)
RETURN g.code AS ground, g.polarity AS polarity, count(*) AS decisions,
       sum(CASE WHEN r.requirementMetAll = true  THEN 1 ELSE 0 END) AS met,
       sum(CASE WHEN r.requirementMetAll = false THEN 1 ELSE 0 END) AS notMet,
       sum(CASE WHEN r.requirementMetAll IS NULL THEN 1 ELSE 0 END) AS noFinding
ORDER BY decisions DESC
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch-size", type=int, default=5000)
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
            if not args.dry_run:
                for statement in SETUP:
                    session.run(statement).consume()
                session.run(WRITE_GROUNDS, rows=[
                    {"code": code, "label": meta["label"],
                     "polarity": meta["polarity"], "article": meta["article"]}
                    for code, meta in GROUND_META.items()
                ]).consume()
                print(f"wrote {len(GROUND_META)} :Ground nodes")

            skip = 0
            while True:
                batch = [dict(r) for r in session.run(
                    FETCH, skip=skip, limit=args.batch_size)]
                if not batch:
                    break

                rows = []
                for record in batch:
                    grouped = defaultdict(lambda: {"findings": [], "qualifiers": [],
                                                   "met": []})
                    for keyword in record["keywords"]:
                        parsed = parse_keyword(keyword)
                        if not parsed:
                            stats["unmapped"] += 1
                            continue
                        stats["mapped"] += 1
                        entry = grouped[parsed["code"]]
                        if parsed["finding"]:
                            entry["findings"].append(parsed["finding"])
                        if parsed["qualifier"]:
                            entry["qualifiers"].append(parsed["qualifier"])
                        if parsed["requirementMet"] is not None:
                            entry["met"].append(parsed["requirementMet"])

                    for code, entry in grouped.items():
                        met = entry["met"]
                        rows.append({
                            "reference": record["reference"],
                            "code": code,
                            "findings": entry["findings"],
                            "qualifiers": entry["qualifiers"],
                            "metAll": all(met) if met else None,
                            "metAny": any(met) if met else None,
                        })
                        stats["dispositions"] += 1

                if rows and not args.dry_run:
                    session.execute_write(
                        lambda tx, r=rows: tx.run(WRITE_DISPOSITIONS, rows=r).consume())

                skip += args.batch_size
                print(f"  {skip:,} decisions", end="\r", flush=True)

            total_links = stats["mapped"] + stats["unmapped"]
            print(f"\nkeyword links {total_links:,}: mapped {stats['mapped']:,} "
                  f"({100.0*stats['mapped']/total_links:.1f}%)")
            print(f"dispositions written: {stats['dispositions']:,} "
                  f"in {time.time()-started:.0f}s")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            print("\nverify (from the graph):")
            print(f"  {'ground':30s} {'polarity':9s} {'decisions':>9s} "
                  f"{'met':>7s} {'notMet':>7s} {'noFinding':>9s}")
            for record in session.run(VERIFY):
                print(f"  {record['ground']:30s} {record['polarity']:9s} "
                      f"{record['decisions']:9,} {record['met']:7,} "
                      f"{record['notMet']:7,} {record['noFinding']:9,}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
