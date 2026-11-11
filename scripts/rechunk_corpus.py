#!/usr/bin/env python3
"""Scenario B -- paragraph re-chunk the whole corpus and build the :Paragraph layer.

Replaces the legacy 500-token/50-overlap chunk generation (657,115 nodes, whose
windows cut mid-sentence) with the paragraph-aligned `para-v1` generation over all
159,597 sections, and extends the :Paragraph layer corpus-wide.

    (:Decision)-[:HAS_SECTION]->(:Section)-[:HAS_PARAGRAPH]->(:Paragraph)
                                     ^                            ^
                            [:PART_OF](:Chunk)-[:COVERS]----------+

Chunks and paragraphs are produced in ONE pass. Tokenising 256M tokens is the
dominant cost, so running `chunk_paragraphs.py` then `chunk_hierarchy.py`
separately would tokenise the corpus three times over (the latter does a verify
pass and a build pass) for no benefit.

Idempotent: ids are deterministic (`<sectionId>_pNNNN`, `<sectionId>_gNNNN`) and
every write is a MERGE that sets only derived properties. The 9,119 chunks already
embedded keep their ids, their text and therefore their `text_embedding` --
nothing in the SET clauses touches it.

Phases, runnable separately because this takes hours:

    rechunk        write para-v1 chunks + paragraphs + COVERS/NEXT   (~1-2 h)
    delete-legacy  drop the 657k generation=NULL chunks              (~10-20 min)
    citations      denormalise caseRef/citation onto both layers     (~minutes)

Usage:
    python3 scripts/rechunk_corpus.py --phase all
    python3 scripts/rechunk_corpus.py --phase rechunk --limit 500   # smoke test
    python3 scripts/rechunk_corpus.py --phase rechunk --resume-from 42000
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.chunker import (  # noqa: E402
    PARAGRAPH_GENERATION,
    chunk_section_paragraphs,
    section_paragraphs,
)

CONSTRAINTS = [
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT paragraph_id IF NOT EXISTS FOR (p:Paragraph) REQUIRE p.id IS UNIQUE",
]

ALL_SECTION_IDS = "MATCH (s:Section) RETURN s.id AS id ORDER BY s.id"

FETCH_SECTIONS = """
UNWIND $ids AS sid
MATCH (s:Section {id: sid})
RETURN s.id AS id, s.type AS type, s.text AS text, s.documentName AS documentName
"""

WRITE_CHUNKS = """
UNWIND $rows AS row
MATCH (s:Section {id: row.sectionId})
MERGE (c:Chunk {id: row.id})
SET c.text           = row.text,
    c.index          = row.index,
    c.tokenCount     = row.tokenCount,
    c.type           = row.type,
    c.documentName   = row.documentName,
    c.sectionContext = row.sectionContext,
    c.paragraphRef   = row.paragraphRef,
    c.paragraphRefs  = row.paragraphRefs,
    c.headingContext = row.headingContext,
    c.generation     = row.generation,
    c.active         = true
MERGE (c)-[:PART_OF]->(s)
"""

WRITE_PARAGRAPHS = """
UNWIND $rows AS row
MATCH (s:Section {id: row.sectionId})
MERGE (p:Paragraph {id: row.id})
SET p.index          = row.index,
    p.ref            = row.ref,
    p.text           = row.text,
    p.tokenCount     = row.tokenCount,
    p.type           = row.type,
    p.documentName   = row.documentName,
    p.headingContext = row.headingContext,
    p.generation     = row.generation
MERGE (s)-[:HAS_PARAGRAPH]->(p)
"""

# Labelled separately, and deliberately so: a label-less `MATCH (a {id: ...})`
# cannot use the uniqueness-constraint index and degrades to an all-nodes scan
# per pair. Measured at ~1M nodes that made this query the entire runtime --
# 22.5 min for 500 sections, a 5-day corpus run.
WRITE_CHUNK_NEXT = """
UNWIND $pairs AS pair
MATCH (a:Chunk {id: pair.from}), (b:Chunk {id: pair.to})
MERGE (a)-[:NEXT]->(b)
"""

WRITE_PARAGRAPH_NEXT = """
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

