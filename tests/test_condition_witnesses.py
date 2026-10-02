"""Log 304 (CR1): the PANDA/OTTER/GIRAFFE conditions need their evidence words in the request."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import ConditionClaim, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402

TRIO = ["run_panda", "run_otter", "run_giraffe"]
GOAL = ("We want to estimate genome-wide regulatory strengths, capturing both the regulatory "
        "communication between TFs and target genes as well as cooperative complexes among TFs.")
# The 2026-10-02 request whose goal sentence was quoted for established_method.
LUNG = ("We just finished sequencing lung cancer tissue transcriptomes and have standard transcription "
        "factor motif binding sites alongside known protein-protein interaction maps. " + GOAL
        + " What framework should we use to build this network?")
GENERIC = [
    LUNG,
    "Our tumor RNA-seq comes with TF motif priors and a protein interaction map. We want to capture how "
    "TFs communicate with their target genes and how TFs cooperate in complexes. Which framework builds "
    "this network? Advice only.",
    "From our cohort's expression data plus motif and PPI priors, we want genome-wide TF-to-gene "
    "regulatory strengths in one network. What framework should we use? Advice only.",
    "Using standard motif and PPI priors with our tumor expression data, we want one genome-scale "
    "TF-to-gene regulatory network. Which framework fits? Advice only.",
]
T1 = ("I need one cohort-wide TF-to-gene regulatory network from my expression matrix, TF motif prior "
      "and PPI data (data/blind-neutral/case-2/). ")


def recommend(task, condition, quote):
    claims = SelectionConditionClaims(claims=[ConditionClaim(condition=condition, text_span=quote)])
    return recommend_from_claims(task, claims, condition_options(TRIO), TRIO)


def test_the_recorded_lung_claim_is_rejected():
    recommendation, rejected = recommend(LUNG, "established_method:yes", GOAL)

    assert recommendation is None
    assert rejected == [{"condition": "established_method:yes", "reason": "condition_not_in_request"}]


@pytest.mark.parametrize("task", GENERIC)
@pytest.mark.parametrize("condition", [
    "established_method:yes", "compute_constraints:constrained", "tf_activity_vs_expression:yes",
])
def test_a_generic_request_states_none_of_the_three_conditions(task, condition):
    recommendation, rejected = recommend(task, condition, task.split(". ")[0])

    assert recommendation is None
    assert rejected[0]["reason"] == "condition_not_in_request"


@pytest.mark.parametrize("task,condition,quote,action", [
    (T1 + "The results must be comparable with the widely published approach.", "established_method:yes",
     "The results must be comparable with the widely published approach.", "run_panda"),
    (T1 + "The real network will be very large, so memory and runtime are a concern.",
     "compute_constraints:constrained", "memory and runtime are a concern", "run_otter"),
    (T1 + "I suspect some regulators are more active in some samples even though their own expression "
     "barely changes.", "tf_activity_vs_expression:yes",
     "I suspect some regulators are more active in some samples", "run_giraffe"),
    ("Last time a similar method ran out of memory and took forever to stop iterating.",
     "compute_constraints:constrained", "ran out of memory", "run_otter"),
    ("我需要一張整體的調控網路，結果要能和已發表的方法比較。", "established_method:yes",
     "結果要能和已發表的方法比較", "run_panda"),
    ("網路會非常大，記憶體和執行時間有限。", "compute_constraints:constrained", "記憶體和執行時間有限", "run_otter"),
    ("我懷疑有些轉錄因子的活性和它自己的表現量不同。", "tf_activity_vs_expression:yes",
     "轉錄因子的活性和它自己的表現量不同", "run_giraffe"),
])
def test_a_stated_condition_still_recommends(task, condition, quote, action):
    recommendation, rejected = recommend(task, condition, quote)

    assert rejected == []
    assert recommendation is not None and recommendation.action == action
