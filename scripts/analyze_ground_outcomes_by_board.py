#!/usr/bin/env python3
"""Q5 (PHARMA_GENERICS_PLAN.md), full version: per-ground outcome rates by board.

    "Do outcome probabilities for a given ground differ measurably across
    the chemistry boards (3.3.01-3.3.10)?"

`scripts/analyze_inventive_step_by_board.py` answers a deliberately narrowed
form of this -- one ground, raw percentages, no inference. That is not enough
to say *measurably*, which is the whole question: with ~300-800 decisions per
board a 6-point gap can be noise, and the plan requires the answer be reported
as "descriptive base rates with confidence intervals and explicit confounders".
So this script adds the three things needed to read the gaps:

1. **Wilson 95% intervals** per board, not bare percentages. Wilson rather than
   normal-approximation because several board x ground cells fall under 100.
2. **A heterogeneity test** -- Pearson chi-square across boards, with a
   permutation p-value (label-shuffling) rather than an asymptotic one, since
   sparse cells make the chi-square distribution a poor approximation and
   scipy is not a dependency of this repo.
3. **Confounder diagnostics**, because boards are specialised by subject
   matter: per-board IPC composition is printed, and `--ipc-prefix` /
   `--since` re-run the same test inside a single technology stratum and a
   common time window. A gap that survives both is a board effect; one that
   vanishes was composition.

Direction, not "met": the response variable is *did this ground work against
the patent surviving*, via `importer.grounds_analytics.ground_against_patent`,
so `met`-polarity grounds (inventive step) and `defect`-polarity grounds
(added subject-matter) point the same way and can be read side by side.

Not forum shopping: you cannot choose your board. These are forecasting base
rates, conditional on the case having been appealed at all.

Read-only.

Usage:
    python3 scripts/analyze_ground_outcomes_by_board.py
    python3 scripts/analyze_ground_outcomes_by_board.py --inter-partes
    python3 scripts/analyze_ground_outcomes_by_board.py --inter-partes --since 2010
    python3 scripts/analyze_ground_outcomes_by_board.py --ipc-prefix A61K A61P
"""

import argparse
import math
import os
import random
import sys
from collections import Counter, defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importer.grounds_analytics import ground_against_patent  # noqa: E402

CHEMISTRY_BOARDS = [f"3.3.{n:02d}" for n in range(1, 11)]

# The substantive attacks a generic actually runs, plus the procedural gate
# that decides whether the attack is even heard.
DEFAULT_GROUNDS = [
    "Art_56_inventive_step",
    "Art_54_novelty",
    "Art_83_sufficiency",
    "Art_123_2_added_matter",
    "Proc_late_filed",
]

FETCH = """
MATCH (d:Decision {isCanonical: true})-[:DECIDED_BY]->(b:Board)
MATCH (d)-[r:DECIDED_GROUND]->(g:Ground)
WHERE g.code IN $groundCodes
  AND r.requirementMetAll IS NOT NULL
  AND b.code IN $boards
  AND ($interPartesOnly = false OR d.isInterPartes = true)
  AND ($since IS NULL OR d.decisionDate >= date({year: $since, month: 1, day: 1}))
  AND ($ipcPrefixes = [] OR EXISTS {
        (d)-[:CLASSIFIED_AS]->(i:IPCClass)
        WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix) })
RETURN b.code AS board,
       g.code AS ground,
       g.label AS groundLabel,
       g.polarity AS polarity,
       r.requirementMetAll AS metAll,
       d.caseNumber AS caseNumber,
       [(d)-[:CLASSIFIED_AS]->(i:IPCClass) | left(i.symbol, 4)] AS ipcSubclasses
"""


