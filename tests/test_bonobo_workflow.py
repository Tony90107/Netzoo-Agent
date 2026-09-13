from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    ToolExecutionResult,
    WorkflowPlan,
    WorkflowStep,
)
from netzoo_agent_core.contracts.handoffs import WorkflowHandoff  # noqa: E402
from netzoo_agent_core.data.bonobo import (  # noqa: E402
    bonobo_api_output_folder,
    inspect_bonobo_inputs_impl,
    load_bonobo_inputs,
    materialize_bonobo_sample_coexpression,
    validate_bonobo_output,
)
from netzoo_agent_core.execution import run_bonobo  # noqa: E402
from netzoo_agent_core.cli.slash_commands import handle_slash_command  # noqa: E402
from netzoo_agent_core.evaluation.plan_review import evaluate_workflow_plan  # noqa: E402
from netzoo_agent_core.evaluation.step_results import evaluate_step_result  # noqa: E402
from netzoo_agent_core.routing.results import structure_tool_result  # noqa: E402
from netzoo_agent_core.data.coexpression import read_coexpression_matrix  # noqa: E402
from netzoo_agent_core.handoff import (  # noqa: E402
    build_bonobo_handoff,
    explicit_bonobo_handoff_requested,
)
from workflow_registry import (  # noqa: E402
    ACTION_DEFINITIONS,
    OUTPUT_CAPABILITIES,
    executor_arguments,
)


def _expression(tmp_path: Path, *, suffix: str = ".tsv") -> Path:
    path = tmp_path / f"expression{suffix}"
    if suffix == ".csv":
        # This mirrors the verified upstream reader, which uses a literal
        # space separator for .csv rather than comma-separated CSV input.
        text = (
            "gene_id s1 s2 s3 s4\n"
            "g1 1.0 2.0 3.0 4.0\n"
            "g2 2.0 3.0 4.0 5.0\n"
            "g3 3.0 4.0 5.0 6.0\n"
        )
    else:
        text = (
            "gene_id\ts1\ts2\ts3\ts4\n"
            "g1\t1.0\t2.0\t3.0\t4.0\n"
            "g2\t2.0\t3.0\t4.0\t5.0\n"
            "g3\t3.0\t4.0\t5.0\t6.0\n"
        )
    path.write_text(text, encoding="utf-8")
    return path


def _decision(expression: Path, output: Path, **overrides) -> TaskDecision:
    values = {
        "action": "run_bonobo",
        "in_scope": True,
        "should_execute": True,
        "confidence": 1.0,
        "reason": "Run BONOBO sample-specific co-expression.",
        "expression_file": str(expression),
        "output_dir": str(output),
        "log_transformed": True,
        "centered": True,
    }
    values.update(overrides)
    return TaskDecision(**values)


def test_bonobo_input_contract_is_gene_by_sample_and_preserves_sample_subset(tmp_path):
    expression = _expression(tmp_path)
    report, ok = inspect_bonobo_inputs_impl(
        str(expression),
        ["s2", "s4"],
        log_transformed=True,
        centered=True,
    )
    assert ok, report
    bundle = load_bonobo_inputs(
        str(expression), ["s2", "s4"], log_transformed=True, centered=True
    )
    assert bundle.gene_ids == ("g1", "g2", "g3")
    assert bundle.sample_ids == ("s1", "s2", "s3", "s4")
    assert bundle.selected_sample_ids == ("s2", "s4")
    assert "selected samples: s2, s4" in report
    assert bonobo_api_output_folder(str(tmp_path / "outputs")).endswith("/")


@pytest.mark.parametrize(
    ("mutator", "needle"),
    [
        (lambda text: text.replace("g2\t", "g1\t", 1), "gene IDs"),
        (lambda text: text.replace("gene_id\ts1\ts2\ts3\ts4", "gene_id\ts1\ts1\ts3\ts4"), "sample IDs"),
        (lambda text: text.replace("g2\t2.0", "g2\tmissing"), "numeric"),
        (lambda text: text.replace("gene_id", "sample_id", 1), "sample-by-gene"),
    ],
)
def test_bonobo_rejects_invalid_matrix_contract(tmp_path, mutator, needle):
    expression = _expression(tmp_path)
    expression.write_text(mutator(expression.read_text(encoding="utf-8")), encoding="utf-8")
    report, ok = inspect_bonobo_inputs_impl(
        str(expression), log_transformed=True, centered=True
    )
    assert not ok
    assert needle.casefold() in report.casefold()


