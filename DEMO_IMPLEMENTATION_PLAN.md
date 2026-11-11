# Demo Implementation Plan — Legal-Appeal GraphRAG over EPO Board of Appeal Decisions

**Goal.** A patent attorney asks a natural-language question. The system retrieves from the
decisions graph, induces a subgraph from the hits, partitions it into coherent legal topics with
Leiden, and returns a per-topic summary grounded in cited decisions.

```
NL question
   │
   ├─▶ [1] question understanding      → structured intent (issues, dates, IPC, outcome, cases)
   ├─▶ [2] multi-channel seed lookup   → vector + fulltext + entity + structured Cypher
   ├─▶ [3] fusion + subgraph induction → bounded, weighted induced subgraph
   ├─▶ [4] Leiden community detection  → legal topic clusters
   ├─▶ [5] per-topic summarization     → map-reduce over member chunks
   └─▶ [6] final synthesis             → answer, organized by topic, with case citations
```

---

## 0. Where we already are (verified against the live DB)

The bibliographic + lexical layers are **already built and loaded**. Confirmed counts:

| Layer | Status |
|---|---|
| `:Decision` 51,299 · `:Case` 48,618 · `:Board` 31 | ✅ loaded |
| `:Section` 159,597 (5 subtypes) · `:Chunk` 657,115 | ✅ loaded |
| `:LegalProvision` 4,205 · `:Keyword` 53,534 · `:IPCClass` 23,509 · `:Party` 36,228 | ✅ loaded |
| `CITES` 74,069 · `CITES_LEGAL_PROVISION` 157,885 · `LANGUAGE_VERSION_OF` 51,299 | ✅ loaded |
| Fulltext index `chunk_text_fulltext` on `Chunk.text` | ✅ exists |
| `:Article` 764 canonical · `CITES_ARTICLE` 143,107 | ✅ **Phase 1.1 done** |
| `:DemoDecision` 1,114 · `:DemoSection` 2,303 · `:Chunk:DemoChunk` 9,119 (`para-v1`) | ✅ **Phase 1.3 done** |
| `demochunk_text_embedding` (1536d) + `demochunk_text_fulltext` | ✅ **Phase 1.4 done — slice embedded** |
| **Full-corpus embeddings** (657k `:Chunk`) | ❌ optional, not run (~$5.50) |
| **Entity layer** | ❌ **does not exist — this plan builds it** |

