"""SAMBAR integration contracts: planning, execution preview, and artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, executor_arguments  # noqa: E402
from netzoo_agent_core.cli.clarification import input_confirmation_continuation  # noqa: E402
from netzoo_agent_core.data.sambar import inspect_sambar_inputs_impl  # noqa: E402
from netzoo_agent_core.interpretation.registry_guidance import (  # noqa: E402
    preferred_registry_composition_actions,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


ROOT = Path(__file__).parents[1]
TOY = ROOT / "data" / "sambar-toy"


def decision(**overrides):
    values = {
        "action": "run_sambar", "in_scope": True, "should_execute": True,
        "confidence": 1.0, "reason": "Run SAMBAR.",
        "mutation_file": str(TOY / "mutation.csv"),
        "exon_size_file": str(TOY / "exon_size.csv"),
        "cancer_gene_file": str(TOY / "cancer_genes.txt"),
        "pathway_file": str(TOY / "pathways.gmt"),
        "output_dir": "outputs/sambar-test", "kmin": 2, "kmax": 3,
    }
    values.update(overrides)
    return agent.TaskDecision(**values)


def test_policy_registry_and_no_direct_handoffs_are_exact():
    policy = ProjectPolicyLoader(ROOT).load()
    spec = policy.workflows["run_sambar"]
    definition = ACTION_DEFINITIONS["run_sambar"]
    assert spec.required_inputs == list(definition.required_inputs)
    assert spec.validation_steps == ["inspect_sambar_inputs"]
    assert spec.output_capability.handoff_targets == []
    assert "not direct inputs to PANDA" in spec.output_capability.handoff_contract


def test_sambar_does_not_invent_untyped_inbound_or_outbound_handoffs():
    policy = ProjectPolicyLoader(ROOT).load()
    sambar = policy.workflows["run_sambar"]

    assert sambar.output_capability.handoff_targets == []
    assert [
        action
        for action, spec in policy.workflows.items()
        if "run_sambar" in spec.output_capability.handoff_targets
    ] == []

    selected = preferred_registry_composition_actions(
        "Run SAMBAR pathway mutation scoring and clustering.",
        agent.TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=1.0,
            reason="SAMBAR is the final requested workflow.",
            capability_match_status="exact",
            matched_actions=["run_sambar"],
            recommended_actions=["run_sambar"],
        ),
        policy.workflows,
    )

    assert selected == ["run_sambar"]


def test_sambar_plans_with_explicit_role_paths_and_has_a_dry_run_preview():
    task = (
        f"Run SAMBAR with mutation_file={TOY / 'mutation.csv'} "
        f"exon_size_file={TOY / 'exon_size.csv'} "
        f"cancer_gene_file={TOY / 'cancer_genes.txt'} "
        f"pathway_file={TOY / 'pathways.gmt'} output_dir=outputs/sambar-test"
    )
    plan = agent.build_workflow_plan(decision(), task)
    assert plan.status == "ready"
    assert [step.action for step in plan.steps] == ["inspect_sambar_inputs", "run_sambar"]
    result = agent.run_sambar.invoke(executor_arguments("run_sambar", decision()))
    assert "Dry run only" in result
    assert "run-sambar" in result
    assert "None" not in result


def test_missing_or_invalid_sambar_input_never_becomes_ready(tmp_path):
    missing_plan = agent.build_workflow_plan(
        decision(mutation_file=None, exon_size_file=str(tmp_path / "exon_size.csv")),
        f"Run SAMBAR with exon_size_file={tmp_path / 'exon_size.csv'}",
    )
    assert missing_plan.status == "needs_input"

    broken = tmp_path / "mutation.csv"
    broken.write_text("sample,G1\nS1,not-a-number\nS2,0\n", encoding="utf-8")
    report, ok = inspect_sambar_inputs_impl(
        str(broken), str(TOY / "exon_size.csv"), str(TOY / "cancer_genes.txt"), str(TOY / "pathways.gmt"),
        {"kmin": 2, "kmax": 2, "cluster": True},
    )
    assert not ok
    assert "non-negative numeric" in report


def test_inferred_sambar_files_require_confirmation_then_become_ready(tmp_path):
    paths = {}
    for source, destination in (
        ("mutation.csv", "a.csv"), ("exon_size.csv", "b.csv"),
        ("cancer_genes.txt", "c.txt"), ("pathways.gmt", "d.gmt"),
    ):
        target = tmp_path / destination
        target.write_bytes((TOY / source).read_bytes())
        paths[source] = target

    class Mapper:
        def invoke(self, _messages):
            return {
                "assignments": [
                    {"path": str(paths["mutation.csv"]), "role": "mutation_file", "confidence": 0.9},
                    {"path": str(paths["exon_size.csv"]), "role": "exon_size_file", "confidence": 0.9},
                    {"path": str(paths["cancer_genes.txt"]), "role": "cancer_gene_file", "confidence": 0.9},
                    {"path": str(paths["pathways.gmt"]), "role": "pathway_file", "confidence": 0.9},
                ]
            }

    task = "Run SAMBAR with " + ", ".join(map(str, paths.values()))
    unconfirmed = agent.build_workflow_plan(
        decision(mutation_file=None, exon_size_file=None, cancer_gene_file=None, pathway_file=None),
        task,
        content_mapper=Mapper(),
    )
    assert unconfirmed.status == "needs_confirmation"
    assert "Are these the files you want to use? [y/N]" in (unconfirmed.question or "")
    continuation = input_confirmation_continuation(unconfirmed, "y", approved=True)
    confirmed = agent.build_workflow_plan(
        decision(mutation_file=None, exon_size_file=None, cancer_gene_file=None, pathway_file=None),
        continuation,
    )
    assert confirmed.status == "ready"


def test_sambar_artifact_contract_rejects_invalid_shape_and_accepts_valid_bundle(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "manifest.json").write_text(json.dumps({"method": "SAMBAR", "parameters": {"cluster": True}}), encoding="utf-8")
    (out / "mt_out.csv").write_text("sample,G1\nS1,1\nS2,0\n", encoding="utf-8")
    (out / "pt_out.csv").write_text(",S1,S2\nP1,1,0\n", encoding="utf-8")
    (out / "clustergroups.csv").write_text(",S1,S2\nX2,0,1\n", encoding="utf-8")
    np.savetxt(out / "dist_matrix.csv", np.asarray([[0.0, 1.0], [1.0, 0.0]]), delimiter=",")
    valid = agent.validate_output_artifacts("run_sambar", decision(output_dir=str(out), kmax=2))
    assert valid.ok, valid.errors
    (out / "dist_matrix.csv").write_text("0,1\n1,0\n2,3\n", encoding="utf-8")
    invalid = agent.validate_output_artifacts("run_sambar", decision(output_dir=str(out), kmax=2))
    assert not invalid.ok
    assert "square" in " ".join(invalid.errors)


def test_sambar_accepts_upstream_pathway_scores_for_nonzero_samples_only(tmp_path):
    """Official SAMBAR omits all-zero samples from the pathway score matrix."""
    out = tmp_path / "out"
    out.mkdir()
    (out / "manifest.json").write_text(
        json.dumps({"method": "SAMBAR", "parameters": {"cluster": False}}),
        encoding="utf-8",
    )
    (out / "mt_out.csv").write_text(
        "sample,G1\nS1,1\nS2,0\nS3,0\n", encoding="utf-8"
    )
    (out / "pt_out.csv").write_text(
        ",S1\nPATHWAY_A,0.5\n", encoding="utf-8"
    )

    valid = agent.validate_output_artifacts(
        "run_sambar", decision(output_dir=str(out), cluster=False)
    )

    assert valid.ok, valid.errors
    assert valid.metrics["sambar_mutation_score_samples"] == 3
    assert valid.metrics["sambar_pathway_score_samples"] == 1


def test_sambar_optional_defaults_never_leak_none_into_strict_schema():
    incomplete = decision().model_copy(update={"norm_patient": None, "distance": None, "linkage": None})
    args = executor_arguments("run_sambar", incomplete)
    assert args["norm_patient"] is True
    assert args["distance"] == "binomial"
    assert args["linkage"] == "complete"
    assert all(value is not None for value in args.values())
