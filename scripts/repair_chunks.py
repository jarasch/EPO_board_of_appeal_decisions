#!/usr/bin/env python3
"""Rebuild only the sections whose chunking changed, and drop their stale embeddings.

Written for the table-row fix in `_is_heading`, but general: it recomputes every
section, compares against what is stored, and rebuilds only where the text
differs.

Why not just re-run `rechunk_corpus.py`: that MERGEs on a deterministic chunk id
and SETs the text. Where the chunking has changed, chunk `..._p0003` keeps the
embedding computed for its *old* text while now holding different text -- a
silent mismatch that no count would reveal. So an affected section has its chunks
and paragraphs deleted and rebuilt, which forces re-embedding.

Unaffected sections are left completely alone, so the ~700k embeddings that are
still correct are never touched.

After this, run:
    python3 scripts/embed_corpus.py      # fills the deleted embeddings
    python3 scripts/mark_canonical.py    # re-flags the rebuilt nodes

Usage:
    python3 scripts/repair_chunks.py --dry-run    # report what would change
    python3 scripts/repair_chunks.py
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

ALL_SECTION_IDS = "MATCH (s:Section) RETURN s.id AS id ORDER BY s.id"

FETCH_SECTIONS = """
UNWIND $ids AS sid
MATCH (s:Section {id: sid})
OPTIONAL MATCH (s)<-[:PART_OF]-(c:Chunk)
RETURN s.id AS id, s.type AS type, s.text AS text, s.documentName AS documentName,
       collect({id: c.id, text: c.text, embedded: c.text_embedding IS NOT NULL}) AS stored
"""

DELETE_SECTION_DERIVED = """
UNWIND $ids AS sid
MATCH (s:Section {id: sid})
OPTIONAL MATCH (s)<-[:PART_OF]-(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
WITH collect(DISTINCT c) + collect(DISTINCT p) AS doomed
UNWIND doomed AS n
WITH n WHERE n IS NOT NULL
DETACH DELETE n
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

# Delete-and-rebuild loses the slice marker labels, so re-apply them from the
# sections, which are the source of truth for slice membership.
REAPPLY_MARKERS = [
    "MATCH (s:DemoSection)<-[:PART_OF]-(c:Chunk) SET c:DemoChunk",
    "MATCH (s:DemoSection)-[:HAS_PARAGRAPH]->(p:Paragraph) SET p:DemoParagraph",
]

# Citations are denormalised, so the rebuilt nodes need them re-derived.
SHORT_SECTION = """{ReasonsForDecision: 'Reasons', AppealOrder: 'Order',
                    Catchword: 'Catchword', HeadNote: 'Headnote',
                    SummaryOfFacts: 'Facts'}"""

ENRICH = """
MATCH (n)-[:PART_OF|HAS_PARAGRAPH]-(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE (n:Chunk OR n:Paragraph) AND n.citation IS NULL
CALL (n, d) {
  WITH n, d, """ + SHORT_SECTION + """ AS shortName,
       d.code + ' ' + toString(toInteger(d.appealNum)) + '/' + right(d.year, 2) AS caseRef
  SET n.caseNumber   = d.caseNumber,
      n.caseRef      = caseRef,
      n.decisionDate = d.decisionDate,
      n.citation     = caseRef + ', ' + coalesce(shortName[n.type], n.type)
                       + coalesce(' ' + coalesce(n.paragraphRef, n.ref), '')
} IN TRANSACTIONS OF 2000 ROWS
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    changed_sections = 0
    lost_embeddings = 0
    recovered_tokens = 0
    scanned = 0
    started = time.time()

    try:
        with driver.session(database=database) as session:
            ids = [r["id"] for r in session.run(ALL_SECTION_IDS)]
            print(f"sections to scan: {len(ids):,}")

            for offset in range(0, len(ids), args.batch_size):
                batch_ids = ids[offset: offset + args.batch_size]
                sections = [dict(r) for r in session.run(FETCH_SECTIONS, ids=batch_ids)]

                to_rebuild, rebuild_ids = [], []
                for section in sections:
                    scanned += 1
                    stored = {c["id"]: c for c in section["stored"] if c["id"]}
                    fresh = chunk_section_paragraphs(section)
                    fresh_by_id = {c["id"]: c for c in fresh}

                    same = (set(stored) == set(fresh_by_id) and all(
                        stored[cid]["text"] == fresh_by_id[cid]["text"] for cid in fresh_by_id))
                    if same:
                        continue

                    changed_sections += 1
                    lost_embeddings += sum(1 for c in stored.values() if c["embedded"])
                    recovered_tokens += (sum(c["tokenCount"] for c in fresh)
                                         - sum(len(stored[c]["text"] or "") // 4
                                               for c in stored))
                    to_rebuild.append(section)
                    rebuild_ids.append(section["id"])

                if to_rebuild and not args.dry_run:
                    session.execute_write(
                        lambda tx: tx.run(DELETE_SECTION_DERIVED, ids=rebuild_ids).consume())

                    chunk_rows, paragraph_rows, covers = [], [], []
                    chunk_next, paragraph_next = [], []
                    for section in to_rebuild:
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
                            pids = [by_index[i] for i in chunk["paragraphIndexes"]
                                    if i in by_index]
                            if pids:
                                covers.append({"chunkId": chunk["id"], "paragraphIds": pids})

                    for query, rows, key in (
                        (WRITE_CHUNKS, chunk_rows, "rows"),
                        (WRITE_PARAGRAPHS, paragraph_rows, "rows"),
                        (WRITE_CHUNK_NEXT, chunk_next, "pairs"),
                        (WRITE_PARAGRAPH_NEXT, paragraph_next, "pairs"),
                        (WRITE_COVERS, covers, "rows"),
                    ):
                        if rows:
                            session.execute_write(
                                lambda tx, q=query, r=rows, k=key:
                                tx.run(q, **{k: r}).consume())

                if scanned % 10000 < args.batch_size:
                    elapsed = time.time() - started
                    print(f"  {scanned:,}/{len(ids):,}  changed={changed_sections:,}"
                          f"  staleEmbeddings={lost_embeddings:,}"
                          f"  {scanned/elapsed:.0f} sec/s", flush=True)

            print(f"\nscanned {scanned:,} sections in {(time.time()-started)/60:.1f} min")
            print(f"changed sections      : {changed_sections:,}")
            print(f"embeddings invalidated: {lost_embeddings:,}")
            print(f"text recovered (approx tokens): {recovered_tokens:,}")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            for query in REAPPLY_MARKERS:
                session.run(query).consume()
            session.run(ENRICH).consume()
            print("markers and citations re-applied")

            missing = session.run(
                "MATCH (c:Chunk) WHERE c.text_embedding IS NULL RETURN count(*) AS n"
            ).single()["n"]
            print(f"\nchunks now needing embedding: {missing:,}")
            print("next: python3 scripts/embed_corpus.py && python3 scripts/mark_canonical.py")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
