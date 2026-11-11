#!/usr/bin/env python3
"""Embed :Chunk.text corpus-wide, committing incrementally.

Complements the `embed_chunks` MCP tool rather than replacing it: that tool is the
right thing for a document-scale lexical graph, but it does not survive a
corpus-scale run. Measured on 702,166 chunks:

  * it loads every matching row *with its text* into memory, embeds all of them,
    and only then writes -- peak RSS 6.4 GB, and no row is committed until the
    last embedding is computed;
  * it emits no progress, so the MCP harness aborts the call at its 1800s idle
    timeout (the server keeps working, but the caller is blind);
  * a failed API request drops its whole batch of 100 with no retry, and the
    call still returns `status: success`. That silently left 44,200 of 702,166
    chunks (6.3%) unembedded -- exactly 442 lost batches.

This script keeps the same embedding input and the same stored vector type, so
its output is interchangeable with the tool's:

    text   trim(coalesce(citation,'') + ' ' + coalesce(headingContext,'') + ' ' + text)
    write  SET c.text_embedding = vector($embedding, $dims, FLOAT32)   (CYPHER 25)

Differences that matter at scale: commit per API batch, bounded memory, retry
with backoff, over-limit texts truncated rather than failing their batch, and a
live rate/ETA. Resumability is implicit -- the selection predicate is
`text_embedding IS NULL`, so embedded rows drop out and re-running continues.

Usage:
    python3 scripts/embed_corpus.py                  # finish whatever is missing
    python3 scripts/embed_corpus.py --dry-run
    python3 scripts/embed_corpus.py --limit 5000     # bounded test
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import tiktoken
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# text-embedding-3-* accept 8192 tokens per input. Leave headroom rather than
# sitting on the limit: one 9,782-token chunk exists corpus-wide, and under the
# MCP tool it took its entire batch of 100 down with it.
MAX_INPUT_TOKENS = 8000

ENCODING = tiktoken.get_encoding("cl100k_base")

# Same composition the MCP tool builds from context_properties=['citation',
# 'headingContext'], so vectors from either path live in one index coherently.
FETCH = """
MATCH (c:Chunk)
WHERE c.text IS NOT NULL
  AND c.text_embedding IS NULL
  AND coalesce(c.active, true) = true
RETURN c.id AS id,
       trim(coalesce(c.citation, '') + ' ' + coalesce(c.headingContext, '')
            + ' ' + c.text) AS text,
       c.tokenCount AS tokenCount
LIMIT $limit
"""

COUNT_REMAINING = """
MATCH (c:Chunk)
WHERE c.text IS NOT NULL AND c.text_embedding IS NULL
  AND coalesce(c.active, true) = true
RETURN count(*) AS remaining
"""

WRITE = """
CYPHER 25
UNWIND $rows AS row
MATCH (c:Chunk {id: row.id})
SET c.text_embedding = vector(row.embedding, $dims, FLOAT32)
RETURN count(c) AS updated
"""


def truncate(text):
    """Cut to the model's input limit, reporting whether it was needed."""
    tokens = ENCODING.encode(text)
    if len(tokens) <= MAX_INPUT_TOKENS:
        return text, False
    return ENCODING.decode(tokens[:MAX_INPUT_TOKENS]), True


def embed_batch(client, model, rows, attempts=5):
    """Embed one batch, retrying with exponential backoff.

    The point of this function: a transient error must cost a retry, not 100
    silently dropped chunks.
    """
    texts, truncated = [], 0
    for row in rows:
        text, was_cut = truncate(row["text"])
        texts.append(text)
        truncated += was_cut

    last_error = None
    for attempt in range(attempts):
        try:
            response = client.embeddings.create(model=model, input=texts)
            vectors = [item.embedding for item in response.data]
            return [{"id": r["id"], "embedding": v} for r, v in zip(rows, vectors)], truncated, None
        except Exception as error:  # noqa: BLE001 -- any API failure is retryable here
            last_error = error
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
    return [], truncated, last_error


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", default=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))
    parser.add_argument("--batch-size", type=int, default=96, help="texts per API request")
    parser.add_argument("--page-size", type=int, default=960, help="rows fetched per round")
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--limit", type=int, help="stop after roughly N chunks")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    done = truncated_total = failed_batches = 0
    started = time.time()

    try:
        with driver.session(database=database) as session:
            remaining = session.run(COUNT_REMAINING).single()["remaining"]
            target = min(remaining, args.limit) if args.limit else remaining
            print(f"chunks to embed: {target:,} (of {remaining:,} missing)")
            print(f"model {args.model}, batch {args.batch_size}, parallel {args.parallel}")

            if args.dry_run:
                rows = [dict(r) for r in session.run(FETCH, limit=5)]
                for row in rows:
                    text, was_cut = truncate(row["text"])
                    print(f"  {row['id']}  {row['tokenCount']} tok"
                          f"{' TRUNCATED' if was_cut else ''}  {text[:70]!r}")
                print("\n-- dry run, nothing written --")
                return

            with ThreadPoolExecutor(max_workers=args.parallel) as pool:
                while done < target:
                    page = [dict(r) for r in session.run(FETCH, limit=args.page_size)]
                    if not page:
                        break

                    batches = [page[i: i + args.batch_size]
                               for i in range(0, len(page), args.batch_size)]
                    results = list(pool.map(
                        lambda b: embed_batch(client, args.model, b), batches))

                    for rows, truncated, error in results:
                        truncated_total += truncated
                        if error is not None:
                            failed_batches += 1
                            print(f"  batch failed after retries: {type(error).__name__}: "
                                  f"{str(error)[:120]}", flush=True)
                            continue
                        if not rows:
                            continue
                        dims = len(rows[0]["embedding"])
                        session.execute_write(
                            lambda tx, r=rows, d=dims:
                            tx.run(WRITE, rows=r, dims=d).consume())
                        done += len(rows)

                    elapsed = time.time() - started
                    rate = done / elapsed if elapsed else 0
                    eta = (target - done) / rate / 60 if rate else 0
                    print(f"  {done:,}/{target:,}  {rate:.0f}/s  ETA {eta:.1f} min"
                          f"  truncated={truncated_total}  failedBatches={failed_batches}",
                          flush=True)

            still = session.run(COUNT_REMAINING).single()["remaining"]
            print(f"\nembedded {done:,} in {(time.time()-started)/60:.1f} min")
            print(f"truncated {truncated_total}, failed batches {failed_batches}")
            print(f"still missing: {still:,}")
            if still and not args.limit:
                print("re-run to retry the remainder (selection is resumable)")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
