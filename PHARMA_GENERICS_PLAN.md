# EPO Board of Appeal Corpus — Business Questions and Delivery Plan
## Perspective: in-house / external patent counsel, generic pharmaceuticals

**Purpose.** Define the business questions a generics patent lawyer actually asks of Board of Appeal
case law — for freedom to operate (FTO), litigation, and invalidation — and set out a plan to answer
5–10 of them on this corpus using semantic retrieval plus GraphRAG grounding.

All counts below were measured against the live database on 2026-09-10, not estimated.

---

## 0. What this corpus is, commercially

51,299 decisions, 1979-03-01 → **2026-03-04**, EN 33,330 / DE 13,876 / FR 4,093.

Pharma/chemistry footprint (IPC first-4 in `A61K, A61P, C07D, C07C, C07K, C12N`):

| Cut | Decisions |
|---|---|
| All pharma/chem | **6,639** |
| …of which inter-partes (has an opponent) — i.e. **opposition appeals** | **4,621** |
| …EN, decided ≥ 2010 | 3,337 |
| …EN, ≥ 2010, inter-partes — **the working slice** | **2,545** (23,717 chunks, 9.93 M tokens) |

`A61K` alone is the **single largest class in the whole corpus** (3,929 decisions) — bigger than
`G06F` (2,516). This corpus is, by volume, more a life-sciences corpus than a software one, which is
the opposite of the assumption behind the existing CII demo slice.

Doctrine coverage, measured by fulltext hit counts over all 666k chunks (distinct decisions):

| Generics-relevant doctrine | Decisions |
|---|---|
| "whole scope" / whole claimed range (effect across the claim) | 1,238 |
| disclaimer(s) | 1,101 |
| therapeutic application / "suitable for use in" | 994 |
| post-published (evidence) | 907 |
| antibody | 820 |
| purity | 353 |
| second medical use | 320 |
| prodrug / pharmaceutically acceptable salt | 303 |
| selection invention / selection from a list | 288 |
| polymorph / crystalline form | 273 |
| Swiss-type | 210 |
| dosage regime(n) | 145 |
| enantiomer / racemate | 128 |
| Markush | 114 |
| bioequivalence | 24 |

Landmark authorities, by in-corpus citation count (`(:Decision)-[:CITES]->(:Case)`):

`G 3/14` 786 · `G 2/10` 599 · `G 1/03` 576 · `G 1/93` 373 · `T 939/92` 362 · `G 2/98` 349 ·
`G 5/83` 326 · **`G 2/08` 134** · **`G 2/21` 118** · **`T 609/02` 112** · **`T 1329/04` 79** ·
`G 1/15` 77 · `G 1/16` 74 · `T 990/96` 42 · `T 1067/08` 39.

The three bolded clusters are the pharma-specific core: dosage-regimen claims (G 2/08), the
plausibility / post-published-evidence rule (G 2/21, T 1329/04, T 609/02). **118 decisions already
apply G 2/21** — a doctrine only 3 years old, with no settled commentary. That is the single most
commercially live question in this corpus for a generics practice.

Generic and originator parties are present as named opponents: Teva 126 · Fresenius Kabi 102 ·
Hexal 91 · STADA 79 · Generics [UK] 76 — plus **Strawman Limited, 90 oppositions**, i.e. the
straw-man channel is directly observable.

### 0.1 What this corpus cannot answer — read before relying on it

This must be stated plainly, because the failure mode of a legal-AI tool is confident scope creep.

1. **It contains no patent claims and no patent specifications.** Only the Board's own text. So the
   literal FTO question — *"is my product within the scope of a live claim?"* — **cannot be answered
   here at all.** What the corpus answers is the adjacent and arguably more valuable question:
   *"if we attack this patent, or if we are sued on it, what happens?"*
2. **Appeals only.** No opposition-division or examining-division decisions. Every base rate computed
   here is conditional on the case having been appealed — a selected, harder-fought population. Do
   not quote a revocation rate from this corpus as an EPO-wide revocation rate.
