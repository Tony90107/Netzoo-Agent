"""Guidance replies claim a control is relevant only when its tags meet the request (Log 221)."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import guidance_contract, render_verified_guidance  # noqa: E402


def _guidance(action, outcome, task):
    decision = agent.TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.95,
        reason="Guidance", requested_outcome=outcome,
        capability_match_status="exact", match_basis="registry_features",
        matched_actions=[action], recommended_actions=[action],
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    return render_verified_guidance(decision, guidance_contract(decision, policy, task))


def test_untagged_controls_are_not_presented_as_matched_to_the_request():
    outcome = agent.RequestedOutcome(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network", entity_types=["tf", "gene"],
        regulator_types=["tf"], target_types=["gene"], granularity="aggregate",
    )
    answer = _guidance(
        "run_otter", outcome,
        "One consensus regulatory network; the last method ran out of memory.",
    )

    assert answer is not None
    assert "for this request:" not in answer
    assert "Controls matching this request" not in answer
    other = re.search(r"Other declared controls \(not matched to this request[^\n]*", answer)
    assert other is not None
    for name in ("output_format", "computing", "precision", "lam", "gamma", "iterations", "eta", "bexp"):
        assert f"`{name}`" in other.group(0)
    assert "`precision`=double" in other.group(0)
    assert "Runtime limits:" in answer
    assert "current runtime unavailable: gpu" in answer


def test_only_controls_whose_tags_meet_the_request_are_listed_in_full():
    outcome = agent.RequestedOutcome(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network", entity_types=["gene"],
        selection_tags=["sparse_pvalue_coexpression"], granularity="sample_specific",
    )
    answer = _guidance("run_bonobo", outcome, "Save sparsification p-values per sample.")

    assert answer is not None
    matched = answer.split("Controls matching this request:\n\n", 1)[1].split("\n\n", 1)[0]
    names = re.findall(r"^- `([^`]+)`", matched, re.M)
    assert names == ["sparsify", "bonobo_confidence", "save_pvals"]
    other = re.search(r"Other declared controls \(not matched to this request[^\n]*", answer).group(0)
    assert "`sample_names`" in other
    assert "`sparsify`" not in other
