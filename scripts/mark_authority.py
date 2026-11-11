#!/usr/bin/env python3
"""Phase E2 -- the authority-weight layer for EXAMINER_PLAN.md.

An examiner is not free to rely on whatever decision ranks highest by cosine
similarity. Only Enlarged Board decisions bind (Art. 112 EPC); ordinary board
decisions bind first-instance practice only insofar as they have been taken up
in the Guidelines. So retrieval has to rank by binding force, not only by
semantic proximity, or it hands an examiner authority they cannot use.

Signals, all already in the graph:

    code == 'G'          Enlarged Board -- binding
    distributionCode     the EPO's own internal circulation tier, and a strong
                         independent predictor of how often a decision is cited:

                             code    decisions   avg times cited
                             A           1,259             44.6
                             (none)      2,060             25.2
                             B             997             10.7
                             C           3,562              4.5
                             D           3,399              2.5

                         An 18x spread between A and D. 'A' is also 90%
                         headnoted and mostly OJ-published, so the tiers agree
                         with each other.
    :HeadNote/:Catchword the boards' own marker that a decision established
                         something (3,501 / 2,272 nodes)
    officialJournalRef   published in the Official Journal
    CITES in-degree      plus a recency-weighted count, because a decision cited
                         30 times since 2021 outranks one cited 30 times in the
                         1990s

Components are stored separately as well as combined, and every decision gets an
`authorityReason` string. A ranking an examiner cannot explain is not usable as
the basis for an official action, so "why is this first" has to be legible --
"Enlarged Board, cited 412x" rather than a bare score.

Usage:
    python3 scripts/mark_authority.py [--dry-run]
"""

import argparse
import os
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase

INDEXES = [
    "CREATE INDEX decision_authorityTier IF NOT EXISTS "
    "FOR (d:Decision) ON (d.authorityTier)",
    "CREATE INDEX decision_authorityWeight IF NOT EXISTS "
    "FOR (d:Decision) ON (d.authorityWeight)",
]

# Citation counts hang off :Case, since that is what CITES points at -- a
# decision and its language versions share one Case.
CITATION_COUNTS = """
MATCH (d:Decision) WHERE d.isCanonical
OPTIONAL MATCH (d)-[:LANGUAGE_VERSION_OF]->(c:Case)
CALL (d, c) {
  WITH d, c
  OPTIONAL MATCH (c)<-[:CITES]-(citing:Decision)
  WITH d, count(DISTINCT citing) AS total,
       count(DISTINCT CASE WHEN citing.decisionDate >= date($recentFrom)
                           THEN citing END) AS recent
  SET d.timesCited = total, d.timesCitedRecent = recent
} IN TRANSACTIONS OF 5000 ROWS
"""

# Tier plus a legible reason. Ordered most-binding first; the first matching
# branch wins.
TIERS = """
MATCH (d:Decision) WHERE d.isCanonical
CALL (d) {
  WITH d,
    EXISTS { (d)-[:HAS_SECTION]->(:HeadNote) } AS headnoted,
    EXISTS { (d)-[:HAS_SECTION]->(:Catchword) } AS catchworded,
    d.officialJournalRef IS NOT NULL AS oj
  WITH d, headnoted, catchworded, oj,
    CASE
      WHEN d.code = 'G' THEN 'binding'
      WHEN d.distributionCode = 'A' OR (oj AND headnoted) THEN 'landmark'
      WHEN d.distributionCode IN ['B', 'C'] OR headnoted OR catchworded
        THEN 'distributed'
      ELSE 'routine'
    END AS tier
  SET d.isHeadnoted = headnoted,
      d.isOjPublished = oj,
      d.authorityTier = tier,
      // Kept as a base score so the composite below stays inspectable: the tier
      // contribution and the citation contribution can always be separated.
      d.authorityTierScore =
        CASE tier WHEN 'binding' THEN 100 WHEN 'landmark' THEN 50
                  WHEN 'distributed' THEN 20 ELSE 0 END
} IN TRANSACTIONS OF 5000 ROWS
"""

# log10 so a decision cited 900 times does not swamp the tier signal entirely;
# each component is capped.
WEIGHT = """
MATCH (d:Decision) WHERE d.isCanonical
CALL (d) {
  WITH d,
    CASE WHEN coalesce(d.timesCited, 0) > 0
         THEN 10.0 * log10(1 + d.timesCited) ELSE 0.0 END AS citeScore,
    CASE WHEN coalesce(d.timesCitedRecent, 0) > 0
         THEN 10.0 * log10(1 + d.timesCitedRecent) ELSE 0.0 END AS recentScore
  SET d.authorityWeight = round(
        d.authorityTierScore
        + (CASE WHEN citeScore > 30 THEN 30 ELSE citeScore END)
        + (CASE WHEN recentScore > 20 THEN 20 ELSE recentScore END), 1),
      d.authorityReason =
        CASE d.authorityTier
          WHEN 'binding'     THEN 'Enlarged Board (binding, Art. 112 EPC)'
          WHEN 'landmark'    THEN 'OJ-published / distribution A'
          WHEN 'distributed' THEN 'headnoted or internally distributed'
          ELSE 'routine, no distribution marker' END
        + CASE WHEN coalesce(d.timesCited, 0) > 0
               THEN ', cited ' + toString(d.timesCited) + 'x'
                    + CASE WHEN coalesce(d.timesCitedRecent, 0) > 0
                           THEN ' (' + toString(d.timesCitedRecent) + ' since 2021)'
                           ELSE '' END
               ELSE ', never cited in corpus' END
} IN TRANSACTIONS OF 5000 ROWS
"""

VERIFY = """
MATCH (d:Decision) WHERE d.isCanonical
RETURN d.authorityTier AS tier, count(*) AS decisions,
       round(avg(d.timesCited), 1) AS avgCited,
       round(avg(d.authorityWeight), 1) AS avgWeight,
       max(d.authorityWeight) AS maxWeight
ORDER BY avgWeight DESC
"""

TOP = """
MATCH (d:Decision) WHERE d.isCanonical
RETURN d.caseNumber AS caseNumber, d.authorityTier AS tier,
       d.authorityWeight AS weight, d.authorityReason AS reason
ORDER BY d.authorityWeight DESC LIMIT 10
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--recent-from", default="2021-03-04",
                        help="start of the recency window (corpus ends 2026-03-04)")
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
            if args.dry_run:
                print("would compute citation counts, tiers and weights "
                      f"(recency window from {args.recent_from})")
                return

            for statement in INDEXES:
                session.run(statement).consume()

            started = time.time()
            session.run(CITATION_COUNTS, recentFrom=args.recent_from).consume()
            print(f"citation counts in {time.time()-started:.0f}s")

            started = time.time()
            session.run(TIERS).consume()
            session.run(WEIGHT).consume()
            print(f"tiers and weights in {time.time()-started:.0f}s")

            print("\nverify:")
            print(f"  {'tier':14s} {'decisions':>9s} {'avgCited':>9s} "
                  f"{'avgWeight':>10s} {'maxWeight':>10s}")
            for record in session.run(VERIFY):
                print(f"  {record['tier']:14s} {record['decisions']:9,} "
                      f"{record['avgCited']:9} {record['avgWeight']:10} "
                      f"{record['maxWeight']:10}")

            print("\nhighest authority in the corpus:")
            for record in session.run(TOP):
                print(f"  {record['caseNumber']:12s} {record['weight']:6}  "
                      f"{record['reason']}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