3. **No national or UPC outcomes**, no SPC data, no product/marketing-authorisation link. Mapping a
   patent to a molecule, a brand, or a launch date requires external data (EPO OPS/Espacenet for
   claims and family, EMA/Orange-Book-equivalent for products).
4. **No settlement or withdrawal economics.** A withdrawn opposition is visible only as a procedural
   termination, and the commercial reason (a licence, a settlement) is never in the text.
5. `A61K` is diluted — it carries nutrition, probiotics, cosmetics and device-adjacent subject
   matter (infant formula, hyaluronic acid fillers). A pure IPC filter is not a pharma filter;
   combine with `A61P`/`C07D` and semantic filtering.
6. **22% of pharma decisions are DE/FR.** German matters commercially here — several of the most
   active generic opponents are German. An EN-only slice silently drops them.

---

## 1. The business questions

Eleven questions, ordered by commercial value to a generics practice. Each states why it matters,
what in the graph answers it, and what must be built first. Q11 sits in Cluster B beside Q5, which
it complements rather than duplicates: Q5 compares boards *per ground*, Q11 measures net direction of
outcome.

### Cluster A — Invalidation strategy (clearing the way)

**Q1. Since G 2/21, when does post-published evidence rescue an inventive-step case — and when is
the asserted technical effect held not "encompassed by the technical teaching" of the application
as filed?**
*Why it matters:* this is the central battleground for attacking second-medical-use and
formulation patents. If the originator's efficacy data came after filing, G 2/21 decides whether it
counts. 118 decisions apply it, all since 2023, and the case law is still forming — no treatise
covers it yet, so a practice that can read the trend line has a real edge.
*Answers with:* semantic retrieval over Reasons paragraphs + `CITES → G 2/21` as a hard graph
filter + per-decision outcome and ground-level disposition. Output should be a split of the 118 into
"effect accepted" vs "effect refused", with the distinguishing fact pattern per side.
*Needs:* outcome layer, ground disposition layer, pharma slice embedded.

**Q2. Which invalidity ground actually kills pharma patents on appeal — sufficiency (Art. 83),
added matter (Art. 123(2)), or inventive step (Art. 56) — and how does that vary by subject-matter
type and decade?**
*Why it matters:* direct resource allocation. An opposition brief has finite pages and the
opponent's evidence budget (experiments, expert declarations) follows the ground chosen. Base rates
per ground, per claim type, tell you where to spend.
*Answers with:* pure graph analytics — `CITES_ARTICLE` × outcome × IPC × year. No LLM needed once
the outcome layer exists. This is the cheapest high-value question in the list.
*Needs:* outcome layer + ground disposition layer.

**Q3. What do boards require to sustain novelty and inventive step of a *secondary* patent — salt,
polymorph, purity, enantiomer, particle size, narrow range selected from a Markush genus?**
*Why it matters:* the evergreening fight. The compound patent expires; the secondary patents are
what actually blocks launch. ~1,000 decisions across the polymorph/purity/selection/enantiomer/
Markush topics.
*Answers with:* semantic retrieval (these concepts are expressed in wildly varying language — pure
keyword search fails on "crystalline modification II", "Form B", "anhydrate") + a Leiden topic split
to separate the two-lists novelty line from the technical-effect/unexpected-property line.

**Q4. Which amendment moves survive Art. 123(2) in opposition — intermediate generalisation, range
narrowing to a disclosed endpoint, deletion from a list, undisclosed disclaimers?**
*Why it matters:* the proprietor's escape route in opposition is amendment. Knowing which auxiliary
requests will survive is what sets the settlement value of the whole dispute, and the inescapable-
trap (Art. 123(2)/(3)) squeeze is the most powerful single attack a generic has.
*Answers with:* `CITES → G 1/03, G 2/10, G 1/16` graph channel + semantic retrieval + outcome.

### Cluster B — Litigation forecasting and party intelligence

