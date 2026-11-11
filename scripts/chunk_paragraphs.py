#!/usr/bin/env python3
"""Phase 1.3 -- paragraph-aware re-chunking of the demo slice.

Writes a *new* chunk generation, `(:Chunk:DemoChunk {generation: 'para-v1'})`, over
the sections marked by scripts/mark_demo_slice.py. The existing 657k token-window
:Chunk nodes are left untouched: chunk ids are suffixed `_pNNNN` rather than
`_NNNN`, so the two generations coexist and can be compared.

Usage:
    python3 scripts/chunk_paragraphs.py [--max-tokens 600] [--batch-size 200]
    python3 scripts/chunk_paragraphs.py --sample 5      # inspect, write nothing
"""

import argparse
import os
import sys
import time
from collections import Counter

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.chunker import PARAGRAPH_GENERATION, chunk_section_paragraphs
from importer.schema import ensure_schema

FETCH_SECTIONS = """
MATCH (s:DemoSection)
RETURN s.id AS id, s.type AS type, s.text AS text, s.documentName AS documentName
ORDER BY s.id
SKIP $skip LIMIT $batchSize
"""

DELETE_GENERATION = """
MATCH (c:DemoChunk {generation: $generation})
CALL (c) {
  DETACH DELETE c
} IN TRANSACTIONS OF 5000 ROWS
"""

WRITE_CHUNKS = """
UNWIND $rows AS row
MATCH (s:Section {id: row.sectionId})
MERGE (c:Chunk {id: row.id})
SET c:DemoChunk,
    c.text = row.text,
    c.index = row.index,
    c.tokenCount = row.tokenCount,
    c.type = row.type,
    c.documentName = row.documentName,
    c.sectionContext = row.sectionContext,
    c.paragraphRef = row.paragraphRef,
    c.paragraphRefs = row.paragraphRefs,
    c.headingContext = row.headingContext,
    c.generation = row.generation,
    c.active = true
MERGE (c)-[:PART_OF]->(s)
"""

NEXT_CHAIN = """
UNWIND $pairs AS pair
MATCH (a:Chunk {id: pair.from}), (b:Chunk {id: pair.to})
MERGE (a)-[:NEXT]->(b)
"""

# Denormalise the attorney-facing citation onto the chunk: "T 1924/17, Reasons 3.2".
# Used both as embedding context (far more informative than the accession number
# in documentName) and as the citation string the summarisation stage prints.
SHORT_SECTION = """{ReasonsForDecision: 'Reasons', AppealOrder: 'Order',
                    Catchword: 'Catchword', HeadNote: 'Headnote'}"""

ENRICH_CITATION = """
MATCH (c:DemoChunk {generation: $generation})-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
CALL (c, d) {
  WITH c, d, """ + SHORT_SECTION + """ AS shortName,
       // Attorneys write "T 1924/17", not the corpus's zero-padded "T 1924/17"
       // variant "T 0001/19" -- so unpad the appeal number and use a 2-digit year.
       d.code + ' ' + toString(toInteger(d.appealNum)) + '/' + right(d.year, 2) AS caseRef
  SET c.caseNumber = d.caseNumber,
      c.caseRef = caseRef,
      c.decisionDate = d.decisionDate,
      c.citation = caseRef + ', ' + coalesce(shortName[c.type], c.type)
                   + coalesce(' ' + c.paragraphRef, '')
} IN TRANSACTIONS OF 2000 ROWS
"""

VERIFY = """
MATCH (c:DemoChunk {generation: $generation})
RETURN count(c) AS chunks,
       sum(c.tokenCount) AS tokens,
       min(c.tokenCount) AS minTokens,
       max(c.tokenCount) AS maxTokens,
       avg(c.tokenCount) AS avgTokens,
       count(CASE WHEN c.paragraphRef IS NULL THEN 1 END) AS withoutRef
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-tokens", type=int, default=600,
                        help="Token budget per chunk; whole paragraphs are packed up to it")
    parser.add_argument("--batch-size", type=int, default=200,
                        help="Sections fetched/chunked per round")
    parser.add_argument("--sample", type=int, metavar="N",
                        help="Chunk N sections, print stats and examples, write nothing")
    return parser.parse_args()


def print_sample(rows_by_section):
    sizes = Counter()
    refless = 0
    total = 0
    for rows in rows_by_section:
        for row in rows:
            total += 1
            sizes[row["tokenCount"] // 100 * 100] += 1
            if row["paragraphRef"] is None:
                refless += 1
    print(f"\n{total} chunks from {len(rows_by_section)} sections; "
          f"{refless} without a paragraph ref ({100 * refless / max(total, 1):.1f}%)")
    print("token-count histogram (bucket of 100):")
    for bucket in sorted(sizes):
        print(f"  {bucket:4d}-{bucket + 99:4d}  {'#' * min(sizes[bucket], 60)} {sizes[bucket]}")

    print("\nfirst section's chunks:")
    for row in rows_by_section[0][:6]:
        head = row["text"][:150].replace("\n", " ")
        print(f"  [{row['id']}] ref={row['paragraphRef']!s:8s} "
              f"tok={row['tokenCount']:3d} heading={row['headingContext']!r}")
        print(f"      {head}...")


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
            if args.sample:
                records = session.run(FETCH_SECTIONS, skip=0, batchSize=args.sample).data()
                print_sample([chunk_section_paragraphs(r, args.max_tokens) for r in records])
                return

            ensure_schema(driver, database)
            session.run(DELETE_GENERATION, generation=PARAGRAPH_GENERATION).consume()
            print(f"Cleared any previous '{PARAGRAPH_GENERATION}' generation")

            skip = 0
            sections = 0
            chunks = 0
            start = time.time()
            while True:
                records = session.run(FETCH_SECTIONS, skip=skip,
                                      batchSize=args.batch_size).data()
                if not records:
                    break

                rows, pairs = [], []
                for record in records:
                    section_rows = chunk_section_paragraphs(record, args.max_tokens)
                    rows.extend(section_rows)
                    pairs.extend(
                        {"from": a["id"], "to": b["id"]}
                        for a, b in zip(section_rows, section_rows[1:])
                    )

                if rows:
                    session.run(WRITE_CHUNKS, rows=rows).consume()
                if pairs:
                    session.run(NEXT_CHAIN, pairs=pairs).consume()

                skip += len(records)
                sections += len(records)
                chunks += len(rows)
                elapsed = time.time() - start
                print(f"  {sections} sections -> {chunks} chunks "
                      f"({elapsed:.1f}s, {sections / elapsed:.1f} sections/s)")

            session.run(ENRICH_CITATION, generation=PARAGRAPH_GENERATION).consume()
            print("  citations denormalised onto chunks")

            stats = session.run(VERIFY, generation=PARAGRAPH_GENERATION).single()
            print(f"\nDone in {time.time() - start:.1f}s")
            print(f"  chunks       {stats['chunks']:,}")
            print(f"  tokens       {stats['tokens']:,}")
            print(f"  tokens/chunk min {stats['minTokens']} / "
                  f"avg {stats['avgTokens']:.0f} / max {stats['maxTokens']}")
            print(f"  without ref  {stats['withoutRef']:,}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
