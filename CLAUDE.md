# Claude Code Agent Context — neo4j-mcp-workspace-template

## 0. Repository-Specific Context: EPO Board of Appeal Decisions

This workspace instance is being used to build a Neo4j graph from a specific data source: a corpus of decisions from the EPO (European Patent Office) Boards of Appeal. The generic template mechanics in the rest of this file (sections 1–8) still apply — this section only describes the source data itself.

**Contents:**
- `data/EPDecisions_March2026.xml` — the corpus. **~1.2 GB, 51,299 `<ep-appeal-decision>` records.** Root element `<ep-appeal-decisions date-produced="YYYYMMDD">`. Decision text is in German, English, and French (mixed within the file, per-decision `lang`/`procedure-lang` attributes).
- `data/ep-appeal-decision.v1.1.dtd` and `data/ep-appeal-decision.v1.1.xsd` — the two equivalent schema definitions for the corpus (DTD and XSD forms of the same v1.1 grammar).
- `data/xml.xsd`, `data/xlink.xsd` — standard W3C schemas imported by the XSD above (xml: namespace attributes, XLink).
- `importer/` (`parser.py`, `loader.py`, `schema.py`), `import_decisions.py`, `enrich_graph.py`, `requirements.txt` — custom Python tooling for parsing this XML corpus and loading/enriching it in Neo4j, layered on top of the workspace template's own MCP-based ingestion path. Prefer the template's `neo4j-ingest` / `neo4j-lexical-graph` / `neo4j-entity-graph` MCP servers (section 4/5 below) for new ingestion work where they fit; treat this custom tooling as existing project-specific code to maintain, not a pattern to duplicate.

**Handling the XML file:** it is too large to load into an editor or into memory with a DOM parser, and too large for the `Read` tool. Treat it as a stream:
- Quick inspection: `head -c N`, `grep`, `xmllint --stream`, or line-oriented tools. The file is written with minimal whitespace, so line counts don't map cleanly to record counts — count records with `grep -c '<ep-appeal-decision '` instead.
- Programmatic parsing: use a streaming/incremental parser (e.g. Python `lxml.etree.iterparse`, or SAX-style parsing) and clear elements as you go. Never `read()` the whole file or build a full DOM.
- Validation against the schema: `xmllint --noout --schema data/ep-appeal-decision.v1.1.xsd data/EPDecisions_March2026.xml` (slow on the full file — consider validating a sample/extract first).

**Record structure:** each `<ep-appeal-decision>` (attributes: `accession-num`, `dtd-version`, `lang`, `procedure-lang`, `appeal-type`) follows this element order (all but the first are optional):

```
ep-appeal-bib-data        -- required: case number, board code, decision date, ECLI, IPC
                              classifications, application/publication refs, parties'
                              addresses, appeal board members, registrar
ep-headword
ep-legal-refs              -- legal provisions/case-law cited, as refs or full citations
ep-keywords / ep-keywords-documentation
ep-cited-decisions
ep-headnote
ep-catchword
ep-summary-of-facts        -- (heading*, p+)+
ep-reasons-for-decision    -- (heading*, p+)+
ep-appeal-order            -- (heading*, p+)+
abstract*
```

Text-bearing elements (`p`, `heading`, `ep-headword`, etc.) allow inline markup: `b`, `i`, `u`, `sup`, `sub`, `smallcaps`. The DTD (`data/ep-appeal-decision.v1.1.dtd`) is the fastest place to check an element's exact allowed children/attributes; the XSD is the canonical/more detailed version of the same grammar.

---

## 1. Setup Status Check

**On every session start, verify the following before doing any work:**

```bash
# Check .env exists
test -f .env && echo ".env OK" || echo ".env MISSING"

# Check .mcp.json exists (Claude Code project-scope MCP config)
test -f .mcp.json && echo ".mcp.json OK" || echo ".mcp.json MISSING"
```

If either file is missing, tell the user:
> "Run `./setup.sh` first to configure credentials and MCP servers, then restart Claude Code."

If both files exist but MCP tools are not available in this session, tell the user:
> "MCP servers are configured but not loaded. Restart Claude Code from this directory to load them."

**Do not attempt graph operations if Neo4j MCP tools are unavailable.**

---

## 2. Supported Coding Tools

This workspace supports 6 AI coding tools. `setup.sh` generates a config file for each:

| Tool | Config file | Skill invocation |
|------|------------|-----------------|
| Claude Code | `.mcp.json` | `/develop-neo4j-graph` |
| Cursor | `.cursor/mcp.json` | auto-triggered |
| Gemini CLI | `.gemini/settings.json` | `/develop-neo4j-graph` or auto-triggered |
| GitHub Copilot VS Code | `.vscode/mcp.json` | auto-triggered |
| OpenCode | `opencode.json` | agent picker |
| Codex CLI | `.codex/config.toml` | `$develop-neo4j-graph` or auto-triggered |