def test_bonobo_rejects_transposed_axis_and_insufficient_samples(tmp_path):
    expression = _expression(tmp_path)
    report, ok = inspect_bonobo_inputs_impl(
        str(expression), genes_axis="columns", log_transformed=True, centered=True
    )
    assert not ok
    assert "gene IDs on rows" in report

    too_few = tmp_path / "too-few.tsv"
    too_few.write_text("gene_id\ts1\ts2\ng1\t1\t2\ng2\t2\t3\n", encoding="utf-8")
    report, ok = inspect_bonobo_inputs_impl(
        str(too_few), log_transformed=True, centered=True
    )
    assert not ok
    assert "at least three" in report


def test_bonobo_rejects_missing_or_duplicate_requested_sample_names(tmp_path):
    expression = _expression(tmp_path)
    report, ok = inspect_bonobo_inputs_impl(
        str(expression), ["s99"], log_transformed=True, centered=True
    )
    assert not ok
    assert "not present" in report
    report, ok = inspect_bonobo_inputs_impl(
        str(expression), ["s2", "s2"], log_transformed=True, centered=True
    )
    assert not ok
    assert "duplicates" in report


def test_bonobo_requires_log_transform_centering_and_pvalues_need_sparsify(tmp_path):
    expression = _expression(tmp_path)
    report, ok = inspect_bonobo_inputs_impl(str(expression), centered=True)
    assert not ok
    assert "log-transformed" in report
    report, ok = inspect_bonobo_inputs_impl(str(expression), log_transformed=True)
    assert not ok
    assert "centered" in report
    report, ok = inspect_bonobo_inputs_impl(
        str(expression), log_transformed=True, centered=True,
        output_dir=str(tmp_path / "out"), save_pvals=True, sparsify=False,
    )
    assert not ok
    assert "requires sparsify" in report


def _fake_bonobo_class():
    class FakeBonobo:
        calls: list[dict] = []

        def __init__(self, expression_file):
            self.expression_file = expression_file

        def run_bonobo(self, **kwargs):
            type(self).calls.append(kwargs)
            root = Path(kwargs["output_folder"])
            root.mkdir(parents=True, exist_ok=True)
            genes = ["g1", "g2", "g3"]
            for sample in kwargs["sample_names"]:
                matrix = pd.DataFrame(np.eye(3), columns=genes)
                network = root / f"bonobo_{sample}{kwargs['output_fmt']}"
                pvalues = root / f"pvals_{sample}{kwargs['output_fmt']}"
                if kwargs["output_fmt"] in {".h5", ".hdf"}:
                    matrix.to_hdf(network, key="bonobo", index=False)
                    if kwargs["sparsify"] and kwargs["save_pvals"]:
                        matrix.to_hdf(pvalues, key="pvals", index=False)
                else:
                    separator = "\t" if kwargs["output_fmt"] == ".txt" else ","
                    matrix.to_csv(network, sep=separator, index=False)
                    if kwargs["sparsify"] and kwargs["save_pvals"]:
                        matrix.to_csv(pvalues, sep=separator, index=False)

    return FakeBonobo


@pytest.mark.parametrize("output_format", [".h5", ".hdf", ".txt", ".csv"])
def test_bonobo_execution_verifies_network_and_optional_pvalue_artifacts(
    tmp_path, output_format
):
    expression = _expression(tmp_path)
    output = tmp_path / f"out-{output_format[1:]}"
    fake = _fake_bonobo_class()
    decision = _decision(
        expression,
        output,
        bonobo_output_format=output_format,
        sample_names=["s2"],
        sparsify=True,
        save_pvals=True,
        bonobo_confidence=0.1,
        precision="double",
        keep_in_memory=True,
    )
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution_bonobo._load_bonobo_api",
        return_value=(fake, "0.11.0"),
    ):
        raw = run_bonobo.invoke(executor_arguments("run_bonobo", decision))
    assert "API execution completed" in raw
    assert "s2" in raw and "s1" not in raw.split("selected samples:", 1)[-1].split("\n", 1)[0]
    assert fake.calls[0]["sample_names"] == ["s2"]
    assert fake.calls[0]["confidence"] == 0.1
    bundle = load_bonobo_inputs(
        str(expression), ["s2"], log_transformed=True, centered=True
    )
    valid, errors, artifacts, metrics = validate_bonobo_output(
        str(output), bundle.gene_ids, bundle.selected_sample_ids, output_format,
        save_pvals=True, sparsify=True,
    )
    assert valid, errors
    assert len(artifacts) == 3
    assert metrics["bonobo_networks"] == 1
    assert metrics["bonobo_pvalues"] == 1
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sparsify_requested"] is True
    assert manifest["network_sparsified"] is False
    assert manifest["pvalue_thresholding_required"] is True
    selected = materialize_bonobo_sample_coexpression(
        str(output), "s2", str(tmp_path / "selected-s2.tsv")
    )
    selected_matrix = read_coexpression_matrix(
        str(selected), expected_gene_ids=list(bundle.gene_ids)
    )
    assert list(selected_matrix.index) == list(bundle.gene_ids)
    with pytest.raises(ValueError):
        read_coexpression_matrix(str(output), expected_gene_ids=list(bundle.gene_ids))