**Environment (verified):** Neo4j 2026.07.1, GDS 2026.07.0, edition **Unlicensed (Community)**,
18 CPUs, **heap 1 GB**. `.env` provides `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `EXTRACTION_MODEL`.

**Feasibility probes run against the live DB (all passed):**

- `gds.graph.project` Cypher-aggregation projection works.
- **`gds.leiden.stream` / `.stats` runs on GDS Community** — Leiden is *not* license-gated here.
  Probe: 483-node citation subgraph → sensible community split.
- Corpus language split: en 33,330 / de 13,876 / fr 4,093.
- Legal paragraph structure (`1.`, `2.1`, `I.`) survives in `Section.text`, `\n\n`-separated.

---

## 1. Decisions taken (and why)

| # | Decision | Rationale |
|---|---|---|
| D1 | **Scope entity extraction to a demo slice**, not the full corpus | 657k chunks ≈ 828M input tokens of LLM extraction — hundreds of $ and many hours. Not demo-viable. |
| D2 | Slice = **EN + Art. 56 EPC + decided ≥ 2015 + IPC G06F/G06Q** (computer-implemented inventions) | Sized at **1,017 decisions / 7,236 Reasons chunks** (verified). CII inventive step is the most demo-legible attorney topic (COMVIK, technical effect). |
| D3 | **Embed the full corpus, extract entities only on the slice** | Embedding is asymmetrically cheap: 275M tokens × $0.02/1M ≈ **$5.50** for all 657k chunks. Gives corpus-wide semantic recall while keeping extraction bounded. |
| D4 | **Ontology-DB path** for extraction, not file-based schema | The `:Keyword` layer is a mess of surface forms — `Inventive step (yes)` / `Inventive step - (yes)` / `Inventive step - yes` / `Erfinderische Tätigkeit (ja)`. The ontology path's normalizers + aliases are exactly the fix, and it stays editable in Bloom. |
| D5 | **Re-chunk the slice on legal paragraph boundaries** before extraction | Current 500-token windows split mid-sentence (verified: a chunk begins `" that a desire exists for re-"`). EPO paragraphs are the citable unit — enables `T 1234/15, Reasons 2.3` citations, which is how attorneys actually cite. |
| D6 | **Leiden on the query-induced subgraph**, not precomputed corpus-wide | Topics must be relative to the question. Also keeps GDS inside the 1 GB heap. |
| D7 | Scope extraction via a **marker label** `:Chunk:DemoChunk` + `source_label="DemoChunk"` | `extract_entities` selects nodes by `source_label`; a second label is the least invasive way to bound the run without touching the 657k-node population. |

---

## 2. Critical finding: the Leiden stage needs hub suppression

This is the make-or-break part of the pipeline, and **naive subgraph induction fails**. Measured on
the real slice:

| Induction strategy | Nodes | Edges | Leiden result |
|---|---|---|---|
| Seeds + `CITES` + **raw** keyword co-occurrence | 17,016 | **1,845,302** | 22 communities, **one 5,435-member blob**, p50 = 7 — unusable |
| Seeds + co-citation + keyword co-occurrence, **keyword df ≤ 40**, edge weight ≥ 2, weighted Leiden `gamma=1.5` | 442 | 8,236 | **45 communities, max 60, p75 = 10 — usable** ✅ |

**Reproduced at build time** on a 700-node COMVIK subgraph (`scripts/probe_topics.py --sweep`).
The absolute df threshold turned out to be the wrong unit: "df ≤ 40" is a 0.2% cut in a 51,299-node
corpus and a 3.6% cut in the 1,114-decision slice, so the shipped cut is a **fraction of the node
count** and rescales with the subgraph. At a 10% cut with a permissive weight threshold the blowup
returns exactly as predicted — 28,199 edges, avg degree 85, modularity 0.376, largest community 27%,
**exit criteria fail**. Tightening the cut to 2% gives 3,006 edges, avg degree 11, modularity 0.516,
18 usable communities, largest 10%.

The other measured lesson: raising `min_weight` buys modularity by **throwing away retrieved
evidence**. At weight ≥ 3 modularity climbs to 0.656 but 69% of seeds end up isolated with no topic
at all. Coverage is the binding constraint for a legal answer, not modularity.

The blowup comes from hub nodes: generic keywords like `Inventive step (yes)` (2,841 decisions) join
thousands of decisions into one clique. **Mandatory mitigations, baked into the design:**

1. **IDF / document-frequency cut** on any node used as a co-occurrence bridge (keywords, and later
   extracted entities). Drop bridges above a df threshold (~40 worked).
2. **Weight by specificity** and require a **minimum edge weight** (≥ 2 shared specific bridges, or
   1 direct citation + 1 bridge).
3. **Degree cap** on expansion; **bounded seed set** (top 200–500, not the whole slice).
4. **Tune `gamma` upward** (1.5 gave the good split; 1.0 under-partitioned).
5. `concurrency: 1` + `randomSeed` — Leiden is non-deterministic at concurrency > 1, and a demo must
   reproduce.
6. Summarize only communities ≥ 5 members; bucket the 2–4 member tail as "related outliers".

---

## 3. Phases

### Phase 1 — Foundation cleanup & embeddings ✅ **DONE**

**1.1 Normalize `LegalProvision`.** ✅ `scripts/normalize_provisions.py` +
`importer/provisions.py`. `EPC1973_Art_056` and `EPC2000_Art_056` are the same article to an
attorney (16,877 + 11,715 decisions). The naive regex `(EPC1973|EPC2000)_Art_.*` sketched here
turned out to miss a third of the population, so the shipped rule parses
`<instrument>_<Art|R>_<number>` instead:

- instruments carry underscores (`RPBA_2020_Art_013(2)`, `Paris_Convention_Art_004`) and typos
  (`EpC2000`, `blankEPC 1973`, `PRBA2020`);
- suffixes must be stripped (`EPC2000_Art_056_(2007)`, `EPC1973_Art_056_Sent_1`);
- the instrument is *kept* in the canonical code — Art. 56 EPC ≠ Art. 56 PCT;
- the version is dropped only for the EPC, whose numbering is stable across 1973/2000. The
  **RPBA 2020 renumbered**, so `RPBA2020_Art_013` and `RPBA_Art_013` stay distinct.

Result: **3,077 of 4,205 codes → 764 `:Article` nodes, covering 98.85% of all 157,885 citations.**
The 1,128 unmapped codes are national court decisions, literature and country names — correctly
left as `:LegalProvision` only. Also emits `(:Decision)-[:CITES_ARTICLE]->(:Article)` (143,107)
so the Phase-4 structured channel filters on one hop without enumerating version variants.

**1.2 Resolve the `CitedCase` redundancy.** ✅ Same script. **71,237 redundant `CITES_CASE` edges
and 9,421 orphaned stubs deleted; 177 unresolved edges / 133 stubs kept** — those out-of-corpus
citations are the only record the citation happened. `enrich_graph.py` already creates
`(:Decision)-[:CITES]->(:Case)` for resolved citations but leaves the `CITES_CASE` → `:CitedCase`
stubs behind (71,414 stub edges vs 74,069 resolved). Delete only the stubs that have a resolved
counterpart; **keep unresolved ones** — for out-of-corpus and raw-text citations the stub is the only
record that the citation happened.

```cypher
MATCH (d:Decision)-[r:CITES_CASE]->(cc:CitedCase)
WHERE cc.appealNum IS NOT NULL
  AND EXISTS { (d)-[:CITES]->(:Case {caseKey: cc.code + '-' + cc.appealNum + '-' + cc.year}) }
