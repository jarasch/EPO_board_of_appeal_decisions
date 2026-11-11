# EPO Board of Appeal Corpus — Business Questions and Delivery Plan
## Perspective: EPO patent examiner (examining division / opposition division member)

**Purpose.** Define the questions a first-instance EPO examiner asks of Board of Appeal case law when
assessing an application or opposition, and set out a plan to answer 5–10 of them on this corpus.

Companion document: `PHARMA_GENERICS_PLAN.md` (external counsel, generics). The two roles look at the
same corpus and want almost opposite things — §0 explains why, because it drives every design choice
below.

Corpus figures marked **[verified]** were measured against the live database on 2026-09-10, or by
direct inspection of the source XML.

---

## 0. Why the examiner's questions are not the attorney's

### 0.1 The authority hierarchy is different, and it is the central design constraint

An attorney wants *the most persuasive* authority. An examiner is subject to a formal hierarchy:

- **Enlarged Board (G) decisions and opinions are binding** on examiners and on the Boards
  (Art. 112 EPC; Art. 21 RPBA — a Board cannot deviate from the EBA without a fresh referral).
- **Ordinary Board (T/J) decisions are not directly binding on examiners.** They bind first-instance
  practice only to the extent they have been taken up in the **Guidelines for Examination**, which
  are what the examiner is actually instructed to apply.
- **The Guidelines do not bind the Boards** — that is a deliberate consequence of the Boards'
  judicial independence (Art. 23(3) EPC).
- **Art. 20 RPBA:** a Board deviating from an earlier Board's interpretation of the Convention must
  give grounds for the deviation.

Three consequences that shape the whole build:

1. **Retrieval must rank by authority, not only by semantic similarity.** A tool that returns the
   most textually similar T-decision, when a G-decision governs the point, gives an examiner an
   answer they cannot rely on. Authority weight has to be a first-class ranking signal:
   G-decision → OJ-published / headnoted T-decision → ordinary T-decision.
2. **The gap between the Guidelines and current case law is itself the highest-value question.** The
   examiner is bound by the Guidelines; the Board on appeal will apply its own case law. Where those
   diverge is precisely where first-instance decisions get set aside. Answering this requires a
   second corpus (§0.3) — the Guidelines are not in this dataset.
3. **Art. 20 RPBA deviations are detectable in text and mark divergent case-law lines.** For an
   examiner, "there is a divergent line on this point" is actionable in a way it is not for an
   attorney: it means the objection is contestable, needs careful framing, and may be a referral
   candidate.

### 0.2 The risk profile is different

An attorney's downside is losing a case. An examiner's downsides are specific and procedural:

- **Being set aside on the merits** — the objection did not hold.
- **Being found to have committed a substantial procedural violation**, with appeal-fee
  reimbursement under Rule 103 and remittal. The recurring triggers in the case law are violations
  of the right to be heard (Art. 113(1)), refusing or failing to appoint oral proceedings, and
  inadequate reasoning under Rule 111(2). Reported examples include **T 1414/18** (stating that an
  application "will be refused" before deciding), **T 2024/21** (depriving the applicant of oral
  proceedings) and **J 9/18** (four separate violations).
- **Remittal is now a sharper signal than it was.** Under **Art. 11 RPBA 2020** a Board "shall not
  remit … unless special reasons present themselves", and "as a rule, fundamental deficiencies which
  are apparent in the proceedings before that department constitute such special reasons". Pre-2020,
  remittal was routine and said little about first-instance quality. Post-2020, a remittal is much
  closer to a finding *about the first instance*. **Any trend analysis must therefore treat
  2020-01-01 as a regime break and never pool across it.**

This is why the examiner-facing questions in Cluster B below are about *self-assessment and
avoidance*, and have no counterpart in the attorney plan.

### 0.3 What is in the corpus — and what must be added

**Verified corpus facts [verified]:**

51,299 decisions, **1979-03-01 → 2026-03-04**. EN 33,330 / DE 13,876 / FR 4,093 — for this role the
non-EN 35% is not optional, since examiners work in all three official languages and a DE-language
decision is equally binding practice.

Structural layers already loaded:

