#!/usr/bin/env python3
"""Q7 (PHARMA_GENERICS_PLAN.md) -- late-filed evidence/request admission under
Art. 12(4)/13(2) RPBA 2020.

    "An opponent's best prior-art document is frequently found late. If it
    is not admitted, the attack dies on procedure regardless of merit. This
    is pure downside risk and the single most preventable way to lose."

Read-only analytics: `CITES_ARTICLE` -> `RPBA2020_Art_012`/`RPBA2020_Art_013`
(canonicalised distinct from the pre-2020 RPBA in Phase 1.1 -- required for
this to be correct, since a decision applying the OLD Art. 12(4) RPBA 2007
is not answering this question) + rule-based admission scoring
(`importer/late_filing.py`) over each decision's `ReasonsForDecision` text.

Reports admitted / not-admitted / mixed / unclear counts, split ex parte vs
inter partes, plus a handful of sample passages per bucket so the "on what
reasoning" half of the question is answerable by reading the actual text --
this is a rule-based presence check, not a reasoning summary, and does not
pretend to be one.

Usage:
    python3 scripts/analyze_late_filing.py [--samples 3]
"""

import argparse
import os
import sys
from collections import Counter, defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.late_filing import classify, match_context  # noqa: E402

RPBA_2020_LATE_FILING_ARTICLES = ("RPBA2020_Art_012", "RPBA2020_Art_013")

FETCH = """
MATCH (d:Decision {isCanonical: true})-[:CITES_ARTICLE]->(a:Article)
WHERE a.code IN $articles
WITH d, collect(DISTINCT a.code) AS articles
MATCH (d)-[:HAS_SECTION]->(:ReasonsForDecision)<-[:PART_OF]-(c:Chunk)
RETURN d.reference AS reference, d.isInterPartes AS isInterPartes,
       articles AS articles, c.id AS chunkId, c.text AS text
"""


def proceeding(is_inter_partes):
    return "inter partes" if is_inter_partes else "ex parte"


def bucket(admitted, not_admitted):
    if admitted and not_admitted:
        return "mixed"
    if admitted:
        return "admitted"
    if not_admitted:
        return "not_admitted"
    return "unclear"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--samples", type=int, default=3,
                        help="sample passages to print per bucket, for the reasoning")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            rows = session.run(FETCH, articles=list(RPBA_2020_LATE_FILING_ARTICLES)).data()

            by_decision = defaultdict(lambda: {"isInterPartes": None, "admitted": False,
                                                "notAdmitted": False, "samplePassages": []})
            for row in rows:
                admitted, not_admitted = classify(row["text"])
                entry = by_decision[row["reference"]]
                entry["isInterPartes"] = row["isInterPartes"]
                entry["admitted"] = entry["admitted"] or admitted
                entry["notAdmitted"] = entry["notAdmitted"] or not_admitted
                if admitted or not_admitted:
                    entry["samplePassages"].append((row["chunkId"], row["text"]))

            print(f"{len(by_decision):,} canonical decisions citing Art. 12/13 RPBA 2020 "
                  "(late-filed evidence/request admission)")

            counts = defaultdict(Counter)
            samples = defaultdict(list)
            for reference, entry in by_decision.items():
                proc = proceeding(entry["isInterPartes"])
                b = bucket(entry["admitted"], entry["notAdmitted"])
                counts[proc][b] += 1
                if entry["samplePassages"]:
                    samples[(proc, b)].append((reference, entry["samplePassages"][0]))

            for proc in sorted(counts):
                total = sum(counts[proc].values())
                print(f"\n{proc} -- {total:,} decisions:")
                for b in ("admitted", "not_admitted", "mixed", "unclear"):
                    n = counts[proc][b]
                    pct = 100.0 * n / total if total else 0.0
                    print(f"  {b:14s} {n:6,}  ({pct:5.1f}%)")

            print("\nCaveat, found by spot-checking real matches: 'decided not to admit' also "
                  "describes what the FIRST-INSTANCE division decided, narrated inside the "
                  "Board's own reasoning -- not the Board's own RPBA 2020 ruling on appeal that "
                  "this question asks about. Read the samples below, do not trust the counts "
                  "above as precise -- see importer/late_filing.py.")

            for (proc, b) in sorted(samples):
                if b in ("unclear",):
                    continue
                print(f"\nSample reasoning -- {proc} / {b}:")
                for reference, (chunk_id, text) in samples[(proc, b)][:args.samples]:
                    snippet = " ".join(match_context(text).split())
                    print(f"  {reference} ({chunk_id}):")
                    print(f"    ...{snippet}...")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
