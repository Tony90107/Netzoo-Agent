"""Log 315: "a handful" or "dozens" must be the user's own words, never a mapped number.

User decision 2026-09-27 #3 (reconfirmed 2026-10-02): the agent does not map a
sample count to few or many. Recorded: after Test 2's "Only expression data"
the recommender claimed cohort_size:many from a sentence with no count at all.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import ConditionClaim, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402

PER_SAMPLE_COEXPRESSION = ["run_lioness_coexpression", "run_bonobo"]
T2_FOLLOW_UP = (
    "Previous NetZoo goal: We have microarray expression profiles from 40 heart failure patients with highly "
    "heterogeneous clinical presentations. A single population-level network would average away individual "
    "differences, but each patient contributed only one tissue biopsy, so a per-patient correlation cannot be "
    "computed. How can we reconstruct a separate regulatory network for each patient from this cohort?\n"
    "User follow-up: I only have expression data. One gene-gene co-expression network per sample (genes only, "
    "no regulator roles) is fine."
)


def _recommend(task, condition, quote):
    claims = SelectionConditionClaims(claims=[ConditionClaim(condition=condition, text_span=quote)])
    return recommend_from_claims(task, claims, condition_options(PER_SAMPLE_COEXPRESSION), PER_SAMPLE_COEXPRESSION)


def test_the_recorded_dozens_claim_after_test_2_is_rejected():
    quote = ("I only have expression data. One gene-gene co-expression network per sample (genes only, "
             "no regulator roles) is fine.")
    recommendation, rejected = _recommend(T2_FOLLOW_UP, "cohort_size:many", quote)
    assert recommendation is None
    assert rejected == [{"condition": "cohort_size:many", "reason": "condition_not_in_request"}]


def test_a_number_alone_is_no_witness_for_either_value():
    task = "I have expression data for 50 patients and want a co-expression network for each. Which tool?"
    for condition in ("cohort_size:many", "cohort_size:few"):
        assert _recommend(task, condition, "50 patients")[0] is None


def test_the_users_own_words_still_recommend():
    few = _recommend("I only have expression data from a handful of patients. Which tool?",
                     "cohort_size:few", "a handful of patients")[0]
    assert few is not None and few.action == "run_bonobo"
    many = _recommend("We have dozens of patients with RNA-seq. Which tool?",
                      "cohort_size:many", "dozens of patients")[0]
    assert many is not None and many.action == "run_lioness_coexpression"


def test_one_value_does_not_witness_the_other():
    assert _recommend("I only have a handful of patients. Which tool?", "cohort_size:many", "a handful of patients")[0] is None
    assert _recommend("We have hundreds of tumour samples. Which tool?", "cohort_size:few", "hundreds of tumour samples")[0] is None
