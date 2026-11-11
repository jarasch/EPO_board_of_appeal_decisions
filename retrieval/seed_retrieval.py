"""Phase 4.1-4.2 -- multi-channel seed lookup and reciprocal rank fusion.

Channels look for the same thing in different ways, because each is blind to
what the others find: paraphrase (semantic), exact strings like case numbers
(lexical), the annotated legal issue via :Keyword (entity), a company/person/
law mentioned anywhere in the text via the spaCy :__Entity__ layer
(named_entity), and bibliographic filters (structured). Each returns a
*ranked list of decisions*; reciprocal rank fusion combines them without
needing the channels' scores to be comparable.

The output is deliberately capped: the subgraph induction in `subgraph.py` is
quadratic in the seed count in the worst case, and the 1 GB heap is the binding
constraint on everything downstream.
"""

from collections import defaultdict

from retrieval.db import embed

VECTOR_INDEX = "demochunk_text_embedding"
FULLTEXT_INDEX = "demochunk_text_fulltext"

# Corpus-wide equivalents, for when the induction thresholds in section 2 of
# DEMO_IMPLEMENTATION_PLAN.md have been re-tuned against 702k chunks. Switching
# the indexes without also switching the DemoDecision filter below returns almost
# nothing -- the channels would retrieve corpus-wide and then filter to the slice.
CORPUS_VECTOR_INDEX = "chunk_text_embedding"
CORPUS_FULLTEXT_INDEX = "chunk_text_fulltext"

# Every channel filters on this. The corpus stores the same decision up to three
# times per language under different accession numbers -- G 2/21 exists as
# G210002EP1 (OJ publication), EU1 (unpublished) and EX1 (extract), byte
# identical at 72 chunks each. `scripts/mark_canonical.py` elects one record per
# (case, language); 881 of 51,299 decisions are marked false.
#
# Filtering here rather than post-hoc because the channels key on d.reference, so
# the three copies otherwise enter fusion as three separate seeds: they consume
# three top-k slots, get counted three times by RRF, and enter the Leiden
# subgraph as three nodes joined by every shared bridge -- inflating exactly the
# co-occurrence edges section 2 of the plan works to suppress.
CANONICAL_FILTER = "d.isCanonical"

# `d:DemoDecision` is a valid boolean predicate in Cypher (a label check), so one
# query serves both scopes: at scope='demo' the OR's left side is false and the
# clause reduces to the old behaviour exactly; at scope='corpus' it short-circuits
# true regardless of label. This is what lets `retrieve_seeds(..., scope=...)`
# reuse one query text instead of forking every channel.
SCOPE_FILTER = "($scope <> 'demo' OR d:DemoDecision)"

# Standard RRF constant: damps the influence of a single channel's top hit, so a
# decision found mid-list by three channels outranks one found first by one.
RRF_K = 60

# Found empirically (retrieval/gold_set.py, scripts/run_gold_set.py): with equal
# weights, a decision ranked #1 in lexical AND #2 in semantic for a gold landmark
# case (G 2/98) still fell to #11 overall -- pushed down by candidates that were
# only moderately ranked, but in all four channels. `entity` and `structured` are
# the reason: both routinely return channel_limit (200) candidates for a query,
# i.e. they are high-recall/low-precision compared to semantic and lexical, so
# their sheer presence systematically outweighs a top-2 hit in the two channels
# that actually score relevance. `structured`'s own rank is not a relevance signal
# at all -- STRUCTURED_QUERY orders by recency, the only signal a pure filter has
# -- so summing it in at full weight is close to adding noise. Same principle
# `retrieval/subgraph.py` already applies to a shared IPC class bridge (also 0.5,
# "a weaker signal"); applied here to fusion instead of subgraph bridges.
CHANNEL_WEIGHTS = {"semantic": 1.0, "lexical": 1.0, "entity": 0.5, "structured": 0.5,
                   "named_entity": 0.5}

DEFAULT_CHANNEL_LIMIT = 200
DEFAULT_SEED_LIMIT = 400

# Index selection is a Python-side decision (kept as two literal pairs, not a
# single corpus-wide index used for both scopes) so that scope='demo' is
# byte-for-byte the same search space `scripts/probe_topics.py` was tuned
# against -- searching the corpus-wide index and filtering to the 1,114-decision
# slice afterwards would starve the top-k of in-slice hits instead.
_INDEXES = {
    "demo":   (VECTOR_INDEX, FULLTEXT_INDEX),
    "corpus": (CORPUS_VECTOR_INDEX, CORPUS_FULLTEXT_INDEX),
}

