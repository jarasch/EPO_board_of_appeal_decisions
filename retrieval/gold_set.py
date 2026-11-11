"""Gold set -- E7.3 (EXAMINER_PLAN.md) / P7.2 (PHARMA_GENERICS_PLAN.md).

Both plans call for "25-30 questions ... with attorney-written reference
answers / ideally drawn from White Book sections". That is a real
constraint this module does not pretend to meet: authoring attorney-grade
relevance judgments, or a White Book-sourced gold standard, needs domain
expertise this agent does not have -- fabricating one would be exactly the
kind of confident-but-wrong grounding both plans spend their entire §7
warning against.

What IS honestly buildable: every landmark-case association below is lifted
verbatim from a claim already stated -- and already checked against the
live database -- in DEMO_IMPLEMENTATION_PLAN.md / EXAMINER_PLAN.md /
PHARMA_GENERICS_PLAN.md (see each entry's `source`). The recall question
this asks is narrower than "would an attorney cite this": it is "does
retrieval surface the specific decision that established a doctrine, when
asked about that doctrine by name" -- a strong, defensible, *reusable*
proxy, not the full gold standard the plans describe. `scripts/run_gold_set.py`
reports it as exactly that, not as a substitute for the real gold set.

Two of these (`comvik_exclusion`, `comvik_technical_effect`) reproduce
DEMO_IMPLEMENTATION_PLAN.md's own Phase 1.4 exit-criteria queries verbatim,
so running the harness re-verifies a claim the plan already made rather than
introducing a new one.
"""

from pydantic import BaseModel


class GoldQuestion(BaseModel):
    id: str
    question: str
    theme: str  # which plan question this touches, e.g. "examiner:Q1"
    expected_cases: list[str]  # a hit on ANY of these counts as recall@k success
    source: str  # exact provenance -- which plan, which claim


GOLD_SET = [
    GoldQuestion(
        id="comvik_exclusion",
        question="How does the COMVIK approach exclude non-technical features from "
                 "the inventive-step assessment of a mixed invention?",
        theme="demo:Phase1.4-exit-criteria",
        expected_cases=["G 1/19", "T 1463/11"],
        source='DEMO_IMPLEMENTATION_PLAN.md 1.4 exit criteria: "vector search for the '
               'COMVIK exclusion returns G 1/19, Reasons 31 and T 1463/11, Reasons 11 '
               '(Cardinal Commerce)"',
    ),
    GoldQuestion(
        id="comvik_technical_effect",
        question='"T 641/00" AND "technical effect"',
        theme="demo:Phase1.4-exit-criteria",
        expected_cases=["T 489/14"],
        source='DEMO_IMPLEMENTATION_PLAN.md 1.4 exit criteria: \'fulltext for "T 641/00" '
               'AND "technical effect" returns T 489/14, Reasons 7 (the G 1/19 referral)\'',
    ),
    GoldQuestion(
        id="disclaimer_gold_standard",
        question="What is the gold standard test for allowing an undisclosed disclaimer "
                 "under Article 123(2) EPC?",
        theme="examiner:Q1 / pharma:Q4",
        expected_cases=["G 2/10", "G 1/03"],
        source="EXAMINER_PLAN.md / PHARMA_GENERICS_PLAN.md landmark table: "
               '"G 2/10 599 (disclaimers, gold standard) · G 1/03 576 (undisclosed disclaimers)"',
    ),
    GoldQuestion(
        id="added_matter_trap",
        question="What is the inescapable trap between Article 123(2) and Article 123(3) "
                 "EPC when a granted claim contains added subject-matter?",
        theme="examiner:Q1",
        expected_cases=["G 1/93"],
        source='EXAMINER_PLAN.md landmark table: "G 1/93 373 (Art. 123(2)/(3) trap)"',
    ),
    GoldQuestion(
        id="agrevo_effect_across_claim",
        question="What must be shown for an inventive-step effect to be credible across "
                 "the whole scope of a claim?",
        theme="examiner:Q1 / pharma:Q1",
        expected_cases=["T 939/92"],
        source='EXAMINER_PLAN.md landmark table: "T 939/92 362 (AgrEvo, effect across '
               'the claim)"',
    ),
    GoldQuestion(
        id="priority_same_invention",
        question="What is the test for claiming priority for 'the same invention'?",
        theme="examiner:Q1",
        expected_cases=["G 2/98"],
        source='EXAMINER_PLAN.md landmark table: "G 2/98 349 (priority, same invention)"',
    ),
    GoldQuestion(
        id="second_medical_use",
        question="Under what conditions is a Swiss-type second medical use claim allowable?",
        theme="pharma:Q8",
        expected_cases=["G 5/83"],
        source='PHARMA_GENERICS_PLAN.md landmark table: "G 5/83 326 (second medical use)"',
    ),
    GoldQuestion(
        id="dosage_regimen",
        question="How is a dosage regimen feature treated for the novelty of a "
                 "second medical use claim?",
        theme="pharma:Q8",
        expected_cases=["G 2/08"],
        source='PHARMA_GENERICS_PLAN.md: "dosage-regimen claims (G 2/08)"',
    ),
    GoldQuestion(
        id="plausibility_post_published_evidence",
        question="When does post-published evidence establish that a technical effect is "
                 "plausible for inventive step?",
        theme="pharma:Q1",
        expected_cases=["G 2/21", "T 609/02", "T 1329/04"],
        source='PHARMA_GENERICS_PLAN.md: "the plausibility / post-published-evidence rule '
               '(G 2/21, T 1329/04, T 609/02)"',
    ),
    GoldQuestion(
        id="partial_priority",
        question="What is the rule for partial priority when a claim encompasses "
                 "alternative subject-matter, some of which was disclosed in the "
                 "priority document and some not?",
        theme="examiner:Q1",
        expected_cases=["G 1/15"],
        source='EXAMINER_PLAN.md landmark table: "G 1/15 77 (partial priority)"',
    ),
    GoldQuestion(
        id="opposition_grounds_clarity",
        question="Can lack of clarity of a granted claim be examined as a ground for "
                 "opposition?",
        theme="examiner:Q1",
        expected_cases=["G 3/14"],
        source='EXAMINER_PLAN.md landmark table: "G 3/14 786 (grounds for opposition / '
               'clarity of granted claims)"',
    ),
    GoldQuestion(
        id="reformatio_in_peius",
        question="Can a board revoke a patent on an appeal filed only by the proprietor?",
        theme="pharma:Q11",
        expected_cases=["G 9/92", "G 4/93"],
        source='PHARMA_GENERICS_PLAN.md Q11: "reformatio in peius, prohibited under '
               'G 9/92 / G 4/93"',
    ),
]