DELETE r
WITH DISTINCT cc WHERE NOT (cc)<-[:CITES_CASE]-() DETACH DELETE cc
```

**1.3 Slice marking + paragraph-aware re-chunking** (D5, D7). ✅
`scripts/mark_demo_slice.py` marks `:DemoDecision` / `:DemoSection`;
`scripts/chunk_paragraphs.py` + `chunk_section_paragraphs()` in `importer/chunker.py` writes the
new generation. Splits `Section.text` on blank lines, keeps unnumbered continuation paragraphs with
the paragraph they belong to, and packs whole paragraphs to a 600-token budget, splitting on
sentence boundaries only when one paragraph exceeds it alone.

Three things the sketch above got wrong, found by inspecting real output:

1. **Roman/letter outline numbering is not paragraph numbering.** `I. THE REFERRED QUESTIONS` is a
   division heading; `I. The appellant lodged an appeal...` is a numbered paragraph. Length +
   terminal punctuation separate them. Without this, `paragraphRef` came out as `"I"` instead of the
   citable `"7"`. Decimal numbering is always treated as a paragraph, so `2.1 Admissibility`
   heading a paragraph keeps its ref.
2. **Sub-40-token orphan chunks** (a stray line from a list of amicus curiae parties) are noise in a
   vector index — merged into a neighbour.
3. **The corpus carries cp1252 bytes decoded as Latin-1**, so typographic quotes land in the C1
   control range (`\x93`/`\x94`). Repaired at chunk time; `Section.text` is left untouched.

Also denormalises an attorney-facing `Chunk.citation` — **`T 1924/17, Reasons 2.3`** (appeal number
unpadded, 2-digit year) — used as embedding context and as the citation string Phase 6 prints.

**Slice as built:** 1,114 decisions · 2,303 sections · **9,119 chunks** · 3.25M tokens ·
min 7 / avg 357 / max 904 tokens. Of the 8,022 Reasons chunks only **128 (1.6%) lack a paragraph
ref**; the ref-less remainder is mostly `AppealOrder`, whose orders are unnumbered by nature.

Also caught here: **~1.7% of the corpus stores the same decision twice** under different accession
numbers (`G190001EP1` / `G190001EX1` — OJ version and extract, byte identical). They share an ECLI
so they hang off one `:Case`; the marker keeps the fullest record per case. This was visible as
duplicate vector hits before the fix and would have double-counted seeds and community members.

**1.4 Embeddings.** ✅ Slice embedded:
`embed_chunks(node_label="DemoChunk", context_properties=["citation","headingContext"])` →
**9,119 / 9,119 nodes, 1536d, `demochunk_text_embedding` + `demochunk_text_fulltext` ONLINE.**
Note the property is `text_embedding`, not `embedding`.

Full corpus (optional, overnight, **not run**): `embed_chunks(node_label="Chunk")` — ~$5.50,
enables corpus-wide vector recall beyond the slice.

**Exit criteria:** ✅ all met. Probe queries return the leading CII authorities — vector search for
the COMVIK exclusion returns `G 1/19, Reasons 31` and `T 1463/11, Reasons 11` (Cardinal Commerce);
fulltext for `"T 641/00" AND "technical effect"` returns `T 489/14, Reasons 7` (the G 1/19 referral).

---

### Phase 2 — Legal-appeal ontology & entity extraction

**2.1 Design the domain ontology.** This is the intellectual core. Entity types a patent attorney
reasons with:

| Entity | Purpose | Example |
|---|---|---|
| `LegalIssue` | The ground in dispute | inventive step, novelty, added subject-matter, sufficiency, clarity, admissibility |
| `LegalTest` | Named doctrine/test applied | problem–solution approach, COMVIK approach, closest prior art, could-would, gold standard, technical effect |
| `ClaimFeature` | Technical feature under assessment | "training a neural network on user telemetry" |
| `PriorArtDocument` | The `D1`/`D2` documents in the reasoning | D1 = WO 2011/… |
| `Argument` | A party's submission | appellant: "the effect is technical because…" |
| `Finding` | The board's conclusion on an issue, with outcome | "no technical contribution → not inventive" |
| `ProceduralAct` | Procedural events | late filing, auxiliary request, remittal, oral proceedings |
| `Outcome` | Operative result | appeal dismissed, decision set aside, remitted, patent revoked/maintained |

Relationships: `MENTIONS` (chunk→entity), `ADDRESSES` (Argument→LegalIssue),
`RAISED_BY` (Argument→Party), `APPLIES_TEST` (Finding→LegalTest),
`RELIES_ON` (Finding→PriorArtDocument), `RESOLVES` (Finding→LegalIssue),
`DECIDED_AS` (LegalIssue→Outcome), `ESTABLISHED_IN` (LegalTest→Case — anchors doctrine to landmark
case law like `T 641/00`, `G 1/19`).

**2.2 Build the ontology in the Ontology DB.**
1. `setup_ontology_db`
2. Write the ontology via Cypher — including **aliases** (`Erfinderische Tätigkeit` → inventive step;
   `Art. 56` / `A56` / `Article 56 EPC` → the `Art_056` article), **normalizers** (case/whitespace,
   strip `(yes)`/`(no)` into a separate outcome field), and a **blocklist** for boilerplate.
3. `generate_schema_from_ontology` → extraction schema.

Save the ontology Cypher to `ontology/legal_appeal_ontology.cypher` so the demo is reproducible.

**2.3 Run extraction.** `extract_entities(ontology_name="legal_appeal", source_label="DemoChunk",
text_parallel=20, batch_size=10)`. Async — poll `check_extraction_status`.

Budget estimate for the slice: ~7.2k chunks × ~1,260 in / ~300 out tokens ≈ **9M in / 2.2M out**.

**2.4 Post-extraction consolidation.** Entity resolution across chunks (merge on normalized name +
type), then compute and store `entity.df` (document frequency) — **required by the Phase 4 hub
suppression**, so this is not optional polish.

**Exit criteria:** every slice chunk has ≥ 1 `MENTIONS`; entity df distribution computed; spot-check
20 chunks for extraction precision against the source text.

---

### Phase 3 — Question understanding

`retrieval/question_parser.py`. One LLM call with structured output, mapping the attorney's question
to an intent object:

```python
class QueryIntent(BaseModel):
    legal_issues:    list[str]         # → LegalIssue / Article lookup
    legal_tests:     list[str]         # → LegalTest lookup
    named_cases:     list[str]         # "T 641/00" → direct Case lookup
    technical_terms: list[str]         # → vector + fulltext
    date_from:       date | None
    date_to:         date | None
    ipc_prefixes:    list[str]
    outcome_filter:  str | None        # allowed / dismissed / remitted
    semantic_query:  str               # cleaned text for vector search
