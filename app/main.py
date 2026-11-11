"""FastAPI app: side-by-side vector-only RAG vs graph-grounded RAG.

Read-only. Both pipelines run concurrently in a thread pool -- the Neo4j driver
and OpenAI client used by `retrieval/db.py` are synchronous, and the two
pipelines are otherwise fully independent, so there is no reason to make a user
wait for them serially.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from retrieval import db
from app.examples import EXAMPLES
from app.pipelines import baseline, graphrag, graphrag_deep

logger = logging.getLogger("app")

STATIC_DIR = Path(__file__).parent / "static"

CAVEATS = [
    "Corpus is EPO Board of Appeal decisions only -- these are appeals, not the full "
    "population of first-instance decisions, and any base rate implied by an answer is "
    "conditional on the case having been appealed.",
    "Retrieval is deduplicated to one canonical record per (case, language) -- see "
    "Decision.isCanonical -- but the corpus otherwise reflects the EPO's own publication.",
    "GraphRAG's citation check is structural: every [n] resolves to a real node with real "
    "text. It does not yet verify that the cited paragraph supports the specific claim next "
    "to it -- that needs a separate faithfulness pass, not built here.",
]

# Pipelines hold no state; one small pool is enough to run the two concurrently
# per request without spinning up threads per call.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pipeline")

app = FastAPI(title="EPO Board of Appeal decisions -- RAG vs GraphRAG")


class AskRequest(BaseModel):
    question: str
    top_k: int = 8


@app.get("/api/health")
def health():
    try:
        with db.session() as session:
            result = session.run(
                "SHOW INDEXES YIELD name, state WHERE name = 'chunk_text_embedding' "
                "RETURN state"
            ).single()
        index_state = result["state"] if result else "MISSING"
    except Exception as error:  # noqa: BLE001 -- health check must never raise
        logger.exception("health check failed")
        return {"neo4j": "unreachable", "error": str(error)}
    return {"neo4j": "ok", "chunk_text_embedding": index_state}


@app.get("/api/examples")
def examples():
    return EXAMPLES


@app.post("/api/ask")
async def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    loop = asyncio.get_event_loop()
    baseline_task = loop.run_in_executor(
        _executor, baseline.run, db.session, question, request.top_k)
    graphrag_task = loop.run_in_executor(
        _executor, graphrag.run, db.session, question, request.top_k)

    results = await asyncio.gather(baseline_task, graphrag_task, return_exceptions=True)
    baseline_result, graphrag_result = results

    if isinstance(baseline_result, Exception):
        logger.exception("baseline pipeline failed", exc_info=baseline_result)
        baseline_result = {"answer": f"Baseline pipeline failed: {baseline_result}",
                            "chunks": [], "unverifiedCaseNumbers": [], "elapsedMs": 0}
    if isinstance(graphrag_result, Exception):
        logger.exception("graphrag pipeline failed", exc_info=graphrag_result)
        graphrag_result = {
            "answer": f"GraphRAG pipeline failed: {graphrag_result}", "rawAnswer": None,
            "sources": [], "graph": {"nodes": [], "edges": []}, "retrievalExplain": {},
            "validation": {"citationsInRange": False, "citationsFound": 0,
                           "unverifiedCaseNumbers": [], "refused": False},
            "elapsedMs": 0,
        }

    return {
        "question": question,
        "baseline": baseline_result,
        "graphrag": graphrag_result,
        "caveats": CAVEATS,
    }


@app.post("/api/ask/deep")
async def ask_deep(request: AskRequest):
    """Multi-agent GraphRAG -- opt-in, separate from `/api/ask` on purpose.

    A dozen-plus LLM calls and 1-2 minutes, not the flat pipeline's two
    calls and a couple of seconds. Never run automatically alongside the
    fast comparison; a user has to explicitly ask for this endpoint.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(_executor, graphrag_deep.run, db.session, question)
    except Exception as error:  # noqa: BLE001
        logger.exception("deep graphrag pipeline failed")
        return {"question": question, "deep": {
            "answer": f"Deep pipeline failed: {error}", "rawAnswer": None,
            "topicCards": [], "sources": [], "graph": {"nodes": [], "edges": []},
            "retrievalIterations": [], "leidenStats": None, "exitCriteria": None,
            "faithfulness": [], "redrafts": 0, "refused": False, "elapsedMs": 0,
        }}

    return {"question": question, "deep": result}


# Mounted last: FastAPI matches routes in registration order, and /api/* must
# not be shadowed by the static catch-all.
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