**Q5. Do outcome probabilities for a given ground differ measurably across the chemistry boards
(3.3.01–3.3.10)?**
*Why it matters:* you cannot choose your board, so this is **not** forum shopping — it is
forecasting. Knowing that your board decides sufficiency attacks in a particular way changes whether
you settle, and how you frame the ground. Must be reported as descriptive base rates with confidence
intervals and explicit confounders (boards are specialised by subject matter, so raw differences are
partly composition, not tendency).
*Answers with:* graph analytics over `DECIDED_BY` × outcome × ground × IPC.

**Q6. What is the track record of specific opponents and proprietors, and does the number of
opponents predict revocation?**
*Why it matters:* opponent count is a free proxy for the commercial value of the patent — one
observed A61K case drew 7 opponents. And knowing an originator's pattern (does it concede by
withdrawing approval of the text, or fight to the order?) is direct input to settlement strategy.
The straw-man question ("Strawman Limited", 90 cases) is a live one: who is behind them, and do
straw-man oppositions perform differently?
*Answers with:* graph analytics over `HAS_OPPONENT`/`HAS_APPLICANT` × outcome.
*Needs:* **party resolution** — the raw `:Party` layer has surface duplicates ("Siemens AG" vs
"Siemens Aktiengesellschaft", four BASF variants) and no corporate-group rollup (Sandoz/Hexal →
Novartis; ratiopharm/Actavis → Teva). Without this the question returns fragments.

**Q11. Which boards decide in favour of the patentee?**
*Why it matters:* Q5 asks whether boards differ *on a given ground*; this asks the blunter
commercial question — net direction of outcome. For a generic it sets the expected value of an
opposition before a brief is written. Same framing caveat as Q5: you cannot choose your board, so
this is forecasting, not forum shopping.

Deliberately **pooled over the whole period rather than sliced by year.** A per-year, per-board rate
is not answerable in this corpus: in the pharma opposition slice since 2016 only 9 boards reach 30
decisions *in total*, and several have years with 1–2 **[verified]**. Pooling is what makes the
question tractable. Time re-enters as a **robustness check, not a reporting axis** — see below.

*The definition is the hard part, and it must be settled before any number is produced.*
"In favour of the patentee" is **not** the dismissal rate. In an opposition appeal either side may be
the appellant, so *appeal dismissed* is pro-patentee when the opponent appealed and anti-patentee
when the proprietor did. A dismissal rate computed without the appellant's role is not a weak
measure — it averages two opposite things.

Worse, **the available outcomes differ by appellant role**, so the rates are not even comparable
across strata. Where only the proprietor appealed the board cannot revoke the patent — that would be
reformatio in peius, prohibited under G 9/92 / G 4/93. A rough probe over the pharma opposition slice
confirms this cleanly **[verified]**: among proprietor-only appeals, revocations are 0 on boards
3.3.01, 3.3.04, 3.3.07, 3.3.08 and 3.3.10. Conversely, where both sides appealed, revocation is the
modal result (3.3.04 56/111, 3.3.08 42/95, 3.3.10 10/13) and clean dismissals are near zero.

The measure must therefore be **computed within appellant-role strata and reported per stratum**,
never pooled into one headline percentage. A single "board X favours patentees 62% of the time"
number is not a simplification of this — it is a different and wrong quantity.

| Operative result | Score |
|---|---|
| Patent maintained as granted | pro-patentee |
| Maintained in amended form | partial — report separately, never merged into either side |
| Patent revoked | anti-patentee |
| Remitted / terminated / inadmissible | excluded from the rate, counted in the denominator note |

*Answers with:* graph analytics over `DECIDED_BY` × outcome × appellant role, with an IPC filter to
hold the technical field roughly constant.

*Needs:* the P2 outcome layer **plus the P2b appellant-role layer** — and P2b is the real blocker,
not the outcome layer. See the measured coverage problem in P2b below: with naive phrase matching,
**60–90% of the pharma slice falls into `unknown`** (board 3.3.07: 774 unknown against 41 opponent /
43 proprietor / 2 both). Until that is fixed this question has no usable denominator.

