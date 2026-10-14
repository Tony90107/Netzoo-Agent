"""M1 step 1 (2026-10-14): one record of each workflow's method, settings and data limits, read from their sources.

`workflow_conditions` holds no value of its own. Each test here changes a source -- a registry control, a runtime
constraint, a size cap -- and sees the record follow, or finds the threshold the enforcing check really applies and
compares it with the record, so the record and the executor cannot drift apart.
"""

from __future__ import annotations

import inspect
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import workflow_registry  # noqa: E402
from netzoo_agent_core import execution, runtime_constraints  # noqa: E402
from netzoo_agent_core.data import (  # noqa: E402
    bonobo, bundles, cobra, dragon, giraffe, inspection, lioness_dragon, otter, preflight,
)
from netzoo_agent_core.execution_lioness_dragon import run_lioness_dragon  # noqa: E402
from netzoo_agent_core.runtime_constraints import RuntimeControlConstraint  # noqa: E402
from netzoo_agent_core.workflow_conditions import (  # noqa: E402
    LIONESS_FAMILY, UNREGISTERED, StatedSetting, all_conditions, conditions_for, data_issue, method_names,
    named_workflows, setting_issue, setting_names, stated_numbers,
)


def test_every_registered_run_workflow_has_one_record():
    found = all_conditions()
    expected = {workflow_registry.ACTION_DEFINITIONS[action].workflow for action in workflow_registry.RUN_ACTIONS}
    assert set(found) == expected and len(found) == 13
    assert {item.action for item in found.values()} == set(workflow_registry.RUN_ACTIONS)
    assert conditions_for("run_dragon") is not None and conditions_for("run_dragon").workflow == "DRAGON"


def test_settings_are_the_registry_controls():
    for workflow, item in all_conditions().items():
        definition = workflow_registry.ACTION_DEFINITIONS[item.action]
        assert list(item.settings) == [control.name for control in definition.controls], workflow
        for control in definition.controls:
            limit = item.settings[control.name]
            assert (limit.control_type, limit.minimum, limit.maximum, limit.allowed_values) == (
                control.control_type, control.minimum, control.maximum, tuple(control.allowed_values))
            assert limit.wired is (control.executor_argument in definition.executor_fields)
    assert not conditions_for("GIRAFFE").settings and not conditions_for("PUMA").settings
    assert "OTTER.lam" in setting_names() and "DRAGON.lambda1" in setting_names()


def test_a_changed_registry_control_is_followed(monkeypatch):
    definitions = dict(workflow_registry.ACTION_DEFINITIONS)
    dragon_definition = definitions["run_dragon"]
    narrowed = tuple(replace(control, maximum=0.5) if control.name == "lambda1" else control
                     for control in dragon_definition.controls)
    unwired = replace(dragon_definition, controls=narrowed,
                      executor_fields=tuple(name for name in dragon_definition.executor_fields if name != "lambda2"))
    definitions["run_dragon"] = unwired
    monkeypatch.setattr("netzoo_agent_core.workflow_conditions.ACTION_DEFINITIONS", definitions)
    record = conditions_for("DRAGON")
    assert record.settings["lambda1"].maximum == 0.5
    assert record.settings["lambda2"].wired is False
    assert "has no setting" in setting_issue(record, StatedSetting("DRAGON.lambda2", "lambda2 of 0.4", "0.4"))


def test_runtime_constraints_are_followed(monkeypatch):
    otter_record = conditions_for("OTTER")
    assert otter_record.settings["computing"].unavailable_values == frozenset({"gpu"})
    assert "not enabled" in setting_issue(otter_record, StatedSetting("OTTER.computing", "on our GPU", "GPU"))
    assert setting_issue(otter_record, StatedSetting("OTTER.computing", "on the CPU", "CPU")) is None
    constraints = {**runtime_constraints._CONSTRAINTS, "run_otter": {
        "precision": RuntimeControlConstraint(frozenset({"single"}), "single precision is off here.")}}
    monkeypatch.setattr(runtime_constraints, "_CONSTRAINTS", constraints)
    changed = conditions_for("OTTER")
    assert changed.settings["computing"].unavailable_values == frozenset()
    assert setting_issue(changed, StatedSetting("OTTER.precision", "single precision", "single")) == (
        "single precision is off here")


def _expression(path: Path, samples: int, genes: int = 6) -> str:
    """Gene-by-sample, labelled, varied, log-scale values."""
    frame = pd.DataFrame({f"S{j + 1}": [((i * 7 + j * 3) % 11) / 3 + 1 + j * 0.1 for i in range(genes)]
                          for j in range(samples)})
    frame.insert(0, "gene", [f"G{i + 1}" for i in range(genes)])
    frame.to_csv(path, sep="\t", index=False)
    return str(path)


