#!/usr/bin/env python3
"""Party resolution -- PHARMA_GENERICS_PLAN.md Phase P4.

Needed by Q6 (opponent/proprietor track record, straw-man detection): the raw
`:Party` layer is 36,228 nodes for what is a much smaller number of real
organisations -- BASF alone has 180+ distinct name strings. Without
resolving these, a "track record" query returns fragments of the same
opponent's history rather than the history.

Builds, above `:Party`:

    (:Party)-[:IS_PARTY_OF {isMultiParty}]->(:Organisation {key, name,
        decisionCount, partyCount, tradingAs, isStrawMan, groupReviewNote})
    (:Organisation)-[:PART_OF_GROUP {evidence, note}]->(:Organisation)   -- corporate parent

Two independent resolution steps, `importer/parties.py`:

1. String normalisation (`normalise`) collapses same-entity spelling variants
   (numbering markers, city qualifiers, legal-form spelling, case, procedural
   annotations) into one grouping key. Mechanical and corpus-wide.
2. `CORPORATE_GROUPS` rolls up *different* legal entities that belong to one
   corporate family (Hexal -> Novartis, ratiopharm -> Teva). Deliberately a
   small, evidence-tagged table, not the full "~100 organisations" the plan
   calls for -- that needs hand-curated M&A research this script does not
   fabricate. Ambiguous cases (Actavis) are flagged `groupReviewNote` with no
   parent asserted rather than guessed.

Query pattern for a rolled-up track record:

    MATCH (o:Organisation)-[:PART_OF_GROUP*0..]->(top:Organisation)
    WHERE NOT (top)-[:PART_OF_GROUP]->()
    ...

Usage:
    python3 scripts/resolve_parties.py [--dry-run] [--sample 20]
"""

import argparse
import os
import sys
import time
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.parties import normalise, resolve_group, is_strawman  # noqa: E402

SETUP = [
    "CREATE CONSTRAINT organisation_key IF NOT EXISTS "
    "FOR (o:Organisation) REQUIRE o.key IS UNIQUE",
]

FETCH_PARTIES = """
MATCH (p:Party)
RETURN p.name AS name,
       count { (p)<-[:HAS_OPPONENT]-() } + count { (p)<-[:HAS_APPLICANT]-() } AS decisions
"""

WRITE_ORGS = """
UNWIND $rows AS row
MERGE (o:Organisation {key: row.key})
SET o.name = row.name,
    o.decisionCount = row.decisionCount,
    o.partyCount = row.partyCount,
    o.tradingAs = row.tradingAs,
    o.isStrawMan = row.isStrawMan,
    o.groupReviewNote = row.groupReviewNote
"""

WRITE_PARTY_LINKS = """
UNWIND $rows AS row
MATCH (p:Party {name: row.partyName})
MATCH (o:Organisation {key: row.orgKey})
MERGE (p)-[r:IS_PARTY_OF]->(o)
SET r.isMultiParty = row.isMultiParty
"""

# group_rows/chain_rows are always fully recomputed from the current
# CORPORATE_GROUPS table, so deleting every existing edge before rewriting
# is correct, not lossy -- and necessary: WRITE_GROUP_PARENTS only ever
# MERGEs, so a rule that is later tightened (e.g. the isMultiParty guard
# added below) would otherwise leave its old, now-wrong edges in the graph
# forever. Found by exactly that: a stale PART_OF_GROUP edge from a
# multi-party string into the Teva rollup survived a rule change until this
# was added.
DELETE_STALE_GROUPS = "MATCH ()-[r:PART_OF_GROUP]->() DELETE r"

WRITE_GROUP_PARENTS = """
UNWIND $rows AS row
MERGE (parent:Organisation {key: row.parentKey})
ON CREATE SET parent.name = row.parentName, parent.decisionCount = 0, parent.partyCount = 0
WITH parent, row
MATCH (child:Organisation {key: row.childKey})
MERGE (child)-[r:PART_OF_GROUP]->(parent)
SET r.evidence = row.evidence, r.note = row.note
"""

VERIFY_TOP_ORGS = """
MATCH (o:Organisation)
RETURN o.name AS name, o.key AS key, o.partyCount AS parties, o.decisionCount AS decisions
ORDER BY decisions DESC LIMIT 20
"""

VERIFY_GROUPS = """
MATCH (child:Organisation)-[r:PART_OF_GROUP]->(parent:Organisation)
RETURN parent.name AS parent, r.evidence AS evidence,
       collect(child.name) AS children, sum(child.decisionCount) AS decisions
ORDER BY decisions DESC
"""

VERIFY_STRAWMAN = """
MATCH (o:Organisation {isStrawMan: true})
RETURN o.name AS name, o.decisionCount AS decisions
ORDER BY decisions DESC
"""

