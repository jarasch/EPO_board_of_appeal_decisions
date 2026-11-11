"""Structured representation of an attorney's question (Phase 3).

`QueryIntent` is the contract between question understanding and retrieval: the
seed channels in `seed_retrieval.py` read only from this object, never from the
raw question. Phase 3 fills it with one LLM call; `from_question` below is the
no-LLM fallback used while the retrieval spine is being built and tested, and by
`--no-parse` on the CLI.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class QueryIntent(BaseModel):
    """What the attorney is asking for, in terms the graph can be queried with."""

    legal_issues: List[str] = Field(
        default_factory=list,
        description="Grounds in dispute: inventive step, novelty, added subject-matter, "
                    "sufficiency, clarity, admissibility",
    )
    legal_tests: List[str] = Field(
        default_factory=list,
        description="Named doctrines or tests: problem-solution approach, COMVIK, "
                    "closest prior art, could-would, gold standard, technical effect",
    )
    named_cases: List[str] = Field(
        default_factory=list,
        description="Decisions named in the question, e.g. 'T 641/00', 'G 1/19'",
    )
    technical_terms: List[str] = Field(
        default_factory=list,
        description="Subject-matter terms to search semantically and lexically",
    )
    articles: List[str] = Field(
        default_factory=list,
        description="Canonical Article codes, e.g. 'EPC_Art_056', 'EPC_Art_123'",
    )
    date_from: Optional[str] = Field(default=None, description="ISO date lower bound")
    date_to: Optional[str] = Field(default=None, description="ISO date upper bound")
    ipc_prefixes: List[str] = Field(
        default_factory=list, description="IPC symbol prefixes, e.g. 'G06N'"
    )
    outcome_types: List[str] = Field(
        default_factory=list,
        description="Decision.outcomeType values, e.g. 'dismissed', 'set_aside_revoked', "
                    "'set_aside_maintained_as_amended', 'set_aside_maintained_as_granted', "
                    "'remitted', 'terminated', 'inadmissible'",
    )
    grounds: List[str] = Field(
        default_factory=list,
        description="Ground.code values the decision must have addressed, e.g. "
                    "'Art_56_inventive_step', 'Art_123_2_added_matter', 'Art_83_sufficiency'",
    )
    grounds_met: Optional[bool] = Field(
        default=None,
        description="If `grounds` is set, further restrict to decisions where every one of "
                    "those grounds was decided met (true) or not met (false). None = either.",
    )
    appellant_role: Optional[str] = Field(
        default=None, description="'opponent' | 'proprietor' | 'both' -- who appealed"
    )
    party_names: List[str] = Field(
        default_factory=list,
        description="Opponent/proprietor names, e.g. 'Novartis', 'Teva'. Matched against the "
                    "resolved :Organisation layer (importer/parties.py), so a corporate-group "
                    "parent name also matches its subsidiaries (e.g. 'Novartis' matches Hexal, "
                    "Sandoz decisions too).",
    )
    min_opponent_count: Optional[int] = Field(
        default=None, description="Only decisions with at least this many named opponents"
    )
    semantic_query: str = Field(
        default="", description="Cleaned question text for vector search"
    )

    @property
    def lexical_terms(self):
        """Terms worth an exact-match lookup, most distinctive first."""
        return self.named_cases + self.legal_tests + self.technical_terms


def from_question(question, **overrides):
    """Build an intent without an LLM: the question drives the semantic channel only.

    Structured filters can still be supplied via `overrides` (the CLI exposes
    them as flags), which keeps the structured channel testable before Phase 3.
    """
    fields = {"semantic_query": question.strip()}
    fields.update({key: value for key, value in overrides.items() if value})
    return QueryIntent(**fields)
