"""spaCy-based, industry-agnostic named-entity recognition over Chunk text.

Deliberately not the LLM ontology-extraction path sketched in
DEMO_IMPLEMENTATION_PLAN.md Phase 2 / PHARMA_GENERICS_PLAN.md P5 -- those are
a fixed, hand-designed schema (LegalIssue, ActiveIngredient, ...) run through
an LLM, bounded to a slice because full-corpus LLM extraction costs hundreds
of dollars (D1 in the demo plan). spaCy's statistical NER is a few cents of
electricity for the whole 672k-chunk canonical corpus, at the cost of a
fixed, generic label set (people/organisations/places/dates/... rather than
legal doctrine) -- the right trade when the ask is "every entity, corpus-wide,
industry-agnostic" rather than "the entities a patent attorney reasons with".

Three trained pipelines, one per corpus language (`Decision.lang`):
en_core_web_sm, de_core_news_sm, fr_core_news_sm. All three ship NER (the
`_trf` transformer variants for de/fr do not -- "Vocabulary, syntax" only,
no entity component -- so they are not an option here even ignoring cost).

Label schemes differ by language and that is a real, not cosmetic, asymmetry:
the English pipeline uses the 18-label OntoNotes scheme (PERSON, ORG, GPE,
LOC, LAW, NORP, DATE, MONEY, ...); the German/French news pipelines use the
4-label CoNLL/WikiNER scheme (PER, LOC, ORG, MISC). `normalise_label` folds
PER -> PERSON so the same real-world entity mentioned in an English and a
German decision lands under one label; it does not invent finer-grained
labels for de/fr that the model never produced.
"""

import re
import unicodedata

PIPELINES = {
    "en": "en_core_web_sm",
    "de": "de_core_news_sm",
    "fr": "fr_core_news_sm",
}

# Union of every label any of the three pipelines can produce, post
# `normalise_label` (en_core_web_sm's 18-label OntoNotes scheme, plus MISC
# from the German/French 4-label scheme -- PER folds into PERSON above, LOC
# and ORG already agree). Fixed and small, so the driver script can create
# one specific-label + :__Entity__ node per type without templating Cypher
# off unvalidated strings.
ALL_LABELS = (
    "CARDINAL", "DATE", "EVENT", "FAC", "GPE", "LANGUAGE", "LAW", "LOC",
    "MISC", "MONEY", "NORP", "ORDINAL", "ORG", "PERCENT", "PERSON",
    "PRODUCT", "QUANTITY", "TIME", "WORK_OF_ART",
)

# Components no downstream consumer here needs -- NER in spaCy's pretrained
# pipelines runs off `tok2vec` in parallel with, not depending on, the
# tagger/parser/lemmatizer/morphologizer/attribute_ruler. Excluding them
# (not just disabling) skips loading their weights entirely, which is most
# of a pretrained pipeline's load time and memory for an NER-only run.
_EXCLUDE_COMPONENTS = ("tagger", "parser", "lemmatizer", "attribute_ruler",
                       "morphologizer")

# PER (German/French) -> PERSON (English) -- the one relabelling applied.
# Everything else keeps the label the model actually assigned; ORG and LOC
# already agree across all three pipelines, and MISC has no English-scheme
# equivalent, so it stays MISC rather than being force-fit into one.
_LABEL_ALIASES = {"PER": "PERSON"}

# Below this many alphanumeric characters a span is almost always tokeniser
# noise (a stray initial, a lone digit) rather than a usable entity.
_MIN_ENTITY_CHARS = 2

_STRIP_CHARS = " \t\n\"'‘’“”.,;:()[]{}«»"

# Leading article, English/German/French -- spaCy is inconsistent about
# whether a span includes it ("the Disciplinary Board of Appeal" in one
# mention, "Disciplinary Board of Appeal" in the next), which would
# otherwise fragment one entity into two keys. Stripped for the *key* only;
# the original span text is kept as the display-name candidate.
_LEADING_ARTICLE_RE = re.compile(
    r"^(?:the|a|an|der|die|das|den|dem|des|ein|eine|einer|eines|"
    r"le|la|les|l['’]|un|une|des)\s+",
    re.IGNORECASE,
)


def normalise_label(label):
    return _LABEL_ALIASES.get(label, label)


def _strip_diacritics(text):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def clean_entity_text(text):
    text = re.sub(r"\s+", " ", text or "").strip(_STRIP_CHARS)
    return text.strip()


def entity_key(text, label):
    """Resolution key: same normalised text + same (normalised) label is
    treated as the same real-world entity, regardless of which chunk,
    decision or language pipeline produced it. Deliberately simple string
    folding -- casefold + strip diacritics + collapse whitespace -- with no
    fuzzy matching or alias table. That is the honest amount of resolution a
    generic, industry-agnostic pass can do; "BASF SE" vs "BASF
    Aktiengesellschaft" is exactly the kind of legal-form variance
    `importer/parties.py` handles for Party nodes specifically, and is out
    of scope for a generic entity layer.
    """
    norm = re.sub(r"\s+", " ", _strip_diacritics(text).casefold()).strip()
    norm = _LEADING_ARTICLE_RE.sub("", norm)
    return f"{label}::{norm}"


def load_pipeline(lang, spacy_module):
    """Load the NER-only pipeline for one corpus language.

    Takes the `spacy` module as a parameter rather than importing it at
    module load time, so importing `importer.entities` (e.g. from a test)
    never requires spaCy to be installed.
    """
    model_name = PIPELINES[lang]
    nlp = spacy_module.load(model_name, exclude=list(_EXCLUDE_COMPONENTS))
    return nlp


def extract_entities(doc):
    """Yield (cleanText, normalisedLabel) for the usable entities in a Doc."""
    for ent in doc.ents:
        text = clean_entity_text(ent.text)
        if len(re.sub(r"[^0-9A-Za-zÀ-ɏ]", "", text)) < _MIN_ENTITY_CHARS:
            continue
        yield text, normalise_label(ent.label_)