*Which boards are measurable at all*, counting only decisions whose appellant role is currently
recoverable **[verified]**: 3.3.10 (213) · 3.3.01 (167) · 3.3.02 (144) · 3.3.08 (110 + 95 both) ·
3.3.04 (101 + 111 both) · 3.3.07 (84). Not measurable: 3.3.03 (3) · 3.3.09 (6) · 3.3.06 (10) ·
3.3.05 (11). So the honest deliverable is **six boards, each with per-stratum rates, denominators and
Wilson intervals** — and an explicit "insufficient data" for the rest rather than a number.

*Time as a robustness check.* Compute the pooled figure, then split at **2020-01-01** (the RPBA 2020
regime break) and check whether the board ranking holds. If it holds, the pooled number is
trustworthy and the stability is itself a finding. If it flips, **report the instability instead of
the number** — a pooled average across two different procedural regimes would otherwise describe a
world that no longer exists. G 2/21 (2023) is a second candidate break, though post-2023 volumes are
too thin per board to test separately.

*One further confounder to surface, not bury:* board **composition churns**, so a pooled figure spans
several panels. With the 2026 business distribution scheme now loaded (`:BoardMember`, 159 people —
see `data/bds/README.md`), the temptation to attribute a tendency to named individuals is immediate
and should be resisted: report at board level only, per the `EXAMINER_PLAN.md` §3 constraint. A board
is an institution with turnover, and that is a limit on what the measure can mean, not a detail.

**Q7. Post-RPBA-2020, how often is late-filed evidence or a late request admitted under Art. 12(4)
and 13(2) RPBA — and on what reasoning?**
*Why it matters:* an opponent's best prior-art document is frequently found late. If it is not
admitted, the attack dies on procedure regardless of merit. This is pure downside risk and the
single most preventable way to lose.
*Answers with:* `CITES_ARTICLE → RPBA_2020_Art_012/013` (already canonicalised in Phase 1.1) +
semantic retrieval + outcome. Note the Phase-1.1 finding that RPBA 2020 renumbering is preserved as
distinct from the old RPBA — required for this question to be correct.

### Cluster C — Freedom to operate and clearance

**Q8. How have boards construed the scope and validity of second-medical-use and Swiss-type claims —
including dosage-regimen claims after G 2/08?**
*Why it matters:* this is the closest the corpus gets to real FTO. It determines whether a
carved-out ("skinny") label is a defensible launch strategy and how much residual infringement risk
a purpose-limited claim leaves. 320 + 210 + 145 decisions.
*Answers with:* semantic retrieval + `CITES → G 2/08, G 5/83` + `CITES_ARTICLE → Art. 54(4)/(5)`.
*Caveat to surface in every answer:* the EPO decides validity, not infringement. Scope findings here
are persuasive context for national/UPC infringement, not determinative.

**Q9. "Here is our candidate product in plain language — what has the EPO already decided about
subject matter like this?"**
*Why it matters:* this is the everyday clearance task, and the flagship use of semantic embeddings.
The analyst describes the product (an extended-release oral formulation of a poorly soluble weak
base, film-coated, once-daily) and gets the analogous decisions back. Keyword search cannot do this
— the decisions use the sponsor's own terminology, not the analyst's.
*Answers with:* vector search over paragraph chunks, then graph expansion to the decision, its
grounds, its outcome, and its cited authorities. **The clearest demonstration of semantic vs keyword,
and the easiest to make legible to a non-technical audience.**

### Cluster D — Drafting support with GraphRAG grounding

**Q10. Draft the argument: given a ground and a fact pattern, assemble the supporting authorities
with exact paragraph citations, plus the counter-arguments boards have rejected.**
*Why it matters:* this is where the time goes. And it is where a plain-LLM tool is
professionally unusable — a hallucinated case number or a real case number with an invented holding
is a malpractice event, not a bug. The value proposition is precisely that GraphRAG grounds every
proposition in a retrieved paragraph.
*Answers with:* the full pipeline, exploiting the `Chunk.citation` property already built
(`T 1924/17, Reasons 2.3`) so every sentence carries a verifiable pinpoint cite.
*Hard requirement:* no proposition without a citation drawn from the retrieved set, and every
citation resolvable back to a chunk ID that a human can open. Refuse to answer over silently
returning an ungrounded claim.