The skill workflow is defined once in `.agents/skills/develop-neo4j-graph/SKILL.md` and shared across all tools via the [Agent Skills](https://agentskills.io) open standard. `.claude/skills/develop-neo4j-graph/` is a symlink to that canonical location.

---

## 3. Project Structure

```
neo4j-mcp-workspace-template/
├── setup.sh                        # Run once before opening any tool
├── .env                            # Credentials (gitignored, created by setup.sh)
├── .env.example                    # Documents all variables — no secrets
├── CLAUDE.md                       # This file (Claude Code context)
├── GEMINI.md                       # Gemini CLI context
├── AGENTS.md                       # Codex CLI context
├── .agents/
│   └── skills/
│       └── develop-neo4j-graph/    # Canonical skill — cross-tool (Agent Skills standard)
│           ├── SKILL.md
│           └── references/
├── .gemini/
│   ├── settings.json               # Generated (gitignored) — Gemini CLI MCP config
│   └── commands/
│       └── develop-neo4j-graph.toml  # Gemini CLI slash command
├── .opencode/
│   └── agents/
│       └── develop-neo4j-graph.md  # OpenCode agent
├── .github/
│   └── copilot-instructions.md     # GitHub Copilot VS Code context
├── .mcp.json                       # Generated (gitignored) — Claude Code MCP config
├── data/                           # Input data (gitignored contents, tracked structure)
│   ├── csv/                        # Structured data
│   └── pdf/                        # PDF documents
├── outputs/                        # Generated outputs (gitignored contents, tracked structure)
│   ├── data_models/                # Graph data model JSON files
│   ├── queries/                    # Cypher query YAML files
│   ├── reports/                    # Markdown reports
│   └── schemas/                    # Pydantic extraction schema files (.json + .py)
├── demo/                           # Demo data scripts and expected outputs (committed)
│   └── expected/                   # Reference outputs for comparison
├── mcp-neo4j-ingest/               # Local: structured CSV ingestion server
├── mcp-neo4j-lexical-graph/        # Local: PDF → lexical graph server
├── mcp-neo4j-entity-graph/         # Local: entity extraction server
├── neo4j-mcp-workspace-dxt/        # Claude Desktop DXT extension
├── mcp-neo4j-graphrag/             # Local: cloned by setup.sh (gitignored)
├── .cursor/
│   └── mcp.json                    # Generated (gitignored) — Cursor MCP config
├── .vscode/
│   └── mcp.json                    # Generated (gitignored) — GitHub Copilot MCP config
├── opencode.json                   # Generated (gitignored) — OpenCode MCP config
├── .codex/
│   └── config.toml                 # Generated (gitignored) — Codex CLI MCP config
└── .claude/
    └── skills/
        ├── develop-neo4j-graph/    # Symlink → .agents/skills/develop-neo4j-graph/
        ├── setup-workspace/        # /setup-workspace validation skill
        └── dev/evaluate-pipeline/  # /dev:evaluate-pipeline skill
```

---

## 4. MCP Servers Reference

Five MCP servers are configured for this workspace:

### `neo4j-data-modeling`
- **Purpose:** Design and validate graph schemas from sample data
- **Key tools:** `list_example_data_models`, `get_example_data_model`, `get_mermaid_config_str`
- **Required env:** none (stateless, no credentials needed)
- **Source:** `uvx mcp-neo4j-data-modeling@0.8.2`

### `neo4j-ingest`
- **Purpose:** Load structured CSV data into Neo4j using parameterized Cypher
- **Key tools:** `ingest_csv_into_neo4j`
- **Required env:** none in mcp.json — reads from `.env` via python-dotenv
- **Source:** local `mcp-neo4j-ingest/` (requires `uv sync`)

### `neo4j-lexical-graph`
- **Purpose:** Parse PDFs into a searchable graph with chunk nodes and embeddings
- **Key tools:** `create_lexical_graph`, `embed_chunks` (also creates fulltext index by default), `generate_chunk_descriptions`, `assign_section_hierarchy`, `verify_lexical_graph`, `list_documents`
- **Parse modes:** `pymupdf` (default), `docling`, `page_image`, `vlm_blocks`
- **Note:** `docling` parse mode requires the optional docling extra. Install via `uv sync --extra docling --directory mcp-neo4j-lexical-graph` or re-run `./setup.sh` after deleting `INSTALL_DOCLING` from `.env`.
- **Required env:** none in mcp.json — reads from `.env` via python-dotenv
- **Source:** local `mcp-neo4j-lexical-graph/` (requires `uv sync`)

### `neo4j-entity-graph`
- **Purpose:** Extract structured entities from lexical graph Chunk nodes using LLM
- **Provider:** Any LiteLLM-compatible provider (100+ supported)
- **Processing:** Async background — use status tool to monitor
- **Required env:** none in mcp.json — reads from `.env` via python-dotenv
- **Source:** local `mcp-neo4j-entity-graph/` (requires `uv sync`)

Two extraction paths — choose one per project:

| Path | When to use | Key tools |
|------|-------------|-----------|
| **File-based** | Developer workflow in Claude Code; quick schema from a data model JSON | `convert_schema` → `extract_entities(schema=...)` |
| **Ontology DB** | Graph-driven; supports normalizers, aliases, blocklists, editable in Bloom; required for Claude Desktop | `setup_ontology_db`, write ontology via Cypher, `generate_schema_from_ontology` → `extract_entities(ontology_name=...)` |

Additional tools: `check_extraction_status`, `cancel_extraction`

### `neo4j-graphrag`
- **Purpose:** Query and write the graph using vector search, fulltext search, and Cypher — the retrieval layer for RAG applications
- **Key tools:** `get_neo4j_schema_and_indexes`, `vector_search`, `fulltext_search`, `read_neo4j_cypher`, `write_neo4j_cypher`, `search_cypher_query`, `read_node_image`
- **Required env:** none in mcp.json — reads from `.env` via python-dotenv
- **Source:** local `mcp-neo4j-graphrag/` (cloned by `setup.sh`, requires `uv sync`)
- **Note:** When using the Ontology DB path, two instances are active — tools are prefixed `documents_*` (documents DB) and `ontology_*` (ontology DB)

### `bigquery` (optional)
- **Purpose:** Query BigQuery as a source database
- **Required:** `toolbox` CLI installed, `BIGQUERY_PROJECT` set
- **Source:** `toolbox --prebuilt bigquery --stdio`

---

## 5. Primary Workflow

One skill covers all use cases:

### `/develop-neo4j-graph` — Unified workflow (CSV + PDF, CHATBOT or ANALYTICAL mode)

| Step | Action | Server |
|------|--------|--------|
| 1 | Analyze source data samples | (file tools) |
| 2 | Use case discussion → infer CHATBOT or ANALYTICAL mode | — |
| 3 | Design graph data model iteratively | `neo4j-data-modeling` |
| 4 | Ingest data (CSV and/or PDF) | `neo4j-ingest` / `neo4j-lexical-graph` + `neo4j-entity-graph` |
| 4.5 | Verify ingestion counts | `neo4j-graphrag` |
| 5–7 | Schema export, entity extraction, verify [PDF only] — file-based (`convert_schema`) or ontology DB (`generate_schema_from_ontology`) | `neo4j-entity-graph` |
| 8 | Output — Q&A report (CHATBOT) or Cypher analysis (ANALYTICAL) | `neo4j-graphrag` |

**Structured data (CSV):** Steps 1 → 3 → 4 → 4.5 → 8

**Unstructured data (PDF):** Full sequence Steps 1 → 8

---

## 6. Credential Management

- **Never ask the user for credentials.** They are in `.env` and injected into the MCP server environment by `setup.sh`.
- **Never read or print passwords** from `.env` or `mcp.json`.
- **Never modify `.cursor/mcp.json` or `.mcp.json`.** These are generated files. Direct the user to re-run `./setup.sh` if credentials need updating.
- **Never write credentials to any file** other than what `setup.sh` manages.
- This repo's `.env` holds a live-looking API key in plaintext. Never read its contents into responses, logs, or committed files. Don't add it to `.gitignore` assuming that's sufficient — flag any accidental exposure immediately rather than silently working around it.

---

## 7. Common Failure Modes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `AuthError` or `Unauthorized` on any Neo4j tool | Wrong credentials in `.env` | Re-run `./setup.sh` (delete `.env` first to re-prompt) |
| `neo4j-lexical-graph` or `neo4j-entity-graph` fail with no embeddings/extractions | Missing `OPENAI_API_KEY` | Add key to `.env`, re-run `./setup.sh` |
| CSV ingestion fails with "file not found" | Relative path used; absolute path required | Use full path: `/path/to/file.csv` |
| MCP tools not found in session | `.mcp.json` or `.cursor/mcp.json` missing, or IDE not restarted | Run `./setup.sh`, then restart IDE/Claude Code |
| `uv` command not found | uv not installed | See https://docs.astral.sh/uv/getting-started/installation/ |
| Entity extraction is slow / appears stuck | Background async processing | Call `check_extraction_status` to check progress |
| `docling` parse mode fails with `ImportError` | docling optional extra not installed | Run `uv sync --extra docling --directory mcp-neo4j-lexical-graph`, then restart IDE |
| `neo4j-ingest` fails immediately at startup | `.env` not found or wrong path at server launch | Ensure `.env` exists in workspace root; re-run `./setup.sh` |

---

## 8. What NOT to Do

- **Do not** run `uv sync` in the workspace root — each server has its own `pyproject.toml`
- **Do not** install MCP servers globally with `pip install` — use `uvx` or the local `uv` setup
- **Do not** modify `~/.claude.json` or any global Claude configuration
- **Do not** add MCP servers to the session at runtime — MCP must be configured before the IDE starts
- **Do not** use relative paths in Cypher `LOAD CSV` or ingest tool calls — always use absolute paths
- **Do not** commit `.env`, `.cursor/mcp.json`, or `.mcp.json` — they are gitignored for security
