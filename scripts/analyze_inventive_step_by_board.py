#!/usr/bin/env python3
"""Q5 (PHARMA_GENERICS_PLAN.md), simplified: inventive step yes/no, by board.

    "Do outcome probabilities for a given ground differ measurably across
    the chemistry boards?"

Deliberately narrower than a full ground x IPC x board x period cross-tab:
one ground (Art. 56 EPC, inventive step), one signal (was it met -- yes/no),
counted per board. Every other ground (added subject-matter Art. 123(2),
sufficiency Art. 83, novelty Art. 54, ...) is ignored outright, not folded
in -- a decision that never reached inventive step (dismissed on novelty
first, say) contributes nothing here rather than being counted as a "no" by
default.

`requirementMetAll` (not `requirementMetAny`) is the "yes" signal: a decision
that found inventive step met for the main request but not an auxiliary
request is a real split outcome, and `requirementMetAll` is false for it --
correct, since it did not cleanly find the invention inventive.

Read-only. Pharma/chemistry board filter and IPC filter are both optional
and off by default -- pass `--board` / `--ipc-prefix` to scope to the
chemistry boards (3.3.01-3.3.10) or a pharma IPC class the way the plan's
worked example does.

Usage:
    python3 scripts/analyze_inventive_step_by_board.py
    python3 scripts/analyze_inventive_step_by_board.py --board 3.3.01 3.3.02 3.3.03 3.3.04 3.3.05 3.3.06 3.3.07 3.3.08 3.3.09 3.3.10
    python3 scripts/analyze_inventive_step_by_board.py --ipc-prefix A61K A61P C07D C07C C07K C12N
"""

import argparse
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

INVENTIVE_STEP = "Art_56_inventive_step"

FETCH = """
MATCH (d:Decision {isCanonical: true})-[:DECIDED_BY]->(b:Board)
MATCH (d)-[r:DECIDED_GROUND]->(:Ground {code: $groundCode})
WHERE r.requirementMetAll IS NOT NULL
  AND ($boards = [] OR b.code IN $boards)
  AND ($ipcPrefixes = [] OR EXISTS {
        (d)-[:CLASSIFIED_AS]->(i:IPCClass)
        WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix) })
RETURN b.code AS board, r.requirementMetAll AS met
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--board", nargs="*", default=[],
                        help="restrict to these Board.code values, e.g. 3.3.01 3.3.02")
    parser.add_argument("--ipc-prefix", nargs="*", default=[],
                        help="restrict to these IPC prefixes, e.g. A61K A61P")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            rows = session.run(FETCH, groundCode=INVENTIVE_STEP, boards=args.board,
                                ipcPrefixes=args.ipc_prefix).data()

            counts = defaultdict(lambda: {"yes": 0, "no": 0})
            for row in rows:
                counts[row["board"]]["yes" if row["met"] else "no"] += 1

            total_yes = sum(c["yes"] for c in counts.values())
            total_no = sum(c["no"] for c in counts.values())
            print(f"{len(rows):,} decisions with an inventive-step finding"
                  + (f" (boards: {args.board})" if args.board else "")
                  + (f" (IPC prefixes: {args.ipc_prefix})" if args.ipc_prefix else ""))
            print(f"overall: {total_yes:,} yes, {total_no:,} no "
                  f"({100.0*total_yes/(total_yes+total_no):.1f}% yes)\n")

            print(f"  {'board':10s} {'yes':>6s} {'no':>6s} {'total':>7s}  {'% yes':>6s}")
            for board in sorted(counts):
                c = counts[board]
                total = c["yes"] + c["no"]
                pct = 100.0 * c["yes"] / total if total else 0.0
                print(f"  {board:10s} {c['yes']:6,} {c['no']:6,} {total:7,}  {pct:5.1f}%")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
