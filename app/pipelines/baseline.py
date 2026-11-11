"""Vector-only RAG -- the naive baseline this app exists to contrast with.

Deliberately the plain thing a first RAG stack looks like: embed the raw
question, take the nearest chunks by cosine similarity, ask the model to write
an answer from them. No graph traversal, no structured filters, no question
understanding. The only hygiene applied is `isCanonical` -- skipping that would
let the ~1.8% duplicate-decision chunks eat top-k slots, which is a data-quality
bug, not a property of "vector-only RAG" as an approach, and comparing against
it would be an unfair fight for the wrong reason.
"""

import time

from retrieval import db
from app.pipelines.common import unverified_case_numbers

TOP_K = 8
# Overfetch before the isCanonical filter -- filtering post-ANN-search means the
# raw top-k from the index can undershoot once duplicates are excluded.
OVERFETCH_FACTOR = 4

VECTOR_SEARCH = """
CALL db.index.vector.queryNodes('chunk_text_embedding', $fetch, $embedding)
YIELD node, score
WHERE node.isCanonical
RETURN node.id AS id, node.text AS text, node.citation AS citation, score
ORDER BY score DESC
LIMIT $limit
"""

SYSTEM_PROMPT = """Answer the question using only the retrieved passages below. Where relevant,
mention case numbers if you know them. Be concise."""


def run(session_factory, question, top_k=TOP_K):
    started = time.time()
    embedding = db.embed(question)

    with session_factory() as session:
        rows = session.run(
            VECTOR_SEARCH, embedding=embedding, limit=top_k, fetch=top_k * OVERFETCH_FACTOR
        ).data()

    passages = "\n\n".join(
        f"({row['citation'] or row['id']}) {row['text']}" for row in rows
    )
    answer = db.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nPassages:\n\n{passages}"},
    ])

    unverified = unverified_case_numbers(answer, [row["citation"] for row in rows])

    return {
        "answer": answer,
        "chunks": [
            {"id": row["id"], "text": row["text"], "citation": row["citation"],
             "score": round(row["score"], 4)}
            for row in rows
        ],
        "unverifiedCaseNumbers": unverified,
        "elapsedMs": round((time.time() - started) * 1000),
    }