# `ORDER BY score DESC` before the aggregating `WITH` is load-bearing: Cypher
# preserves row order into `collect()`, so `collect(node.id)[0]` is the id of the
# highest-scoring chunk for that decision, not an arbitrary one. This is what
# lets the app cite the paragraph that actually matched instead of just the
# decision it belongs to.
SEMANTIC_QUERY = """
CALL db.index.vector.queryNodes($index, $limit, $embedding)
YIELD node, score
MATCH (node)-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE """ + CANONICAL_FILTER + " AND " + SCOPE_FILTER + """
WITH d, node, score
ORDER BY score DESC
WITH d, collect(node.id)[0] AS chunkId, collect(score)[0] AS score
RETURN d.reference AS reference, score AS score, chunkId AS chunkId
ORDER BY score DESC
"""

LEXICAL_QUERY = """
CALL db.index.fulltext.queryNodes($index, $luceneQuery, {limit: $limit})
YIELD node, score
MATCH (node)-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE """ + CANONICAL_FILTER + " AND " + SCOPE_FILTER + """
WITH d, node, score
ORDER BY score DESC
WITH d, collect(node.id)[0] AS chunkId, collect(score)[0] AS score
RETURN d.reference AS reference, score AS score, chunkId AS chunkId
ORDER BY score DESC
"""

# Step 2 of the build order ran the entity channel against the existing
# :Keyword layer, with Phase 2 originally scoped to replace it with an
# extracted (:Chunk)-[:MENTIONS]->(:LegalIssue|:LegalTest) *doctrinal*
# ontology. That extraction pass was superseded by an industry-agnostic
# spaCy NER pass instead (importer/entities.py) -- generic PERSON/ORG/LAW/
# GPE labels, not legal doctrine, so it is not a drop-in replacement for
# this channel: ":Keyword" text like "Inventive step (yes)" has no spaCy
# equivalent. This channel stays on :Keyword; the spaCy layer is wired in
# below as a separate `named_entity` channel for a different question
# ("does this decision mention this company/person/law") that :Keyword
# cannot answer at all.
#
# No chunk id here -- a keyword lives on the :Decision, not on a specific
# paragraph. The caller falls back to a decision-level citation anchor for any
# seed found only by this channel or the structured one below.
KEYWORD_QUERY = """
UNWIND $terms AS term
MATCH (d:Decision)-[:HAS_KEYWORD]->(k:Keyword)
WHERE """ + CANONICAL_FILTER + " AND " + SCOPE_FILTER + """
  AND toLower(k.text) CONTAINS toLower(term)
RETURN d.reference AS reference, count(DISTINCT k) AS score
ORDER BY score DESC
LIMIT $limit
"""

# spaCy-extracted generic entities (importer/entities.py, scripts/
# extract_entities_spacy.py) -- "does this decision mention this company/
# person/law", a question :Keyword cannot answer since it only carries the
# EPO's own doctrinal headwords. Complements `partyNames`'s use in
# STRUCTURED_QUERY below rather than duplicating it: the structured filter
# only catches a *formal* opponent/applicant (:HAS_OPPONENT/:HAS_APPLICANT);
# this catches the same name mentioned anywhere in the text -- a cited prior
# -art assignee, a third party, a company discussed only in passing.
#
# `MAX_ENTITY_DF` mirrors the hub-suppression the demo plan already applies
# to :Keyword-as-bridge (df cut, tuned there to ~2% of the node population):
# 1000 is ~2% of the 51,299-decision corpus. Confirmed necessary on this
# layer specifically -- generic entities like "EPC" (df 29,831) and "Board"
# (df 20,109) top the frequency table (see scripts/extract_entities_spacy.py
# verify output), and would otherwise swamp every query regardless of terms.
MAX_ENTITY_DF = 1000

NAMED_ENTITY_QUERY = """
UNWIND $terms AS term
MATCH (e:__Entity__)
WHERE toLower(e.text) CONTAINS toLower(term) AND coalesce(e.df, 0) <= $maxDf
MATCH (c:Chunk)-[:MENTIONS]->(e)
MATCH (c)-[:PART_OF]->(:Section)<-[:HAS_SECTION]-(d:Decision)
WHERE """ + CANONICAL_FILTER + " AND " + SCOPE_FILTER + """
WITH d, count(DISTINCT e) AS score, collect(c.id)[0] AS chunkId
RETURN d.reference AS reference, score AS score, chunkId AS chunkId
ORDER BY score DESC
LIMIT $limit
"""