COUNT_LEGACY = "MATCH (c:Chunk) WHERE c.generation IS NULL RETURN count(c) AS legacy"

# Guard: never delete the legacy generation until para-v1 covers every section
# that legacy covered, or the corpus loses lexical coverage entirely.
LEGACY_COVERAGE_CHECK = """
MATCH (s:Section)<-[:PART_OF]-(c:Chunk)
WHERE c.generation IS NULL
WITH DISTINCT s
WHERE NOT EXISTS { (s)<-[:PART_OF]-(:Chunk {generation: $generation}) }
RETURN count(s) AS uncovered
"""

DELETE_LEGACY = """
MATCH (c:Chunk) WHERE c.generation IS NULL
CALL (c) {
  DETACH DELETE c
} IN TRANSACTIONS OF 5000 ROWS
"""

SHORT_SECTION = """{ReasonsForDecision: 'Reasons', AppealOrder: 'Order',
                    Catchword: 'Catchword', HeadNote: 'Headnote',
                    SummaryOfFacts: 'Facts'}"""

ENRICH_CHUNKS = """
MATCH (c:Chunk {generation: $generation})-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
CALL (c, d) {
  WITH c, d, """ + SHORT_SECTION + """ AS shortName,
       d.code + ' ' + toString(toInteger(d.appealNum)) + '/' + right(d.year, 2) AS caseRef
  SET c.caseNumber   = d.caseNumber,
      c.caseRef      = caseRef,
      c.decisionDate = d.decisionDate,
      c.citation     = caseRef + ', ' + coalesce(shortName[c.type], c.type)
                       + coalesce(' ' + c.paragraphRef, '')
} IN TRANSACTIONS OF 2000 ROWS
"""