| Layer | Count |
|---|---|
| `:Decision` / `:Case` / `:Board` | 51,299 / 48,618 / 31 |
| `:ReasonsForDecision` / `:AppealOrder` / `:SummaryOfFacts` | 51,276 / 51,263 / 51,285 |
| `:HeadNote` / `:Catchword` | **3,501 / 2,272** |
| `:Chunk` (fulltext-indexed, `chunk_text_fulltext`) | 666,234 |
| `:Article` (canonical) / `:LegalProvision` | 764 / 4,205 |
| `CITES` (decision→case) / `CITES_ARTICLE` | 74,069 / 143,107 |
| `:Keyword` / `:IPCClass` / `:Party` | 53,534 / 23,509 / 36,228 |

Two of these matter disproportionately for this role:

- **`:HeadNote` (3,501) and `:Catchword` (2,272) are the EPO's own precedential-importance markers.**
  A headnoted decision is one the Boards themselves flagged as establishing something. This is a
  ready-made authority-weight signal, already loaded, currently unused. It is the cheapest path to
  the §0.1(1) ranking requirement.
- **`CITES` (74,069 edges) is a citation network**, which makes the "is this still good law?"
  question (Q2, Q5) a graph problem rather than a text problem.

Landmark authority citation counts **[verified]** — note how strongly examiner-relevant the top of
this list is, versus the pharma-weighted list in the companion plan:

`G 3/14` 786 (grounds for opposition / clarity of granted claims) · `G 2/10` 599 (disclaimers,
gold standard) · `G 1/03` 576 (undisclosed disclaimers) · `G 1/93` 373 (Art. 123(2)/(3) trap) ·
`T 939/92` 362 (AgrEvo, effect across the claim) · `G 2/98` 349 (priority, same invention) ·
`G 5/83` 326 (second medical use) · `G 2/08` 134 · `G 2/21` 118 · `G 1/15` 77 (partial priority) ·
`G 1/16` 74.

**Now measured [verified]** — the three queries that were originally interrupted:

1. **Authority signals are well populated.** `distributionCode` present on **45,649** decisions,
   `officialJournalRef` on **3,059**, headnoted on **3,501**. So a graded authority scale (E2) has a
   real basis rather than a binary headnoted/not flag. The `distributionCode` value distribution
   still needs a breakdown before it can be mapped onto tiers.
2. **Ex parte 20,491 · inter partes 30,808.** Both populations are large enough to analyse
   separately, which is mandatory: ex parte appeals come from *examining* divisions and inter partes
   from *opposition* divisions, so they answer different examiners' questions. **Every base rate in
   Cluster B must be split — pooling them answers neither.** (Note the earlier `HAS_OPPONENT`
   relationship count of 44,525 does not give this split, since one decision can have up to 7
   opponents.)
3. **Q6 has a rich seam.** **2,026** decisions have an order mentioning reimbursement. Supporting
   provision citations: **Art. 113** (right to be heard) 3,273 decisions · **Rule 67** 1,365 ·
   **Rule 103** 1,193 · **Art. 116** (oral proceedings) 569 · **Rule 111** (form/reasoning of
   decisions) 332. Note that Rule 67 (EPC 1973) and Rule 103 (EPC 2000) are the *same* provision
   across a renumbering and must be merged — 1,365 + 1,193 — which is exactly what the Phase 1.1
   canonicalisation exists to handle, and a concrete example of why Q6 would silently under-report
   by half without it.