# Bibliographic filters. Absent filters must not shrink the result set, hence the
# `$x IS NULL OR ...` shape rather than a dynamically assembled WHERE clause.
#
# P6 (PHARMA_GENERICS_PLAN.md): outcome/ground/appellant-role/party filters read
# from layers that did not exist when this channel was first built --
# `scripts/classify_outcomes.py`, `classify_grounds.py`, `classify_appellant_roles.py`,
# `resolve_parties.py`. `partyNames` is matched through the resolved :Organisation
# rollup (not raw :Party.name) specifically so a corporate-group parent name
# also catches its subsidiaries -- matching raw Party strings would miss every
# BASF/Hexal/Sandoz spelling variant `importer/parties.py` exists to collapse.
STRUCTURED_QUERY = """
MATCH (d:Decision)
WHERE """ + CANONICAL_FILTER + " AND " + SCOPE_FILTER + """
  AND ($dateFrom IS NULL OR d.decisionDate >= date($dateFrom))
  AND ($dateTo   IS NULL OR d.decisionDate <= date($dateTo))
  AND ($articles = [] OR EXISTS {
        (d)-[:CITES_ARTICLE]->(a:Article) WHERE a.code IN $articles })
  AND ($ipcPrefixes = [] OR EXISTS {
        (d)-[:CLASSIFIED_AS]->(i:IPCClass)
        WHERE any(prefix IN $ipcPrefixes WHERE i.symbol STARTS WITH prefix) })
  AND ($namedCases = [] OR EXISTS {
        (d)-[:CITES]->(c:Case) WHERE c.caseNumber IN $namedCases
                                  OR replace(c.caseNumber, ' 0', ' ') IN $namedCases })
  AND ($outcomeTypes = [] OR d.outcomeType IN $outcomeTypes)
  AND ($appellantRole IS NULL OR d.appellantRole = $appellantRole)
  AND ($minOpponentCount IS NULL
       OR count { (d)-[:HAS_OPPONENT]->() } >= $minOpponentCount)
  AND ($grounds = [] OR EXISTS {
        (d)-[r:DECIDED_GROUND]->(g:Ground) WHERE g.code IN $grounds
          AND ($groundsMet IS NULL OR r.requirementMetAll = $groundsMet) })
  AND ($partyNames = [] OR EXISTS {
        (d)-[:HAS_OPPONENT|HAS_APPLICANT]->(:Party)-[:IS_PARTY_OF]->(:Organisation)
          -[:PART_OF_GROUP*0..3]->(o:Organisation)
        // CONTAINS, not exact match: a caller writes "Novartis", the resolved
        // canonical name is "Novartis AG" (importer/parties.py picks the
        // fullest legal-form spelling as the display name, not the bare mark).
        WHERE any(name IN $partyNamesLower WHERE toLower(o.name) CONTAINS name) })
// Recency is the only ranking signal a pure filter has; the later case law is
// what an attorney wants first.
RETURN d.reference AS reference, d.decisionDate AS score
ORDER BY d.decisionDate DESC
LIMIT $limit
"""


def _lucene_query(terms):
    """Quote each term as a phrase and OR them together."""
    phrases = [f'"{term}"' for term in terms if term and '"' not in term]
    return " OR ".join(phrases) if phrases else None


def _rank(rows):
    """Ranked list of decision references from a channel's result rows."""
    return [row["reference"] for row in rows]


def _chunk_ids(rows):
    """{reference: chunkId} for rows that carry one (semantic/lexical only)."""
    return {row["reference"]: row["chunkId"] for row in rows if row.get("chunkId")}


def _pad_case_number(case_ref):
    """'T 641/00' -> 'T 0641/00', the zero-padded form stored on :Case."""
    parts = case_ref.replace("/", " ").split()
    if len(parts) != 3 or not parts[1].isdigit():
        return case_ref
    return f"{parts[0]} {int(parts[1]):04d}/{parts[2]}"


