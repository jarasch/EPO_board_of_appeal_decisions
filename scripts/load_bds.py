#!/usr/bin/env python3
"""Load an EPO business distribution scheme (BDS) year into Neo4j.

The BDS is published annually by the Presidium of the Boards of Appeal under
Rule 12b(4) EPC, as articles in the Official Journal -- for 2026, OJ EPO 2026,
A11 (Legal Board) and A12 (Technical Boards). A12 Article 1 is the IPC
allocation, A12 Article 2 the composition per board, A11 Article 1 the Legal
Board's chair and members.

None of this is in `data/EPDecisions_March2026.xml`: the DTD declares
`ep-appeal-board` / `ep-board-chairman` / `ep-board-member` / `ep-registrar`,
but those tags occur zero times in the corpus. The corpus gives the deciding
*board*, never the people, and never the allocation.

Run `scripts/extract_bds_html.py` first to turn the OJ HTML into the two CSVs
this reads. See `data/bds/README.md`.

Graph model
-----------
    (:Board {code})-[:HAS_ALLOCATION]->(:BdsAllocation {year, ruleRaw, ...})
    (:IPCClass)-[:ALLOCATED_TO {year, validFrom, validUntil}]->(:Board)
    (:BoardMember {name})-[:SERVED_ON {year, role, isDeputy}]->(:Board)

`BdsAllocation` keeps the published rule verbatim plus the parsed prefixes;
`ALLOCATED_TO` is the materialised join against the corpus's `:IPCClass` nodes.
Allocations carry validity windows because the scheme is not uniform across the
year -- in 2026, board 3.5.01 is wound down as from 01.05.2026.

Only unambiguous rules are materialised. Subgroup ranges such as
"A61K31/00-31/375" cannot be expressed as a symbol prefix, so their main groups
are recorded as `contested` and left unallocated rather than handed to the wrong
board -- see `importer/ipc_rules.py`.

Personal data
-------------
`:BoardMember` nodes are identifiable natural persons. They are NOT loaded
unless you pass `--with-members`, everything is scoped by `--year`, and
`--delete-year` removes a year's composition including orphaned members. See
`EXAMINER_PLAN.md` section 3 before building anything per-person on top.

Usage:
    python3 scripts/load_bds.py --year 2026 [--dry-run]
    python3 scripts/load_bds.py --year 2026 --with-members
    python3 scripts/load_bds.py --year 2026 --delete-year
"""

import argparse
import csv
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importer.ipc_rules import parse_rule  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "bds")

ROLES = {"chair", "technical", "legal"}

CONSTRAINTS = [
    "CREATE CONSTRAINT bds_allocation_key IF NOT EXISTS "
    "FOR (a:BdsAllocation) REQUIRE a.key IS UNIQUE",
    "CREATE CONSTRAINT board_member_name IF NOT EXISTS "
    "FOR (m:BoardMember) REQUIRE m.name IS UNIQUE",
]

ALLOCATION_QUERY = """
UNWIND $rows AS row
MERGE (b:Board {code: row.boardCode})
  ON CREATE SET b.createdByBds = true
MERGE (a:BdsAllocation {key: row.key})
SET a.year        = row.year,
    a.boardCode   = row.boardCode,
    a.ruleRaw     = row.ruleRaw,
    a.validFrom   = date(row.validFrom),
    a.validUntil  = date(row.validUntil),
    a.includes    = row.includes,
    a.excludes    = row.excludes,
    a.contested   = row.contested,
    a.parseStatus = row.parseStatus,
    a.sourceNote  = row.sourceNote
MERGE (b)-[:HAS_ALLOCATION]->(a)
"""

# `none(...)` over an empty exclusion list is true, so rules without exclusions
# behave correctly.
MATERIALISE_QUERY = """
UNWIND $rows AS row
MATCH (b:Board {code: row.boardCode})
MATCH (i:IPCClass)
WHERE any(p IN row.includes WHERE i.symbol STARTS WITH p)
  AND none(p IN row.excludes WHERE i.symbol STARTS WITH p)
MERGE (i)-[r:ALLOCATED_TO {
    year: row.year, validFrom: date(row.validFrom), validUntil: date(row.validUntil)
}]->(b)
SET r.source = 'OJ-BDS', r.parseStatus = row.parseStatus
RETURN count(r) AS edges
"""

MEMBER_QUERY = """
UNWIND $rows AS row
MERGE (b:Board {code: row.boardCode})
  ON CREATE SET b.createdByBds = true
MERGE (m:BoardMember {name: row.name})
MERGE (m)-[s:SERVED_ON {year: row.year, role: row.role}]->(b)
SET s.isDeputy = row.isDeputy, s.validity = row.validity
"""

DELETE_QUERIES = [
    ("allocation nodes", "MATCH (a:BdsAllocation {year: $year}) DETACH DELETE a"),
    ("allocation edges", "MATCH ()-[r:ALLOCATED_TO {year: $year}]->() DELETE r"),
    ("composition edges", "MATCH (:BoardMember)-[s:SERVED_ON {year: $year}]->() DELETE s"),
    ("orphaned members", "MATCH (m:BoardMember) WHERE NOT (m)-[:SERVED_ON]->() DELETE m"),
]


