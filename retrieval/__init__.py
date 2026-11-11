"""Legal-appeal GraphRAG retrieval pipeline over the EPO decisions graph.

Stages, in the order `ask.py` runs them:

    intent      question -> structured QueryIntent          (Phase 3)
    seeds       multi-channel lookup + reciprocal rank fusion (Phase 4.1-4.2)
    subgraph    weighted, hub-suppressed subgraph induction  (Phase 4.3)
    communities Leiden topic detection + topic identity      (Phase 5)
    summarize   per-topic map-reduce, grounded synthesis      (Phase 6)
"""
