#!/usr/bin/env python3
"""Post-import enrichment for the EPO Board of Appeal decisions graph.

Adds a (:Case) layer that groups the language variants of a single legal
case (Decision nodes sharing the same non-unique `ecli`), and resolves the
(:CitedCase) reference stubs created during import into direct
(:Decision)-[:CITES]->(:Case) relationships wherever the cited case exists
in the corpus.

Credentials are read from .env (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE).
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from importer.schema import ensure_schema

BUILD_CASE_NODES = """
MATCH (d:Decision)
WITH d.ecli AS ecli, collect(d) AS decisions
CALL (ecli, decisions) {
  WITH ecli, decisions, decisions[0] AS rep
  MERGE (c:Case {ecli: ecli})
  SET c.caseKey = rep.code + '-' + rep.appealNum + '-' + rep.year,
      c.caseNumber = rep.caseNumber,
      // Attorney-facing form: "T 336/14", not the corpus's padded "T 0336/14".
      c.caseRef = rep.code + ' ' + toString(toInteger(rep.appealNum))
                  + '/' + right(rep.year, 2),
      c.code = rep.code,
      c.appealNum = rep.appealNum,
      c.year = rep.year,
      c.boardCode = rep.boardCode,
      c.decisionDate = rep.decisionDate
  WITH c, decisions
  UNWIND decisions AS d2
  MERGE (d2)-[:LANGUAGE_VERSION_OF]->(c)
} IN TRANSACTIONS OF 500 ROWS
"""

RESOLVE_CITATIONS = """
MATCH (d:Decision)-[:CITES_CASE]->(cc:CitedCase)
WHERE cc.appealNum IS NOT NULL AND cc.year IS NOT NULL
MATCH (target:Case {caseKey: cc.code + '-' + cc.appealNum + '-' + cc.year})
WITH d, target
CALL (d, target) {
  MERGE (d)-[:CITES]->(target)
} IN TRANSACTIONS OF 1000 ROWS
"""


def main():
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    ensure_schema(driver, database)

    with driver.session(database=database) as session:
        print("Building Case nodes and LANGUAGE_VERSION_OF links...")
        session.run(BUILD_CASE_NODES).consume()

        print("Resolving CitedCase stubs into Decision-[:CITES]->Case links...")
        session.run(RESOLVE_CITATIONS).consume()

        counts = session.run(
            "MATCH (c:Case) WITH count(c) AS cases "
            "MATCH ()-[r:LANGUAGE_VERSION_OF]->() WITH cases, count(r) AS versions "
            "MATCH ()-[r2:CITES]->(:Case) "
            "RETURN cases, versions, count(r2) AS resolvedCitations"
        ).single()
        print(f"Case nodes: {counts['cases']}")
        print(f"LANGUAGE_VERSION_OF relationships: {counts['versions']}")
        print(f"Resolved CITES relationships: {counts['resolvedCitations']}")

    driver.close()


if __name__ == "__main__":
    main()
