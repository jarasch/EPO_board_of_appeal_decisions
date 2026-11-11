#!/usr/bin/env python3
"""Q6 (PHARMA_GENERICS_PLAN.md) -- opponent/proprietor track record, and does
the number of opponents predict revocation?

    "What is the track record of specific opponents and proprietors, and
    does the number of opponents predict revocation? ... Needs: party
    resolution -- the raw :Party layer has surface duplicates ... and no
    corporate-group rollup ... Without this the question returns fragments."

Two read-only reports:

1. Per-organisation track record, rolled up through `:PART_OF_GROUP`
   (`scripts/resolve_parties.py`, P4) so a query for "Novartis" picks up its
   Hexal/Sandoz oppositions too -- reported separately as opponent and as
   proprietor, since a track record defending patents and a track record
   attacking them are different questions. Suppressed below MIN_SUPPORT.
2. Revocation rate by opponent count (1, 2, 3, 4, 5+), with a Wilson
   interval and the same support floor, from `importer/stats.py`.

Usage:
    python3 scripts/analyze_opponent_track_record.py [--top 20] [--min-support 5]
"""

import argparse
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.patentee_analytics import resolve_direction  # noqa: E402
from importer.stats import score_rate  # noqa: E402

# `dismissed` is not in this set on purpose -- like Q11, it has no direction
# of its own; `resolve_direction` below resolves it via `appellantRole`. An
# earlier version of this script scored only bare revoked/maintained
# outcomes and got 85-98% "revocation rates" -- implausible, and wrong: it
# was silently excluding the ~10,000 `dismissed` decisions (the single most
# common outcome in the corpus) from the denominator entirely.
TRACK_RECORD = """
MATCH (d:Decision {isCanonical: true, isInterPartes: true})
      -[rel:HAS_OPPONENT|HAS_APPLICANT]->(:Party)-[:IS_PARTY_OF]->(base:Organisation)
OPTIONAL MATCH (base)-[:PART_OF_GROUP*0..3]->(top:Organisation)
WHERE NOT (top)-[:PART_OF_GROUP]->()
WITH d, rel, coalesce(top, base) AS org
RETURN org.name AS org, type(rel) AS role, d.outcomeType AS outcomeType,
       d.appellantRole AS appellantRole
"""

OPPONENT_COUNT = """
MATCH (d:Decision {isCanonical: true, isInterPartes: true})
RETURN d.outcomeType AS outcomeType, d.appellantRole AS appellantRole,
       count { (d)-[:HAS_OPPONENT]->() } AS opponentCount
"""


def _bucket_count(n):
    return str(n) if n < 5 else "5+"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--min-support", type=int, default=5,
                        help="minimum decisions before an organisation's track record is shown")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            # --- 1. per-organisation track record ---------------------------
            # "Won"/"lost" is relative to the org's role in that decision, via
            # the same patentee-direction resolution Q11 uses: for an
            # opponent, `anti_patentee` (patent killed) is a win; for a
            # proprietor, `pro_patentee` (patent survived) is a win.
            records = session.run(TRACK_RECORD).data()
            by_org_role = defaultdict(lambda: {"won": 0, "lost": 0, "partial": 0, "excluded": 0})
            for record in records:
                direction = resolve_direction(record["outcomeType"], record["appellantRole"])
                key = (record["org"], record["role"])
                if direction == "partial":
                    by_org_role[key]["partial"] += 1
                elif direction == "excluded":
                    by_org_role[key]["excluded"] += 1
                elif (direction == "anti_patentee") == (record["role"] == "HAS_OPPONENT"):
                    by_org_role[key]["won"] += 1
                else:
                    by_org_role[key]["lost"] += 1

            for role, title in (("HAS_OPPONENT", "As opponent (attacking a patent)"),
                                ("HAS_APPLICANT", "As proprietor (defending a patent)")):
                rows = [(org, counts) for (org, r), counts in by_org_role.items()
                        if r == role and counts["won"] + counts["lost"] >= args.min_support]
                rows.sort(key=lambda item: -(item[1]["won"] + item[1]["lost"]))
                print(f"\n{title} -- top {args.top} by decision count "
                      f"(>= {args.min_support} scored decisions):")
                print(f"  {'organisation':45s} {'n':>5s} {'won':>6s} {'lost':>6s} "
                      f"{'win rate':>20s}")
                for org, counts in rows[:args.top]:
                    total = counts["won"] + counts["lost"]
                    rate, lo, hi = score_rate(counts["won"], total, min_support=1)
                    rate_str = f"{rate:.0%} [{lo:.0%}, {hi:.0%}]" if rate is not None else "n/a"
                    print(f"  {org[:45]:45s} {total:5,} {counts['won']:6,} "
                          f"{counts['lost']:6,}  {rate_str:>20s}")

            # --- 2. opponent count vs revocation -----------------------------
            # "Revoked" here means anti_patentee via the same appellantRole
            # -aware resolution as above -- a dismissed opponent appeal
            # against a patent already revoked below is a revocation in
            # substance, and scoring only the bare `revoked` outcome type
            # would miss most of them (see the note on TRACK_RECORD above).
            count_records = session.run(OPPONENT_COUNT).data()
            by_bucket = defaultdict(lambda: {"revoked": 0, "survived": 0})
            for record in count_records:
                direction = resolve_direction(record["outcomeType"], record["appellantRole"])
                if direction not in ("anti_patentee", "pro_patentee"):
                    continue
                bucket = _bucket_count(record["opponentCount"])
                by_bucket[bucket]["revoked" if direction == "anti_patentee"
                                  else "survived"] += 1

            print("\nRevocation rate by opponent count (partial/remitted/terminated/"
                  "inadmissible/unresolved-role excluded, per the same scoring as Q11):")
            print(f"  {'opponents':10s} {'n':>6s} {'revoked':>8s}  {'rate':>6s} {'95% CI':>15s}")
            for bucket in sorted(by_bucket, key=lambda b: (b == "5+", b)):
                counts = by_bucket[bucket]
                total = counts["revoked"] + counts["survived"]
                rate, lo, hi = score_rate(counts["revoked"], total)
                rate_str = f"{rate:.1%}" if rate is not None else "insufficient"
                ci_str = f"[{lo:.1%}, {hi:.1%}]" if rate is not None else "(need >=20)"
                print(f"  {bucket:10s} {total:6,} {counts['revoked']:8,}  "
                      f"{rate_str:>6s} {ci_str:>15s}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