def read_allocation(path, year):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            board_code = (row.get("board_code") or "").strip()
            if not board_code:
                continue
            rule_raw = (row.get("rule_raw") or "").strip()
            valid_from = (row.get("valid_from") or f"{year}-01-01").strip()
            valid_until = (row.get("valid_until") or f"{year}-12-31").strip()

            parsed = (
                parse_rule(rule_raw)
                if rule_raw
                # An empty rule is a real published state -- a board with no
                # allocation this year -- not a parse failure.
                else {"includes": [], "excludes": [], "contested": [], "parseStatus": "none"}
            )
            rows.append({
                "key": f"{year}-{board_code}-{valid_from}-{index}",
                "year": year,
                "boardCode": board_code,
                "ruleRaw": rule_raw,
                "validFrom": valid_from,
                "validUntil": valid_until,
                "sourceNote": (row.get("source_note") or "").strip() or None,
                **parsed,
            })
    return rows


def read_members(path, year):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            board_code = (row.get("board_code") or "").strip()
            name = (row.get("name") or "").strip()
            role = (row.get("role") or "").strip().lower()
            if not board_code or not name:
                continue
            if role not in ROLES:
                raise SystemExit(
                    f"{path}: role {role!r} for {name!r} is not one of {sorted(ROLES)}"
                )
            rows.append({
                "year": year,
                "boardCode": board_code,
                "name": name,
                "role": role,
                "isDeputy": (row.get("is_deputy") or "").strip().lower()
                in ("true", "yes", "1", "y"),
                "validity": (row.get("validity") or "").strip() or None,
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--allocation", help="defaults to data/bds/bds_<year>_allocation.csv")
    parser.add_argument("--members", help="defaults to data/bds/bds_<year>_members.csv")
    parser.add_argument(
        "--with-members",
        action="store_true",
        help="also load named board members (personal data -- off by default)",
    )
    parser.add_argument(
        "--delete-year",
        action="store_true",
        help="remove this year's allocation and composition, then exit",
    )
    parser.add_argument("--dry-run", action="store_true", help="parse and report, write nothing")
    args = parser.parse_args()

    load_dotenv()
    allocation_path = args.allocation or os.path.join(DATA_DIR, f"bds_{args.year}_allocation.csv")
    members_path = args.members or os.path.join(DATA_DIR, f"bds_{args.year}_members.csv")

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        with driver.session(database=database) as session:
            if args.delete_year:
                for label, query in DELETE_QUERIES:
                    counters = session.run(query, year=args.year).consume().counters
                    print(
                        f"deleted {label}: {counters.nodes_deleted} nodes, "
                        f"{counters.relationships_deleted} rels"
                    )
                return

            allocation = read_allocation(allocation_path, args.year)
            if not allocation:
                raise SystemExit(
                    f"{allocation_path} has no rows.\n"
                    "Run scripts/extract_bds_html.py first -- see data/bds/README.md."
                )

            by_status = {}
            for row in allocation:
                by_status.setdefault(row["parseStatus"], []).append(row)
            print(
                f"allocation rows: {len(allocation)} "
                + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_status.items()))
            )
            for row in by_status.get("unparsed", []):
                print(f"  UNPARSED {row['boardCode']}: {row['ruleRaw'][:90]}")
            for row in by_status.get("partial", []):
                print(f"  partial  {row['boardCode']}: contested {row['contested']}")

            members = []
            if args.with_members and os.path.exists(members_path):
                members = read_members(members_path, args.year)
                print(f"members: {len(members)} entries")
            elif args.with_members:
                print(f"members: {members_path} not found, skipping")
            else:
                print("members: skipped (pass --with-members to load personal data)")

            materialisable = [r for r in allocation if r["parseStatus"] in ("parsed", "partial")]

            if args.dry_run:
                print("\n-- dry run, nothing written --")
                for row in materialisable[:5]:
                    print(f"  {row['boardCode']}: +{len(row['includes'])} -{len(row['excludes'])}")
                return

            for constraint in CONSTRAINTS:
                session.run(constraint)

            session.run(ALLOCATION_QUERY, rows=allocation).consume()
            print(f"wrote {len(allocation)} :BdsAllocation nodes")

            if materialisable:
                edges = session.run(MATERIALISE_QUERY, rows=materialisable).single()["edges"]
                print(f"materialised {edges} (:IPCClass)-[:ALLOCATED_TO]->(:Board) edges")

            if members:
                session.run(MEMBER_QUERY, rows=members).consume()
                print(f"wrote {len(members)} member entries")

            unknown = session.run(
                "MATCH (b:Board) WHERE b.createdByBds AND NOT (b)<-[:DECIDED_BY]-() "
                "RETURN collect(b.code) AS codes"
            ).single()["codes"]
            if unknown:
                print(f"note: boards in the BDS with no decisions in the corpus: {unknown}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
