"""Regressions for the remaining end-to-end architecture findings."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.content_mapping import _preview  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    ContextualReplyResolution, FollowUpContext, LLMUsage, NextTurnPrompt,
)
from netzoo_agent_core.cli.follow_up import (  # noqa: E402
    build_workflow_continuation, resolve_next_turn_input,
)
from netzoo_agent_core.evaluation.plan_review import evaluate_workflow_plan  # noqa: E402
from netzoo_agent_core.graph.continuation_invocation import continue_workflow  # noqa: E402
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.capability import validate_task_text  # noqa: E402
from netzoo_agent_core.routing.method_rejections import unsupported_algorithm_request  # noqa: E402


@pytest.mark.parametrize(
    "task",
    [
        "Run PANDA. I do not want differential expression.",
        "Run PANDA; do not perform mutation calling.",
    ],
)
def test_declined_deliverable_does_not_block_requested_workflow(task):
    assert validate_task_text(task, "run_panda", matched_actions=["run_panda"]) is None


@pytest.mark.parametrize(
    "task",
    [
        "Previously I tried Gaussian process active learning. Now run PANDA to infer a regulatory network.",
        "Run PANDA to infer a regulatory network; do not use Gaussian process active learning.",
    ],
)
def test_historical_or_declined_algorithm_is_not_a_requested_method(task):
    assert unsupported_algorithm_request(task) is None


def test_content_preview_reads_only_its_bounded_prefix(tmp_path):
    path = tmp_path / "large.tsv"
    path.write_bytes(b"Gene\tSample\n" + b"A" * 1_000_000)
    with patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read")):
        preview = _preview(path)
    assert preview.startswith("Gene\tSample")
    assert len(preview) <= 4_000


def test_plan_review_rejects_step_argument_that_changes_approved_input(tmp_path):
    network_a = tmp_path / "network-a.tsv"
    network_b = tmp_path / "network-b.tsv"
    for path in (network_a, network_b):
        path.write_text("source\ttarget\tweight\na\tb\t1\nc\td\t2\n")
    output = tmp_path / "output"
    task = f"Run CONDOR network_file={network_a} output_dir={output}"
    decision = TaskDecision(
        action="run_condor", in_scope=True, should_execute=True,
        intent_type="run_analysis", confidence=1, reason="Explicit CONDOR run.",
        network_file=str(network_a), output_dir=str(output),
    )
    plan = build_workflow_plan(decision, task)
    assert plan.status == "ready"
    assert evaluate_workflow_plan(plan, task).status == "approved"
    plan.steps[-1].arguments["network_file"] = str(network_b)

    evaluation = evaluate_workflow_plan(plan, task)
    assert evaluation.status == "rejected"
    assert any(item.criterion == "step_argument_alignment" and item.result == "fail"
               for item in evaluation.rubric)


def test_accepted_workflow_keeps_prior_explicit_inputs_and_controls():
    prior = (
        "Which workflow should I use? expression_file=data/expression.tsv "
        "coexpression_file=data/coexpression.tsv motif_file=data/motif.tsv "
        "ppi_file=data/ppi.tsv taxon=human precision=single lam=0.2"
    )
    prompt = NextTurnPrompt(
        kind="recommended_workflow", question="Continue?", continuation_action="run_otter",
    )
    context = FollowUpContext(
        prior_user_goal=prior, prompt_kind=prompt.kind, prompt_question=prompt.question,
        candidate_actions=["run_otter"], continuation_action="run_otter",
    )
    resolution = ContextualReplyResolution(
        kind="accept_workflow", reason="Accepted the recommendation.",
        selected_action="run_otter",
    )
    task = resolve_next_turn_input(prompt, resolution, "Use OTTER with precision=double")
    continuation = build_workflow_continuation(prompt, context, resolution, task)
    assert continuation is not None
    graph_context = SimpleNamespace(
        project_policy=ProjectPolicyLoader(Path(__file__).parents[1]).load(),
        recorder=Mock(),
    )
    invoked = continue_workflow(
        graph_context,
        {"workflow_continuation": continuation.model_dump(), "run_id": "test"},
        task,
        LLMUsage(),
    )
    decision = invoked.decision
    assert decision.action == "run_otter"
    assert decision.expression_file == "data/expression.tsv"
    assert decision.coexpression_file == "data/coexpression.tsv"
    assert decision.motif_file == "data/motif.tsv"
    assert decision.ppi_file == "data/ppi.tsv"
    assert decision.taxon == "human"
    assert decision.lam == 0.2
    assert decision.precision == "double"