**Selection for a first delivery: Q1, Q2, Q3, Q7, Q9, Q10.** Q1 is the highest-value and most
defensible (recent, bounded, 118 decisions). Q2 and Q7 are near-free once the outcome layer exists.
Q9 and Q10 are the two capability demonstrations (semantic search; grounded drafting). Q3 exercises
the topic-clustering machinery on genuinely messy language. Q5, Q6, Q8, Q11 follow once party
resolution and the outcome layer are validated.

Q11 in particular should **not** be brought forward, and is now gated on P2b rather than on P2. It is
the most likely of the eleven to be quoted out of context — a board-level "favours patentees" number
travels further than its caveats do — so it ships only once appellant-role coverage clears the
`unknown` < 25% gate, the per-stratum reporting is in place, and sub-threshold suppression is
demonstrably working.

---

## 2. Plan

The existing pipeline (`DEMO_IMPLEMENTATION_PLAN.md`, Phases 1–5) is **reusable as-is** — the
retrieval → subgraph induction → Leiden → summarise spine is domain-neutral and already validated,
including the measured hub-suppression parameters that keep the induced subgraph usable. What is
domain-specific is the slice, the ontology, and two structural layers that do not yet exist.

### Phase P1 — Pharma slice, re-chunk, embed  *(no LLM cost beyond ~$0.20 of embeddings)*

Reuse `scripts/mark_demo_slice.py`, `scripts/chunk_paragraphs.py`, `embed_chunks`.

- Slice definition: IPC ∈ {A61K, A61P, C07D, C07C, C07K, C12N} **AND** inter-partes (has opponent)
  **AND** decided ≥ 2010. Language: start EN (2,545 decisions), keep the DE/FR extension explicit as
  a follow-on rather than a silent omission.
- New marker labels `:PharmaDecision` / `:PharmaSection` / `:Chunk:PharmaChunk`, generation
  `pharma-para-v1`. Same marker-label pattern as D7 — bounded, re-runnable blast radius.
- Paragraph-boundary re-chunking with the `Chunk.citation` denormalisation. Non-negotiable: the
  citable unit in a legal answer is `T 1234/15, Reasons 2.3`.
- Embed: 23,717 chunks ≈ 9.93 M tokens ≈ **$0.20**. Also embed `HeadNote` and `Catchword` chunks —
  in pharma these are unusually informative and short, so they make excellent high-precision seeds.
- **Also embed the full corpus** (657k chunks, ~$5.50 per the existing estimate). At this price there
  is no reason to keep semantic recall confined to a slice; extraction is what needs bounding, not
  embedding.

*Exit:* vector search for `"post-published evidence of a technical effect not derivable from the
application as filed"` returns G 2/21-citing decisions in the top 10; for
`"crystalline form with improved dissolution"` returns polymorph decisions.

### Phase P2 — Outcome layer  ← *the critical missing piece*

**None of Q1, Q2, Q5, Q6, Q7, Q11 can be answered without this, and it does not exist today.**

`AppealOrder` text is short, formulaic and machine-parseable. Verified samples include
`The appeal is dismissed.` · `1. The decision under appeal is set aside. 2. The patent is revoked.` ·
`…set aside… remitted to the opposition division with the order to maintain the patent on the basis
of auxiliary request 6…` · `The appeal proceedings are terminated.` · `…Reimbursement of the appeal
fee is ordered.`

Build a **rule-based** classifier (not an LLM) over 51,263 `AppealOrder` nodes, emitting
`(:Decision)-[:HAS_OUTCOME]->(:Outcome {type})` with types: `dismissed`, `set_aside_revoked`,
`set_aside_maintained_as_amended`, `set_aside_maintained_as_granted`, `remitted`, `terminated`,
`inadmissible`; plus booleans `feeReimbursed`, `costsApportioned` and the surviving request
(`auxiliary request 6`).

