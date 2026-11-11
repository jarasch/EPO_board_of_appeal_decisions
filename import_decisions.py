#!/usr/bin/env python3
"""Import the EPO Board of Appeal decisions XML export into Neo4j.

Usage:
    python3 import_decisions.py [--file PATH] [--limit N] [--batch-size N] [--dry-run]

Credentials are read from .env (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE).
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

from importer.parser import iter_decisions
from importer.loader import load_batch
from importer.schema import ensure_schema

DEFAULT_XML_PATH = os.path.join("data", "EPDecisions_March2026.xml")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", default=DEFAULT_XML_PATH, help="Path to the source XML file")
    p.add_argument("--limit", type=int, default=None, help="Only import the first N decisions")
    p.add_argument("--batch-size", type=int, default=200, help="Decisions per write transaction")
    p.add_argument("--log-every", type=int, default=2000, help="Progress log interval (decisions)")
    p.add_argument("--dry-run", action="store_true", help="Parse only, do not write to Neo4j")
    return p.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    if not os.path.exists(args.file):
        sys.exit(f"Source file not found: {args.file}")

    driver = None
    if not args.dry_run:
        uri = os.environ["NEO4J_URI"]
        user = os.environ["NEO4J_USER"]
        password = os.environ["NEO4J_PASSWORD"]
        database = os.environ.get("NEO4J_DATABASE", "neo4j")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        ensure_schema(driver, database)

    batch = []
    total = 0
    start = time.time()

    def flush():
        nonlocal batch
        if not batch:
            return
        if driver is not None:
            load_batch(driver, database, batch)
        batch = []

    try:
        for decision, related in iter_decisions(args.file, limit=args.limit):
            batch.append((decision, related))
            total += 1
            if len(batch) >= args.batch_size:
                flush()
            if total % args.log_every == 0:
                elapsed = time.time() - start
                print(f"  {total} decisions processed ({elapsed:.1f}s, {total/elapsed:.1f}/s)")
        flush()
    finally:
        if driver is not None:
            driver.close()

    elapsed = time.time() - start
    print(f"Done: {total} decisions in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