ENRICH_PARAGRAPHS = """
MATCH (p:Paragraph {generation: $generation})<-[:HAS_PARAGRAPH]-(:Section)
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
MATCH (c:Chunk {generation: $generation})
WITH count(c) AS chunks, sum(c.tokenCount) AS chunkTokens,
     count(CASE WHEN c.text_embedding IS NOT NULL THEN 1 END) AS embedded
MATCH (p:Paragraph {generation: $generation})
RETURN chunks, chunkTokens, embedded,
       count(p) AS paragraphs, sum(p.tokenCount) AS paragraphTokens
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--phase", default="all",
                        choices=["all", "rechunk", "delete-legacy", "citations", "verify"])
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--generation", default=PARAGRAPH_GENERATION)
    parser.add_argument("--limit", type=int, help="process only the first N sections")
    parser.add_argument("--resume-from", type=int, default=0,
                        help="skip the first N sections (ids are ordered and stable)")
    return parser.parse_args()


def rechunk(session, args):
    ids = [record["id"] for record in session.run(ALL_SECTION_IDS)]
    if args.limit:
        ids = ids[: args.limit]
    ids = ids[args.resume_from:]

    total = len(ids)
    print(f"sections to process: {total:,} (from offset {args.resume_from:,})")
    stats = {"chunks": 0, "paragraphs": 0, "covers": 0, "next": 0}
    started = time.time()

    for offset in range(0, total, args.batch_size):
        batch_ids = ids[offset: offset + args.batch_size]
        sections = [dict(r) for r in session.run(FETCH_SECTIONS, ids=batch_ids)]

        chunk_rows, paragraph_rows, covers = [], [], []
        chunk_next, paragraph_next = [], []
        for section in sections:
            paragraphs = section_paragraphs(section)
            chunks = chunk_section_paragraphs(section)
            if not chunks:
                continue
            paragraph_rows.extend(paragraphs)
            chunk_rows.extend(chunks)
            paragraph_next.extend({"from": a["id"], "to": b["id"]}
                                  for a, b in zip(paragraphs, paragraphs[1:]))
            chunk_next.extend({"from": a["id"], "to": b["id"]}
                              for a, b in zip(chunks, chunks[1:]))
            by_index = {p["index"]: p["id"] for p in paragraphs}
            for chunk in chunks:
                pids = [by_index[i] for i in chunk["paragraphIndexes"] if i in by_index]
                if pids:
                    covers.append({"chunkId": chunk["id"], "paragraphIds": pids})

        if chunk_rows:
            session.execute_write(lambda tx: tx.run(WRITE_CHUNKS, rows=chunk_rows).consume())
        if paragraph_rows:
            session.execute_write(lambda tx: tx.run(WRITE_PARAGRAPHS, rows=paragraph_rows).consume())
        if chunk_next:
            session.execute_write(lambda tx: tx.run(WRITE_CHUNK_NEXT, pairs=chunk_next).consume())
        if paragraph_next:
            session.execute_write(
                lambda tx: tx.run(WRITE_PARAGRAPH_NEXT, pairs=paragraph_next).consume())
        if covers:
            session.execute_write(lambda tx: tx.run(WRITE_COVERS, rows=covers).consume())

        stats["chunks"] += len(chunk_rows)
        stats["paragraphs"] += len(paragraph_rows)
        stats["covers"] += len(covers)
        stats["next"] += len(chunk_next) + len(paragraph_next)

        done = min(offset + args.batch_size, total)
        elapsed = time.time() - started
        rate = done / elapsed if elapsed else 0
        eta = (total - done) / rate / 60 if rate else 0
        print(f"  {done:,}/{total:,} sections  {rate:.0f} sec/s  ETA {eta:.0f} min  "
              f"chunks={stats['chunks']:,} paragraphs={stats['paragraphs']:,}",
              flush=True)

    print(f"\nrechunk done in {(time.time()-started)/60:.1f} min: "
          + ", ".join(f"{k}={v:,}" for k, v in stats.items()))


def delete_legacy(session, args):
    legacy = session.run(COUNT_LEGACY).single()["legacy"]
    print(f"legacy chunks (generation IS NULL): {legacy:,}")
    if not legacy:
        print("nothing to delete")
        return

    uncovered = session.run(LEGACY_COVERAGE_CHECK, generation=args.generation).single()["uncovered"]
    if uncovered:
        raise SystemExit(
            f"ABORTED -- {uncovered:,} sections have legacy chunks but no "
            f"'{args.generation}' chunks. Deleting now would lose lexical coverage. "
            "Run --phase rechunk to completion first."
        )
    print("coverage check passed -- every legacy-covered section has para-v1 chunks")

    started = time.time()
    session.run(DELETE_LEGACY).consume()
    remaining = session.run(COUNT_LEGACY).single()["legacy"]
    print(f"deleted in {(time.time()-started)/60:.1f} min, remaining legacy: {remaining:,}")


def main():
    args = parse_args()
    load_dotenv()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            phases = (["rechunk", "delete-legacy", "citations", "verify"]
                      if args.phase == "all" else [args.phase])

            if "rechunk" in phases:
                for constraint in CONSTRAINTS:
                    session.run(constraint)
                rechunk(session, args)

            if "delete-legacy" in phases:
                print("\n== delete-legacy ==")
                delete_legacy(session, args)

            if "citations" in phases:
                print("\n== citations ==")
                started = time.time()
                session.run(ENRICH_CHUNKS, generation=args.generation).consume()
                session.run(ENRICH_PARAGRAPHS, generation=args.generation).consume()
                print(f"enriched in {(time.time()-started)/60:.1f} min")

            if "verify" in phases:
                print("\n== verify ==")
                result = session.run(VERIFY, generation=args.generation).single()
                for key in result.keys():
                    print(f"  {key:18s} {result[key]:,}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
