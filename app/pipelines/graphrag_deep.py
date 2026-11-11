"""Multi-agent GraphRAG -- thin adapter over `retrieval/multiagent.py`.

Opt-in, slower, more expensive than `graphrag.py`'s single retrieve-then
-generate pass: a dozen-plus LLM calls (iterative retrieval assessment,
parallel per-topic summarizers, synthesis, a faithfulness critic, and up to
one redraft) versus two. Not wired into the default `/api/ask` comparison
for exactly that reason -- see `app/main.py`'s separate `/api/ask/deep`
route, which a user has to explicitly request.
"""

from retrieval.multiagent import run_deep

TOP_N = 200  # seed_limit, not "top sources" -- see retrieval/multiagent.py


def run(session_factory, question, top_n=TOP_N):
    return run_deep(session_factory, question, seed_limit=top_n)