def run_channels(session, intent, channel_limit=DEFAULT_CHANNEL_LIMIT, scope="demo"):
    """Run every channel the intent has terms for.

    Returns ({channel_name: [reference, ...]}, {reference: chunkId}). The second
    dict is the pinpoint citation anchor: the specific chunk that made a decision
    a seed, for the channels that operate at chunk granularity. `scope='demo'`
    reproduces the original DemoDecision-only behaviour exactly (SCOPE_FILTER
    above); `scope='corpus'` searches all 50k+ canonical decisions.
    """
    vector_index, fulltext_index = _INDEXES[scope]
    channels = {}
    best_chunks = {}

    if intent.semantic_query:
        rows = session.run(SEMANTIC_QUERY, index=vector_index, limit=channel_limit,
                           embedding=embed(intent.semantic_query), scope=scope).data()
        channels["semantic"] = _rank(rows)
        best_chunks.update(_chunk_ids(rows))

    lucene = _lucene_query(intent.lexical_terms)
    if lucene:
        rows = session.run(LEXICAL_QUERY, index=fulltext_index,
                           luceneQuery=lucene, limit=channel_limit, scope=scope).data()
        channels["lexical"] = _rank(rows)
        # Semantic wins where both channels hit the same decision: embedding
        # similarity is a better proxy for "the passage that matches the
        # question" than a lexical/BM25 score, which only says a term occurs.
        best_chunks = {**_chunk_ids(rows), **best_chunks}

    entity_terms = intent.legal_issues + intent.legal_tests
    if entity_terms:
        rows = session.run(KEYWORD_QUERY, terms=entity_terms, limit=channel_limit,
                           scope=scope).data()
        channels["entity"] = _rank(rows)

    if intent.party_names:
        rows = session.run(NAMED_ENTITY_QUERY, terms=intent.party_names,
                           maxDf=MAX_ENTITY_DF, limit=channel_limit, scope=scope).data()
        channels["named_entity"] = _rank(rows)
        best_chunks = {**_chunk_ids(rows), **best_chunks}

    named_cases = [_pad_case_number(case) for case in intent.named_cases]
    has_filter = any([intent.date_from, intent.date_to, intent.articles,
                      intent.ipc_prefixes, named_cases, intent.outcome_types,
                      intent.grounds, intent.appellant_role, intent.party_names,
                      intent.min_opponent_count])
    if has_filter:
        rows = session.run(STRUCTURED_QUERY, dateFrom=intent.date_from,
                           dateTo=intent.date_to, articles=intent.articles,
                           ipcPrefixes=intent.ipc_prefixes, namedCases=named_cases,
                           outcomeTypes=intent.outcome_types, grounds=intent.grounds,
                           groundsMet=intent.grounds_met,
                           appellantRole=intent.appellant_role,
                           partyNames=intent.party_names,
                           partyNamesLower=[p.lower() for p in intent.party_names],
                           minOpponentCount=intent.min_opponent_count,
                           limit=channel_limit, scope=scope).data()
        channels["structured"] = _rank(rows)

    return channels, best_chunks


def fuse(channels, seed_limit=DEFAULT_SEED_LIMIT, k=RRF_K, best_chunks=None,
         weights=None):
    """Reciprocal rank fusion over the per-channel ranked lists.

    Returns [{reference, score, channels, chunkId}] descending, capped at
    `seed_limit`. `chunkId` is None for a seed found only by a decision-level
    channel (entity/structured) -- the caller falls back to a decision-level
    citation anchor in that case.

    `weights` (default `CHANNEL_WEIGHTS`) scales each channel's contribution
    before summing -- see the comment on `CHANNEL_WEIGHTS` for why `entity`/
    `structured` are downweighted relative to `semantic`/`lexical`.
    """
    best_chunks = best_chunks or {}
    weights = weights if weights is not None else CHANNEL_WEIGHTS
    scores = defaultdict(float)
    found_by = defaultdict(list)
    for name, references in channels.items():
        weight = weights.get(name, 1.0)
        for rank, reference in enumerate(references, start=1):
            scores[reference] += weight / (k + rank)
            found_by[reference].append(name)

    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"reference": reference, "score": score, "channels": found_by[reference],
         "chunkId": best_chunks.get(reference)}
        for reference, score in ordered[:seed_limit]
    ]


def retrieve_seeds(session, intent, channel_limit=DEFAULT_CHANNEL_LIMIT,
                   seed_limit=DEFAULT_SEED_LIMIT, scope="demo"):
    """Run the channels and fuse them. Returns (seeds, channels) for --explain.

    Each seed dict carries a `chunkId` (see `fuse`); existing callers that only
    read `reference`/`score`/`channels` are unaffected.
    """
    channels, best_chunks = run_channels(session, intent, channel_limit, scope=scope)
    return fuse(channels, seed_limit, best_chunks=best_chunks), channels
