#!/usr/bin/env python3
"""Build the appellant-role layer -- PHARMA_GENERICS_PLAN.md Phase P2b.

    (:Decision {appellantRole, appellantRoleConflict})

`appellantRole` in {opponent, proprietor, both, unknown}. Rules live in
`importer/appellant_role.py`; this script fetches every canonical inter
partes decision's `SummaryOfFacts` text, classifies it, cross-checks the
reformatio-in-peius invariant against the existing outcome layer (P2 /
`scripts/classify_outcomes.py`), and writes the result.

`appellantRoleConflict` is set when a decision classified "proprietor" would
otherwise pair with a "revoked" outcome -- reformatio in peius (G 9/92 /
G 4/93) makes that pairing impossible, so it is demoted to "unknown" rather
than written as a confident wrong answer, and the decision is flagged for
manual inspection rather than silently dropped.

Usage:
    python3 scripts/classify_appellant_roles.py [--dry-run] [--batch-size 2000]
"""

import argparse
import os
import sys
import time
from collections import Counter

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.appellant_role import classify, violates_reformatio_in_peius  # noqa: E402

SETUP = [
    "CREATE INDEX decision_appellant_role IF NOT EXISTS "
    "FOR (d:Decision) ON (d.appellantRole)",
]

FETCH = """
MATCH (d:Decision)-[:HAS_SECTION]->(sf:SummaryOfFacts)
WHERE d.isCanonical AND d.isInterPartes
RETURN d.reference AS reference, d.outcomeType AS outcomeType, sf.text AS text
ORDER BY d.reference
SKIP $skip LIMIT $limit
"""

WRITE = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
SET d.appellantRole = row.role, d.appellantRoleConflict = row.conflict
"""

VERIFY = """
MATCH (d:Decision) WHERE d.isCanonical AND d.isInterPartes
RETURN d.appellantRole AS role, count(*) AS decisions
ORDER BY decisions DESC
"""

VERIFY_BY_BOARD_ROLE_UNKNOWN = """
MATCH (d:Decision)-[:DECIDED_BY]->(b:Board)
WHERE d.isCanonical AND d.isInterPartes
WITH b.code AS board, count(*) AS total,
     sum(CASE WHEN d.appellantRole = 'unknown' THEN 1 ELSE 0 END) AS unknown
WHERE total >= 20
RETURN board, total, unknown, round(100.0 * unknown / total, 1) AS unknownPct
ORDER BY total DESC LIMIT 15
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    stats = Counter()
    conflicts = []
    started = time.time()

    try:
        with driver.session(database=database) as session:
            if not args.dry_run:
                for statement in SETUP:
                    session.run(statement).consume()

            skip = 0
            while True:
                batch = [dict(r) for r in session.run(
                    FETCH, skip=skip, limit=args.batch_size)]
                if not batch:
                    break

                rows = []
                for record in batch:
                    role = classify(record["text"])
                    conflict = violates_reformatio_in_peius(role, record["outcomeType"])
                    if conflict:
                        conflicts.append((record["reference"], record["outcomeType"]))
                        role = "unknown"
                    rows.append({"reference": record["reference"], "role": role,
                                 "conflict": conflict})
                    stats[role] += 1
                    stats["total"] += 1

                if rows and not args.dry_run:
                    session.execute_write(
                        lambda tx, r=rows: tx.run(WRITE, rows=r).consume())

                skip += args.batch_size
                print(f"  {skip:,} decisions", end="\r", flush=True)

            total = stats["total"] or 1
            print(f"\nclassified {total:,} inter partes decisions in "
                  f"{time.time()-started:.0f}s")
            for role in ("opponent", "proprietor", "both", "unknown"):
                print(f"  {role:12s} {stats[role]:7,}  ({100.0*stats[role]/total:.1f}%)")

            if conflicts:
                print(f"\n{len(conflicts)} reformatio-in-peius conflicts demoted to "
                      "'unknown' (proprietor-only appeal would pair with a revoked "
                      "outcome) -- flagged appellantRoleConflict=true for review:")
                for reference, outcome in conflicts[:20]:
                    print(f"  {reference}  outcomeType={outcome}")
                if len(conflicts) > 20:
                    print(f"  ... and {len(conflicts)-20} more")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            print("\nverify (from the graph):")
            for record in session.run(VERIFY):
                print(f"  {record['role'] or 'null':12s} {record['decisions']:7,}")

            print("\nverify -- unknown share by board (boards with >=20 inter partes "
                  "decisions):")
            for record in session.run(VERIFY_BY_BOARD_ROLE_UNKNOWN):
                print(f"  {record['board']:10s} total={record['total']:5,}  "
                      f"unknown={record['unknown']:5,}  ({record['unknownPct']}%)")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
