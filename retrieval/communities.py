"""Phase 5 -- Leiden topic detection over the query-induced subgraph.

Leiden runs on the *query-induced* subgraph rather than corpus-wide because the
topics have to be relative to the question: "non-technical business features" is
a topic in a COMVIK query and noise in an added-subject-matter one. It also keeps
the GDS projection inside the 1 GB heap.

Three non-obvious operational points:

* **Determinism.** Leiden is non-deterministic above concurrency 1, and a demo
  has to reproduce, so `concurrency: 1` + a fixed `randomSeed`.
* **Projections leak.** A named graph survives the query that made it and eats
  heap across demo runs, so every projection is dropped in a `finally`.
* **`gamma` is the resolution knob.** 1.0 under-partitions this data into a few
  large blobs; higher values split harder. It is the first thing to raise when
  the exit criteria fail.

A community is only a topic once you can name it, so `topic_identity` scores each
community's bridges by over-representation against the subgraph baseline -- that
is what turns "community 7" into "COMVIK / non-technical business features".
"""

from dataclasses import dataclass

GRAPH_NAME = "legalTopics"


@dataclass
class LeidenConfig:
    gamma: float = 1.5
    max_levels: int = 10
    random_seed: int = 42
    concurrency: int = 1
    min_community_size: int = 5
    """Communities below this are bucketed as "related outliers", not summarised."""

    max_community_share: float = 0.25
    """Exit criterion: no single community may hold more than this share of nodes."""


# Cypher-aggregation projection. Leiden requires an undirected graph, hence
# `undirectedRelationshipTypes`. Decisions with no surviving edge are simply
# absent from the projection -- they are unclusterable, and `describe()` reports
# them as isolated.
#
# `{label}` -- "DemoDecision" (default) or "Decision" for corpus scope, same
# caveat as retrieval/subgraph.py: rescaling df-fraction cuts are designed to
# generalise, but corpus-scale Leiden exit criteria still need checking, not
# assuming.
PROJECT = """
UNWIND $edges AS edge
MATCH (a:{label} {{reference: edge.a}}), (z:{label} {{reference: edge.z}})
WITH gds.graph.project(
  $graphName, a, z,
  {{relationshipProperties: {{weight: edge.weight}}}},
  {{undirectedRelationshipTypes: ['*']}}
) AS g
RETURN g.graphName AS graphName, g.nodeCount AS nodeCount,
       g.relationshipCount AS relationshipCount
"""

STATS = """
CALL gds.leiden.stats($graphName, {
  gamma: $gamma, maxLevels: $maxLevels, randomSeed: $randomSeed,
  concurrency: $concurrency, relationshipWeightProperty: 'weight'
})
YIELD communityCount, modularity, modularities, ranLevels
RETURN communityCount, modularity, modularities, ranLevels
"""

STREAM = """
CALL gds.leiden.stream($graphName, {
  gamma: $gamma, maxLevels: $maxLevels, randomSeed: $randomSeed,
  concurrency: $concurrency, relationshipWeightProperty: 'weight'
})
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS d, communityId
RETURN communityId,
       collect({reference: d.reference,
                caseRef: d.code + ' ' + toString(toInteger(d.appealNum))
                         + '/' + right(d.year, 2),
                decisionDate: toString(d.decisionDate), boardCode: d.boardCode}) AS members
ORDER BY size(members) DESC
"""
# :Decision carries the same `code`/`appealNum`/`year`/`boardCode` properties
# as :DemoDecision, so STREAM needs no label parameterisation -- only the
# node lookup in PROJECT does (it MATCHes by label + reference).

DROP = "CALL gds.graph.drop($graphName, false) YIELD graphName RETURN graphName"

