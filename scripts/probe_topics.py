#!/usr/bin/env python3
"""Run and inspect the Phase 4 + 5 spine (retrieval -> induction -> Leiden).

Step 2 of the build order: prove the hardest stage works against the *existing*
:Keyword layer, before spending any entity-extraction budget. Phase 3 (LLM
question parsing) and Phase 6 (summarisation) are not wired in yet, so the
intent is assembled from the flags below.

    python3 scripts/probe_topics.py "how have the boards applied COMVIK to machine learning claims"
    python3 scripts/probe_topics.py "..." --tests COMVIK "technical effect" --date-from 2018-01-01
    python3 scripts/probe_topics.py "..." --sweep      # grid over the induction/Leiden knobs
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval import communities as com
from retrieval import subgraph as sub
from retrieval.db import session
from retrieval.intent import from_question
from retrieval.seed_retrieval import retrieve_seeds

SWEEP_GRID = [
    (df_fraction, min_weight, gamma)
    for df_fraction in (0.02, 0.05, 0.10)
    for min_weight in (1.0, 2.0, 3.0)
    for gamma in (1.0, 1.5, 2.0)
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question")
    parser.add_argument("--issues", nargs="*", default=[], help="Legal issues (entity channel)")
    parser.add_argument("--tests", nargs="*", default=[], help="Named doctrines/tests")
    parser.add_argument("--cases", nargs="*", default=[], help="Cited decisions, e.g. 'T 641/00'")
    parser.add_argument("--terms", nargs="*", default=[], help="Technical terms (lexical channel)")
    parser.add_argument("--articles", nargs="*", default=[], help="Canonical Article codes")
    parser.add_argument("--ipc", nargs="*", default=[], help="IPC prefixes")
    parser.add_argument("--date-from", default=None)
    parser.add_argument("--date-to", default=None)
    parser.add_argument("--channel-limit", type=int, default=200)
    parser.add_argument("--seed-limit", type=int, default=400)
    # One source of truth for the tuned values: the config dataclasses.
    parser.add_argument("--df-fraction", type=float,
                        default=sub.InductionConfig.df_max_fraction)
    parser.add_argument("--min-weight", type=float,
                        default=sub.InductionConfig.min_weight)
    parser.add_argument("--gamma", type=float, default=com.LeidenConfig.gamma)
    parser.add_argument("--no-expand", action="store_true", help="Seeds only, no expansion")
    parser.add_argument("--sweep", action="store_true",
                        help="Grid over df-fraction x min-weight x gamma")
    return parser.parse_args()


def build_intent(args):
    return from_question(
        args.question,
        legal_issues=args.issues,
        legal_tests=args.tests,
        named_cases=args.cases,
        technical_terms=args.terms,
        articles=args.articles,
        ipc_prefixes=args.ipc,
        date_from=args.date_from,
        date_to=args.date_to,
    )


def run_once(open_session, seeds, args, df_fraction, min_weight, gamma):
    config = sub.InductionConfig(df_max_fraction=df_fraction, min_weight=min_weight)
    induced = sub.induce(open_session, [s["reference"] for s in seeds], config,
                         expand_seeds=not args.no_expand)
    leiden = com.LeidenConfig(gamma=gamma)
    result = com.detect(open_session, induced, leiden)
    return induced, result, com.check_exit_criteria(result, leiden)


def print_sweep(open_session, seeds, args):
    print(f"\n{'df':>5} {'minW':>5} {'gamma':>5} | {'nodes':>6} {'edges':>6} {'iso':>5} "
          f"{'deg':>5} | {'comm':>5} {'>=5':>4} {'max%':>5} {'mod':>7} | ok")
    print("-" * 84)
    for df_fraction, min_weight, gamma in SWEEP_GRID:
        try:
            induced, result, criteria = run_once(
                open_session, seeds, args, df_fraction, min_weight, gamma)
        except sub.SubgraphTooLarge as error:
            print(f"{df_fraction:>5} {min_weight:>5} {gamma:>5} | {error}")
            continue
        stats = sub.describe(induced)
        leiden_stats = result["stats"] or {}
        print(f"{df_fraction:>5} {min_weight:>5} {gamma:>5} | "
              f"{stats['nodes']:>6} {stats['edges']:>6} {stats['isolated']:>5} "
              f"{stats['avg_degree']:>5} | "
              f"{leiden_stats.get('communityCount', 0):>5} "
              f"{criteria['usable_communities']:>4} "
              f"{criteria['largest_share'] * 100:>4.0f}% "
              f"{leiden_stats.get('modularity', 0):>7.3f} | "
              f"{'yes' if criteria['ok'] else 'no'}")


def print_explain(open_session, seeds, channels, args):
    induced, result, criteria = run_once(
        open_session, seeds, args, args.df_fraction, args.min_weight, args.gamma)
    stats = sub.describe(induced)

    print("\n[4.1] channels")
    for name, references in channels.items():
        print(f"  {name:11s} {len(references):>4} decisions")
    print(f"\n[4.2] fused seeds: {len(seeds)}")
    multi = [s for s in seeds if len(s["channels"]) > 1]
    print(f"  found by >1 channel: {len(multi)}")
    for seed in seeds[:5]:
        print(f"    {seed['reference']}  {'+'.join(seed['channels'])}")

    print(f"\n[4.3] induced subgraph (df_max={stats['df_max']}, "
          f"min_weight={args.min_weight})")
    for key in ("nodes", "expanded", "edges", "isolated", "avg_degree", "max_degree"):
        print(f"  {key:12s} {stats[key]}")

    leiden_stats = result["stats"] or {}
    print(f"\n[5] Leiden (gamma={args.gamma}, seed=42, concurrency=1)")
    if not leiden_stats:
        print(f"  {result.get('note')}")
        return
    print(f"  projected    {leiden_stats['projected']['nodes']} nodes / "
          f"{leiden_stats['projected']['edges']} rels")
    print(f"  communities  {leiden_stats['communityCount']} "
          f"({criteria['usable_communities']} with >= 5 members)")
    print(f"  modularity   {leiden_stats['modularity']:.3f}  "
          f"levels {leiden_stats['ranLevels']}")
    print(f"  exit criteria: {'PASS' if criteria['ok'] else 'FAIL -- ' + criteria['reason']}")

    identity = com.topic_identity(open_session, induced, result["communities"])
    print(f"\n[5] topics ({len(result['communities'])} usable, "
          f"{len(result['outliers'])} outlier communities)")
    for community in result["communities"]:
        labels = identity.get(community["id"], [])[:5]
        print(f"\n  community {community['id']} -- {community['size']} decisions")
        for item in labels:
            print(f"    {item['lift']:5.1f}x  {item['count']:>3}/{item['subgraphCount']:<4} "
                  f"{item['source']:14s} {str(item['name'])[:70]}")
        cases = [m["caseRef"] for m in community["members"][:6]]
        print(f"    members: {', '.join(cases)}"
              f"{' ...' if community['size'] > 6 else ''}")


def main():
    args = parse_args()
    intent = build_intent(args)

    with session() as open_session:
        seeds, channels = retrieve_seeds(open_session, intent,
                                         args.channel_limit, args.seed_limit)
        if not seeds:
            print("No seeds retrieved -- check the question and filters.")
            return
        if args.sweep:
            print_sweep(open_session, seeds, args)
        else:
            print_explain(open_session, seeds, channels, args)


if __name__ == "__main__":
    main()
