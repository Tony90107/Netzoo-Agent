"""Log 323: two first passes that fell back on validation (TEST_PROMPTS Tests 2 and 5).

SH: a single assumption written as a string is wrapped in the declared list,
so the first pass is patched instead of rewritten from scratch. FI: when the
request states patient grouping, a reading of a result the grouping workflow
produces on the way is folded into the grouping reading with its inputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.semantic_shape import normalize_semantic_shape  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.terminal_goal_fold import _STEPS, fold_intermediate_readings  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

FALLBACKS = json.loads((ROOT / "docs" / "research-log" / "validation-fallbacks-2026-10-03"
                        / "test5-fallbacks.json").read_text())


def test_a_string_assumption_becomes_a_one_item_list():
    payload = {"request_mode": "guidance", "semantic_goal": "x", "assumptions": "a patch-level note",
               "outcome_hypotheses": [{"assumptions": "Each patient has one sample.", "confidence": 0.9}]}
    normalized, notes = normalize_semantic_shape(payload)
    assert normalized["outcome_hypotheses"][0]["assumptions"] == ["Each patient has one sample."]
    assert normalized["assumptions"] == ["a patch-level note"]
    assert len(notes) == 2 and payload["outcome_hypotheses"][0]["assumptions"] == "Each patient has one sample."


def test_a_list_and_a_missing_confidence_are_left_alone():
    payload = {"outcome_hypotheses": [{"assumptions": ["kept"]}]}
    normalized, notes = normalize_semantic_shape(payload)
    assert normalized == payload and notes == []
    assert "confidence" not in normalized["outcome_hypotheses"][0]


def test_the_steps_are_what_the_grouping_workflow_also_produces():
    assert _STEPS == {"pathway_mutation_matrix", "gene_mutation_scores", "sample_distance_matrix"}


def test_test5_fallbacks_fold_into_one_valid_grouping_reading():
    for case in FALLBACKS:
        interpretation = SemanticInterpretation.model_validate(case["rejected_interpretation"])
        assert not validate_outcome_hypotheses(case["task"], [h.model_copy(deep=True) for h in
                                                              interpretation.outcome_hypotheses],
                                               interpretation.request_mode).valid
        folded, notes = fold_intermediate_readings(case["task"], interpretation)
        assert [note["inputs_moved"] for note in notes] == [["mutation_matrix"]]
        [reading] = folded.outcome_hypotheses
        assert reading.outcome.artifact_type == "sample_cluster_assignment"
        assert reading.outcome.input_artifacts == ["mutation_matrix"]
        assert validate_outcome_hypotheses(case["task"], folded.outcome_hypotheses, folded.request_mode).valid
        assert match_semantic_request(case["task"], folded.outcome_hypotheses,
                                      request_mode="guidance").matched_actions == ["run_sambar"]


def test_no_fold_without_a_stated_grouping_goal():
    case = FALLBACKS[0]
    interpretation = SemanticInterpretation.model_validate(case["rejected_interpretation"])
    task = "Summarize these scattered gene-level mutations into pathway-level scores for each patient."
    assert fold_intermediate_readings(task, interpretation) == (interpretation, [])
