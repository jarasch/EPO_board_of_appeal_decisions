#!/usr/bin/env python3
"""Corpus-wide, industry-agnostic named-entity recognition via spaCy.

Not the LLM ontology-extraction path in DEMO_IMPLEMENTATION_PLAN.md Phase 2 /
PHARMA_GENERICS_PLAN.md P5 -- this is deliberately generic (people,
organisations, places, dates, ...), not a hand-designed legal/pharma schema,
and runs as local CPU inference rather than LLM calls, so the entire
canonical corpus is in scope, not a cost-bounded slice.

Writes, for every canonical, active Chunk:

    (:Chunk)-[:MENTIONS]->(:{LABEL}:__Entity__ {key, text, label, df, chunkCount})

`{LABEL}` is the entity's own type (ORG, PERSON, GPE, LAW, MISC, ...) --
kept as the primary label so a caller who cares can `MATCH (:ORG)` directly.
`:__Entity__` is a second, generic label every extracted entity carries
regardless of type, for code that wants "any entity" without enumerating
the label set (subgraph induction bridges, Bloom perspectives, ad hoc
Cypher). See `importer/entities.py` for the label normalisation (English's
18-label OntoNotes scheme vs German/French's 4-label PER/LOC/ORG/MISC
scheme) and the resolution key (case/diacritic folding + leading-article
stripping) that merges the same real-world entity across chunks, decisions
and languages.

`df` (document frequency -- distinct canonical decisions mentioning the
entity) and `chunkCount` are computed in a second pass over the finished
:__Entity__ layer once extraction completes, not accumulated in memory
during the run -- DEMO_IMPLEMENTATION_PLAN.md Phase 2.4 flags `entity.df` as
required, not optional, for the hub-suppression cut the existing
`retrieval/subgraph.py` induction already applies to the `:Keyword` layer.

Resumable: each processed Chunk is flagged `nerProcessed`, and the fetch
query only ever asks for chunks that aren't yet -- rerunning after an
interruption (or a `Ctrl-C`) picks back up rather than redoing work, which
matters here: a plain single-process run over the ~672k canonical chunks
takes on the order of 1-2 hours (measured throughput on this pipeline is
~130 texts/sec for English-length passages).

Usage:
    python3 scripts/extract_entities_spacy.py [--batch-size 500] [--limit N]
                                               [--dry-run] [--skip-df]
"""

import argparse
import os
import sys
import time
from collections import Counter

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spacy  # noqa: E402
from importer.entities import ALL_LABELS, entity_key, extract_entities, load_pipeline  # noqa: E402

SETUP = [
    "CREATE INDEX chunk_ner_processed IF NOT EXISTS FOR (c:Chunk) ON (c.nerProcessed)",
    "CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:__Entity__) REQUIRE e.key IS UNIQUE",
]

FETCH_BATCH = """
MATCH (c:Chunk)-[:PART_OF]->(s)<-[:HAS_SECTION]-(d:Decision)
WHERE d.isCanonical AND c.nerProcessed IS NULL
RETURN c.id AS chunkId, c.text AS text, d.lang AS lang
LIMIT $limit
"""

MARK_PROCESSED = """
UNWIND $chunkIds AS chunkId
MATCH (c:Chunk {id: chunkId})
SET c.nerProcessed = true
"""

# One MERGE per label so the label itself is a literal in the query text --
# never interpolated from model output -- rather than built dynamically from
# a value that ultimately comes from spaCy's output. `label` is validated
# against `importer.entities.ALL_LABELS` before this template is filled in.
WRITE_ENTITIES_AND_MENTIONS_TEMPLATE = """
UNWIND $rows AS row
MERGE (e:__Entity__:{label} {{key: row.entityKey}})
ON CREATE SET e.text = row.text, e.label = row.label
WITH e, row
MATCH (c:Chunk {{id: row.chunkId}})
MERGE (c)-[:MENTIONS]->(e)
"""

COMPUTE_DF = """
MATCH (e:__Entity__)
CALL (e) {
  WITH e
  MATCH (e)<-[:MENTIONS]-(c:Chunk)
  OPTIONAL MATCH (c)-[:PART_OF]->(s)<-[:HAS_SECTION]-(d:Decision)
  RETURN count(DISTINCT c) AS chunkCount, count(DISTINCT d) AS df
} IN TRANSACTIONS OF 200 ROWS
SET e.chunkCount = chunkCount, e.df = df
"""

VERIFY_COUNTS = """
MATCH (e:__Entity__)
RETURN e.label AS label, count(*) AS entities, sum(e.chunkCount) AS totalMentions
ORDER BY totalMentions DESC
"""