def test_bonobo_dry_run_does_not_import_or_create_output(tmp_path):
    expression = _expression(tmp_path)
    output = tmp_path / "dry-run"
    decision = _decision(expression, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", False), patch(
        "netzoo_agent_core.execution_bonobo._load_bonobo_api",
        side_effect=AssertionError("dry-run must not import BONOBO"),
    ):
        raw = run_bonobo.invoke(executor_arguments("run_bonobo", decision))
    assert "Python API preview" in raw
    assert "no analysis was executed" in raw
    assert not output.exists()


def test_bonobo_pvalue_preview_explains_that_upstream_retains_the_full_network(tmp_path):
    expression = _expression(tmp_path)
    output = tmp_path / "pvalue-preview"
    decision = _decision(
        expression,
        output,
        sample_names=["s2"],
        sparsify=True,
        save_pvals=True,
    )
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", False):
        raw = run_bonobo.invoke(executor_arguments("run_bonobo", decision))

    assert "retains the full co-expression matrix" in raw
    assert "threshold it from the saved p-value matrix" in raw


def test_bonobo_missing_runtime_is_typed(tmp_path):
    expression = _expression(tmp_path)
    output = tmp_path / "missing-runtime"
    decision = _decision(expression, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution_bonobo._load_bonobo_api",
        side_effect=ModuleNotFoundError("No module named 'netZooPy.bonobo'"),
    ):
        raw = run_bonobo.invoke(executor_arguments("run_bonobo", decision))
    result = structure_tool_result("run_bonobo", decision, raw)
    assert result.status == "failed"
    assert result.error_code == "BONOBO_NETZOOPY_MISSING"


def test_bonobo_plan_gate_and_no_direct_panda_puma_handoff(tmp_path):
    expression = _expression(tmp_path)
    output = tmp_path / "planned"
    decision = _decision(expression, output, sample_names=["s2"])
    plan = build_workflow_plan(
        decision,
        f"Run BONOBO expression_file={expression} output_dir={output} "
        "sample_names=s2 log_transformed=true centered=true",
    )
    assert plan.status == "ready"
    assert [step.action for step in plan.steps] == [
        "inspect_bonobo_inputs",
        "run_bonobo",
    ]
    definition = ACTION_DEFINITIONS["run_bonobo"]
    capability = OUTPUT_CAPABILITIES["run_bonobo"]
    assert "sample_names" in definition.executor_fields
    assert capability.handoff_targets == ()
    assert "not a direct PANDA/PUMA" in capability.handoff_contract
    evaluation = evaluate_workflow_plan(
        plan,
        f"Run BONOBO expression_file={expression} output_dir={output} "
        "sample_names=s2 log_transformed=true centered=true",
    )
    assert evaluation.status == "approved", evaluation
    execute_gate = handle_slash_command(
        "/execute", current_plan=plan, current_plan_evaluation=evaluation
    )
    assert execute_gate.handled and execute_gate.execute_once
    assert "Confirm" in execute_gate.message

    missing = build_workflow_plan(
        TaskDecision(
            action="run_bonobo", in_scope=True, should_execute=True,
            confidence=1.0, reason="Run BONOBO.",
        ),
        "Run BONOBO.",
    )
    assert missing.status == "needs_input"
    assert "expression_file" in missing.missing_inputs
    assert "output_dir" not in missing.missing_inputs


@pytest.mark.parametrize(
    "task",
    [
        "Explain the difference between BONOBO and PANDA.",
        "Run BONOBO and explain its output; do not run another workflow.",
        "Run BONOBO and PANDA as separate analyses.",
    ],
)
def test_bonobo_comparison_or_separate_analysis_is_not_a_handoff(task):
    assert not explicit_bonobo_handoff_requested(task)


def test_bonobo_explicit_unregistered_consumer_is_still_blocked():
    task = "Run BONOBO, then pass the result to MAGIC workflow."
    assert explicit_bonobo_handoff_requested(task)
    handoff = build_bonobo_handoff(
        task,
        TaskDecision(
            action="run_bonobo",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason=task,
        ),
    )
    assert handoff is not None
    assert handoff.status == "blocked_no_consumer"