```

Worked demo questions:
- *"How have the boards applied the COMVIK approach to machine-learning claims since 2018?"*
- *"What arguments succeeded against added-subject-matter objections for numerical ranges?"*
- *"Which decisions cite T 641/00 and still found a technical effect in a business method?"*

---

### Phase 4 — Retrieval, fusion, subgraph induction ✅ **DONE (against the `Keyword` layer)**

`retrieval/seed_retrieval.py` + `retrieval/subgraph.py`, driven by `scripts/probe_topics.py`.
Per the build order this runs against the existing `:Keyword` layer; Phase 2 swaps the entity
channel and the entity bridges for the extracted layer and compares.

**4.1 Four parallel channels** (each returns ranked chunks/decisions):

| Channel | Tool | Catches |
|---|---|---|
| Semantic | `vector_search` on `demochunk_text_embedding` | paraphrase, concept drift |
| Lexical | `fulltext_search` on `chunk_text_fulltext` | exact terms, case numbers `T 641/00` |
| Entity | Cypher on the Phase-2 layer | `LegalTest{name:'COMVIK'}` → chunks |
| Structured | Cypher on bib metadata | date / IPC / board / outcome / Article filters |

**4.2 Fusion.** Reciprocal rank fusion across channels → **top 200–500 seeds** (hard cap, per §2.3).

**4.3 Induction.** Expand seeds along typed edges with a per-node degree cap:
`Chunk→Section→Decision→Case`, `Decision-[:CITES]->Case` (1–2 hops), co-citation,
`Chunk-[:MENTIONS]->Entity<-[:MENTIONS]-Chunk` **filtered to entities below the df threshold**.
Emit a weighted edge list: direct citation = 1.0, shared specific entity = 2.0, summed, **keep
weight ≥ 2.0**.

**Exit criteria:** ✅ induced subgraph stays under ~5k nodes / ~50k edges — asserted in code
(`SubgraphTooLarge`). Measured on the three worked questions: **564–700 nodes, 1,075–3,006 edges**.

Two design points that came out of building it:

- **Bridges are not nodes.** Cited cases, keywords, articles and IPC classes stay bridges, so the
  landmark authorities that make the topology meaningful — `T 641/00` (2002), `T 769/92`, `T 1227/05`
  — contribute without dragging un-chunked, pre-2015 decisions into a graph whose members have to be
  summarisable in Phase 6.
- **A fourth bridge channel was added:** shared canonical `Article` (from Phase 1.1) and shared IPC
  class, the latter at half weight since technical-field similarity is a weaker signal for a *legal*
  topic than co-citation is. Measured pair contributions were comparable across all four
  (IPC 8,888 · Keyword 6,543 · Case 5,412 · Article 2,480), and the slice's `Keyword` layer alone is
  too thin to carry the graph: **2.6 keywords per decision, and 1,025 of its 1,251 keywords have
  df = 1**, so they can never bridge anything. That is independent evidence for D4 — the extracted
  entity layer is what this stage actually needs.

---

### Phase 5 — Leiden topic detection ✅ **DONE**

`retrieval/communities.py`. Project the Phase-4 edge list with the Cypher-aggregation form —
note `undirectedRelationshipTypes: ['*']`, since Leiden requires an undirected graph — and run
Leiden with the **validated parameters**:

```cypher
CALL gds.leiden.stats($graph, {
  gamma: 1.5, maxLevels: 10, randomSeed: 42,
  concurrency: 1, relationshipWeightProperty: 'weight'
})
```

Then `gds.leiden.stream` for assignments. Always `gds.graph.drop` in a `finally` — leaked projections
eat the 1 GB heap across demo runs.

Per community, compute a **topic identity** before summarizing: the entities most over-represented
inside the community versus the corpus baseline (TF-IDF style). This is what makes a cluster
"COMVIK / non-technical business features" rather than "community 7".

**Exit criteria:** ≥ 5 communities with ≥ 5 members; no community > 25% of the subgraph. If violated,
raise `gamma` / lower the df threshold and retry (bounded retry loop, log what changed).

✅ **Met on all three worked questions** — 13–18 usable communities, modularity 0.516–0.627, largest
community 10–14%. `gds.graph.list()` is empty after runs, so the projections are not leaking.
**Determinism verified:** three consecutive runs gave bit-identical community assignments and
modularity to 6 decimals.

The topics are doctrinally coherent, which is the thing that actually matters — for the COMVIK
question, Leiden separated:

| Community | Identifying bridges (lift × in/out) | Reads as |
|---|---|---|
| 53 decisions | `T 336/14` 10.6× · `T 1802/13` 11.6× · `T 1143/06` 8.6× · `T 1741/08` 5.8× | GUI / presentation of information, broken technical chain |
| 45 decisions | `T 1463/11` 8.6× · `T 641/00` 2.7× · `Inventive step - skilled person` 13.0× | COMVIK / the notional business person |
| 44 decisions | `G 1/19` 6.6× · `T 769/92` 14.5× · `T 1227/05` 8.0× | Simulation and the technical-effect requirement |
| 38 decisions | `T 2230/10` 16.6× · `T 598/14` 13.8× · `T 697/17` 10.4× | Business methods / data processing |
| 35 decisions | `G 10/93` 18.3× · `Art. 12 RPBA` 6.2× · `Late-filed request - admitted (no)` 8.9× | Admissibility of late-filed requests |

Topic identity needed one addition: bridges are filtered to **lift ≥ 1.5**. Without it every
community lists `Art. 56 EPC` at lift 1.0 — cited by all 700 nodes, so it carries no information
about which topic a community is.

---

### Phase 6 — Summarization & synthesis

`retrieval/summarize.py`.

**6.1 Per-community, map-reduce.** Map: summarize member chunks in batches (grouped by decision so
one decision's reasoning stays together). Reduce: fuse into a topic card:

```
Topic: Non-technical business features under COMVIK
Legal issue: inventive step (Art. 56 EPC)  ·  12 decisions  ·  2016–2024
Doctrine: features solving a purely administrative problem are excluded from the
          inventive-step assessment (COMVIK, T 641/00)