VERIFY_TOP = """
MATCH (e:__Entity__)
RETURN e.label AS label, e.text AS text, e.df AS df, e.chunkCount AS chunkCount
ORDER BY e.df DESC LIMIT 20
"""


def process_batch(nlp_by_lang, batch):
    """Run NER over one fetched batch, grouped by language pipeline.

    Returns entity+mentions rows and the list of chunk ids processed --
    every fetched chunk is marked processed even if it produced zero
    entities, so an empty chunk does not get re-fetched forever.
    """
    by_lang = {}
    for record in batch:
        by_lang.setdefault(record["lang"], []).append(record)

    rows = []
    for lang, records in by_lang.items():
        nlp = nlp_by_lang.get(lang)
        if nlp is None:
            continue  # no pipeline for this language -- corpus is en/de/fr only
        texts = [r["text"] or "" for r in records]
        for record, doc in zip(records, nlp.pipe(texts, batch_size=64)):
            for text, label in extract_entities(doc):
                rows.append({
                    "chunkId": record["chunkId"], "entityKey": entity_key(text, label),
                    "text": text, "label": label,
                })

    return rows, [r["chunkId"] for r in batch]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch-size", type=int, default=500,
                        help="chunks fetched/processed per round-trip")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after processing this many chunks (testing)")
    parser.add_argument("--skip-df", action="store_true",
                        help="skip the post-pass df/chunkCount computation")
    parser.add_argument("--dry-run", action="store_true",
                        help="run NER on one batch, print samples, write nothing")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    print("loading spaCy pipelines...")
    nlp_by_lang = {lang: load_pipeline(lang, spacy) for lang in ("en", "de", "fr")}
    for lang, nlp in nlp_by_lang.items():
        print(f"  {lang}: {nlp.meta['name']} {nlp.meta['version']} -- {nlp.pipe_names}")

    write_templates = {
        label: WRITE_ENTITIES_AND_MENTIONS_TEMPLATE.format(label=label)
        for label in ALL_LABELS
    }

    stats = Counter()
    started = time.time()
    total_processed = 0

    try:
        with driver.session(database=database) as session:
            if not args.dry_run:
                for statement in SETUP:
                    session.run(statement).consume()

            while True:
                limit = args.batch_size
                if args.limit is not None:
                    limit = min(limit, args.limit - total_processed)
                    if limit <= 0:
                        break

                batch = [dict(r) for r in session.run(FETCH_BATCH, limit=limit)]
                if not batch:
                    break

                rows, chunk_ids = process_batch(nlp_by_lang, batch)
                stats["chunks"] += len(chunk_ids)
                stats["mentions"] += len(rows)

                if args.dry_run:
                    print(f"\n-- sample batch: {len(chunk_ids)} chunks, "
                          f"{len(rows)} entity mentions --")
                    for row in rows[:30]:
                        print(f"  [{row['label']:10s}] {row['text']!r}  "
                              f"({row['chunkId']})")
                    print("\n-- dry run, nothing written --")
                    return

                rows_by_label = {}
                for row in rows:
                    rows_by_label.setdefault(row["label"], []).append(row)
                for label, label_rows in rows_by_label.items():
                    session.execute_write(
                        lambda tx, q=write_templates[label], r=label_rows:
                            tx.run(q, rows=r).consume())

                session.execute_write(
                    lambda tx, ids=chunk_ids: tx.run(MARK_PROCESSED, chunkIds=ids).consume())

                total_processed += len(chunk_ids)
                elapsed = time.time() - started
                rate = total_processed / elapsed if elapsed else 0
                print(f"  {total_processed:,} chunks, {stats['mentions']:,} mentions "
                      f"-- {rate:.1f} chunks/s, {elapsed/60:.1f} min elapsed", end="\r",
                      flush=True)

            print(f"\ndone: {stats['chunks']:,} chunks, {stats['mentions']:,} mentions "
                  f"in {(time.time()-started)/60:.1f} min")

            if not args.skip_df:
                print("computing entity.df / entity.chunkCount ...")
                started_df = time.time()
                session.run(COMPUTE_DF).consume()
                print(f"  done in {(time.time()-started_df)/60:.1f} min")

            print("\nverify -- by label:")
            for record in session.run(VERIFY_COUNTS):
                print(f"  {record['label']:12s} {record['entities']:8,} entities  "
                      f"{record['totalMentions'] or 0:10,} chunk mentions")

            if not args.skip_df:
                print("\nverify -- highest document frequency:")
                for record in session.run(VERIFY_TOP):
                    print(f"  [{record['label']:10s}] {record['text']:40s} "
                          f"df={record['df']:6} chunks={record['chunkCount']:6}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
