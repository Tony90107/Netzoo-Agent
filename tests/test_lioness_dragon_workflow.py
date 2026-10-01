"""LIONESS-DRAGON: one two-layer partial-correlation network per sample (Log 290)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.data import lioness_dragon as module  # noqa: E402
from netzoo_agent_core.data.dragon import validate_dragon_output  # noqa: E402
from netzoo_agent_core.data.lioness_dragon import (  # noqa: E402
    lioness_dragon_networks,
    lioness_dragon_size,
    validate_lioness_dragon_output,
    write_lioness_dragon_table,
)
from netzoo_agent_core.execution_lioness_dragon import run_lioness_dragon  # noqa: E402
from netzoo_agent_core.routing.dispatch import execute_selected_tool  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, EXTERNAL_REFERENCES, OUTPUT_CAPABILITIES  # noqa: E402

EXECUTOR = "netzoo_agent_core.execution_lioness_dragon"


def _layer(path: Path, ids=("s1", "s2", "s3", "s4"), features=("a", "b")) -> Path:
    rows = [[(index + 1) * (offset + 2) + (index * offset) % 3 for offset in range(len(features))]
            for index in range(len(ids))]
    frame = pd.DataFrame(rows, columns=features)
    frame.insert(0, "sample_id", ids)
    frame.to_csv(path, sep="\t", index=False)
    return path


def _correlation(x1, x2, lambdas):
    """A deterministic stand-in for get_partial_correlation_dragon: the feature correlation."""
    return np.corrcoef(np.hstack([x1, x2]).T)


class FakeDragon:
    calls: list[int] = []

    @staticmethod
    def estimate_penalty_parameters_dragon(x1, x2):
        FakeDragon.calls.append(x1.shape[0])
        return [0.2, 0.3], None

    @staticmethod
    def get_partial_correlation_dragon(x1, x2, lambdas):
        FakeDragon.calls.append(x1.shape[0])
        return _correlation(x1, x2, lambdas)


def _decision(first: Path, second: Path, tmp_path: Path, **kwargs) -> TaskDecision:
    return TaskDecision(
        action="run_lioness_dragon", in_scope=True, should_execute=True, confidence=1.0,
        reason="Run LIONESS-DRAGON.", omics_layer_1=str(first), omics_layer_2=str(second),
        output_file=str(tmp_path / "dragon-aggregate.tsv"),
        lioness_output=str(tmp_path / "lioness-dragon.tsv"), **kwargs,
    )


def test_it_is_registered_as_sample_specific_dragon_only():
    definition = ACTION_DEFINITIONS["run_lioness_dragon"]
    capability = OUTPUT_CAPABILITIES["run_lioness_dragon"]
    assert definition.required_inputs == ("omics_layer_1", "omics_layer_2", "output_file", "lioness_output")
    assert definition.validation_steps == ("inspect_dragon_inputs",)
    assert capability.artifact_type == OUTPUT_CAPABILITIES["run_dragon"].artifact_type == "multi_omic_network"
    # Sample-specific only, so an aggregate request stays DRAGON's with no new tie.
    assert capability.granularities == frozenset({"sample_specific"})
    assert OUTPUT_CAPABILITIES["run_dragon"].granularities == frozenset({"aggregate"})
    assert capability.guidance_predecessors == ("run_dragon",)
    assert capability.entity_types == OUTPUT_CAPABILITIES["run_dragon"].entity_types
    assert {"sample_specific", "leave_one_out_network_inference"} <= capability.selection_tags


def test_each_network_follows_netzoopys_lioness_formula():
    rng = np.random.default_rng(7)
    x1, x2 = rng.normal(size=(6, 3)), rng.normal(size=(6, 2))
    full, networks = lioness_dragon_networks(_correlation, x1, x2, [0.1, 0.1])
    seen = dict(networks)
    assert sorted(seen) == list(range(6))
    for k, network in seen.items():
        keep = np.arange(6) != k
        without = _correlation(x1[keep], x2[keep], None)
        # netZooPy lioness_for_dragon.py: n * (N_all - N_without_k) + N_without_k
        assert np.allclose(network, 6 * (full - without) + without)


def test_the_per_sample_table_round_trips_and_lines_up_with_the_aggregate(tmp_path):
    nodes = ["layer1::a", "layer1::b", "layer2::m"]
    networks = iter([(0, np.full((3, 3), 0.1)), (1, np.full((3, 3), 0.2)), (2, np.full((3, 3), 0.3))])
    path = write_lioness_dragon_table(str(tmp_path / "per-sample.tsv"), ["s1", "s2", "s3"], nodes, networks)
    frame = pd.read_csv(path, sep="\t")
    assert list(frame.columns) == ["source", "target", "s1", "s2", "s3"]
    assert list(zip(frame["source"], frame["target"])) == [
        ("layer1::a", "layer1::b"), ("layer1::a", "layer2::m"), ("layer1::b", "layer2::m")]
    ok, errors, metrics = validate_lioness_dragon_output(path, expected_samples=3)
    assert ok, errors
    assert metrics == {"samples": 3, "edges": 3}
    assert lioness_dragon_size(3, 3) == 9


def test_a_broken_table_is_refused(tmp_path):
    bad = tmp_path / "bad.tsv"
    bad.write_text("source\ttarget\ts1\nlayer1::a\tlayer1::b\tinf\n", encoding="utf-8")
    ok, errors, _ = validate_lioness_dragon_output(str(bad))
    assert not ok and any("finite" in error for error in errors)
    gap = tmp_path / "gap.tsv"
    gap.write_text("source\ttarget\ts1\nlayer1::a\tlayer1::b\t0.1\nlayer1::a\tlayer2::m\t0.2\n", encoding="utf-8")
    ok, errors, _ = validate_lioness_dragon_output(str(gap))
    assert not ok and any("every feature pair" in error for error in errors)
    ok, errors, _ = validate_lioness_dragon_output(str(tmp_path / "missing.tsv"))
    assert not ok


def test_a_dry_run_previews_and_writes_nothing(tmp_path):
    first, second = _layer(tmp_path / "l1.tsv"), _layer(tmp_path / "l2.tsv", features=("m",))
    with patch(f"{EXECUTOR}.settings.EXECUTE_TOOLS", False):
        report = run_lioness_dragon.invoke({
            "omics_layer_1": str(first), "omics_layer_2": str(second),
            "output_file": str(tmp_path / "agg.tsv"), "lioness_output": str(tmp_path / "ls.tsv")})
    assert "LIONESS-DRAGON Python API preview" in report and "12 per-sample values" in report
    assert "(3 feature pairs x 4 samples)" in report
    assert not (tmp_path / "agg.tsv").exists() and not (tmp_path / "ls.tsv").exists()


def test_guards_refuse_before_any_api_call(tmp_path):
    first, second = _layer(tmp_path / "l1.tsv"), _layer(tmp_path / "l2.tsv", features=("m",))
    base = {"omics_layer_1": str(first), "omics_layer_2": str(second),
            "output_file": str(tmp_path / "agg.tsv"), "lioness_output": str(tmp_path / "ls.tsv")}
    assert "supplied together" in run_lioness_dragon.invoke({**base, "lambda1": 0.2})
    assert "overwrite an omics input" in run_lioness_dragon.invoke({**base, "lioness_output": str(first)})
    assert "must be different files" in run_lioness_dragon.invoke({**base, "lioness_output": base["output_file"]})
    with patch(f"{EXECUTOR}.LIONESS_DRAGON_MAX_VALUES", 5):
        refused = run_lioness_dragon.invoke(base)
    assert "12 per-sample values" in refused and "run DRAGON for one aggregate network" in refused
    mismatch = _layer(tmp_path / "other.tsv", ids=("s1", "s2", "s3", "x"), features=("m",))
    assert "input validation failed" in run_lioness_dragon.invoke({**base, "omics_layer_2": str(mismatch)})


def test_execution_writes_both_outputs_and_the_run_validates(tmp_path):
    first = _layer(tmp_path / "l1.tsv", ids=("s1", "s2", "s3", "s4", "s5"))
    second = _layer(tmp_path / "l2.tsv", ids=("s5", "s3", "s1", "s2", "s4"), features=("m", "n"))
    FakeDragon.calls = []
    decision = _decision(first, second, tmp_path)
    with patch(f"{EXECUTOR}.settings.EXECUTE_TOOLS", True), patch(f"{EXECUTOR}._load_dragon_api", return_value=FakeDragon):
        result = execute_selected_tool(decision)
    assert "LIONESS-DRAGON API execution completed" in result, result
    # The penalty is estimated once on all 5 samples; then one fit on all and one per left-out sample.
    assert FakeDragon.calls == [5, 5, 4, 4, 4, 4, 4]
    assert validate_dragon_output(decision.output_file, "matrix")[0]
    ok, errors, metrics = validate_lioness_dragon_output(decision.lioness_output, expected_samples=5)
    assert ok, errors
    assert metrics["edges"] == 6  # 4 features
    table = pd.read_csv(decision.lioness_output, sep="\t")
    assert list(table.columns[2:]) == ["s1", "s2", "s3", "s4", "s5"]  # layer 1's sample order


def test_planning_names_the_outputs_after_the_method_and_keeps_two_layers(tmp_path):
    plan = build_workflow_plan(
        TaskDecision(action="run_lioness_dragon", in_scope=True, should_execute=True,
                     confidence=1.0, reason="Run LIONESS-DRAGON."),
        "Run LIONESS-DRAGON.",
    )
    assert plan.status == "needs_input"
    assert {"omics_layer_1", "omics_layer_2"} <= set(plan.missing_inputs)
    defaults = {item.field: item.value for item in plan.evidence if item.status == "defaulted"}
    assert Path(defaults["output_file"]).name == "dragon-aggregate.tsv"
    assert Path(defaults["lioness_output"]).name == "lioness-dragon.tsv"
    first, second = _layer(tmp_path / "l1.tsv"), _layer(tmp_path / "l2.tsv", features=("m",))
    three = build_workflow_plan(
        _decision(first, second, tmp_path),
        f"Run LIONESS-DRAGON with omics_layer_1={first} omics_layer_2={second}; I also have three omics layers.",
    )
    assert "LIONESS-DRAGON accepts exactly two omics layers" in (three.question or "")


def test_a_dragon_result_is_no_longer_named_panda_by_default():
    plan = build_workflow_plan(
        TaskDecision(action="run_dragon", in_scope=True, should_execute=True, confidence=1.0, reason="Run DRAGON."),
        "Run DRAGON.",
    )
    defaults = {item.field: item.value for item in plan.evidence if item.status == "defaulted"}
    assert Path(defaults["output_file"]).name == "dragon.tsv"


@pytest.mark.parametrize("tags,listed", [({"relaxed_graph_matching", "sample_specific"}, True), ({"bayesian"}, False)])
def test_lioness_otter_is_named_only_for_an_otter_style_gap(tags, listed):
    reference = next(ref for ref in EXTERNAL_REFERENCES if ref.name == "LIONESS-OTTER")
    assert reference.artifact_types == frozenset({"regulatory_network"})
    assert "not registered in this agent" in reference.availability
    assert bool(reference.selection_tags & tags) is listed
    assert "run_lioness_otter" not in ACTION_DEFINITIONS


def test_a_per_sample_request_is_answered_with_lioness_dragon_directly():
    from netzoo_agent_core.contracts import RequestedOutcome
    from netzoo_agent_core.interpretation.concept_answers import render_workflow_composition_guidance
    from netzoo_agent_core.policy import ProjectPolicyLoader

    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="Per-sample multi-omic guidance.", capability_match_status="exact",
        matched_actions=["run_lioness_dragon"], recommended_actions=["run_dragon", "run_lioness_dragon"],
        requested_outcome=RequestedOutcome(operation="infer", artifact_type="multi_omic_network",
                                           granularity="sample_specific"),
    )
    answer = render_workflow_composition_guidance(decision, policy, None)
    # The same direct card LIONESS-PANDA gets, with readable input labels (live
    # trials in Log 291 showed the generic two-workflow card and raw field names).
    assert "For the sample-specific output you described, use **LIONESS-DRAGON**." in answer
    assert "`omics_layer_1`: Omics layer 1 (samples x features)" in answer
    assert "`omics_layer_1`: omics_layer_1" not in answer
    assert "You do not need to run **DRAGON** separately" in answer
    unstated = decision.model_copy(update={"requested_outcome": decision.requested_outcome.model_copy(
        update={"granularity": "unknown"})})
    assert "I matched your goal to an aggregate and a sample-specific workflow." in (
        render_workflow_composition_guidance(unstated, policy, None) or "")


def test_module_constants_are_the_declared_ones():
    assert module.LIONESS_DRAGON_MIN_SAMPLES == 3
    assert module.LIONESS_DRAGON_MAX_VALUES == 20_000_000
