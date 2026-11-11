#!/usr/bin/env python3
"""Add the :Paragraph layer between :Section and :Chunk.

Before this, the document hierarchy stopped at the section: a chunk carried
`paragraphRef` as a property, so the numbered legal paragraph was a label on the
retrieval unit rather than an addressable thing. A chunk that packs paragraphs
8 through 8.5 cites as "Reasons 8" and 8.1-8.5 are not reachable at all.

    before   (:Decision)-[:HAS_SECTION]->(:Section)<-[:PART_OF]-(:Chunk)
    after    (:Decision)-[:HAS_SECTION]->(:Section)-[:HAS_PARAGRAPH]->(:Paragraph)
                                              ^                          ^
                                              |                          |
                                     [:PART_OF](:Chunk)-[:COVERS]--------+

Both levels are now first-class, with different jobs:

    :Section    the XML division -- Reasons / Order / Headnote / Catchword
    :Paragraph  the citable legal unit -- "Reasons 2.3". Exact, one per
                paragraph group, `NEXT`-chained in reading order
    :Chunk      the retrieval unit -- packed to ~600 tokens for embedding
                quality, linked by :COVERS to every paragraph it spans

**This is additive.** Chunk text, ids, and therefore the existing embeddings are
untouched: the same `chunk_section_paragraphs` output is used, and the script
verifies every computed chunk against what is already in the graph before it
writes anything. A mismatch aborts, because it would mean the stored embeddings
no longer correspond to the stored text.

The :Chunk -> :Paragraph links come from exact paragraph-group indices tracked
through packing, not from the `paragraphRefs` property, which is best-effort --
an enumeration inside a quoted claim can add spurious refs.

Usage:
    python3 scripts/chunk_hierarchy.py [--dry-run] [--batch-size 200]
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.chunker import (  # noqa: E402
    PARAGRAPH_GENERATION,
    chunk_section_paragraphs,
    section_paragraphs,
)

CONSTRAINT = (
    "CREATE CONSTRAINT paragraph_id IF NOT EXISTS "
    "FOR (p:Paragraph) REQUIRE p.id IS UNIQUE"
)

COUNT_SECTIONS = "MATCH (s:DemoSection) RETURN count(s) AS total"

READ_SECTIONS = """
MATCH (s:DemoSection)
RETURN s.id AS id, s.type AS type, s.text AS text, s.documentName AS documentName
ORDER BY s.id
SKIP $skip LIMIT $batchSize
"""

READ_CHUNKS = """
MATCH (c:DemoChunk {generation: $generation})-[:PART_OF]->(s:Section)
WHERE s.id IN $sectionIds
RETURN c.id AS id, c.text AS text
"""

WRITE_PARAGRAPHS = """
UNWIND $rows AS row
MATCH (s:Section {id: row.sectionId})
MERGE (p:Paragraph {id: row.id})
SET p:DemoParagraph,
    p.index          = row.index,
    p.ref            = row.ref,
    p.text           = row.text,
    p.tokenCount     = row.tokenCount,
    p.type           = row.type,
    p.documentName   = row.documentName,
    p.headingContext = row.headingContext,
    p.generation     = row.generation
MERGE (s)-[:HAS_PARAGRAPH]->(p)
"""

PARAGRAPH_NEXT = """
UNWIND $pairs AS pair
MATCH (a:Paragraph {id: pair.from}), (b:Paragraph {id: pair.to})
MERGE (a)-[:NEXT]->(b)
"""

WRITE_COVERS = """
UNWIND $rows AS row
MATCH (c:Chunk {id: row.chunkId})
UNWIND row.paragraphIds AS pid
MATCH (p:Paragraph {id: pid})
MERGE (c)-[:COVERS]->(p)
"""

# Same formula as the chunk citation, so a paragraph cite and a chunk cite of the
# same passage are string-identical where they should be.
SHORT_SECTION = """{ReasonsForDecision: 'Reasons', AppealOrder: 'Order',
                    Catchword: 'Catchword', HeadNote: 'Headnote',
                    SummaryOfFacts: 'Facts'}"""

ENRICH_CITATION = """
MATCH (p:DemoParagraph {generation: $generation})<-[:HAS_PARAGRAPH]-(:Section)
      <-[:HAS_SECTION]-(d:Decision)
CALL (p, d) {
  WITH p, d, """ + SHORT_SECTION + """ AS shortName,
       d.code + ' ' + toString(toInteger(d.appealNum)) + '/' + right(d.year, 2) AS caseRef
  SET p.caseNumber   = d.caseNumber,
      p.caseRef      = caseRef,
      p.decisionDate = d.decisionDate,
      p.citation     = caseRef + ', ' + coalesce(shortName[p.type], p.type)
                       + coalesce(' ' + p.ref, '')
} IN TRANSACTIONS OF 2000 ROWS
"""

VERIFY = """
MATCH (p:DemoParagraph {generation: $generation})
WITH count(p) AS paragraphs,
     count(CASE WHEN p.ref IS NULL THEN 1 END) AS withoutRef,
     sum(p.tokenCount) AS tokens
