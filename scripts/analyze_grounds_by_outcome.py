#!/usr/bin/env python3
"""Q5 (EXAMINER_PLAN.md) -- why are first-instance decisions set aside?

    "What are the most common reasons first-instance decisions are set
    aside, by ground and technical field? Must be split ex parte (examining
    division) vs inter partes (opposition division) -- the failure modes
    differ."

Read-only analytics: outcome (`Decision.setAside`) x ground disposition
(`DECIDED_GROUND`, `importer/grounds_analytics.py` for the polarity-aware
scoring) x ex parte/inter partes x optional IPC/board/period filters.

For each `:Decision` where the board set aside the decision under appeal,
counts which grounds' findings went against the first-instance result --
"against" meaning the ground it was appealed on on grounds of, in the sense
that ground's finding is what a board setting the decision aside actually
turned on, per `ground_against_patent`'s polarity-aware scoring.

This is a plain frequency count, not a rate -- there is no natural
denominator for "how many times could this ground have been the reason" the
way Q11's pro/anti split has one, so no Wilson interval applies here; the
count itself, split ex parte/inter partes, is the answer the plan asks for.

Usage:
    python3 scripts/analyze_grounds_by_outcome.py [--ipc-prefix A61K ...]
                                                   [--board 3.3.01 ...]
"""

import argparse
import os
import sys
from collections import Counter, defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.grounds_analytics import ground_against_patent  # noqa: E402

FETCH = """
MATCH (d:Decision)-[:DECIDED_BY]->(b:Board)
WHERE d.isCanonical AND d.setAside = true
  AND ($ipcPrefixes = [] OR EXISTS {
        (d)-[:CLASSIFIED_AS]->(i:IPCClass)
        WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix) })
  AND ($boards = [] OR b.code IN $boards)
WITH d, b
OPTIONAL MATCH (d)-[r:DECIDED_GROUND]->(g:Ground)
RETURN d.reference AS reference, d.isInterPartes AS isInterPartes,
       b.code AS board, toString(d.decisionDate) AS decisionDate,
       collect({code: g.code, label: g.label, polarity: g.polarity,
                metAll: r.requirementMetAll}) AS grounds
"""


def proceeding(is_inter_partes):
    return "inter partes (opposition)" if is_inter_partes else "ex parte (examining)"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ipc-prefix", nargs="*", default=[])
    parser.add_argument("--board", nargs="*", default=[])
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            records = session.run(FETCH, ipcPrefixes=args.ipc_prefix,
                                   boards=args.board).data()
            print(f"{len(records):,} set-aside decisions"
                  + (f" (IPC prefixes: {args.ipc_prefix})" if args.ipc_prefix else "")
                  + (f" (boards: {args.board})" if args.board else ""))

            # decision-level: how many set-aside decisions had >=1 ground
            # going against the first-instance result, vs none identifiable
            # (ground addressed with a mixed per-request finding, or no
            # DECIDED_GROUND link at all -- the corpus's own :Keyword
            # coverage is 84.2% of decisions per scripts/classify_grounds.py)
            reasons_by_proceeding = defaultdict(Counter)
            no_identifiable_ground = Counter()

            for record in records:
                proc = proceeding(record["isInterPartes"])
                against = [g for g in record["grounds"] if g["code"]
                           and ground_against_patent(g["polarity"], g["metAll"])]
                if not against:
                    no_identifiable_ground[proc] += 1
                    continue
                for g in against:
                    reasons_by_proceeding[proc][(g["code"], g["label"])] += 1

            for proc in sorted(reasons_by_proceeding):
                total_decisions = sum(1 for r in records if proceeding(r["isInterPartes"]) == proc)
                print(f"\n{proc} -- {total_decisions:,} set-aside decisions "
                      f"({no_identifiable_ground[proc]:,} with no ground identifiable "
                      "from :Keyword coverage):")
                print(f"  {'ground':32s} {'count':>6s}  {'% of set-aside decisions':>24s}")
                for (code, label), count in reasons_by_proceeding[proc].most_common(args.top):
                    pct = 100.0 * count / total_decisions if total_decisions else 0.0
                    print(f"  {label or code:32s} {count:6,}  {pct:23.1f}%")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
