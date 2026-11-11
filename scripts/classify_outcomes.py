#!/usr/bin/env python3
"""Build the outcome layer: the join key every base rate in both plans needs.

Writes, for each decision:

    (:Decision)-[:HAS_OUTCOME]->(:Outcome {type})     one Outcome node per type
    Decision.outcomeType, .setAside, .feeReimbursed,
            .feeReimbursementRefused, .costsApportioned,
            .remittalInstruction, .survivingRequest

plus the two partition flags that both PHARMA_GENERICS_PLAN.md and
EXAMINER_PLAN.md require, because pooling across either boundary produces a
number that answers no question:

    Decision.isInterPartes   opposition appeal (has an opponent) vs ex parte.
                             Ex parte appeals come from examining divisions,
                             inter partes from opposition divisions.
    Decision.rpbaRegime      'pre2020' / 'post2020', split at 2020-01-01.
                             Art. 11 RPBA 2020 changed remittal from routine to
                             "special reasons ... fundamental deficiencies", so
                             a remittal rate pooled across the break is
                             meaningless.

Classification logic and its validation live in `importer/outcomes.py`. Only
canonical decisions are classified (`scripts/mark_canonical.py`); the 881
duplicate records would otherwise be counted two or three times each, and they
are concentrated in the most-cited G, D, J and W series.

Usage:
    python3 scripts/classify_outcomes.py [--dry-run]
"""

import argparse
import os
import sys
import time
from collections import Counter

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.outcomes import classify_order  # noqa: E402

INDEXES = [
    "CREATE CONSTRAINT outcome_type IF NOT EXISTS "
    "FOR (o:Outcome) REQUIRE o.type IS UNIQUE",
    "CREATE INDEX decision_outcomeType IF NOT EXISTS "
    "FOR (d:Decision) ON (d.outcomeType)",
    "CREATE INDEX decision_rpbaRegime IF NOT EXISTS "
    "FOR (d:Decision) ON (d.rpbaRegime)",
]

FETCH = """
MATCH (d:Decision)-[:HAS_SECTION]->(o:AppealOrder)
WHERE d.isCanonical
RETURN d.reference AS reference, o.text AS text,
       EXISTS { (d)-[:HAS_OPPONENT]->() } AS interPartes,
       d.decisionDate AS decisionDate
ORDER BY d.reference
SKIP $skip LIMIT $limit
"""

WRITE = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (o:Outcome {type: row.type})
MERGE (d)-[:HAS_OUTCOME]->(o)
SET d.outcomeType              = row.type,
    d.setAside                 = row.setAside,
    d.feeReimbursed            = row.feeReimbursed,
    d.feeReimbursementRefused  = row.feeReimbursementRefused,
    d.costsApportioned         = row.costsApportioned,
    d.remittalInstruction      = row.remittalInstruction,
    d.survivingRequest         = row.survivingRequest,
    d.isInterPartes            = row.interPartes,
    d.rpbaRegime               = row.rpbaRegime
"""

# Decisions with no order section at all -- they cannot be classified and must
# stay visible rather than defaulting to anything.
MARK_NO_ORDER = """
MATCH (d:Decision)
WHERE d.isCanonical AND NOT EXISTS { (d)-[:HAS_SECTION]->(:AppealOrder) }
SET d.outcomeType = 'no_order'
RETURN count(*) AS n
"""

VERIFY = """
MATCH (d:Decision) WHERE d.isCanonical
RETURN d.outcomeType AS type, count(*) AS n,
       sum(CASE WHEN d.feeReimbursed THEN 1 ELSE 0 END) AS feeReimbursed,
       sum(CASE WHEN d.isInterPartes THEN 1 ELSE 0 END) AS interPartes
ORDER BY n DESC
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

    counts = Counter()
    started = time.time()

    try:
        with driver.session(database=database) as session:
            if not args.dry_run:
                for statement in INDEXES:
                    session.run(statement).consume()

            skip = 0
            while True:
                batch = [dict(r) for r in session.run(
                    FETCH, skip=skip, limit=args.batch_size)]
                if not batch:
                    break

                rows = []
                for record in batch:
                    result = classify_order(record["text"])
                    counts[result["type"]] += 1
                    date = record["decisionDate"]
                    rows.append({
                        "reference": record["reference"],
                        "interPartes": record["interPartes"],
                        "rpbaRegime": (
                            "post2020" if date and date.year >= 2020 else "pre2020"),
                        **result,
                    })

                if not args.dry_run:
                    session.execute_write(
                        lambda tx, r=rows: tx.run(WRITE, rows=r).consume())

                skip += args.batch_size
                print(f"  {skip:,} classified", end="\r", flush=True)

            total = sum(counts.values())
            print(f"\nclassified {total:,} canonical decisions "
                  f"in {time.time()-started:.0f}s")
            unclassified = counts.get("unclassified", 0)
            print(f"unclassified: {unclassified:,} ({100.0*unclassified/total:.2f}%)")

            if args.dry_run:
                for outcome, n in counts.most_common():
                    print(f"  {outcome:34s} {n:7,}")
                print("\n-- dry run, nothing written --")
                return

            no_order = session.run(MARK_NO_ORDER).single()["n"]
            print(f"decisions with no order section: {no_order:,} (marked 'no_order')")

            print("\nverify (from the graph):")
            for record in session.run(VERIFY):
                print(f"  {record['type'] or '(null)':34s} {record['n']:7,}"
                      f"  feeReimb={record['feeReimbursed']:5,}"
                      f"  interPartes={record['interPartes']:6,}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
