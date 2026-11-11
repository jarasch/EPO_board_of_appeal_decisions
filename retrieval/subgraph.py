"""Phase 4.3 -- weighted, hub-suppressed subgraph induction.

This is the stage that fails naively, and it fails loudly: seeds plus *raw*
keyword co-occurrence produced 17,016 nodes / 1,845,302 edges and Leiden returned
one 5,435-member blob. The cause is hub bridges -- a generic keyword like
`Inventive step (yes)` joins thousands of unrelated decisions into one clique.

Every mitigation here exists for that reason:

* **Document-frequency cut**, computed *inside the induced node set* rather than
  over the corpus. A cut of 40 documents means something very different in a
  1,114-node slice than in a 51,299-decision corpus, so the cut is a fraction of
  the node count and rescales with the subgraph.
* **Weight by channel**, so a decision actually citing another counts for more
  than a shared IPC class.
* **Minimum edge weight**, so an edge needs real corroboration to survive.
* **Bounded seeds and a node cap**, because the 1 GB heap is the binding
  constraint on the GDS projection downstream.

Nodes are decisions. Cited cases, keywords, articles and IPC classes are *bridges*,
not nodes: that keeps landmark authorities outside the slice (T 641/00 is from
2002) contributing to the topology without dragging un-chunked decisions into a
graph whose members have to be summarisable.
"""

from dataclasses import dataclass, field

# Bridge channels: (relationship type, bridge label, default weight per shared bridge).
# Co-citation and shared keywords/articles are doctrinal signals; a shared IPC class
# is only a technical-field signal, so it is worth half an edge and cannot on its
# own put an edge over the default threshold.
BRIDGE_CHANNELS = {
    "cocite": ("CITES", "Case", 1.0),
    "keyword": ("HAS_KEYWORD", "Keyword", 1.0),
    "article": ("CITES_ARTICLE", "Article", 1.0),
    "ipc": ("CLASSIFIED_AS", "IPCClass", 0.5),
}

DIRECT_CITE_WEIGHT = 2.0


@dataclass
class InductionConfig:
    """Knobs for the induction.

    Defaults come from the `scripts/probe_topics.py --sweep` grid over
    df_max_fraction x min_weight x gamma on a 700-node COMVIK subgraph:

        df    minW  | edges  isolated  avg deg | usable  max%  modularity
        0.02  1.0   |  3006       141     10.8 |     18   10%       0.516  <- default
        0.05  2.0   |  1288       266      5.9 |     15   13%       0.629
        0.05  3.0   |   371       480      3.4 |     11   15%       0.656
        0.10  1.0   | 28199        33     84.6 |      6   27%       0.376  <- FAILS

    The last row is the plan's hub blowup, reproduced: relax the df cut and the
    graph collapses towards one blob with the modularity to match. Higher
    min_weight buys modularity by *discarding retrieved evidence* -- at 3.0, 69%
    of seeds end up isolated and get no topic at all. The default therefore cuts
    hubs hard and accepts a single specific bridge, which keeps isolation at 20%
    while still splitting into legible doctrinal topics.
    """

    df_max_fraction: float = 0.02
    """Drop a bridge shared by more than this fraction of the node set."""

    df_max_floor: int = 8
    """...but never cut below this many documents, or small subgraphs lose every bridge."""

    min_weight: float = 1.0
    """Keep an edge only at or above this summed weight."""

    expand_min_shared: int = 2
    """A non-seed decision joins the node set on this many shared specific bridges."""

    expand_cap: int = 300
    """Hard cap on decisions added by expansion."""

    max_nodes: int = 5000
    """Assertion bound -- exceeding it means the induction is misconfigured."""

    max_edges: int = 50000
    """Assertion bound, as above."""

    direct_cite_weight: float = DIRECT_CITE_WEIGHT
    channel_weights: dict = field(
        default_factory=lambda: {name: weight for name, (_, _, weight) in BRIDGE_CHANNELS.items()}
    )

    def df_max(self, node_count):
        return max(self.df_max_floor, int(node_count * self.df_max_fraction))


class SubgraphTooLarge(RuntimeError):
    """Raised when induction breaches the configured node/edge bounds."""


# `{label}` is the decision label -- "DemoDecision" (default, matches every
# existing caller e.g. scripts/probe_topics.py) or "Decision" for a corpus-
# wide induction. The hub-suppression math (`InductionConfig.df_max`) is
# deliberately a *fraction of the induced node count*, not an absolute
# corpus-wide count (see the module docstring's df-cut discussion) -- it was
# designed to rescale with whatever subgraph it is handed, so corpus scope
# is not a fresh tuning problem in principle. It has not been *measured* at
# corpus scale the way demo scope was (DEMO_IMPLEMENTATION_PLAN.md's sweep
# table), so treat a corpus-scope run's exit criteria (`check_exit_criteria`
# in communities.py) as something to check every time, not assume.
EXPAND_QUERY = """
UNWIND $refs AS ref
MATCH (seed:{label} {{reference: ref}})-[r]->(bridge)
WHERE type(r) IN $bridgeRels
WITH bridge, count(DISTINCT seed) AS seedDf
WHERE seedDf <= $dfMax
MATCH (bridge)<-[r2]-(candidate:{label})
WHERE type(r2) IN $bridgeRels AND NOT candidate.reference IN $refs
WITH candidate, count(DISTINCT bridge) AS shared
WHERE shared >= $minShared
RETURN candidate.reference AS reference, shared
ORDER BY shared DESC, reference
LIMIT $expandCap
"""

