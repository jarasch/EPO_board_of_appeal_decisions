"""Neo4j and OpenAI clients, configured from .env."""

import os
from contextlib import contextmanager
from functools import lru_cache

from dotenv import load_dotenv
from neo4j import GraphDatabase, NotificationDisabledCategory

load_dotenv()

DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EXTRACTION_MODEL = os.environ.get("EXTRACTION_MODEL", "gpt-5.4")


@contextmanager
def session():
    """A Neo4j session on the configured database."""
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        # `db.index.vector.queryNodes` is deprecated in favour of a `SEARCH`
        # clause that this server does not yet accept, so the warning is noise on
        # every query in the semantic channel.
        notifications_disabled_categories=[NotificationDisabledCategory.DEPRECATION],
    )
    try:
        with driver.session(database=DATABASE) as open_session:
            yield open_session
    finally:
        driver.close()


@lru_cache(maxsize=1)
def _openai():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def embed(text, model=None):
    """Embed one query string with the same model used for the chunk index."""
    response = _openai().embeddings.create(
        model=model or EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def chat(messages, model=None, response_format=None, **kwargs):
    """One chat completion. `response_format` may be a pydantic model."""
    model = model or EXTRACTION_MODEL
    # The gpt-5 family rejects the sampling params older models expect.
    if model.startswith("gpt-5"):
        kwargs.setdefault("reasoning_effort", "low")
    else:
        kwargs.setdefault("temperature", 0)

    if response_format is not None:
        completion = _openai().chat.completions.parse(
            model=model, messages=messages, response_format=response_format, **kwargs
        )
        return completion.choices[0].message.parsed

    completion = _openai().chat.completions.create(model=model, messages=messages, **kwargs)
    return completion.choices[0].message.content