def _layer(path: Path, samples: int, features: int = 2) -> str:
    """Sample-by-feature, as DRAGON reads it."""
    frame = pd.DataFrame({f"f{k + 1}": [(j + 1) * (k + 2) + (j * k) % 3 for j in range(samples)]
                          for k in range(features)})
    frame.insert(0, "sample_id", [f"s{j + 1}" for j in range(samples)])
    frame.to_csv(path, sep="\t", index=False)
    return str(path)


def _enforced(check, lowest: int = 1, highest: int = 6) -> int:
    """The smallest sample count the check accepts."""
    return next(n for n in range(lowest, highest) if check(n))


def test_lioness_minimum_is_what_preflight_enforces(tmp_path):
    accepted = _enforced(lambda n: not preflight._validate_lioness_sample_count(
        _expression(tmp_path / f"lioness{n}.tsv", n)))
    for workflow in ("LIONESS-PANDA", "LIONESS-PUMA", "LIONESS-COEXPRESSION"):
        assert conditions_for(workflow).min_samples == accepted == inspection.LIONESS_MIN_SAMPLES
    # The other three sites read the same constant; none keeps its own literal.
    for module in (preflight, bundles, execution):
        assert "sample_count < 3" not in inspect.getsource(module)


def test_bonobo_minimum_is_what_its_loader_enforces(tmp_path):
    def accepts(n):
        try:
            bonobo.load_bonobo_inputs(_expression(tmp_path / f"bonobo{n}.tsv", n), log_transformed=True,
                                      centered=True)
        except ValueError as error:
            return "at least three total samples" not in str(error)
        return True
    assert conditions_for("BONOBO").min_samples == _enforced(accepts, lowest=2) == bonobo.BONOBO_MIN_SAMPLES


def test_dragon_minimum_is_what_its_reader_enforces(tmp_path):
    def accepts(n):
        _, errors = dragon._read_layer(_layer(tmp_path / f"layer{n}.tsv", n), "omics_layer_1")
        return not any("at least three samples" in error for error in errors)
    assert conditions_for("DRAGON").min_samples == _enforced(accepts) == dragon.DRAGON_MIN_SAMPLES
    assert conditions_for("LIONESS-DRAGON").min_samples == max(
        dragon.DRAGON_MIN_SAMPLES, lioness_dragon.LIONESS_DRAGON_MIN_SAMPLES)
    assert conditions_for("DRAGON").omics_layers == conditions_for("LIONESS-DRAGON").omics_layers == 2


def test_cobra_giraffe_and_otter_minimums_are_what_their_readers_enforce(tmp_path):
    def cobra_accepts(n):
        design = pd.DataFrame({"sample": [f"S{j + 1}" for j in range(n)], "batch": [j % 2 for j in range(n)]})
        design.to_csv(tmp_path / f"design{n}.tsv", sep="\t", index=False)
        try:
            cobra.load_cobra_inputs(_expression(tmp_path / f"cobra{n}.tsv", n), str(tmp_path / f"design{n}.tsv"))
        except ValueError as error:
            return "at least two samples" not in str(error)
        return True

    def giraffe_accepts(n):
        try:
            giraffe._read_expression(_expression(tmp_path / f"giraffe{n}.tsv", n))
        except giraffe.GiraffeInputError:  # the file is otherwise valid; both sample checks read the constant
            return False
        return True

    def otter_accepts(n):
        try:
            otter._read_expression(_expression(tmp_path / f"otter{n}.tsv", n))
        except ValueError as error:
            return "at least two sample columns" not in str(error)
        return True

    assert conditions_for("COBRA").min_samples == _enforced(cobra_accepts) == cobra.COBRA_MIN_SAMPLES
    assert conditions_for("GIRAFFE").min_samples == _enforced(giraffe_accepts) == giraffe.GIRAFFE_MIN_SAMPLES
    assert conditions_for("OTTER").min_samples == _enforced(otter_accepts) == otter.OTTER_MIN_EXPRESSION_SAMPLES
    for workflow in ("PANDA", "PUMA", "CONDOR", "SAMBAR"):
        assert conditions_for(workflow).min_samples is None