# Over-representation of a bridge inside the community versus the whole subgraph.
# The +1 in the denominator is Laplace smoothing: without it a bridge appearing
# once, inside one community, scores infinitely specific.
TOPIC_IDENTITY = """
UNWIND $communities AS community
CALL (community) {
  WITH community
  UNWIND $bridgeRels AS rel
  CALL (community, rel) {
    WITH community, rel
    MATCH (d:{label})-[r]->(bridge)
    WHERE type(r) = rel AND d.reference IN $allRefs
    WITH bridge, rel,
         count(CASE WHEN d.reference IN community.refs THEN 1 END) AS inCommunity,
         count(*) AS inSubgraph
    WHERE inCommunity >= 2
    WITH coalesce(bridge.label, bridge.text, bridge.caseRef, bridge.symbol) AS name,
         rel AS source, inCommunity, inSubgraph,
         (1.0 * inCommunity / community.size) /
         (1.0 * (inSubgraph + 1) / $subgraphSize) AS lift
    // A bridge no more common inside the community than across the subgraph
    // (`Art. 56 EPC`, which every decision in this slice cites) says nothing
    // about what the community is about.
    WHERE lift >= $minLift
    RETURN name, source, inCommunity, inSubgraph, lift
  }
  RETURN name, source, inCommunity, inSubgraph, lift
  ORDER BY lift * inCommunity DESC
  LIMIT $topN
}
RETURN community.id AS communityId,
       collect({name: name, source: source, count: inCommunity,
                subgraphCount: inSubgraph, lift: lift}) AS identity
"""

BRIDGE_RELS = ["HAS_KEYWORD", "CITES_ARTICLE", "CITES", "CLASSIFIED_AS"]


def detect(session, subgraph, config=None, graph_name=GRAPH_NAME, decision_label="DemoDecision"):
    """Project, run Leiden, stream assignments, always drop the projection.

    `decision_label`: "DemoDecision" (default) or "Decision" for corpus
    scope -- must match whatever label `subgraph.induce()` used to build
    `subgraph`, or PROJECT's node lookup finds nothing.

    Returns {stats, communities, outliers} where `communities` are the ones at or
    above `min_community_size`, descending by size, and `outliers` is the small
    tail bucketed together.
    """
    config = config or LeidenConfig()
    if not subgraph["edges"]:
        return {"stats": None, "communities": [], "outliers": [],
                "note": "no edges survived induction"}

    params = {
        "graphName": graph_name,
        "gamma": config.gamma,
        "maxLevels": config.max_levels,
        "randomSeed": config.random_seed,
        "concurrency": config.concurrency,
    }

    # A projection left over from a crashed run would silently be reused.
    session.run(DROP, graphName=graph_name).consume()
    try:
        projection = session.run(
            PROJECT.format(label=decision_label), graphName=graph_name,
            edges=[{"a": e["a"], "z": e["z"], "weight": e["weight"]}
                   for e in subgraph["edges"]],
        ).single()
        stats = session.run(STATS, **params).single().data()
        stats["projected"] = {"nodes": projection["nodeCount"],
                              "edges": projection["relationshipCount"]}
        rows = session.run(STREAM, **params).data()
    finally:
        session.run(DROP, graphName=graph_name).consume()

    communities, outliers = [], []
    for row in rows:
        entry = {"id": row["communityId"], "size": len(row["members"]),
                 "members": row["members"]}
        (communities if entry["size"] >= config.min_community_size else outliers).append(entry)

    return {"stats": stats, "communities": communities, "outliers": outliers}


MIN_LIFT = 1.5


def topic_identity(session, subgraph, communities, top_n=8, min_lift=MIN_LIFT,
                    decision_label="DemoDecision"):
    """Name each community by the bridges most over-represented inside it."""
    if not communities:
        return {}
    payload = [{"id": c["id"], "size": c["size"],
                "refs": [m["reference"] for m in c["members"]]} for c in communities]
    # .replace, not .format: the query body is full of literal Cypher map/
    # block braces (CALL (...) { ... }) that .format would choke on.
    rows = session.run(
        TOPIC_IDENTITY.replace("{label}", decision_label), communities=payload,
        allRefs=subgraph["nodes"], subgraphSize=len(subgraph["nodes"]),
        bridgeRels=BRIDGE_RELS, topN=top_n, minLift=min_lift,
    ).data()
    return {row["communityId"]: row["identity"] for row in rows}


def check_exit_criteria(result, config=None):
    """Phase 5 exit criteria: >=5 usable communities, none dominating the subgraph."""
    config = config or LeidenConfig()
    communities = result["communities"]
    total = sum(c["size"] for c in communities) + sum(c["size"] for c in result["outliers"])
    largest = max((c["size"] for c in communities), default=0)
    share = largest / total if total else 0.0
    return {
        "usable_communities": len(communities),
        "largest_share": round(share, 3),
        "ok": len(communities) >= 5 and share <= config.max_community_share,
        "reason": (
            "" if len(communities) >= 5 and share <= config.max_community_share
            else f"{len(communities)} communities >= {config.min_community_size} members, "
                 f"largest holds {share:.0%} (limit {config.max_community_share:.0%})"
        ),
    }
