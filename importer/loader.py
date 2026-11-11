"""Batches parsed decisions into staging lists and writes them to Neo4j via
parameterized UNWIND queries (one query per node/relationship type per batch)."""

from importer.parser import SECTION_DEFS

SECTION_LABELS = [label for label, _ in SECTION_DEFS]

DECISION_QUERY = """
UNWIND $rows AS row
MERGE (d:Decision {reference: row.reference})
SET d.url = row.url,
    d.ecli = row.ecli,
    d.caseNumber = row.caseNumber,
    d.code = row.code,
    d.appealNum = row.appealNum,
    d.year = row.year,
    d.lang = row.lang,
    d.procedureLang = row.procedureLang,
    d.appealType = row.appealType,
    d.dtdVersion = row.dtdVersion,
    d.volume = row.volume,
    d.distributionCode = row.distributionCode,
    d.boardCode = row.boardCode,
    d.decisionDate = CASE WHEN row.decisionDate IS NOT NULL THEN date(row.decisionDate) ELSE NULL END,
    d.headword = row.headword,
    d.inventionTitle = row.inventionTitle,
    d.yearOfCaseLaw = row.yearOfCaseLaw,
    d.officialJournalRef = row.officialJournalRef
WITH d, row
WHERE row.boardCode IS NOT NULL
MERGE (b:Board {code: row.boardCode})
MERGE (d)-[:DECIDED_BY]->(b)
"""

# {label} is filled in at format-time per section type (see PARTY_QUERY_TEMPLATE
# below for the same pattern) -- avoids needing dynamic label support in Cypher.
SECTION_QUERY_TEMPLATE = """
UNWIND $rows AS row
MATCH (d:Decision {{reference: row.reference}})
MERGE (s:Section:{label} {{id: row.id}})
SET s.text = row.text, s.type = row.type, s.documentName = row.reference
MERGE (d)-[:HAS_SECTION]->(s)
"""

APPLICATION_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (a:Application {key: row.key})
SET a.country = row.country, a.number = row.number, a.kind = row.kind,
    a.date = CASE WHEN row.date IS NOT NULL THEN date(row.date) ELSE NULL END
MERGE (d)-[:CONCERNS_APPLICATION]->(a)
"""

PUBLICATION_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (p:Publication {key: row.key})
SET p.country = row.country, p.number = row.number, p.kind = row.kind,
    p.date = CASE WHEN row.date IS NOT NULL THEN date(row.date) ELSE NULL END
MERGE (d)-[:RESULTED_IN_PUBLICATION]->(p)
"""

IPC_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (i:IPCClass {symbol: row.symbol})
MERGE (d)-[:CLASSIFIED_AS]->(i)
"""

KEYWORD_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (k:Keyword {text: row.text})
MERGE (d)-[:HAS_KEYWORD]->(k)
"""

LEGAL_REF_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (l:LegalProvision {code: row.code})
SET l.document = row.document, l.documentPart = row.documentPart
MERGE (d)-[:CITES_LEGAL_PROVISION]->(l)
"""

CITED_CASE_QUERY = """
UNWIND $rows AS row
MATCH (d:Decision {reference: row.reference})
MERGE (c:CitedCase {key: row.key})
SET c.code = row.code, c.country = row.country,
    c.appealNum = row.appealNum, c.year = row.year, c.raw = row.raw
MERGE (d)-[:CITES_CASE]->(c)
"""

# role -> relationship type, applied to a flat list of {reference, name}
PARTY_ROLE_RELS = {
    "applicants": "HAS_APPLICANT",
    "opponents": "HAS_OPPONENT",
    "representatives": "HAS_REPRESENTATIVE",
    "chairman": "HAS_CHAIRMAN",
    "boardMembers": "HAS_BOARD_MEMBER",
    "registrar": "HAS_REGISTRAR",
}

PARTY_QUERY_TEMPLATE = """
UNWIND $rows AS row
MATCH (d:Decision {{reference: row.reference}})
MERGE (p:Party {{name: row.name}})
MERGE (d)-[:{rel}]->(p)
"""


def stage_batch(batch):
    """Flatten a list of (decision, related) tuples into per-type row lists."""
    staged = {
        "decisions": [],
        "applications": [],
        "publications": [],
        "ipc": [],
        "keywords": [],
        "legalRefs": [],
        "citedCases": [],
        "parties": {role: [] for role in PARTY_ROLE_RELS},
        "sections": {label: [] for label in SECTION_LABELS},
    }

    for decision, related in batch:
        ref = decision["reference"]
        staged["decisions"].append(decision)

        for section in related["sections"]:
            staged["sections"][section["type"]].append({
                "reference": ref,
                "id": f"{ref}_{section['type']}",
                "type": section["type"],
                "text": section["text"],
            })

        if related["application"]:
            staged["applications"].append({"reference": ref, **related["application"]})
        if related["publication"]:
            staged["publications"].append({"reference": ref, **related["publication"]})
        for symbol in related["ipcSymbols"]:
            staged["ipc"].append({"reference": ref, "symbol": symbol})
        for text in related["keywords"]:
            staged["keywords"].append({"reference": ref, "text": text})
        for ref_row in related["legalRefs"]:
            staged["legalRefs"].append({"reference": ref, **ref_row})
        for cited in related["citedCases"]:
            staged["citedCases"].append({"reference": ref, **cited})

        for role in ("applicants", "opponents", "representatives", "boardMembers"):
            for name in related[role]:
                staged["parties"][role].append({"reference": ref, "name": name})
        if related["chairman"]:
            staged["parties"]["chairman"].append({"reference": ref, "name": related["chairman"]})
        if related["registrar"]:
            staged["parties"]["registrar"].append({"reference": ref, "name": related["registrar"]})

    return staged


def write_batch(tx, staged):
    tx.run(DECISION_QUERY, rows=staged["decisions"])
    for label in SECTION_LABELS:
        rows = staged["sections"][label]
        if rows:
            tx.run(SECTION_QUERY_TEMPLATE.format(label=label), rows=rows)
    if staged["applications"]:
        tx.run(APPLICATION_QUERY, rows=staged["applications"])
    if staged["publications"]:
        tx.run(PUBLICATION_QUERY, rows=staged["publications"])
    if staged["ipc"]:
        tx.run(IPC_QUERY, rows=staged["ipc"])
    if staged["keywords"]:
        tx.run(KEYWORD_QUERY, rows=staged["keywords"])
    if staged["legalRefs"]:
        tx.run(LEGAL_REF_QUERY, rows=staged["legalRefs"])
    if staged["citedCases"]:
        tx.run(CITED_CASE_QUERY, rows=staged["citedCases"])
    for role, rel in PARTY_ROLE_RELS.items():
        rows = staged["parties"][role]
        if rows:
            tx.run(PARTY_QUERY_TEMPLATE.format(rel=rel), rows=rows)


def load_batch(driver, database, batch):
    staged = stage_batch(batch)
    with driver.session(database=database) as session:
        session.execute_write(write_batch, staged)