def test_lioness_dragon_cap_is_the_executors(tmp_path):
    from netzoo_agent_core import execution_lioness_dragon

    record = conditions_for("LIONESS-DRAGON")
    assert record.max_values == lioness_dragon.LIONESS_DRAGON_MAX_VALUES
    assert execution_lioness_dragon.LIONESS_DRAGON_MAX_VALUES == lioness_dragon.LIONESS_DRAGON_MAX_VALUES
    assert record.size is lioness_dragon.lioness_dragon_size is execution_lioness_dragon.lioness_dragon_size
    assert all(item.max_values is None for name, item in all_conditions().items() if name != "LIONESS-DRAGON")
    # 3 samples x (2 + 2) features = 18 values: refused by the executor and by the record under the same cap.
    base = {"omics_layer_1": _layer(tmp_path / "one.tsv", 3), "omics_layer_2": _layer(tmp_path / "two.tsv", 3),
            "output_file": str(tmp_path / "agg.tsv"), "lioness_output": str(tmp_path / "per.tsv")}
    with patch.object(execution_lioness_dragon, "LIONESS_DRAGON_MAX_VALUES", 10), \
            patch.object(lioness_dragon, "LIONESS_DRAGON_MAX_VALUES", 10):
        assert "18 per-sample values" in run_lioness_dragon.invoke(base)
        assert "give 18" in data_issue(conditions_for("LIONESS-DRAGON"), 3, 4)
    assert data_issue(conditions_for("LIONESS-DRAGON"), 3, 4) is None


def test_named_methods_stand_for_registered_workflows_only():
    assert method_names()[-1] == LIONESS_FAMILY and "TIGER" not in method_names()
    assert named_workflows("PANDA") == {"PANDA", "LIONESS-PANDA"}
    assert named_workflows("DRAGON") == {"DRAGON", "LIONESS-DRAGON"}
    assert named_workflows("OTTER") == {"OTTER"}  # no LIONESS-OTTER is registered
    assert named_workflows("LIONESS-PUMA") == {"LIONESS-PUMA"}
    assert named_workflows(LIONESS_FAMILY) == {
        "LIONESS-PANDA", "LIONESS-PUMA", "LIONESS-COEXPRESSION", "LIONESS-DRAGON"}
    assert named_workflows("TIGER") == named_workflows(UNREGISTERED) == frozenset()


@pytest.mark.parametrize(("text", "numbers"), [
    ("all 20,000 genes and 800 proteins for our 300 patients", [20000, 800, 300]),
    ("exactly two RNA-seq samples", [2]),
    ("lambda1 0.3 and lambda2 0.4", [0.3, 0.4]),  # a name's own digit is not a value
    ("20k genes", [20000]),
    ("a single sample", [1]),
    ("no number here", []),
])
def test_stated_numbers(text, numbers):
    assert stated_numbers(text) == numbers


def test_setting_issues():
    giraffe_record, otter_record, dragon_record = (conditions_for(name) for name in ("GIRAFFE", "OTTER", "DRAGON"))
    assert "passes no settings" in setting_issue(
        giraffe_record, StatedSetting("OTTER.lam", "its regularisation lambda", "0.5"))
    assert "has no setting" in setting_issue(
        otter_record, StatedSetting(UNREGISTERED, "an L1 sparsity penalty of 0.1", "0.1"))
    assert "between 0 and 1" in setting_issue(dragon_record, StatedSetting("DRAGON.lambda1", "lambda1", "1.5"))
    assert setting_issue(dragon_record, StatedSetting("DRAGON.lambda1", "fixed lambdas", "0.2")) is None
    # Another family member's control of the same name is the workflow's own.
    assert setting_issue(conditions_for("LIONESS-DRAGON"), StatedSetting("DRAGON.lambda2", "lambda2", "0.4")) is None
    assert setting_issue(dragon_record, StatedSetting("DRAGON.output_format", "as an edge list", "an edge list")) is None
    assert "whole number" in setting_issue(conditions_for("SAMBAR"), StatedSetting("SAMBAR.kmin", "kmin", "2.5"))
    # A value the words do not state is never judged.
    assert setting_issue(dragon_record, StatedSetting("DRAGON.lambda1", "a small lambda", "small")) is None


def test_data_issues():
    assert "at least 3 samples" in data_issue(conditions_for("BONOBO"), 2, None)
    assert "at least 3 samples" in data_issue(conditions_for("LIONESS-COEXPRESSION"), 2, None)
    assert data_issue(conditions_for("BONOBO"), 9, None) is None
    assert data_issue(conditions_for("PANDA"), 1, None) is None
    assert "64,892,880,000" in data_issue(conditions_for("LIONESS-DRAGON"), 300, 20_800)
    assert data_issue(conditions_for("LIONESS-DRAGON"), 30, 900) is None  # P19: 12,136,500 values
    assert data_issue(conditions_for("LIONESS-DRAGON"), None, 20_800) is None  # samples not stated
    assert data_issue(conditions_for("DRAGON"), 300, 20_800) is None  # no cap on the aggregate network
