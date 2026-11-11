#!/usr/bin/env python3
"""Mark one canonical :Decision per (case, language), corpus-wide.

The corpus stores the same decision several times under different accession
numbers. The reference encodes both axes: `G210002EP1` is language E (English),
form P (OJ publication); `EU1` and `EX1` are the unpublished version and the
extract of the same text. Measured on G 2/21:

    G210002DP1  de  122 chunks  49,320 tokens
    G210002EP1  en   72 chunks  26,068 tokens
    G210002EU1  en   72 chunks  26,068 tokens   <-- identical to EP1
    G210002EX1  en   72 chunks  26,068 tokens   <-- identical to EP1
    G210002FP1  fr   93 chunks  38,671 tokens

910 of 48,618 cases (1.9%) carry more than one decision, but they are
concentrated in the G and D series -- the most-cited decisions in the corpus --
so the effect on retrieval is out of all proportion to the count. A vector
search for the G 2/21 subject matter returned `G 2/21, Reasons 85` three times,
spending three of five top-k slots on one passage.

Deduplication is per **(case, language)**, not per case. `mark_demo_slice.py`
collapses per case, which is right for an EN-only slice but corpus-wide would
discard the German and French records entirely -- 35% of the corpus, and equally
authoritative practice.

Selection rule, matching the demo slice so the two agree: the record with the
most section text wins, tie-broken on reference so the choice is reproducible.

Writes `isCanonical` on both :Decision and :Chunk. On :Chunk because ad-hoc
vector search returns chunks and needs to filter without a three-hop traversal;
note it cannot serve as a vector-index prefilter without rebuilding the index
(`chunk_text_embedding` is pinned to ['documentName', 'type']).

Usage:
    python3 scripts/mark_canonical.py [--dry-run]
"""

import argparse
import os
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

INDEX = ("CREATE INDEX decision_isCanonical IF NOT EXISTS "
         "FOR (d:Decision) ON (d.isCanonical)")

# Order by total section text descending, then reference, and take the first per
# (case, language). COLLECT{} keeps this to one pass over the sections.
MARK_DECISIONS = """
MATCH (d:Decision)-[:LANGUAGE_VERSION_OF]->(case:Case)
WITH case, coalesce(d.lang, '?') AS lang, d,
     COLLECT { MATCH (d)-[:HAS_SECTION]->(s:Section) RETURN size(s.text) } AS sizes
WITH case, lang, d, reduce(t = 0, n IN sizes | t + n) AS textSize
ORDER BY textSize DESC, d.reference
WITH case, lang, collect(d) AS ranked
WITH ranked[0] AS canonical, ranked[1..] AS duplicates
CALL (canonical, duplicates) {
  SET canonical.isCanonical = true
  WITH duplicates
  UNWIND duplicates AS dup
  SET dup.isCanonical = false
} IN TRANSACTIONS OF 1000 ROWS
"""

# Chunks inherit the flag from the decision that owns their section.
MARK_CHUNKS = """
MATCH (d:Decision)-[:HAS_SECTION]->(:Section)<-[:PART_OF]-(c:Chunk)
CALL (d, c) {
  SET c.isCanonical = d.isCanonical
} IN TRANSACTIONS OF 10000 ROWS
"""

MARK_PARAGRAPHS = """
MATCH (d:Decision)-[:HAS_SECTION]->(:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
CALL (d, p) {
  SET p.isCanonical = d.isCanonical
} IN TRANSACTIONS OF 10000 ROWS
"""

PREVIEW = """
MATCH (d:Decision)-[:LANGUAGE_VERSION_OF]->(case:Case)
WITH case, coalesce(d.lang, '?') AS lang, collect(d.reference) AS refs
WHERE size(refs) > 1
RETURN case.caseRef AS caseRef, lang, refs ORDER BY size(refs) DESC LIMIT 8
"""

VERIFY = """
MATCH (d:Decision)
WITH count(*) AS decisions,
     count(CASE WHEN d.isCanonical THEN 1 END) AS canonical,
     count(CASE WHEN d.isCanonical = false THEN 1 END) AS duplicates,
     count(CASE WHEN d.isCanonical IS NULL THEN 1 END) AS unmarked
MATCH (c:Chunk)
RETURN decisions, canonical, duplicates, unmarked,
       count(CASE WHEN c.isCanonical THEN 1 END) AS canonicalChunks,
       count(CASE WHEN c.isCanonical = false THEN 1 END) AS duplicateChunks
"""

# Every (case, language) must end with exactly one canonical record.
INVARIANT = """
MATCH (d:Decision {isCanonical: true})-[:LANGUAGE_VERSION_OF]->(case:Case)
WITH case, coalesce(d.lang, '?') AS lang, count(*) AS n
WHERE n <> 1
RETURN count(*) AS violations
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            print("same-language duplicate groups (sample):")
            for record in session.run(PREVIEW):
                print(f"  {record['caseRef']:12s} {record['lang']}  {record['refs']}")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            session.run(INDEX).consume()

            started = time.time()
            session.run(MARK_DECISIONS).consume()
            print(f"\ndecisions marked in {time.time()-started:.0f}s")

            started = time.time()
            session.run(MARK_CHUNKS).consume()
            session.run(MARK_PARAGRAPHS).consume()
            print(f"chunks + paragraphs marked in {time.time()-started:.0f}s")

            result = session.run(VERIFY).single()
            print("\nverify:")
            for key in result.keys():
                print(f"  {key:18s} {result[key]:,}")

            violations = session.run(INVARIANT).single()["violations"]
            print(f"  {'invariant':18s} "
                  f"{'OK -- exactly one canonical per (case, language)' if violations == 0 else f'FAILED: {violations} groups'}")
            if violations:
                raise SystemExit(1)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
