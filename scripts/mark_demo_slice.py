#!/usr/bin/env python3
"""Mark the demo slice with :DemoDecision / :DemoSection labels.

Entity extraction over all 657k corpus chunks is not demo-viable (~828M input
tokens), so the demo is scoped to one legally coherent slice: English decisions
on inventive step (Art. 56 EPC) from 2015 onwards in the computer-implemented
invention classes (IPC G06F / G06Q). That is the COMVIK / technical-effect
case law an attorney actually argues about.

Marker labels rather than a property so downstream tools can select the slice by
`source_label` / `node_label` without touching the rest of the corpus, and so the
blast radius of an extraction run is explicit and re-runnable.

Idempotent, and removes markers from anything that no longer matches the slice.

Usage:
    python3 scripts/mark_demo_slice.py [--dry-run]
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The Reasons carry the legal argument; the Order carries the operative outcome;
# headnote/catchword are tiny and legally dense. SummaryOfFacts is deliberately
# excluded -- it is 43% more text for mostly procedural recitation.
SLICE_SECTION_TYPES = ["ReasonsForDecision", "AppealOrder", "Catchword", "HeadNote"]

SLICE_PREDICATE = """
MATCH (d:Decision)
WHERE d.lang = $lang
  AND d.decisionDate >= date($decidedFrom)
  AND EXISTS { (d)-[:CITES_ARTICLE]->(:Article {code: $article}) }
  AND EXISTS {
    (d)-[:CLASSIFIED_AS]->(i:IPCClass)
    WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix)
  }
// ~1.7% of the corpus records the same decision twice under different accession
// numbers (G190001EP1 / G190001EX1 -- the OJ version and the extract, byte
// identical here). They share an ECLI, so they hang off one :Case; keep the
// fullest record per case, tie-broken on reference so the slice is reproducible.
MATCH (d)-[:LANGUAGE_VERSION_OF]->(case:Case)
WITH case, d, COLLECT { MATCH (d)-[:HAS_SECTION]->(s:Section) RETURN size(s.text) } AS sizes
WITH case, d ORDER BY reduce(t = 0, n IN sizes | t + n) DESC, d.reference
WITH case, collect(d)[0] AS d
"""

CLEAR_MARKERS = """
MATCH (n) WHERE n:DemoDecision OR n:DemoSection
CALL (n) {
  REMOVE n:DemoDecision, n:DemoSection
} IN TRANSACTIONS OF 5000 ROWS
"""

MARK_SLICE = SLICE_PREDICATE + """
CALL (d) {
  SET d:DemoDecision
  WITH d
  MATCH (d)-[:HAS_SECTION]->(s:Section)
  WHERE s.type IN $sectionTypes AND s.text IS NOT NULL
  SET s:DemoSection
} IN TRANSACTIONS OF 200 ROWS
"""

COUNT_SLICE = SLICE_PREDICATE + """
OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
WHERE s.type IN $sectionTypes AND s.text IS NOT NULL
RETURN count(DISTINCT d) AS decisions, count(s) AS sections,
       sum(size(s.text)) AS chars
"""

REPORT = """
MATCH (s:DemoSection)
RETURN s.type AS sectionType, count(s) AS sections, sum(size(s.text)) AS chars
ORDER BY chars DESC
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--decided-from", default="2015-01-01")
    parser.add_argument("--article", default="EPC_Art_056",
                        help="Canonical Article code from scripts/normalize_provisions.py")
    parser.add_argument("--ipc-prefixes", nargs="+", default=["G06F", "G06Q"])
    parser.add_argument("--section-types", nargs="+", default=SLICE_SECTION_TYPES)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report the slice size without writing labels")
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    params = {
        "lang": args.lang,
        "decidedFrom": args.decided_from,
        "article": args.article,
        "ipcPrefixes": args.ipc_prefixes,
        "sectionTypes": args.section_types,
    }

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    driver.verify_connectivity()

    try:
        with driver.session(database=database) as session:
            counts = session.run(COUNT_SLICE, **params).single()
            print(f"Slice: lang={args.lang} decided>={args.decided_from} "
                  f"{args.article} IPC={'/'.join(args.ipc_prefixes)}")
            print(f"  {counts['decisions']} decisions, {counts['sections']} sections, "
                  f"{counts['chars'] or 0:,} chars "
                  f"(~{(counts['chars'] or 0) // 4:,} tokens)")

            if args.dry_run:
                print("--dry-run: no labels written")
                return

            session.run(CLEAR_MARKERS).consume()
            session.run(MARK_SLICE, **params).consume()

            print("\nMarked:")
            for row in session.run(REPORT):
                print(f"  {row['sectionType']:20s} {row['sections']:6d} sections  "
                      f"{row['chars']:>12,} chars")
            total = session.run(
                "RETURN COUNT { (:DemoDecision) } AS decisions, "
                "COUNT { (:DemoSection) } AS sections"
            ).single()
            print(f"  {'TOTAL':20s} {total['sections']:6d} sections "
                  f"across {total['decisions']} decisions")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
