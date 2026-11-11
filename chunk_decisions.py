#!/usr/bin/env python3
"""Chunk Section text into :Chunk nodes for embedding/search.

Splits each Section's text (headnote, catchword, summaryOfFacts,
reasonsForDecision, appealOrder, abstractText -- each its own (:Section) node,
see importer/parser.py's SECTION_DEFS) into token-window chunks and writes
them as (:Chunk)-[:PART_OF]->(:Section), chained in order via
(:Chunk)-[:NEXT]->(:Chunk) -- the same node shape the neo4j-lexical-graph MCP
server's own pipeline writes, so its embed_chunks tool can be run against them
directly afterwards (node_label="Chunk", defaults otherwise).

Usage:
    python3 chunk_decisions.py [--batch-size N] [--chunk-size N] [--chunk-overlap N] [--dry-run]

Credentials are read from .env (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE).
"""

import argparse
import os
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

from importer.chunker import chunk_section
from importer.schema import ensure_schema

FETCH_QUERY = """
MATCH (s:Section)
RETURN s.id AS id, s.type AS type, s.text AS text, s.documentName AS documentName
ORDER BY s.id
SKIP $skip LIMIT $batchSize
"""

WRITE_QUERY = """
UNWIND $rows AS row
MATCH (s:Section {id: row.sectionId})
MERGE (c:Chunk {id: row.id})
SET c.text = row.text,
    c.index = row.index,
    c.tokenCount = row.tokenCount,
    c.type = row.type,
    c.documentName = row.documentName,
    c.sectionContext = row.sectionContext,
    c.active = true
MERGE (c)-[:PART_OF]->(s)
"""

NEXT_QUERY = """
UNWIND $pairs AS pair
MATCH (a:Chunk {id: pair.from}), (b:Chunk {id: pair.to})
MERGE (a)-[:NEXT]->(b)
"""


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch-size", type=int, default=1000, help="Sections fetched/chunked per round")
    p.add_argument("--chunk-size", type=int, default=500, help="Target tokens per chunk")
    p.add_argument("--chunk-overlap", type=int, default=50, help="Token overlap between chunks")
    p.add_argument("--dry-run", action="store_true", help="Chunk only, do not write to Neo4j")
    return p.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    ensure_schema(driver, database)

    skip = 0
    total_sections = 0
    total_chunks = 0
    start = time.time()

    try:
        with driver.session(database=database) as session:
            while True:
                records = session.run(FETCH_QUERY, skip=skip, batchSize=args.batch_size).data()
                if not records:
                    break

                rows = []
                pairs = []
                for record in records:
                    section_rows = chunk_section(record, args.chunk_size, args.chunk_overlap)
                    rows.extend(section_rows)
                    pairs.extend(
                        {"from": a["id"], "to": b["id"]}
                        for a, b in zip(section_rows, section_rows[1:])
                    )

                if not args.dry_run and rows:
                    session.run(WRITE_QUERY, rows=rows)
                    if pairs:
                        session.run(NEXT_QUERY, pairs=pairs)

                skip += len(records)
                total_sections += len(records)
                total_chunks += len(rows)
                elapsed = time.time() - start
                print(f"  {total_sections} sections chunked, {total_chunks} chunks "
                      f"({elapsed:.1f}s, {total_sections/elapsed:.1f} sections/s)")
    finally:
        driver.close()

    elapsed = time.time() - start
    print(f"Done: {total_sections} sections, {total_chunks} chunks in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