def wilson(successes, total, z=1.96):
    """Wilson score interval -- holds up where the normal approximation does not."""
    if total == 0:
        return (0.0, 0.0)
    phat = successes / total
    denominator = 1 + z * z / total
    centre = (phat + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def chi_square(rows):
    """Pearson chi-square over a board x {against, for} table."""
    boards = sorted({board for board, _ in rows})
    against = Counter(board for board, flag in rows if flag)
    totals = Counter(board for board, _ in rows)
    grand_total = len(rows)
    grand_against = sum(1 for _, flag in rows if flag)
    if grand_against in (0, grand_total):
        return 0.0, len(boards) - 1
    p = grand_against / grand_total
    statistic = 0.0
    for board in boards:
        n = totals[board]
        for observed, expected in ((against[board], n * p), (n - against[board], n * (1 - p))):
            if expected > 0:
                statistic += (observed - expected) ** 2 / expected
    return statistic, len(boards) - 1


def permutation_p(rows, observed_statistic, iterations=10000, seed=0):
    """How often does reshuffling board labels beat the observed chi-square?

    Exchangeability under the null is exactly what we want to test: if the
    board carries no information, the labels are arbitrary.
    """
    rng = random.Random(seed)
    boards = [board for board, _ in rows]
    flags = [flag for _, flag in rows]
    hits = 0
    for _ in range(iterations):
        rng.shuffle(flags)
        statistic, _ = chi_square(list(zip(boards, flags)))
        if statistic >= observed_statistic:
            hits += 1
    # add-one smoothing: a permutation test cannot report p = 0
    return (hits + 1) / (iterations + 1)


def report_ground(ground_label, rows, ipc_by_board, show_ipc):
    """rows: list of (board, against_patent_bool)."""
    boards = sorted({board for board, _ in rows})
    against = Counter(board for board, flag in rows if flag)
    totals = Counter(board for board, _ in rows)
    grand_total = len(rows)
    grand_against = sum(1 for _, flag in rows if flag)

    print(f"\n{ground_label}")
    print(f"  n = {grand_total:,} decisions with a scorable finding; "
          f"pooled rate against the patent = {100.0 * grand_against / grand_total:.1f}%")
    header = f"  {'board':8s} {'n':>6s} {'against':>8s} {'rate':>7s}  {'95% CI (Wilson)':>18s}"
    if show_ipc:
        header += "   top IPC subclasses"
    print(header)
    for board in boards:
        n = totals[board]
        k = against[board]
        low, high = wilson(k, n)
        line = (f"  {board:8s} {n:6,} {k:8,} {100.0 * k / n:6.1f}%  "
                f"{100.0 * low:7.1f}% - {100.0 * high:5.1f}%")
        if show_ipc:
            top = ", ".join(f"{sym} {100.0 * share:.0f}%"
                            for sym, share in ipc_by_board.get(board, []))
            line += f"   {top}"
        print(line)

    statistic, df = chi_square(rows)
    p = permutation_p(rows, statistic)
    spread = max(against[b] / totals[b] for b in boards) - min(against[b] / totals[b] for b in boards)
    verdict = "differ measurably" if p < 0.05 else "NOT distinguishable from noise"
    print(f"  heterogeneity: chi2 = {statistic:.1f} (df {df}), permutation p = {p:.4f} "
          f"-> boards {verdict}")
    print(f"  spread: {100.0 * spread:.1f} points between the highest and lowest board")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--board", nargs="*", default=CHEMISTRY_BOARDS,
                        help="Board.code values (default: chemistry boards 3.3.01-3.3.10)")
    parser.add_argument("--ground", nargs="*", default=DEFAULT_GROUNDS,
                        help="Ground.code values to report")
    parser.add_argument("--ipc-prefix", nargs="*", default=[],
                        help="restrict to decisions carrying one of these IPC prefixes")
    parser.add_argument("--inter-partes", action="store_true",
                        help="opposition appeals only (drops ex parte examination appeals)")
    parser.add_argument("--since", type=int, default=None,
                        help="decision year floor, for a common observation window")
    parser.add_argument("--min-n", type=int, default=30,
                        help="drop board x ground cells below this many decisions")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            rows = session.run(
                FETCH,
                groundCodes=args.ground,
                boards=args.board,
                ipcPrefixes=args.ipc_prefix,
                interPartesOnly=args.inter_partes,
                since=args.since,
            ).data()
    finally:
        driver.close()

    scope = ["canonical decisions", f"boards {args.board[0]}-{args.board[-1]}"]
    if args.inter_partes:
        scope.append("inter partes only")
    if args.since:
        scope.append(f"decided {args.since} or later")
    if args.ipc_prefix:
        scope.append(f"IPC in {args.ipc_prefix}")
    print("scope: " + "; ".join(scope))
    print(f"{len(rows):,} (decision, ground) findings fetched")

    by_ground = defaultdict(list)
    labels = {}
    ipc_counts = defaultdict(Counter)
    ipc_totals = Counter()
    unscorable = 0
    for row in rows:
        flag = ground_against_patent(row["polarity"], row["metAll"])
        if flag is None:
            unscorable += 1
            continue
        by_ground[row["ground"]].append((row["board"], flag))
        labels[row["ground"]] = f"{row['groundLabel']} ({row['ground']})"
        for subclass in set(row["ipcSubclasses"] or []):
            ipc_counts[row["board"]][subclass] += 1
        ipc_totals[row["board"]] += 1

    if unscorable:
        print(f"{unscorable:,} findings unscorable (unrecognised polarity) -- excluded")

    ipc_by_board = {
        board: [(sym, n / ipc_totals[board]) for sym, n in counter.most_common(3)]
        for board, counter in ipc_counts.items()
    }

    for ground in args.ground:
        rows_for_ground = by_ground.get(ground)
        if not rows_for_ground:
            print(f"\n{ground}: no scorable findings in scope")
            continue
        totals = Counter(board for board, _ in rows_for_ground)
        kept = [(board, flag) for board, flag in rows_for_ground
                if totals[board] >= args.min_n]
        dropped = sorted(b for b in totals if totals[b] < args.min_n)
        if dropped:
            print(f"\n(dropping boards under n={args.min_n} for "
                  f"{labels[ground]}: {', '.join(dropped)})")
        if kept:
            report_ground(labels[ground], kept, ipc_by_board,
                          show_ipc=(ground == args.ground[0]))


if __name__ == "__main__":
    main()