# One bridge channel: collect the in-set decisions per bridge, drop hub bridges,
# then emit every pair from the collected list. Pairing from the collected list
# rather than re-matching keeps this linear in the number of surviving bridges.
_BRIDGE_BLOCK = """
  UNWIND $refs AS ref
  MATCH (d:{decision_label} {{reference: ref}})-[:{rel}]->(bridge:{label})
  WITH bridge, collect(DISTINCT d) AS members
  WITH bridge, members, size(members) AS df
  WHERE df >= 2 AND df <= $dfMax
  UNWIND members AS a
  UNWIND members AS z
  WITH a, z WHERE elementId(a) < elementId(z)
  RETURN a.reference AS a, z.reference AS z,
         $weights['{name}'] AS w, '{name}' AS kind
"""

_DIRECT_CITE_BLOCK = """
  UNWIND $refs AS ref
  MATCH (x:{label} {{reference: ref}})-[:CITES]->(:Case)<-[:LANGUAGE_VERSION_OF]-(y:{label})
  WHERE y.reference IN $refs AND elementId(x) <> elementId(y)
  WITH CASE WHEN elementId(x) < elementId(y) THEN x ELSE y END AS a,
       CASE WHEN elementId(x) < elementId(y) THEN y ELSE x END AS z
  RETURN DISTINCT a.reference AS a, z.reference AS z,
         $directCiteWeight AS w, 'cite' AS kind
"""


def _edge_query(channels, decision_label):
    blocks = [_DIRECT_CITE_BLOCK.format(label=decision_label)]
    for name in channels:
        rel, label, _ = BRIDGE_CHANNELS[name]
        blocks.append(_BRIDGE_BLOCK.format(rel=rel, label=label, name=name,
                                            decision_label=decision_label))
    return (
        "CALL () {" + "  UNION ALL\n".join(blocks) + "}\n"
        "WITH a, z, sum(w) AS weight, collect(DISTINCT kind) AS kinds\n"
        "WHERE weight >= $minWeight\n"
        "RETURN a, z, weight, kinds\n"
    )


def expand(session, seed_references, config, channels=None, decision_label="DemoDecision"):
    """Grow the seed set by decisions sharing specific bridges with a seed."""
    channels = channels or list(BRIDGE_CHANNELS)
    bridge_rels = [BRIDGE_CHANNELS[name][0] for name in channels]
    rows = session.run(
        EXPAND_QUERY.format(label=decision_label),
        refs=list(seed_references),
        bridgeRels=bridge_rels,
        dfMax=config.df_max(len(seed_references)),
        minShared=config.expand_min_shared,
        expandCap=config.expand_cap,
    ).data()
    return [row["reference"] for row in rows]


def induce(session, seed_references, config=None, channels=None, expand_seeds=True,
           decision_label="DemoDecision"):
    """Induce the weighted subgraph over `seed_references` (plus expansion).

    `decision_label`: "DemoDecision" (default) or "Decision" for corpus scope
    -- see the module-level note above `EXPAND_QUERY`.

    Returns {nodes, edges, df_max, expanded, channels}: `edges` is a list of
    {a, z, weight, kinds} ready for a GDS Cypher-aggregation projection.
    """
    config = config or InductionConfig()
    channels = channels or list(BRIDGE_CHANNELS)

    nodes = list(dict.fromkeys(seed_references))
    expanded = (expand(session, nodes, config, channels, decision_label)
                if expand_seeds else [])
    nodes = list(dict.fromkeys(nodes + expanded))

    if len(nodes) > config.max_nodes:
        raise SubgraphTooLarge(
            f"{len(nodes)} nodes exceeds max_nodes={config.max_nodes}; "
            "lower expand_cap or the seed limit"
        )

    df_max = config.df_max(len(nodes))
    edges = session.run(
        _edge_query(channels, decision_label),
        refs=nodes,
        dfMax=df_max,
        minWeight=config.min_weight,
        directCiteWeight=config.direct_cite_weight,
        weights=config.channel_weights,
    ).data()

    if len(edges) > config.max_edges:
        raise SubgraphTooLarge(
            f"{len(edges)} edges exceeds max_edges={config.max_edges}; "
            "raise min_weight or lower df_max_fraction"
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "df_max": df_max,
        "expanded": expanded,
        "channels": channels,
    }


def describe(subgraph):
    """One-line stats for --explain."""
    nodes, edges = subgraph["nodes"], subgraph["edges"]
    degrees = {}
    for edge in edges:
        degrees[edge["a"]] = degrees.get(edge["a"], 0) + 1
        degrees[edge["z"]] = degrees.get(edge["z"], 0) + 1
    connected = len(degrees)
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "expanded": len(subgraph["expanded"]),
        "df_max": subgraph["df_max"],
        "isolated": len(nodes) - connected,
        "avg_degree": round(2 * len(edges) / connected, 1) if connected else 0.0,
        "max_degree": max(degrees.values()) if degrees else 0,
    }
