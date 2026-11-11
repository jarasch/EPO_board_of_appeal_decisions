#!/usr/bin/env python3
"""Phase 1.1 + 1.2 foundation cleanup.

1.1  Build the canonical (:Article) layer over :LegalProvision and link each
     Decision straight to the canonical article it cites, so a query for
     "Art. 56 EPC" no longer has to enumerate EPC1973/EPC2000/(2007) variants.

1.2  Drop the redundant (:Decision)-[:CITES_CASE]->(:CitedCase) stubs -- but only
     where enrich_graph.py already resolved the same citation into
     (:Decision)-[:CITES]->(:Case). Unresolved stubs are the *only* record that an
     out-of-corpus case was cited, so they stay.

Idempotent: re-running makes no further changes. Credentials come from .env.

Usage:
    python3 scripts/normalize_provisions.py [--dry-run]
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.provisions import canonicalise
from importer.schema import ensure_schema

FETCH_PROVISIONS = "MATCH (l:LegalProvision) RETURN l.code AS code"

WRITE_ARTICLES = """
UNWIND $rows AS row
MATCH (l:LegalProvision {code: row.raw})
MERGE (a:Article {code: row.code})
  ON CREATE SET a.instrument = row.instrument, a.kind = row.kind,
                a.number = row.number, a.label = row.label
SET l.canonicalCode = row.code
MERGE (l)-[:CANONICAL_AS]->(a)
"""

LINK_DECISIONS = """
MATCH (d:Decision)-[:CITES_LEGAL_PROVISION]->(:LegalProvision)-[:CANONICAL_AS]->(a:Article)
WITH DISTINCT d, a
CALL (d, a) {
  MERGE (d)-[:CITES_ARTICLE]->(a)
} IN TRANSACTIONS OF 5000 ROWS
"""

# Only stubs whose citation is already resolved. caseKey is not unique (~290 case
# numbers cover two decisions), so EXISTS on the pattern, not an equality join.
DELETE_REDUNDANT_STUB_RELS = """
MATCH (d:Decision)-[r:CITES_CASE]->(cc:CitedCase)
WHERE cc.appealNum IS NOT NULL AND cc.year IS NOT NULL
  AND EXISTS { (d)-[:CITES]->(:Case {caseKey: cc.code + '-' + cc.appealNum + '-' + cc.year}) }
CALL (r) {
  DELETE r
} IN TRANSACTIONS OF 5000 ROWS
"""

# Backfill for :Case nodes created by an enrich_graph.py run that predates
# caseRef. New runs set it at MERGE time.
BACKFILL_CASE_REF = """
MATCH (c:Case)
WHERE c.caseRef IS NULL AND c.appealNum IS NOT NULL AND c.year IS NOT NULL
CALL (c) {
  SET c.caseRef = c.code + ' ' + toString(toInteger(c.appealNum)) + '/' + right(c.year, 2)
} IN TRANSACTIONS OF 5000 ROWS
"""

COUNT_REDUNDANT_STUB_RELS = """
MATCH (d:Decision)-[r:CITES_CASE]->(cc:CitedCase)
WITH r, cc.appealNum IS NOT NULL AND cc.year IS NOT NULL
       AND EXISTS { (d)-[:CITES]->(:Case {caseKey: cc.code + '-' + cc.appealNum + '-' + cc.year}) }
       AS resolved
RETURN count(CASE WHEN resolved THEN 1 END) AS redundant,
       count(CASE WHEN NOT resolved THEN 1 END) AS unresolved
"""

DELETE_ORPHAN_STUBS = """
MATCH (cc:CitedCase) WHERE NOT (cc)<-[:CITES_CASE]-()
CALL (cc) {
  DETACH DELETE cc
} IN TRANSACTIONS OF 1000 ROWS
"""

COUNTS = """
RETURN COUNT { (:Article) } AS articles,
       COUNT { (:LegalProvision)-[:CANONICAL_AS]->(:Article) } AS canonicalLinks,
       COUNT { (l:LegalProvision) WHERE l.canonicalCode IS NULL } AS unmappedProvisions,
       COUNT { ()-[:CITES_ARTICLE]->() } AS citesArticle,
       COUNT { ()-[:CITES_CASE]->() } AS citesCase,
       COUNT { (:CitedCase) } AS citedCaseStubs
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing")
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    driver.verify_connectivity()

    try:
        with driver.session(database=database) as session:
            codes = [r["code"] for r in session.run(FETCH_PROVISIONS)]
            rows = []
            for code in codes:
                canonical = canonicalise(code)
                if canonical:
                    rows.append({"raw": code, **canonical})

            distinct = len({row["code"] for row in rows})
            print(f"1.1  {len(codes)} LegalProvision codes -> {len(rows)} mapped "
                  f"onto {distinct} canonical Article nodes "
                  f"({len(codes) - len(rows)} free-text codes left unmapped)")

            if args.dry_run:
                redundant = session.run(COUNT_REDUNDANT_STUB_RELS).single()
                print(f"1.2  {redundant['redundant']} redundant CITES_CASE relationships "
                      f"would be deleted; {redundant['unresolved']} unresolved kept")
                print("--dry-run: no writes performed")
                return

            ensure_schema(driver, database)

            for start in range(0, len(rows), 1000):
                session.run(WRITE_ARTICLES, rows=rows[start:start + 1000]).consume()
            print("1.1  canonical Article nodes and CANONICAL_AS links written")

            session.run(LINK_DECISIONS).consume()
            print("1.1  Decision-[:CITES_ARTICLE]->Article links written")

            deleted = session.run(DELETE_REDUNDANT_STUB_RELS).consume()
            print(f"1.2  {deleted.counters.relationships_deleted} redundant "
                  f"CITES_CASE relationships deleted")

            orphans = session.run(DELETE_ORPHAN_STUBS).consume()
            print(f"1.2  {orphans.counters.nodes_deleted} orphaned CitedCase stubs deleted")

            backfill = session.run(BACKFILL_CASE_REF).consume()
            print(f"1.2  {backfill.counters.properties_set} Case.caseRef values backfilled")

            counts = session.run(COUNTS).single()
            print("\nPost-state:")
            for key in counts.keys():
                print(f"  {key:22s} {counts[key]}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