@pytest.mark.parametrize(
    ("task", "status"),
    [
        ("Run BONOBO, then pass the result to a regulatory-network workflow", "blocked_no_consumer"),
        ("Run BONOBO, then pass the result to PANDA", "blocked_incompatible"),
    ],
)
def test_bonobo_explicit_downstream_request_is_blocked_during_planning(
    tmp_path, task, status
):
    expression = _expression(tmp_path)
    decision = _decision(expression, tmp_path / "planned")
    plan = build_workflow_plan(
        decision,
        f"{task} expression_file={expression} output_dir={tmp_path / 'planned'} "
        "log_transformed=true centered=true",
    )

    assert plan.status == "needs_input"
    assert plan.workflow_handoff is not None
    assert plan.workflow_handoff.status == status
    assert plan.workflow_handoff.source_artifact_type == "coexpression_network"
    assert plan.workflow_handoff.source_granularity == "sample_specific"
    assert not plan.steps
    assert "no execution is permitted" in plan.question.casefold()
    assert evaluate_workflow_plan(plan, task).status == "deferred"


def test_bonobo_handoff_accepts_only_a_registered_sample_specific_consumer():
    consumer_capability = replace(
        ACTION_DEFINITIONS["run_panda"].output_capability,
        granularities=frozenset({"sample_specific"}),
        accepted_input_granularities=frozenset({"sample_specific"}),
    )
    registry = dict(ACTION_DEFINITIONS)
    registry["run_panda"] = replace(
        ACTION_DEFINITIONS["run_panda"], output_capability=consumer_capability
    )
    decision = TaskDecision(
        action="run_bonobo",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run BONOBO then PANDA.",
        sample_names=["s2"],
    )

    handoff = build_bonobo_handoff(
        "Run BONOBO then pass the selected sample result to PANDA",
        decision,
        registry,
    )

    assert handoff is not None
    assert handoff.status == "validated"
    assert handoff.consumer_action == "run_panda"
    assert handoff.consumer_input_field == "coexpression_file"
    assert handoff.required_prior_inputs == ["motif_file", "ppi_file"]
    assert handoff.sample_ids == ["s2"]


def test_bonobo_handoff_output_verification_preserves_planned_artifacts_and_identity():
    decision = TaskDecision(
        action="run_bonobo",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run BONOBO then PANDA.",
    )
    handoff = WorkflowHandoff(
        producer_action="run_bonobo",
        producer_workflow="BONOBO",
        source_artifact_type="coexpression_network",
        source_granularity="sample_specific",
        produced_artifacts=["coexpression_network"],
        source_artifact_paths=["/tmp/bonobo/bonobo-s2.h5"],
        artifact_paths={"coexpression_network": ["/tmp/bonobo/bonobo-s2.h5"]},
        sample_ids=["s2"],
        gene_ids=["g1", "g2"],
        consumer_action="run_panda",
        consumer_workflow="PANDA",
        consumer_input_field="coexpression_file",
        status="validated",
        reason="registered sample-specific test consumer",
    )
    plan = WorkflowPlan(
        workflow="BONOBO -> PANDA",
        objective=decision.reason,
        decision=decision.model_dump(),
        workflow_handoff=handoff,
        steps=[WorkflowStep(action="run_bonobo", purpose="test")],
        status="ready",
    )
    matching = ToolExecutionResult(
        action="run_bonobo",
        status="success",
        summary="verified",
        artifacts=["/tmp/bonobo/bonobo-s2.h5"],
        metrics={"bonobo_samples": 1, "bonobo_genes": 2},
    )
    assert evaluate_step_result(plan, 0, matching).status == "completed"

    missing = matching.model_copy(
        update={"artifacts": [], "metrics": {"bonobo_samples": 1, "bonobo_genes": 2}}
    )
    evaluation = evaluate_step_result(plan, 0, missing)
    assert evaluation.status == "failed"
    assert "handoff contract" in evaluation.reason


def test_bonobo_binds_natural_language_sample_selection(tmp_path):
    expression = tmp_path / "expression-20.tsv"
    samples = [f"S{index:02d}" for index in range(1, 21)]
    rows = ["gene_id\t" + "\t".join(samples)]
    rows.extend(
        f"g{gene}\t" + "\t".join(str(gene + sample) for sample in range(1, 21))
        for gene in range(1, 4)
    )
    expression.write_text("\n".join(rows) + "\n", encoding="utf-8")
    output = tmp_path / "bonobo-output"
    plan = build_workflow_plan(
        _decision(expression, output),
        f"我想從一份包含 20 個樣本的 expression matrix 中，只分析 S01 和 S07，"
        f"產生兩張 sample-specific gene-gene co-expression matrix，並且在 sparsify 後輸出 p-value matrix。 "
        f"expression_file={expression} output_dir={output} sparsify=true save_pvals=true "
        "log_transformed=true centered=true",
    )

    assert plan.status == "ready"
    assert plan.decision["sample_names"] == ["S01", "S07"]
    assert plan.decision["sparsify"] is True
    assert plan.decision["save_pvals"] is True
