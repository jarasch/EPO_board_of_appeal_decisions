"""Canned example questions for the UI's chip row.

Drawn from PHARMA_GENERICS_PLAN.md and EXAMINER_PLAN.md, restricted to questions
answerable with what actually exists today (canonical dedup, outcome, ground
disposition, authority weight, paragraph-level citation). Nothing here depends
on the appellant-role layer or the citator -- neither is built yet, so pharma
Q11 and the examiner's divergence question (Q2) are deliberately not chips.
"""

EXAMPLES = {
    "pharma": [
        "Since G 2/21, when does post-published evidence rescue an inventive-step case "
        "for a second medical use claim?",
        "What has the EPO decided about the validity of polymorph and crystalline-form "
        "claims over a prior compound patent?",
        "How do boards treat late-filed evidence under Art. 12 and 13 RPBA 2020 in "
        "opposition appeals?",
        "What arguments have succeeded against an added-subject-matter objection for a "
        "numerical range?",
    ],
    "examiner": [
        "What is the current standard for added subject-matter under Article 123(2) EPC, "
        "and what is the leading authority?",
        "What procedural acts have led to a substantial procedural violation and "
        "reimbursement of the appeal fee?",
        "How has the Enlarged Board addressed plausibility and post-published evidence "
        "for inventive step?",
        "What is the test for assessing inventive step of a computer-implemented "
        "invention (the COMVIK approach)?",
    ],
}