Outcomes: dismissed 9 · set aside 3
Key decisions: T 1924/17 (Reasons 3.2) · T 0817/16 (Reasons 5.1) · …
```

**6.2 Final synthesis.** One call over the topic cards + the original question → an answer organized
by topic, every claim carrying a case number + ECLI + paragraph ref. Explicitly instruct: no claim
without a citation drawn from the retrieved set.

**6.3 Cache back to the graph.** Persist `(:CommunitySummary {queryFingerprint, communityId, …})`
linked to member decisions, so repeat demo questions are instant and the summaries are inspectable
in Bloom.

---

### Phase 7 — Demo surface

- `ask.py "question"` — single entrypoint running Phases 3→6, printing the formatted answer plus a
  `--explain` mode showing seed counts, subgraph size, community distribution, and modularity. The
  explain mode *is* the demo: it makes the graph reasoning visible instead of a black-box answer.
- `demo/questions.md` — 5–6 canned questions with expected answer shape.
- `demo/expected/` — recorded outputs for regression comparison (fixed `randomSeed` makes this
  meaningful).

---

## 4. Deliverables

```
DEMO_IMPLEMENTATION_PLAN.md              this file
ontology/legal_appeal_ontology.cypher    Phase 2.2 — ontology definition
outputs/schemas/legal_appeal_entities.py generated extraction schema
importer/chunker.py                      ✅ extended: chunk_section_paragraphs (Phase 1.3)
importer/provisions.py                   ✅ code -> canonical Article parsing (Phase 1.1)
scripts/normalize_provisions.py          ✅ Phase 1.1 + 1.2
scripts/mark_demo_slice.py               ✅ marks :DemoDecision / :DemoSection
scripts/chunk_paragraphs.py              ✅ writes the :DemoChunk 'para-v1' generation
retrieval/db.py                          ✅ Neo4j + OpenAI clients from .env
retrieval/intent.py                      ✅ QueryIntent model (Phase 3 fills it via LLM)
retrieval/seed_retrieval.py              ✅ Phase 4.1–4.2
retrieval/subgraph.py                    ✅ Phase 4.3
retrieval/communities.py                 ✅ Phase 5
scripts/probe_topics.py                  ✅ Phase 4+5 driver: --explain view and --sweep grid
retrieval/question_parser.py             Phase 3
retrieval/summarize.py                   Phase 6
ask.py                                   Phase 7 entrypoint
demo/questions.md, demo/expected/        Phase 7 fixtures
```

`requirements.txt` additions: ✅ `openai`, `pydantic` (query embedding, LLM calls, structured
intent/output — outside the MCP path). `litellm` not needed so far; `openai` covers both the
embedding and chat calls against the configured models.

---

## 5. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Hub blowup in subgraph induction** | **High — measured, not hypothetical** | §2 mitigations; assert subgraph bounds in code |
| **1 GB heap** vs GDS projections | High | Bounded seeds, `stream`/`stats` not `write`, drop in `finally` |
| Entity extraction quality on split chunks | Medium | Phase 1.3 paragraph chunking; spot-check gate in 2.4 |
| Leiden non-determinism | Medium | `concurrency: 1` + `randomSeed: 42` |
| GDS Community concurrency cap (4) | Low | Subgraphs are small; not on the critical path |
| Multilingual corpus (18k de/fr decisions) | Low for demo | Slice is EN-only; ontology aliases carry de/fr terms as a stretch goal |
| Extraction cost creep if slice grows | Medium | `:DemoChunk` marker makes the blast radius explicit and re-runnable |
| Summaries hallucinating uncited holdings | High for credibility | Citation-required prompting + every topic card traces to member chunk IDs |

---

## 6. Suggested build order

1. ✅ **Phase 1** (cleanup, re-chunk, embed slice) — unblocks everything, no LLM cost beyond embeddings.
2. ✅ **Phase 4 + 5 against the existing `Keyword` layer** — the §2 recipe already works *today*
   without the entity layer. This gets an end-to-end demo running early and de-risks the hardest
   stage first. **Confirmed: the retrieval → induction → Leiden spine works and is reproducible.**
3. **Phase 2** (ontology + extraction) — then swap `Keyword` bridges for real entity bridges and
   compare community quality. Step 2 sharpened the case for this: the slice's keyword layer averages
   2.6 keywords per decision and 82% of its keywords have df = 1, so co-citation is currently doing
   most of the work. Co-citation cannot express *why* two decisions belong together, which is
   exactly what the topic cards in Phase 6 have to say.
4. **Phase 3, 6, 7** — question parsing, summarization, CLI.

Step 2 is the important sequencing call: the retrieval→Leiden→summarize spine is provably buildable
now, so build it before spending extraction budget.
