#!/usr/bin/env python3
"""Q11 -- which boards decide in favour of the patentee? (PHARMA_GENERICS_PLAN.md)

Read-only analytics, not a graph write: this question is exactly the one the
plan flags as most likely to be quoted out of context ("a board-level
'favours patentees' number travels further than its caveats do"), so the
result is not persisted as a queryable Decision property -- persisting it
would put one number one Cypher query away from being lifted out of the
per-stratum, interval-qualified table it is only meaningful inside.

Reports, per board, PER APPELLANT-ROLE STRATUM (never pooled across roles --
see `importer/patentee_analytics.py`):

    pro-patentee rate = pro_patentee / (pro_patentee + anti_patentee)

with a 95% Wilson interval and a hard support floor (MIN_SUPPORT=20): below
that, the cell prints "insufficient data", not a number. `partial` and
`excluded` (remitted/terminated/inadmissible/unresolved-dismissal) are
reported as raw counts alongside the rate, never folded into either side.

Robustness check: splits at the RPBA 2020 regime break (2020-01-01) and
reports whether each board's ranking-by-rate is stable across the split. An
unstable ranking means the pooled figure describes a world that no longer
exists, and is reported as such rather than smoothed over.

Usage:
    python3 scripts/analyze_patentee_outcomes.py [--ipc-prefix A61K A61P ...]
"""

import argparse
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.patentee_analytics import (  # noqa: E402
    MIN_SUPPORT, REGIME_BREAK, resolve_direction, score_rate,
)

FETCH = """
MATCH (d:Decision)-[:DECIDED_BY]->(b:Board)
WHERE d.isCanonical AND d.isInterPartes
  AND ($ipcPrefixes = [] OR EXISTS {
        (d)-[:CLASSIFIED_AS]->(i:IPCClass)
        WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix) })
RETURN b.code AS board, d.outcomeType AS outcomeType,
       d.appellantRole AS appellantRole, toString(d.decisionDate) AS decisionDate
"""

STRATA = ("opponent", "proprietor", "both")


def aggregate(records):
    """(board, role) -> Counter(pro/partial/anti/excluded)."""
    cells = defaultdict(lambda: {"pro": 0, "partial": 0, "anti": 0, "excluded": 0})
    for record in records:
        role = record["appellantRole"]
        if role not in STRATA:
            continue  # unknown -- no stratum to score it into, not a silent guess
        direction = resolve_direction(record["outcomeType"], role)
        key = (record["board"], role)
        if direction == "pro_patentee":
            cells[key]["pro"] += 1
        elif direction == "anti_patentee":
            cells[key]["anti"] += 1
        elif direction == "partial":
            cells[key]["partial"] += 1
        else:
            cells[key]["excluded"] += 1
    return cells


def print_table(cells, title):
    print(f"\n{title}")
    print(f"  {'board':10s} {'role':11s} {'pro':>5s} {'partial':>8s} {'anti':>5s} "
          f"{'excl':>5s}  {'rate':>6s} {'95% CI':>15s}")
    for (board, role), counts in sorted(cells.items()):
        rate, lo, hi = score_rate(counts["pro"], counts["pro"] + counts["anti"])
        rate_str = f"{rate:.1%}" if rate is not None else "insufficient"
        ci_str = f"[{lo:.1%}, {hi:.1%}]" if rate is not None else f"(need >={MIN_SUPPORT})"
        print(f"  {board:10s} {role:11s} {counts['pro']:5d} {counts['partial']:8d} "
              f"{counts['anti']:5d} {counts['excluded']:5d}  {rate_str:>6s} {ci_str:>15s}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ipc-prefix", nargs="*", default=[],
                        help="hold technical field roughly constant, e.g. A61K A61P")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            records = session.run(FETCH, ipcPrefixes=args.ipc_prefix).data()
            print(f"{len(records):,} canonical inter partes decisions"
                  + (f" (IPC prefixes: {args.ipc_prefix})" if args.ipc_prefix else ""))

            pooled = aggregate(records)
            print_table(pooled, "Pooled, whole period:")

            pre = aggregate(r for r in records if r["decisionDate"] and r["decisionDate"] < REGIME_BREAK)
            post = aggregate(r for r in records if r["decisionDate"] and r["decisionDate"] >= REGIME_BREAK)
            print_table(pre, f"Pre-{REGIME_BREAK} (before RPBA 2020):")
            print_table(post, f"Post-{REGIME_BREAK} (after RPBA 2020):")

            print("\nRegime-break robustness check (ranking by pro-patentee rate, "
                  "opponent-appellant stratum -- the largest and most comparable one):")
            pre_ranked = _ranked(pre, "opponent")
            post_ranked = _ranked(post, "opponent")
            common = [b for b in pre_ranked if b in post_ranked]
            if len(common) < 2:
                print("  Not enough boards with sufficient support in both sub-periods "
                      "to compare a ranking.")
            else:
                pre_order = [b for b in pre_ranked if b in common]
                post_order = [b for b in post_ranked if b in common]
                stable = pre_order == post_order
                print(f"  pre-2020 order:  {pre_order}")
                print(f"  post-2020 order: {post_order}")
                if stable:
                    print("  STABLE -- the pooled ranking is not an artefact of the regime "
                          "break; reporting it is defensible.")
                else:
                    print("  UNSTABLE -- the ranking flips across the regime break. Per the "
                          "plan: report this instability instead of the pooled number, which "
                          "would describe a world that no longer exists.")
    finally:
        driver.close()


def _ranked(cells, role):
    """Boards with sufficient support in this stratum, ordered by rate desc."""
    scored = []
    for (board, r), counts in cells.items():
        if r != role:
            continue
        rate, _, _ = score_rate(counts["pro"], counts["pro"] + counts["anti"])
        if rate is not None:
            scored.append((board, rate))
    scored.sort(key=lambda item: -item[1])
    return [board for board, _ in scored]


if __name__ == "__main__":
    main()
