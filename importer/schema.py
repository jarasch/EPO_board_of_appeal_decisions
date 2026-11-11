"""Neo4j schema (constraints/indexes) for the EPO Board of Appeal decisions graph."""

CONSTRAINTS = [
    "CREATE CONSTRAINT decision_reference IF NOT EXISTS FOR (d:Decision) REQUIRE d.reference IS UNIQUE",
    "CREATE CONSTRAINT board_code IF NOT EXISTS FOR (b:Board) REQUIRE b.code IS UNIQUE",
    "CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT application_key IF NOT EXISTS FOR (a:Application) REQUIRE a.key IS UNIQUE",
    "CREATE CONSTRAINT publication_key IF NOT EXISTS FOR (p:Publication) REQUIRE p.key IS UNIQUE",
    "CREATE CONSTRAINT ipc_symbol IF NOT EXISTS FOR (i:IPCClass) REQUIRE i.symbol IS UNIQUE",
    "CREATE CONSTRAINT keyword_text IF NOT EXISTS FOR (k:Keyword) REQUIRE k.text IS UNIQUE",
    "CREATE CONSTRAINT legal_provision_code IF NOT EXISTS FOR (l:LegalProvision) REQUIRE l.code IS UNIQUE",
    "CREATE CONSTRAINT cited_case_key IF NOT EXISTS FOR (c:CitedCase) REQUIRE c.key IS UNIQUE",
    "CREATE CONSTRAINT case_ecli IF NOT EXISTS FOR (c:Case) REQUIRE c.ecli IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
    # Canonical article layer (scripts/normalize_provisions.py): collapses the
    # EPC1973/EPC2000/RPBA2020/... version prefixes of :LegalProvision onto one
    # node per (instrument, kind, article number).
    "CREATE CONSTRAINT article_code IF NOT EXISTS FOR (a:Article) REQUIRE a.code IS UNIQUE",
    "CREATE INDEX legal_provision_canonical IF NOT EXISTS FOR (l:LegalProvision) ON (l.canonicalCode)",
    # NOTE: caseKey (code+appealNum+year) is deliberately NOT unique — a small number of
    # case numbers (~290) cover two distinct decisions issued on different dates (e.g. an
    # interim ruling followed by a later one), so it's indexed but not constrained.
    "CREATE INDEX case_key IF NOT EXISTS FOR (c:Case) ON (c.caseKey)",
    "CREATE INDEX decision_ecli IF NOT EXISTS FOR (d:Decision) ON (d.ecli)",
    "CREATE INDEX decision_case_number IF NOT EXISTS FOR (d:Decision) ON (d.caseNumber)",
    "CREATE INDEX chunk_document_name IF NOT EXISTS FOR (c:Chunk) ON (c.documentName)",
    "CREATE INDEX section_document_name IF NOT EXISTS FOR (s:Section) ON (s.documentName)",
]


def ensure_schema(driver, database):
    with driver.session(database=database) as session:
        for stmt in CONSTRAINTS:
            session.run(stmt)