Rules, not an LLM, because outcome is the join key for every statistic downstream — it must be
auditable, deterministic and 100% reproducible, and a 2% LLM error rate would silently poison every
base rate. Manually label 200 random orders as a test set; require ≥ 99% precision, and route
anything unmatched to an explicit `unclassified` bucket rather than guessing. **Report the
`unclassified` count in every answer that uses base rates.**

**P2b — appellant-role layer.** Required by Q11, and it sharpens Q5 and Q6 for the same reason: in
an inter partes appeal the operative result only has a direction once you know who appealed. Emit
`Decision.appellantRole ∈ {proprietor, opponent, both, unknown}`.

**This is harder than the outcome layer, and the effort must not be underestimated.** Corpus-wide
phrase counts look encouraging — `"appellant (opponent)"` 5,881 decisions, `"appellant (patent
proprietor)"` 3,356, `"respondent (patent proprietor)"` 3,798, cross-appeals 930 — but that is only
~30% of the 30,808 inter partes decisions, and **within the pharma opposition slice the naive
patterns leave 60–90% unresolved** **[verified]**:

| Board | proprietor | opponent | both | **unknown** |
|---|---|---|---|---|
| 3.3.07 | 43 | 41 | 2 | **774** |
| 3.3.04 | 31 | 70 | 111 | **665** |
| 3.3.02 | 35 | 109 | 12 | **592** |
| 3.3.01 | 76 | 91 | 12 | **429** |
| 3.3.10 | 82 | 131 | 13 | **326** |
| 3.3.08 | 35 | 75 | 95 | **339** |

