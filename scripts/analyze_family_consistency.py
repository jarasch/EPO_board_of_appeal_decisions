#!/usr/bin/env python3
"""Q8 (EXAMINER_PLAN.md) -- am I consistent with how comparable cases were treated?

    "Am I consistent with how comparable cases have been treated -- same
    claim type, same doctrine, same technical field, and in particular the
    same family (parent/divisional)? ... Caveat: family linkage via
    application number alone is incomplete -- full family resolution needs
    EPO OPS."

That caveat is not a rounding error here -- it is disqualifying for the
literal question. EPO divisional applications get a fresh application
number (not derived from the parent's), and `:Application` carries only
`{number, country, key}`, no priority or parent-application field. There is
therefore no field in this corpus that links a divisional to its parent, and
this script does not pretend otherwise.

What IS in the corpus and checkable: 2,085 `:Application` nodes have more
than one canonical `:Decision` attached via `CONCERNS_APPLICATION` -- the
same application litigated more than once (a remittal followed by a second
appeal, a second opposition, a petition for review). That is a narrower,
honest version of "comparable case": not a different member of a patent
family, but the *same* application, decided more than once. A ground
decided one way in one round and the opposite way in another, on the same
application, is a real consistency signal this corpus can actually support.

True parent/divisional family consistency (the question as literally asked)
remains blocked on EPO OPS, per the plan.

One more honest limitation: a flipped finding on the same application is a
*candidate* for review, not proof of inconsistency. Claims are routinely
amended between rounds (e.g. after a remittal) -- a ground found "not met"
against the original claims and "met" against amended claims is amendment
working as intended, not a contradiction. This script has no claim-text
comparison, so it cannot tell the two apart; it surfaces every flip for a
human to check, deliberately over- rather than under-inclusive.

Usage:
    python3 scripts/analyze_family_consistency.py [--show 20]
"""

import argparse
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

FETCH = """
MATCH (a:Application)<-[:CONCERNS_APPLICATION]-(d:Decision {isCanonical: true})
WITH a, collect(d) AS decisions
WHERE size(decisions) > 1
UNWIND decisions AS d
OPTIONAL MATCH (d)-[r:DECIDED_GROUND]->(g:Ground)
RETURN a.number AS application, d.reference AS reference,
       toString(d.decisionDate) AS decisionDate,
       g.code AS groundCode, g.label AS groundLabel, r.requirementMetAll AS metAll
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--show", type=int, default=20,
                        help="how many contradictions to print in detail")
    args = parser.parse_args()

    load_dotenv()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            records = session.run(FETCH).data()

            # (application, groundCode) -> {reference: (metAll, decisionDate, label)}
            findings = defaultdict(dict)
            applications = set()
            for record in records:
                applications.add(record["application"])
                if record["groundCode"] is None or record["metAll"] is None:
                    continue
                key = (record["application"], record["groundCode"])
                findings[key][record["reference"]] = (
                    record["metAll"], record["decisionDate"], record["groundLabel"])

            comparisons = 0
            contradictions = []
            for (application, ground_code), by_decision in findings.items():
                if len(by_decision) < 2:
                    continue
                comparisons += 1
                values = {v[0] for v in by_decision.values()}
                if len(values) > 1:
                    contradictions.append((application, ground_code, by_decision))

            print(f"{len(applications):,} applications with more than one canonical decision")
            print(f"{comparisons:,} (application, ground) pairs with a re-decided finding "
                  "in at least 2 of those decisions")
            print(f"{len(contradictions):,} flipped -- same application, same ground, "
                  "opposite finding across decisions (candidates for review, not proven "
                  "inconsistencies -- claims may have been legitimately amended between "
                  "rounds; this script does not compare claim text)")

            print(f"\nFirst {min(args.show, len(contradictions))} contradictions:")
            for application, ground_code, by_decision in contradictions[:args.show]:
                label = next(v[2] for v in by_decision.values() if v[2])
                print(f"\n  application {application}  --  {label} ({ground_code})")
                for reference, (met_all, date, _) in sorted(by_decision.items(),
                                                              key=lambda kv: kv[1][1] or ""):
                    print(f"    {reference:15s} {date or 'unknown date':12s} "
                          f"requirementMetAll={met_all}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
