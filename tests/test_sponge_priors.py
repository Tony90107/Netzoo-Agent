"""SPONGE priors (kuijjerlab/sponge, 2026-11-08): a preparation step read from the request's own words.

"Build the motif and PPI priors with SPONGE for SOX2 and MYC, then run PANDA on expr.tsv" is planned as build_priors
with PANDA recorded as the next step; once the priors are built, PANDA is offered with the two files. Nothing is
downloaded until /execute, and the plan says what the run downloads.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.execution_sponge import sponge_input_errors, validate_sponge_output  # noqa: E402
from netzoo_agent_core.interpretation.ruled_out import route_available  # noqa: E402
from netzoo_agent_core.prior_request import (  # noqa: E402
    PRIOR_CONSUMERS, SPONGE_MOTIFS_JASPAR2026, prior_decision, prior_requested, requested_tf_names,
    sponge_plan_lines,
)
from netzoo_agent_core.routing.authorization import action_operation_kind  # noqa: E402
from workflow_registry import PREPARATION_ACTIONS  # noqa: E402

EXECUTE = SimpleNamespace(request_mode="execute")


@pytest.mark.parametrize("task", [
    "Build the motif and PPI priors with SPONGE for SOX2 and MYC.",
    "Please generate a motif prior for the TFs SOX2, MYC and FOXF2.",
    "Use SPONGE to make PANDA priors.",
    "幫我用 SPONGE 建立 motif 先驗",
])
def test_a_command_to_build_priors_is_a_sponge_step(task):
    assert prior_requested(task, EXECUTE)


@pytest.mark.parametrize("task", [
    "Run PANDA with my motif prior /data/motif.tsv.",  # a prior the user has
    "What is a motif prior?",  # a question
    "Don't build new priors; use mine.",
    "Normalize my counts with SNAIL.",
])
def test_other_requests_are_left_to_routing(task):
    assert not prior_requested(task, EXECUTE)


def test_settings_are_read_from_explicit_words_only():
    task = ("Build the motif and PPI priors with SPONGE for the TFs SOX2, MYC and FOXF2 using JASPAR 2024 on hg19, "
            "with promoters -1000/+500 bp, then run PANDA with expression_file=/data/expr.tsv.")
    decision = prior_decision(task, EXECUTE)
    assert decision.action == "build_priors" and decision.then_action == "run_panda"
    assert decision.sponge_tf_names == ["SOX2", "MYC", "FOXF2"]
    assert (decision.jaspar_release, decision.genome_assembly) == ("JASPAR2024", "hg19")
    assert (decision.promoter_upstream, decision.promoter_downstream) == (1000, 500)
    plain = prior_decision("Build the priors with SPONGE.", EXECUTE)
    assert (plain.sponge_tf_names, plain.jaspar_release, plain.genome_assembly, plain.then_action) == (None, None, None, None)
    assert requested_tf_names("tf_names=sox2, myc") == ["SOX2", "MYC"]


def test_the_plan_says_what_a_run_without_a_tf_list_downloads():
    lines = sponge_plan_lines({})
    assert lines[0] == "- TFs: every vertebrate JASPAR CORE motif [SPONGE default]"
    assert f"{SPONGE_MOTIFS_JASPAR2026:,} in JASPAR2026" in lines[-1] and "hours" in lines[-1]
    named = sponge_plan_lines({"sponge_tf_names": ["SOX2", "MYC"], "promoter_upstream": 1000})
    assert named[0] == "- TFs: SOX2, MYC [from your request]" and "for each of the 2 TFs" in named[-1]
    assert "1000 bp upstream to 250 bp downstream" in named[3]


def test_sponge_is_human_only_and_waits_for_execute():
    assert sponge_input_errors({"taxon": "mouse"})[0].startswith("SPONGE builds human priors only")
    assert sponge_input_errors({"taxon": "Homo sapiens"}) == []
    assert action_operation_kind("build_priors") == "transform" and "build_priors" in PREPARATION_ACTIONS
    assert {"run_panda", "run_scorpion", "run_otter", "run_lioness_panda"} <= PRIOR_CONSUMERS


def test_a_missing_motif_prior_names_sponge_instead_of_nothing():
    reason = route_available("run_panda", {"motif_prior": "I don't have a motif file"})
    assert "PANDA needs a TF motif prior; SPONGE (registered) can build a human motif prior" in reason
    assert "no registered workflow or tool provides it" not in reason


def test_the_output_check_reads_both_priors_and_the_manifest(tmp_path):
    (tmp_path / "motif_prior.tsv").write_text("SOX2\tA2M\t1\nMYC\tA2M\t1\n")
    (tmp_path / "ppi_prior.tsv").write_text("SOX2\tMYC\t0.782\n")
    (tmp_path / "manifest.json").write_text('{"summary": {"motif_edges": 2, "motif_tfs": 2, '
                                            '"requested_tfs_without_motif_edges": ["NOTATF"]}}')
    errors, artifacts, metrics = validate_sponge_output(str(tmp_path))
    assert errors == [] and len(artifacts) == 3
    # A string: a list failed the artifact-result schema once a requested TF had no edges (2026-11-10, MAX).
    assert metrics["sponge_motif_edges"] == 2 and metrics["sponge_requested_tfs_without_motif_edges"] == "NOTATF"


def test_once_built_the_next_workflow_is_offered_with_both_priors(tmp_path):
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt

    decision = prior_decision("Build the priors with SPONGE for SOX2, then run PANDA.", EXECUTE)
    decision = decision.model_copy(update={"output_dir": str(tmp_path)})
    state = {
        "decision": decision.model_dump(),
        "plan": {"workflow": "SPONGE-PRIORS", "objective": "x", "decision": decision.model_dump(), "status": "ready"},
        "tool_results": [{"action": "build_priors", "status": "success", "summary": "ok", "raw_output": "ok"}],
        "evaluation": {"status": "completed"},
    }
    prompt = build_next_turn_prompt(state)
    assert prompt.continuation_action == "run_panda"
    assert prompt.carried_inputs == {"motif_file": str(tmp_path / "motif_prior.tsv"),
                                     "ppi_file": str(tmp_path / "ppi_prior.tsv")}


def test_the_dry_run_shows_the_settings_and_the_download():
    from netzoo_agent_core.contracts import ToolExecutionResult, WorkflowPlan
    from netzoo_agent_core.evaluation.rendering import render_compact_execution_response

    decision = prior_decision("Build the priors with SPONGE for the TFs SOX2 and MYC.", EXECUTE)
    plan = WorkflowPlan(workflow="SPONGE-PRIORS", objective=decision.reason, decision=decision.model_dump(),
                        status="ready")
    text = render_compact_execution_response(
        plan, [ToolExecutionResult(action="build_priors", status="dry_run", summary="planned", raw_output="")], None)
    assert "Settings" in text and "- TFs: SOX2, MYC [from your request]" in text
    assert "for each of the 2 TFs" in text and "human" in text


def test_a_sponge_request_is_routed_before_the_semantic_reading(monkeypatch):
    import netzoo_agent_core.graph.router_invocation as router

    def fail(*args, **kwargs):
        raise AssertionError("the semantic interpreter must not be asked")
    monkeypatch.setattr(router, "_invoke_semantic_interpreter", fail)
    state = {"method_comparison": None, "workflow_continuation": None}
    monkeypatch.setattr(router, "_current_usage", lambda context, state: None)
    task = ("Build the motif and PPI priors with SPONGE for the TF MYC, write them to output_dir=tmp/p, "
            "then run PANDA with expression_file=data/expr.tsv.")
    result = router._route_request(SimpleNamespace(), state, task)
    assert result.decision.action == "build_priors" and result.reason_code == "sponge_priors"
    assert result.decision.then_action == "run_panda" and result.decision.output_dir == "tmp/p"