The parenthetical formula is a modern, English convention. Older decisions and the 22% DE/FR
population use other constructions ("the opponent lodged an appeal", "die Einsprechende hat
Beschwerde eingelegt"), and board 3.3.10 shows the same problem in the *outcome* parse — 285 of its
326 `unknown`-role decisions also fail the order-text patterns, which points at older or
non-English order formulae rather than at the role extraction alone.

So P2b is **rules first, LLM for the residue**: exhaust the cheap formulae, then run a bounded
extraction pass over the remaining `SummaryOfFacts` openings, which are short and highly stereotyped.
Budget this as a real work item, not a day.

Two design points:

- `both` is a real category, not a fallback — where each side appealed, no dismissal is directional
  and the case must be scored on the operative result alone.
- `unknown` must stay visible in every denominator, and ex parte appeals have no opponent to begin
  with.

*A free correctness gate:* reformatio in peius means a proprietor-only appeal **cannot** end in
revocation. Any `proprietor` + `revoked` pair is therefore a labelling error in one of the two
layers. The probe already shows this holding — 0 such pairs on five of six measurable boards, 4 on
3.3.02 — so those 4 are the first cases to inspect. Assert this invariant in code and fail loudly.

*Exit:* `unknown` below 25% in the pharma slice; ≥ 95% agreement on a hand-labelled sample of 100
inter partes decisions; zero `proprietor` + `revoked` pairs; every Cluster-B answer prints its
`unknown` share.

*Effort: P2 small (1–2 days). P2b is the larger of the two — assume a week including the extraction
pass and the multilingual formulae. Value: unlocks five of the eleven questions.*

### Phase P3 — Ground-level disposition layer

Outcome alone says who won, not *on what*. Q2 needs per-decision, per-ground findings:
Art. 54 / 56 / 83 / 84 / 123(2) / 123(3) → decided-for-proprietor / decided-for-opponent /
not-reached.

Two sources, combined:
1. **`Keyword`** — the EPO's own headword layer already carries `Inventive step - (no)`,
   `Sufficiency of disclosure - (yes)`, `Amendments - added subject-matter (yes)`. But it is a mess
   of surface forms (`Inventive step (yes)` / `Inventive step - (yes)` / `Inventive step - yes` /
   `Erfinderische Tätigkeit - (ja)` are four nodes for one concept) and averages only ~2.6 keywords
   per decision with a long df=1 tail. Normalise into `(:Ground)` + a parenthetical yes/no outcome —
   this is the same normalisation Phase 1.1 did for provisions, and the D4 rationale applies.
2. **Extraction from Reasons text** where keywords are absent or uninformative.

*Exit:* ≥ 80% of slice decisions have at least one typed ground disposition; the keyword-derived and
text-derived dispositions agree on ≥ 90% of the cases where both exist (disagreements are the
interesting audit set).

### Phase P4 — Party resolution

Canonical `(:Organisation)` above `:Party`, in two steps: (a) string normalisation for legal-form
and case variants; (b) a **hand-curated** corporate-group table for the ~100 organisations that
matter in pharma (Teva ⊃ ratiopharm, Actavis; Novartis ⊃ Sandoz, Hexal; Viatris ⊃ Mylan; plus the
straw-man filers). Hand-curated because M&A history is not inferable from strings and a wrong
rollup produces a confidently wrong track record. Flag `isStrawMan` where identifiable.

*Needed by Q6 only — defer if Q6 is out of the first delivery.*

### Phase P5 — Pharma ontology and entity extraction

Reuse the ontology-DB path (D4) and `extract_entities` with `source_label="PharmaChunk"`. Replace
the CII entity set with:

| Entity | Example |
|---|---|
| `ActiveIngredient` (INN) | atorvastatin, pembrolizumab |
| `TherapeuticIndication` | type 2 diabetes, multiple sclerosis |
| `ClaimType` | compound · salt · polymorph · formulation · process · second-medical-use · dosage-regimen · device-combination |
| `LegalTest` | problem–solution · closest prior art · could-would · two-lists novelty · gold standard · plausibility / technical teaching (G 2/21) · reformulation of the technical problem |
| `PriorArtDocument` | D1 = WO 2004/… (the `D`-numbering in the reasoning) |
| `EvidenceType` | post-published data · comparative example · expert declaration · experimental report · common general knowledge |
| `TechnicalEffect` | improved bioavailability, reduced hygroscopicity |
| `Argument` / `Finding` | party submission → board's conclusion on a ground |

Aliases must carry DE/FR terms (`Erfinderische Tätigkeit`, `activité inventive`) so the ontology
extends to the 22% non-EN pharma population without a rebuild.

Cost: 23.7k chunks × ~1.3k in / ~0.3k out ≈ 31 M in / 7 M out tokens. Consider extracting on the
~8k `Reasons`-only chunks of the Q1/Q3 sub-slices first, and expanding once precision is measured.

Then **Phase 2.4 consolidation is mandatory, not polish**: entity resolution plus stored `entity.df`,
because the Phase-4 hub suppression reads `df` and the measured failure mode without it is a
1.8 M-edge subgraph and one 5,435-member Leiden blob.

### Phase P6 — Question-specific retrieval

Reuse `retrieval/seed_retrieval.py` (4-channel RRF fusion), `retrieval/subgraph.py`,
`retrieval/communities.py` unchanged. Extend the structured channel with the new filters:
`HAS_OUTCOME`, ground disposition, `Organisation`, opponent count.

Two answer shapes, because the ten questions are not one shape:

- **Analytical (Q2, Q5, Q6, Q7):** parameterised Cypher → a table plus base rates with denominators,
  confidence intervals and the `unclassified` count. No LLM in the numeric path — the LLM writes the
  narrative *around* numbers computed by Cypher, never the numbers themselves.
- **Doctrinal (Q1, Q3, Q4, Q8, Q9, Q10):** semantic + graph retrieval → Leiden topics → per-topic
  cards → synthesis with pinpoint citations.

### Phase P7 — Grounding discipline and evaluation

The professional-credibility gate. Nothing ships without it.

1. **Citation integrity:** every citation in an answer must resolve to a chunk ID in the retrieved
   set. Post-generation validator that rejects any case number not in the retrieval set — cheap,
   deterministic, and it catches the failure mode that would end the tool's usefulness.
2. **Gold set:** 25–30 questions across the ten themes with attorney-written reference answers.
   Score retrieval recall (is the decision an attorney would cite in the retrieved set?) separately
   from synthesis faithfulness (does the cited paragraph actually support the proposition?).
   Retrieval failures and hallucination failures need different fixes; a single blended score hides
   both.
3. **Semantic vs keyword A/B** on Q9 and Q3 — the value claim for embeddings must be measured, not
   asserted. Report recall@10 for both.
4. **Mandatory answer footer:** date coverage of the retrieved set, appeals-only caveat, and the
   validity-not-infringement caveat on any FTO-flavoured answer.

### Build order

1. **P2 (outcome layer)** — 1–2 days, unlocks Q2/Q7 almost immediately and is a prerequisite for
   everything analytical. Start here.
2. **P1 (slice + chunk + embed)** — cheap, unblocks all semantic work. Q9 is demonstrable at the end
   of P1+P2.
3. **P3 (ground disposition)** — completes Q2, sharpens Q1.
4. **P6 + P7 on Q1, Q2, Q7, Q9** — a working end-to-end answer on four questions before any
   extraction spend.
5. **P5 (ontology + extraction)**, then re-run Q1/Q3 and compare topic quality against the
   keyword-bridge baseline. Same sequencing logic as the existing plan's step 2: prove the spine
   before spending extraction budget.
6. **P4** → Q6; DE/FR extension → all questions.

---

## 3. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Base rates read as EPO-wide when they are appeals-only** | **High — this is the misuse most likely to cause real harm** | Denominator and the appeals-only caveat printed in every analytical answer, not in a footnote |
| Hallucinated or mis-attributed citations | **High — malpractice-grade** | P7.1 validator; refuse rather than answer ungrounded |
| Outcome misclassification poisoning every statistic | High | Rule-based, 200-order labelled test set, ≥99% precision gate, explicit `unclassified` bucket |
| **Q11 reported as one headline "favours patentees" percentage per board.** Outcomes available differ by appellant role (reformatio in peius bars revocation on a proprietor-only appeal), so pooling strata produces a different and wrong quantity | **High — silently wrong, not visibly wrong** | Per-stratum rates only, never a single blended figure; assert the `proprietor` + `revoked` invariant in code |
| **Q11 quoted as a per-board score off thin cells.** Only 6 boards have recoverable-role volumes worth measuring; 3.3.03/05/06/09 have 3–11 | **High — a plausible-looking percentage is more dangerous than a blank** | Minimum support (≥ 20 scored decisions per stratum) enforced in code, not prose; Wilson intervals and denominators beside every rate; **suppress** below threshold and say "insufficient data" |
| **Appellant role unresolved for 60–90% of the pharma slice** under naive phrase matching, gutting Q11's denominator | **High — measured, not hypothetical** | P2b as re-scoped: rules first, bounded LLM pass for the residue, multilingual formulae; exit gate of `unknown` < 25% before Q11 ships |
| Pooled figures spanning the RPBA 2020 regime break describing a world that no longer exists | Medium | Pre/post-2020 split as a mandatory robustness check; report instability instead of the number when the ranking flips |
| Board tendency attributed to named individuals now that the 2026 scheme is loaded (`:BoardMember`, 159 people) | Medium–High | Report at board level only, per `EXAMINER_PLAN.md` §3; state composition churn as a limit on what a decade-long trend can mean |
| Hub blowup in subgraph induction | High — measured, not hypothetical | Inherit the validated df-cut / min-weight / gamma=1.5 parameters; assert subgraph bounds in code |
| `A61K` dilution (nutrition, cosmetics, fillers) | Medium | Combine with A61P/C07D; semantic re-ranking; report the slice composition |
| Party fragmentation producing wrong track records | Medium | P4; suppress Q6 answers for organisations below a support threshold |
| EN-only slice dropping German pharma litigation | Medium | Ontology aliases from the start; DE/FR extension scheduled, not silently dropped |
| Extraction precision on chemical/biological entities | Medium | INN dictionary as a validation gate; spot-check 20 chunks before scaling |
| Users expecting true FTO (claim-scope) answers | Medium | §0.1 caveat surfaced in the product, not just the docs; state what external data would be required |
| 1 GB heap vs GDS projections | Medium | Bounded seeds, `stream`/`stats` not `write`, drop projections in `finally` |