VERIFY_NEEDS_REVIEW = """
MATCH (o:Organisation) WHERE o.groupReviewNote IS NOT NULL
RETURN o.name AS name, o.decisionCount AS decisions
ORDER BY decisions DESC
"""


def build_rows(party_records):
    groups = defaultdict(list)
    multi_party_count = 0

    for record in party_records:
        name = record["name"]
        weight = record["decisions"] or 0
        resolved = normalise(name)
        if resolved["isMultiParty"]:
            multi_party_count += 1
        groups[resolved["key"]].append({
            "partyName": name,
            "weight": weight,
            "cleanName": resolved["cleanName"],
            "tradingAs": resolved["tradingAs"],
            "isWithdrawn": resolved["isWithdrawn"],
            "isFormerOpponent": resolved["isFormerOpponent"],
            "isMultiParty": resolved["isMultiParty"],
        })

    org_rows, party_link_rows = [], []
    org_by_key = {}
    trading_as_by_key = {}
    samples = []

    for key, members in groups.items():
        # Canonical display name: most-cited spelling, preferring a clean
        # (non-withdrawn/non-former-opponent) variant and a shorter string
        # as tie-breakers.
        best = sorted(
            members,
            key=lambda m: (-m["weight"], m["isWithdrawn"], m["isFormerOpponent"],
                           len(m["cleanName"]), m["cleanName"]),
        )[0]
        display_name = best["cleanName"] or key
        trading_as = next((m["tradingAs"] for m in members if m["tradingAs"]), None)
        decision_count = sum(m["weight"] for m in members)

        row = {
            "key": key, "name": display_name, "decisionCount": decision_count,
            "partyCount": len(members), "tradingAs": trading_as,
            "isStrawMan": is_strawman(display_name), "groupReviewNote": None,
            # True only when EVERY member is a multi-party-glued string (a
            # single-legal-entity org routinely has one such variant among
            # several clean ones -- that is fine, string-normalisation still
            # grouped it correctly). Guards corporate-group matching below:
            # matching a company-name regex against "Bayer AG 2) BASF AG"
            # can hit on either name by coincidence, so these orgs are never
            # candidates for a group rollup, regardless of which regex fires.
            "allMultiParty": all(m["isMultiParty"] for m in members),
        }
        org_rows.append(row)
        org_by_key[key] = row
        trading_as_by_key[key] = trading_as
        for member in members:
            party_link_rows.append({
                "partyName": member["partyName"], "orgKey": key,
                "isMultiParty": member["isMultiParty"],
            })
        if len(members) > 1:
            samples.append((display_name, decision_count, len(members),
                             sorted({m["partyName"] for m in members})))

    def _parent_ref(parent_name):
        """Resolve a group-table parent name onto an existing base
        Organisation where one already exists (e.g. "Teva Pharmaceutical
        Industries Ltd." is itself a 129-decision opponent in the corpus),
        rather than creating a same-name node disconnected from it. Falls
        back to a synthetic `grp:` node only when no such entity exists as
        its own party (e.g. "Mylan" as the trading-as target, if it were not
        also itself an opponent name)."""
        candidate = normalise(parent_name)["key"]
        if candidate in org_by_key:
            return candidate, org_by_key[candidate]["name"]
        return "grp:" + parent_name.casefold(), parent_name

    # Group-parent resolution runs as its own pass, after every base
    # Organisation is known, so `_parent_ref` can see the full key set
    # regardless of dict-iteration order above.
    group_rows, chain_rows = [], []
    parent_refs_seen = {}  # parentName -> (parentKey, resolved parentName)

    for key, row in org_by_key.items():
        if row["allMultiParty"]:
            continue
        group = resolve_group(row["name"], trading_as_by_key[key])
        if not group:
            continue
        if group["evidence"] == "needs_review":
            row["groupReviewNote"] = group["note"]
            continue
        parent_key, parent_name = _parent_ref(group["parent"])
        if parent_key == key:
            continue  # a group's own name matched its own row; not a self-link
        parent_refs_seen[parent_name] = (parent_key, group["parent"])
        group_rows.append({
            "childKey": key, "parentKey": parent_key, "parentName": parent_name,
            "evidence": group["evidence"], "note": group["note"],
        })

    # Chain group parents that themselves belong to a further group
    # (Generics [UK] "trading as Mylan" -> Mylan -> Viatris Inc.). Written in
    # a later pass by the caller, so the child node is guaranteed to exist
    # (either as a base org already written, or as a synthetic node created
    # by the pass above) before this row references it.
    for resolved_name, (parent_key, table_name) in parent_refs_seen.items():
        grp = resolve_group(table_name, None)
        if grp and grp.get("parent") and grp["parent"] != table_name:
            grandparent_key, grandparent_name = _parent_ref(grp["parent"])
            if grandparent_key == parent_key:
                continue
            chain_rows.append({
                "childKey": parent_key, "parentKey": grandparent_key,
                "parentName": grandparent_name, "evidence": grp["evidence"],
                "note": grp["note"],
            })

    samples.sort(key=lambda s: -s[1])
    return org_rows, party_link_rows, group_rows, chain_rows, samples, multi_party_count


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, default=10,
                        help="how many merged-organisation examples to print")
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
            started = time.time()
            party_records = [dict(r) for r in session.run(FETCH_PARTIES)]
            print(f"fetched {len(party_records):,} :Party nodes in "
                  f"{time.time()-started:.0f}s")

            org_rows, party_link_rows, group_rows, chain_rows, samples, multi_party_count = \
                build_rows(party_records)

            print(f"\n{len(party_records):,} parties -> {len(org_rows):,} organisations "
                  f"({100.0*(1 - len(org_rows)/len(party_records)):.1f}% reduction)")
            print(f"{multi_party_count:,} party strings look like >1 entity glued "
                  "together (flagged isMultiParty on IS_PARTY_OF, not split)")
            print(f"{len(group_rows):,} organisations rolled up to a corporate parent "
                  f"({len(chain_rows)} of those parents chain to a further parent)")
            print(f"{sum(1 for r in org_rows if r['isStrawMan']):,} organisations "
                  "flagged isStrawMan")
            print(f"{sum(1 for r in org_rows if r['groupReviewNote']):,} organisations "
                  "flagged for manual group-parent review")

            print(f"\nlargest merges (top {args.sample}):")
            for name, decisions, n_variants, variants in samples[:args.sample]:
                print(f"  {name!r} <- {n_variants} variants, {decisions} decisions")
                for variant in variants[:6]:
                    print(f"      {variant!r}")
                if len(variants) > 6:
                    print(f"      ... and {len(variants)-6} more")

            print("\ncorporate groups that would be written:")
            name_by_key = {row["key"]: row["name"] for row in org_rows}
            for row in group_rows + chain_rows:
                name_by_key.setdefault(row["parentKey"], row["parentName"])
            by_parent_key = defaultdict(list)
            for row in group_rows + chain_rows:
                by_parent_key[row["parentKey"]].append(row)
            for parent_key, rows in sorted(by_parent_key.items(),
                                            key=lambda kv: name_by_key[kv[0]]):
                children = ", ".join(name_by_key[r["childKey"]] for r in rows)
                print(f"  {name_by_key[parent_key]}  <- {children}  [{rows[0]['evidence']}]")

            print("\nflagged isStrawMan:")
            for row in sorted((r for r in org_rows if r["isStrawMan"]),
                               key=lambda r: -r["decisionCount"]):
                print(f"  {row['name']} -- {row['decisionCount']} decisions")

            print("\nflagged for manual group-parent review:")
            for row in sorted((r for r in org_rows if r["groupReviewNote"]),
                               key=lambda r: -r["decisionCount"]):
                print(f"  {row['name']} -- {row['decisionCount']} decisions")
                print(f"      {row['groupReviewNote']}")

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                return

            for statement in SETUP:
                session.run(statement).consume()

            session.run(WRITE_ORGS, rows=org_rows).consume()
            print(f"\nwrote {len(org_rows):,} :Organisation nodes")

            batch_size = 2000
            for start in range(0, len(party_link_rows), batch_size):
                batch = party_link_rows[start:start + batch_size]
                session.execute_write(
                    lambda tx, r=batch: tx.run(WRITE_PARTY_LINKS, rows=r).consume())
                print(f"  {min(start+batch_size, len(party_link_rows)):,} / "
                      f"{len(party_link_rows):,} party links", end="\r", flush=True)
            print()

            session.run(DELETE_STALE_GROUPS).consume()
            if group_rows:
                session.run(WRITE_GROUP_PARENTS, rows=group_rows).consume()
            if chain_rows:
                # Separate pass: each row's child key is a parent node created
                # by the pass above, so it must run after that one commits.
                session.run(WRITE_GROUP_PARENTS, rows=chain_rows).consume()
            print(f"wrote {len(group_rows) + len(chain_rows):,} PART_OF_GROUP edges")

            print("\nverify -- top organisations by decision count:")
            for record in session.run(VERIFY_TOP_ORGS):
                print(f"  {record['name']:45s} {record['parties']:4} variants  "
                      f"{record['decisions']:5,} decisions")

            print("\nverify -- corporate groups:")
            for record in session.run(VERIFY_GROUPS):
                print(f"  {record['parent']:30s} [{record['evidence']}]  "
                      f"{record['decisions']:5,} decisions  <- {record['children']}")

            print("\nverify -- straw-man opponents:")
            for record in session.run(VERIFY_STRAWMAN):
                print(f"  {record['name']:30s} {record['decisions']:5,} decisions")

            print("\nverify -- flagged for manual group-parent review:")
            for record in session.run(VERIFY_NEEDS_REVIEW):
                print(f"  {record['name']:30s} {record['decisions']:5,} decisions")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