MATCH (c:DemoChunk {generation: $generation})
WITH paragraphs, withoutRef, tokens, count(c) AS chunks,
     count(CASE WHEN NOT (c)-[:COVERS]->(:Paragraph) THEN 1 END) AS chunksWithoutCovers
MATCH ()-[r:COVERS]->()
RETURN paragraphs, withoutRef, tokens, chunks, chunksWithoutCovers, count(r) AS coversEdges
"""

ORPHANS = """
MATCH (p:DemoParagraph {generation: $generation})
WHERE NOT (p)<-[:COVERS]-(:Chunk)
RETURN p.type AS type, count(*) AS paragraphs, sum(p.tokenCount) AS tokens
ORDER BY paragraphs DESC
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--generation", default=PARAGRAPH_GENERATION)
    parser.add_argument("--dry-run", action="store_true", help="verify and report, write nothing")
    return parser.parse_args()


def build(sections):
    """Compute paragraph rows and chunk->paragraph links for a batch of sections."""
    paragraph_rows, next_pairs, covers = [], [], []

    for section in sections:
        paragraphs = section_paragraphs(section)
        if not paragraphs:
            continue
        paragraph_rows.extend(paragraphs)
        next_pairs.extend(
            {"from": a["id"], "to": b["id"]}
            for a, b in zip(paragraphs, paragraphs[1:])
        )
        by_index = {p["index"]: p["id"] for p in paragraphs}
        for chunk in chunk_section_paragraphs(section):
            ids = [by_index[i] for i in chunk["paragraphIndexes"] if i in by_index]
            if ids:
                covers.append({"chunkId": chunk["id"], "paragraphIds": ids})

    return paragraph_rows, next_pairs, covers


def verify_chunks_unchanged(session, sections, generation):
    """Confirm the recomputed chunks match the graph exactly.

    If text or ids have drifted, the stored embeddings no longer describe the
    stored text, and linking paragraphs to them would be linking to stale nodes.
    """
    computed = {}
    for section in sections:
        for chunk in chunk_section_paragraphs(section):
            computed[chunk["id"]] = chunk["text"]

    stored = {
        record["id"]: record["text"]
        for record in session.run(
            READ_CHUNKS, generation=generation, sectionIds=[s["id"] for s in sections]
        )
    }

    missing = sorted(set(computed) - set(stored))
    extra = sorted(set(stored) - set(computed))
    changed = sorted(cid for cid in set(computed) & set(stored) if computed[cid] != stored[cid])
    return missing, extra, changed


def main():
    args = parse_args()
    load_dotenv()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    totals = {"paragraphs": 0, "covers": 0, "next": 0}
    drift = {"missing": [], "extra": [], "changed": []}

    try:
        with driver.session(database=database) as session:
            if not args.dry_run:
                session.run(CONSTRAINT)

            total = session.run(COUNT_SECTIONS).single()["total"]
            print(f"sections to process: {total}")

            skip = 0
            while skip < total:
                sections = [
                    dict(record)
                    for record in session.run(
                        READ_SECTIONS, skip=skip, batchSize=args.batch_size
                    )
                ]
                if not sections:
                    break

                missing, extra, changed = verify_chunks_unchanged(
                    session, sections, args.generation
                )
                drift["missing"].extend(missing)
                drift["extra"].extend(extra)
                drift["changed"].extend(changed)

                paragraph_rows, next_pairs, covers = build(sections)
                totals["paragraphs"] += len(paragraph_rows)
                totals["next"] += len(next_pairs)
                totals["covers"] += len(covers)

                if not args.dry_run and not any(drift.values()):
                    session.execute_write(
                        lambda tx: tx.run(WRITE_PARAGRAPHS, rows=paragraph_rows).consume()
                    )
                    if next_pairs:
                        session.execute_write(
                            lambda tx: tx.run(PARAGRAPH_NEXT, pairs=next_pairs).consume()
                        )
                    if covers:
                        session.execute_write(
                            lambda tx: tx.run(WRITE_COVERS, rows=covers).consume()
                        )

                skip += args.batch_size
                print(f"  {min(skip, total)}/{total} sections", end="\r")

            print()
            if any(drift.values()):
                print("ABORTED -- recomputed chunks do not match the graph:")
                for kind, ids in drift.items():
                    if ids:
                        print(f"  {kind}: {len(ids)} e.g. {ids[:3]}")
                print("\nThe stored embeddings would not match the stored text. "
                      "Re-run scripts/chunk_paragraphs.py and re-embed before adding "
                      "the paragraph layer.")
                raise SystemExit(1)

            print("chunk identity verified -- text and ids unchanged, embeddings still valid")
            print(f"computed: {totals['paragraphs']} paragraphs, "
                  f"{totals['next']} NEXT, {totals['covers']} chunks with COVERS")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            session.run(ENRICH_CITATION, generation=args.generation).consume()

            result = session.run(VERIFY, generation=args.generation).single()
            print("\nverified in graph:")
            for key in result.keys():
                print(f"  {key:22s} {result[key]}")

            print("\nparagraphs not covered by any chunk:")
            for record in session.run(ORPHANS, generation=args.generation):
                print(f"  {record['type']:22s} {record['paragraphs']:6d} "
                      f"({record['tokens']} tokens)")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
