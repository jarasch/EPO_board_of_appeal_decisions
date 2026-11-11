"""Citation-treatment classification -- EXAMINER_PLAN.md Phase E5, LLM half.

The non-LLM half (`importer/citator.py`, `scripts/locate_citing_passages.py`)
already found *where* a citing decision names a top-cited case. This module
decides *how* it treats it -- the genuine LLM task the plan calls for:
"short passage in, one label out."

Six labels, the plan's own vocabulary:

    followed            treats the cited ratio as controlling, reaches the
                         same conclusion on an analogous point, no qualification
    applied              applies a specific test/principle from the cited
                         decision to this case's facts (e.g. problem-solution
                         approach from the case that established it)
    distinguished        acknowledges the cited decision but finds it does not
                         control here because the facts/circumstances differ
    declined_to_follow   considered the cited decision and chose not to follow
                         its reasoning on this point, without invoking Art. 20 RPBA
    deviated_art20        explicitly deviates from the cited decision's
                         interpretation of the Convention and gives grounds,
                         as Art. 20 RPBA requires ("the Board deviates from...",
                         "the Board does not follow...")
    merely_referenced    cited in a list, in passing, or as background, with
                         no substantive engagement with its specific holding

Batched (several passages per LLM call, not one call per passage) to
amortise the fixed prompt overhead across a genuinely narrow per-item task.
`item` in the response schema is the caller's own numbering, not a
list-order assumption -- if the model drops or reorders an item, the
mismatch is detected rather than silently misattributing a label to the
wrong citation.
"""

from typing import List, Literal

from pydantic import BaseModel

TREATMENTS = ("followed", "applied", "distinguished", "declined_to_follow",
              "deviated_art20", "merely_referenced")

SYSTEM_PROMPT = """You classify how an EPO Board of Appeal decision treats a case it cites, from
the passage that names it. For each numbered item, read the citing passage and decide the
treatment of the NAMED case in that passage:

followed            treats the cited ratio as controlling and reaches the same conclusion on an
                    analogous point, without qualification
applied             applies a specific test or principle stated in the cited decision to this
                    case's own facts
distinguished       acknowledges the cited decision but finds it does not control here because
                    the facts or circumstances differ
declined_to_follow  considered the cited decision and chose not to follow its reasoning on this
                    point, without invoking Art. 20 RPBA
deviated_art20      explicitly deviates from the cited decision's interpretation of the
                    Convention and gives grounds, as Art. 20 RPBA requires (look for language
                    like "the Board deviates from" / "the Board does not follow")
merely_referenced   cited in a list, in passing, or as background, with no substantive
                    engagement with its specific holding

Return exactly one classification per numbered item, using its number in `item`. Default to
merely_referenced when the passage does not clearly support a stronger label -- do not guess
distinguished/declined_to_follow/deviated_art20 without clear textual support, since those are
the labels a currency check relies on most."""


class PassageTreatment(BaseModel):
    item: int
    treatment: Literal[
        "followed", "applied", "distinguished", "declined_to_follow",
        "deviated_art20", "merely_referenced",
    ]


class TreatmentBatch(BaseModel):
    classifications: List[PassageTreatment]


def build_prompt(batch):
    """`batch`: list of {item, caseRef, citingRef, passageText}. Returns the
    user-message content for one classification call."""
    blocks = []
    for entry in batch:
        text = (entry["passageText"] or "")[:2000]
        blocks.append(
            f"Item {entry['item']}: decision {entry['citingRef']} citing {entry['caseRef']}\n"
            f'"{text}"'
        )
    return "\n\n".join(blocks)


def classify_batch(chat_fn, batch):
    """Run one LLM call over `batch` (see `build_prompt`).

    Returns {item: treatment}. Items the model dropped or mislabelled with
    an out-of-range number are simply absent from the result -- the caller
    decides whether to retry, not this function.
    """
    if not batch:
        return {}
    result = chat_fn(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(batch)},
        ],
        response_format=TreatmentBatch,
    )
    valid_items = {entry["item"] for entry in batch}
    return {c.item: c.treatment for c in result.classifications if c.item in valid_items}
