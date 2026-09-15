from __future__ import annotations

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.policy import (  # noqa: E402
    ConditionalOutputSpec,
    WorkflowControlSpec,
)
from netzoo_agent_core.policy import ProjectPolicyError, ProjectPolicyLoader  # noqa: E402


def _policy():
    return ProjectPolicyLoader().load()


def test_project_policy_round_trip_contains_registry_controls_and_conditions():
    policy = _policy()
    bonobo = policy.workflows["run_bonobo"]
    assert {item.name for item in bonobo.controls} >= {
        "sample_names",
        "sparsify",
        "save_pvals",
        "bonobo_confidence",
    }
    assert any(
        rule.when == {"sparsify": True, "save_pvals": True}
        for rule in bonobo.output_capability.conditional_outputs
    )
    assert all(
        spec.input_validator == action
        for action, spec in policy.workflows.items()
    )


def test_input_validator_cannot_drift_from_the_code_registry():
    policy = _policy()
    panda = policy.workflows["run_panda"]
    with pytest.raises(ProjectPolicyError, match="input_validator conflict"):
        ProjectPolicyLoader._validate_against_code(
            {
                **policy.workflows,
                "run_panda": panda.model_copy(
                    update={"input_validator": "run_cobra"}
                ),
            }
        )


def test_unknown_control_type_is_rejected_by_the_typed_policy_schema():
    with pytest.raises(ValidationError):
        WorkflowControlSpec.model_validate(
            {
                "name": "bad",
                "type": "not-a-control-type",
                "executor_argument": "bad",
            }
        )


def test_unknown_executor_argument_is_rejected_against_the_code_registry():
    policy = _policy()
    bonobo = policy.workflows["run_bonobo"]
    controls = [
        item.model_copy(
            update={"executor_argument": "missing_executor_argument"}
        )
        if item.name == "sparsify"
        else item
        for item in bonobo.controls
    ]
    with pytest.raises(ProjectPolicyError, match="controls conflict|unknown executor"):
        ProjectPolicyLoader._validate_against_code(
            {**policy.workflows, "run_bonobo": bonobo.model_copy(update={"controls": controls})}
        )


def test_required_optional_collision_is_rejected():
    policy = _policy()
    bonobo = policy.workflows["run_bonobo"]
    with pytest.raises(ProjectPolicyError, match="invalid optional inputs"):
        ProjectPolicyLoader._validate_against_code(
            {
                **policy.workflows,
                "run_bonobo": bonobo.model_copy(
                    update={
                        "optional_inputs": [
                            *bonobo.optional_inputs,
                            "expression_file",
                        ]
                    }
                ),
            }
        )


def test_conditional_output_cannot_reference_an_unregistered_control():
    policy = _policy()
    bonobo = policy.workflows["run_bonobo"]
    invalid_rule = ConditionalOutputSpec(
        when={"unregistered_control": True},
        produced_artifacts=["coexpression_network"],
        semantics="invalid test rule",
    )
    with pytest.raises(ProjectPolicyError, match="unknown controls"):
        ProjectPolicyLoader._validate_against_code(
            {
                **policy.workflows,
                "run_bonobo": bonobo.model_copy(
                    update={
                        "output_capability": bonobo.output_capability.model_copy(
                            update={
                                "conditional_outputs":[invalid_rule]
                            }
                        )
                    }
                ),
            }
        )