**Gaps requiring other datasets** (the user's "maybe some others"), in descending value:

| Dataset | Unlocks | Availability |
|---|---|---|
| **Guidelines for Examination** (all annual editions, incl. current) | **Q3** — the Guidelines-vs-case-law gap. Also gives the layer that actually binds the examiner. Versioned editions let you date when a doctrine entered first-instance practice. | Published free by the EPO in HTML; multiple editions needed for the time series |
| **"Case Law of the Boards of Appeal" (the White Book)** | A **ready-made doctrine taxonomy** — the EPO's own systematised chapter/section tree mapping legal issues to decisions. Use this as the `LegalIssue` ontology instead of inventing one, and as a gold standard for retrieval evaluation. Substantial shortcut. | Published free by the EPO |
| **EPC + Implementing Regulations text** | Grounds the 764 `:Article` nodes in actual provision text; enables provision-first navigation, which is how examiners think | Free |
| **Pending EBA referral list** (G-numbers under deliberation) | Flags points of law that are *currently unsettled* — an examiner should know before building an objection on one | EPO website; small |
| **Espacenet / EPO OPS** | Claims, description and family for the application under assessment — needed to go from "case law on this doctrine" to "case law on this application" | Free API, rate-limited |
| **Board member / chairman / registrar data** | Panel-level consistency analysis (see the ethics constraint in §3) | **Not obtainable from this corpus at all.** Requires the OJ EPO business distribution scheme (published annually) or the per-decision signature blocks on the EPO Register. See below |

**Verified finding on the last row — board composition is not in this dataset.** The DTD *declares*
`ep-appeal-board`, `ep-board-chairman`, `ep-board-member` and `ep-registrar`, and
`importer/parser.py:187-198` + `importer/loader.py:95-101,150-156` already extract and map them to
`HAS_CHAIRMAN` / `HAS_BOARD_MEMBER` / `HAS_REGISTRAR`. But **those four tag names occur zero times in
the 1.1 GB corpus**, in any bracket form — verified by direct grep over the whole file. By contrast
`ep-distribution-code` occurs 96,948 times and `ep-official-journal` 12,236 times, so this is a
genuine absence in the data delivery, not a scanning artefact. Confirmed from the other side:
`db.relationshipTypes()` shows `:Party` carrying only `HAS_APPLICANT` and `HAS_OPPONENT`.

The decision *text* does not carry it either — no signature blocks survive in this corpus. The 1,538
chunks matching `"The Registrar"` / `"Der Vorsitzende"` are all substantive narrative references
("the Registrar subsequently ascertained that…"), inspected and confirmed.

**Consequence:** the corpus identifies the deciding *board* (31 `:Board` nodes, by code) but never
the *people*. Every panel-level question in this plan is therefore blocked on an external join, which
is what makes the §3 data-protection constraint a decision to take deliberately rather than a
property of data already on disk.

---

## 1. The questions

Nine questions. Cluster A is "build an objection that holds"; Cluster B is "will my decision
survive"; Cluster C is consistency and currency.

### Cluster A — Building an objection that holds

**Q1. For the objection I intend to raise, what is the controlling authority and the precise test —
ranked by binding force?**
*Why it matters:* the daily task. An examiner drafting an Art. 94(3) communication or a refusal
needs the current formulation of the standard (the Art. 123(2) "gold standard" of G 2/10; the
Art. 83/84 boundary; could-would; the AgrEvo effect-across-the-claim line of T 939/92) with a
pinpoint citation that will not be picked apart on appeal.
*Answers with:* semantic retrieval over Reasons paragraphs, **re-ranked by authority weight**
(G-decision > headnoted/OJ-published > ordinary T), plus `CITES_ARTICLE` as a hard structured filter.
Output: the test as stated, the governing decision, the pinpoint cite, and the most recent
Board application of it.
*Needs:* authority-weight layer (P2), pharma-independent slice embedded (P1).

**Q2. Is this point of law settled, or is there a divergent line — and has anything superseded the
decision I was about to cite?**
*Why it matters:* the single highest-utility feature for this role, and the one a plain semantic
search fundamentally cannot provide. Citing a decision that a later Board declined to follow is a
concrete way to lose on appeal. Conversely, knowing that a point is genuinely divergent tells the
examiner to frame the objection defensively — and identifies referral candidates under
Art. 112(1)(a), which requires exactly this: a need to ensure uniform application of the law.
*Answers with:* a **citator built on the `CITES` network (74,069 edges)** plus treatment
classification of the citing passage — followed / applied / distinguished / declined to follow /
deviated-with-grounds under Art. 20 RPBA. Art. 20 deviations are stated explicitly in the text
("the Board deviates from…", "the Board does not follow T …"), so they are detectable, and they are
the ground truth for divergence detection. Divergence then reads off the citation graph as competing
clusters of decisions that cite each other but not across.
*This is the flagship question: it is where the graph earns its place over pure vector search.*

**Q3. Where does the Guidelines position I am bound to apply diverge from current Board case law?**
*Why it matters:* the structural fault line identified in §0.1. The examiner applies the Guidelines;
the Board applies its case law; the gap is where decisions get set aside — through no fault of the
examiner. Surfacing it is valuable both to the individual examiner and to the Guidelines revision
process itself.
*Answers with:* cross-corpus alignment — Guidelines section ↔ case-law doctrine, via shared
provision (`Art.`/`Rule`) and semantic matching, then flag pairs where recent decisions state a test
the Guidelines text does not reflect.
*Needs:* the Guidelines corpus. **Blocked on the dataset, not on the method.** Highest value per
unit of effort *once* that corpus is in.

**Q4. How have the Boards assessed subject matter technically like this application, on this ground?**
*Why it matters:* doctrine in the abstract is not enough — the examiner needs to know how the
technical-effect standard was applied in *this* field. This is the pure semantic-search use case:
the examiner describes the claimed subject matter in their own words and gets analogous assessments
back, without guessing the applicant's vocabulary.
*Answers with:* vector search over paragraph chunks + IPC-class structured filter + graph expansion
to ground, outcome and cited authority.

### Cluster B — Will my decision survive appeal?

**Q5. What are the most common reasons first-instance decisions are set aside, by ground and
technical field?**
*Why it matters:* directly informs how to build and write a decision. Must be split ex parte
(examining division) vs inter partes (opposition division) — the failure modes differ.
*Answers with:* graph analytics — outcome × ground disposition × IPC × Board × period.
*Needs:* outcome layer (P3) and ground disposition layer (P4). **Cannot be answered at all today.**

**Q6. Which procedural acts trigger a substantial procedural violation finding and appeal-fee
reimbursement — i.e. what is the concrete "do not do this" list?**
*Why it matters:* pure preventable downside, and the most actionable output in this document. The
recurring triggers are known from commentary — right to be heard (Art. 113(1)), oral-proceedings
handling, reasoning under Rule 111(2) — but this corpus can produce the *complete, dated,
citable* list rather than the anecdotal one, including the near-miss cases where the Board found no
violation and explained why.
*Answers with:* `:AppealOrder` text (`Reimbursement of the appeal fee is ordered` — observed in real
samples, e.g. T 1839/09) + `CITES_ARTICLE → Art. 113 / Rule 103 / Rule 111` + semantic retrieval
over the Reasons passage that justifies the reimbursement.
*Note the regime break:* Art. 11 RPBA 2020 changed what remittal means (§0.2), so pre- and
post-2020 must be reported separately.

**Q7. Has the reasoning pattern I am about to use been criticised — insufficient reasoning, failure
to address a submission, hindsight in the problem-solution approach, wrong closest prior art?**
*Why it matters:* the difference between an objection that is right and a decision that holds is
usually the reasoning, not the conclusion. This surfaces the specific, repeated reasoning defects
the Boards call out.
*Answers with:* semantic retrieval restricted to Reasons passages that discuss the first-instance
decision's reasoning, plus Leiden topic clustering to group the defect types.

### Cluster C — Consistency and currency

**Q8. Am I consistent with how comparable cases have been treated — same claim type, same doctrine,
same technical field, and in particular the same family (parent/divisional)?**
*Why it matters:* consistency of application is a core institutional obligation and a frequent
applicant complaint. Divisional-versus-parent inconsistency is the most visible and least defensible
form of it.
*Answers with:* `CONCERNS_APPLICATION` (45,921 `:Application` nodes) for family linkage +
outcome/ground layers + IPC.
*Caveat:* family linkage via application number alone is incomplete — full family resolution needs
EPO OPS.

**Q9. Which decisions should actually be cited in a communication, and are they current?**
*Why it matters:* a communication citing a superseded or non-representative decision invites an
appeal. This is Q1 and Q2 composed into the deliverable form the examiner needs: a short, ranked,
currency-checked citation list with pinpoint references.
*Answers with:* Q1 ranking + Q2 citator status + `Chunk.citation` pinpoint cites
(`T 1924/17, Reasons 2.3`, already built).

**Recommended first delivery: Q6, Q1, Q2, Q4, Q5.** Q6 first — it is narrow, high-value, entirely
preventable risk, and derivable from `:AppealOrder` text plus article citations with **no entity
extraction at all**. Q1 and Q4 then demonstrate authority-ranked semantic retrieval. Q2 is the
flagship graph capability and the main build. Q5 follows once the outcome and ground layers land.
Q3 stays scheduled but explicitly blocked on ingesting the Guidelines. Q7/Q8/Q9 build on the same
layers and need no new infrastructure.

---

## 2. Plan

The Phase 1–5 spine from `DEMO_IMPLEMENTATION_PLAN.md` (retrieval → subgraph induction → Leiden →
summarise) is domain-neutral and reused unchanged, including the measured hub-suppression parameters.
`PHARMA_GENERICS_PLAN.md` Phases P2–P3 (outcome layer, ground disposition) are **shared
infrastructure** — build them once, both roles consume them. What is genuinely new here is the
authority-weight layer and the citator.

### Phase E1 — Slice, re-chunk, embed the whole corpus

Unlike both existing plans, the examiner slice should not be narrow: an examiner in any directorate
needs their own field, so field-specific slicing defeats the purpose.

- **Embed the full corpus** — 657k `:Chunk`, ~$5.50 per the existing estimate. At that price, slicing
  for cost is not justified; the existing CII vector index (9,119 `:DemoChunk`) covers 1.4% of the
  corpus and is useless outside software.
- Paragraph-boundary re-chunking corpus-wide, reusing `scripts/chunk_paragraphs.py`, for the
  `Chunk.citation` pinpoint property. This is the expensive step in wall-clock, not in money.
- **Embed `:HeadNote` and `:Catchword` separately** (3,501 + 2,272 nodes) as a **high-authority index**.
  They are short, dense, and pre-filtered to precedentially important decisions — a two-index
  retrieval strategy (headnote index for authority, chunk index for recall) directly implements the
  §0.1(1) ranking requirement at almost no cost.
- **Do not restrict to EN.** 35% of the corpus is DE/FR and equally binding. Run the
  `[to measure]` language×field breakdown first: if a directorate's case law is substantially
  German, an EN-only tool is worse than no tool because its silence looks like absence of authority.
  A multilingual embedding model, or query translation, is a real decision to take here rather than
  inherit from the CII demo.

*Exit:* for a doctrinal query, the top-10 from the headnote index contains the governing G-decision
where one exists; spot-checked on Art. 123(2) (expect G 2/10), opposition grounds (expect G 3/14).

### Phase E2 — Authority-weight layer  ← *new, and specific to this role*

Compute and store `Decision.authorityWeight` from:
1. **Is it an EBA decision** (`caseNumber` prefix `G`, and `Art. 23` cases) — binding, top tier.
2. **Headnoted / catchworded** — `HAS_SECTION → :HeadNote|:Catchword`.
3. **OJ-published** — `officialJournalRef`.
4. **`distributionCode`** — present on 45,649 decisions; still needs its value distribution broken
   down before the values can be mapped onto authority tiers.
5. **Citation-network centrality** — in-degree on `CITES`, and recency-weighted in-degree (a
   decision cited 30 times in the last 5 years outranks one cited 30 times in the 1990s).

Keep these as **separate, inspectable fields plus one composite**, not a single opaque score. An
examiner must be able to see *why* a decision is ranked high — "G-decision", "headnoted, cited 84
times since 2020" — because an unexplained ranking is not usable as a basis for an official action.

*Effort: small. Value: prerequisite for Q1, Q9, and for making Q2 legible.*

### Phase E3 — Outcome layer  *(shared with `PHARMA_GENERICS_PLAN.md` P2)*

Rule-based classification of 51,263 `:AppealOrder` nodes into `dismissed`,
`set_aside_revoked`, `set_aside_maintained_as_amended`, `set_aside_maintained_as_granted`,
`remitted`, `terminated`, `inadmissible`, plus **`feeReimbursed`** and `costsApportioned`.

For this role `feeReimbursed` is not a minor flag — **it is the primary signal for Q6**, and it is
present verbatim in the order text (`Reimbursement of the appeal fee is ordered`, verified in real
samples). Rules rather than an LLM, because outcome is the join key for every statistic and must be
auditable; 200 hand-labelled orders as a test set, ≥99% precision gate, explicit `unclassified`
bucket reported in every answer.

Add the ex parte / inter partes flag here (`EXISTS{(d)-[:HAS_OPPONENT]->()}`) and the
**pre/post 2020-01-01 RPBA regime flag**, so no downstream query can accidentally pool across either
boundary.

### Phase E4 — Ground disposition layer  *(shared with P3)*

Per decision, per ground (Art. 54 / 56 / 83 / 84 / 123(2) / 123(3) / 82 / 52-53 / 113 / procedural):
decided-for-applicant / decided-against / not-reached. Sources: the EPO's own `:Keyword` headwords
(normalised — `Inventive step - (yes)` / `Inventive step (yes)` / `Inventive step - yes` /
`Erfinderische Tätigkeit - (ja)` are four nodes for one concept), plus extraction from Reasons where
keywords are thin.

### Phase E5 — Citator  ← *the flagship build, Q2*

For each `CITES` edge, classify the **treatment** by extracting and labelling the citing passage:
`followed` / `applied` / `distinguished` / `declined_to_follow` / `deviated_art20` /
`merely_referenced`. Store on the relationship.

Method: locate the citing passage (the chunk containing the cited case number — cheap, since case
numbers are highly distinctive strings and the fulltext index already exists), then classify it.
Classification is a genuine LLM task, but a narrow one: short passage in, one label out. Bound the
first pass to citations of the ~500 most-cited decisions, which covers the large majority of edges
for a small fraction of the cost.

Then derive:
- **Currency status** per decision: has anything declined to follow it, and when.
- **Divergence detection:** competing clusters in the citation graph on the same provision — Leiden
  over the `CITES` subgraph for a given `Article`, where two communities that both cite the provision
  but barely cite each other, and contain `declined_to_follow` or `deviated_art20` edges, are a
  divergent line. This is the existing Phase-5 machinery pointed at a new question, so the
  hub-suppression parameters carry over.
- **Referral candidates:** divergent lines with recent activity and no governing G-decision.

*Validate against ground truth:* the White Book (§0.3) already documents the known divergent lines,
and existing G-referrals are known divergences that were resolved. Both give a real evaluation set —
a divergence detector that fails to find the divergences that actually led to referrals is not
working, and this is checkable rather than a matter of opinion.

### Phase E6 — Guidelines corpus and gap analysis  *(Q3 — blocked on data)*

Ingest the Guidelines (current + historical editions) as a second document graph, link
`GuidelineSection → Article`, align to case-law doctrine, and flag divergences. Scheduled, but do
not start before E5 — the citator's treatment labels are what make "current case law" a well-defined
thing to compare the Guidelines against.

### Phase E7 — Grounding discipline and evaluation

Same discipline as the companion plan, with one addition specific to this role.

1. **Citation integrity validator** — every citation in an answer must resolve to a chunk ID in the
   retrieved set; reject any case number that is not. Deterministic and cheap.
2. **Authority disclosure** — every cited decision displayed with its binding status
   (EBA / headnoted / ordinary) and its citator status. **An answer that presents an ordinary
   T-decision without flagging that it is not binding on the examiner is a wrong answer even when
   every word of it is true**, because it misrepresents what the examiner may rely on.
3. **Gold set:** 25–30 questions with reference answers, ideally drawn from White Book sections so
   the reference is the EPO's own systematisation. Score retrieval recall separately from synthesis
   faithfulness.
4. **Semantic vs keyword A/B** on Q4 and Q7, reporting recall@10 — the embedding value claim gets
   measured, not asserted.
5. **Never output a recommendation.** The tool retrieves and characterises authority; it does not
   say whether to refuse, grant or object. See §3.

### Build order

1. **E3 (outcome layer, incl. `feeReimbursed`)** — 1–2 days, and it alone gets Q6 substantially
   answered. Shared with the generics plan, so it is the highest-leverage item in either document.
2. **E1 (corpus-wide chunk + embed, incl. the headnote index)** — ~$5.50 plus wall-clock; unblocks
   everything semantic.
3. **E2 (authority weights)** — small; makes Q1/Q4 usable rather than merely functional.
4. **Deliver Q6, Q1, Q4** end-to-end. First real value, no extraction spend yet.
5. **E4** → Q5, Q8.
6. **E5 (citator)** → Q2, Q9. The main build; validate against White Book divergences.
7. **E6** → Q3, once the Guidelines are ingested.

The three originally-outstanding sizing queries are now run (§0.3). The one remaining prerequisite
is the `distributionCode` value breakdown, which feeds E2's tiering.

---

## 3. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Analytics on named individuals**, if member data is ever joined in from the OJ business distribution scheme (§0.3) — an examiner-facing tool becomes a per-person overturn scoreboard. | **High if the join is made — but latent, not live.** Board composition is absent from this corpus (verified, §0.3), so the risk arrives only with a deliberate decision to add it. These would be identifiable natural persons under EU data protection law, and the same machinery pointed at examiner names is a workplace-surveillance tool. | Aggregate to the Board (31 nodes), never the individual. Suppress panel-level output below a support threshold. Individual-level self-assessment only opt-in and self-service, where the examiner sees their own data and nobody else does. **Settle this with the data-protection function before joining member data, not after — the absence of the data today is the natural moment to decide it.** |
| **The tool being read as advice on the outcome** rather than as a finder of authority | **High** | Retrieval and characterisation only; no recommendation to grant, refuse or object (E7.5). The examiner decides; the tool must never appear to have decided |
| Presenting non-binding T-decisions as if they were binding | High | E7.2 authority disclosure, mandatory and non-suppressible |
| **Pooling across the Art. 11 RPBA 2020 break**, making remittal trends meaningless | High | Regime flag on every decision (E3); block un-split queries in the analytical path rather than trusting the caller |
| Pooling ex parte and inter partes base rates | High | Same — flag in E3, enforced split |
| Appeals-only base rates read as office-wide rates | High | Denominators and the appeals-only caveat printed in every analytical answer |
| Hallucinated or superseded citations in an official communication | **High — an official action is a legal act** | E7.1 validator plus E5 citator status; refuse rather than answer ungrounded |
| Citator treatment misclassification creating false "superseded" flags | Medium | Conservative labelling — default to `merely_referenced` when uncertain; show the citing passage so the examiner verifies rather than trusts |
| EN-only retrieval hiding DE/FR authority | Medium | Multilingual decision taken explicitly in E1, not inherited from the CII demo |
| Hub blowup in subgraph induction / Leiden | Medium — measured, not hypothetical | Inherit the validated df-cut / min-weight / gamma parameters; assert bounds in code |
| Guidelines corpus unavailable or hard to version | Medium | Q3 is explicitly scheduled last and blocked; nothing else depends on it |
| 1 GB heap vs GDS projections, now over a much larger corpus | Medium | Bounded seeds, `stream`/`stats` not `write`, drop projections in `finally`; E5's `CITES`-only projections are small |

---

## Sources

Role and authority-hierarchy research:

- [What is precedent and does the EPO have it? — IPKat](https://ipkitten.blogspot.com/2014/07/what-is-precedent-and-does-epo-have-it.html)
- [EPO Guidelines: To follow or not to follow? — Venner Shipley](https://www.vennershipley.com/insights-events/epo-guidelines-to-follow-or-not-to-follow/)
- [Guidelines for Examination in the EPO — Wikipedia](https://en.wikipedia.org/wiki/Guidelines_for_Examination_in_the_European_Patent_Office)
- [Case Law of the Boards of Appeal of the EPO — Wikipedia](https://en.wikipedia.org/wiki/Case_Law_of_the_Boards_of_Appeal_of_the_European_Patent_Office)
- [The Boards of Appeal of the EPO — WIPO, Chapter 11](https://www.wipo.int/edocs/pubdocs/en/wipo-pub-1079-chapter11-en-the-boards-of-appeal-of-the-european-patent-office-an-international-guide-to-patent-case-management-for-judges.pdf)
- [RPBA 2020: Revised Rules of Procedure at EPO Boards of Appeal — Novagraaf](https://www.novagraaf.com/en/insights/rpba-2020-revised-rules-procedure-epo-boards-appeal/)
- [Special reasons? Remittals from the EPO Boards of Appeal — Boult Wade Tennant](https://www.boult.com/bulletins/special-reasons-remittals-from-the-epo-boards-of-appeal/)
- [New Rules of Procedure in EPO appeals — early case law suggests remittal will remain common — Mathys & Squire](https://www.mathys-squire.com/insights-and-events/news/new-rules-of-procedure-in-epo-appeals-early-case-law-suggests-remittal-will-remain-common/)
- [EPO examination reports: "will be refused" a substantial procedural violation? — D Young & Co](https://www.dyoung.com/en/knowledgebank/articles/epo-will-be-refused)
- [Substantial procedural violation by the Examining Division for not appointing Oral Proceedings (T 2024/21) — NLO](https://www.nlo.eu/en/news/substantial-procedural-violation-examining-division-not-appointing-oral-proceedings-t-202421)
- [J 9/18: four substantial procedural violations — D Young & Co](https://www.dyoung.com/en/knowledgebank/articles/j0009-18-procedural-violations)
- [The EPO Examining Division are Criticized by the Boards of Appeal for Breaking the Rules of Procedure — Schlich](https://www.schlich.co.uk/the-epo-examining-division-are-criticized-by-the-boards-of-appeal-for-breaking-the-rules-of-procedure/)
