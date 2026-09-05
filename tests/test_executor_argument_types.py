"""Optional executor inputs must respect their declared type, for every workflow.

Text adapters use an empty string to mean "omitted", but a numeric or boolean
optional is typed `X | None` in both the decision contract and the tool schema.
Coercing those to "" makes a valid plan fail its own tool validation.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, executor_arguments  # noqa: E402


RUNNABLE = sorted(action for action, item in ACTION_DEFINITIONS.items() if item.run)


def unspecified_decision(action):
    return TaskDecision(
        action=action, in_scope=True, should_execute=True, confidence=1.0,
        intent_type="run_analysis", reason="Typed argument contract check.",
    )


def is_text(field_name):
    annotation = TaskDecision.model_fields[field_name].annotation
    return "str" in str(annotation)


@pytest.mark.parametrize("action", RUNNABLE, ids=RUNNABLE)
def test_no_optional_input_is_coerced_across_its_declared_type(action):
    arguments = executor_arguments(action, unspecified_decision(action))

    for field_name, value in arguments.items():
        if value == "" and not is_text(field_name):
            pytest.fail(f"{action}.{field_name}: {TaskDecision.model_fields[field_name].annotation} received ''")


@pytest.mark.parametrize("action", RUNNABLE, ids=RUNNABLE)
def test_every_executor_argument_satisfies_its_own_tool_schema(action):
    """The registry payload must validate against the real tool's args schema."""
    from netzoo_agent_core import execution

    tool = getattr(execution, action, None)
    if tool is None or not hasattr(tool, "args_schema"):
        pytest.fail(f"{action} has no runnable tool exposed for argument validation")
    arguments = executor_arguments(action, unspecified_decision(action))
    fields = tool.args_schema.model_fields
    # Required paths come from input confirmation; this contract owns the optionals.
    payload = {name: "placeholder" for name, field in fields.items() if field.is_required()}
    optional = ACTION_DEFINITIONS[action].optional_inputs
    payload.update({
        name: value for name, value in arguments.items()
        if name in optional and name in fields and not fields[name].is_required()
    })

    tool.args_schema.model_validate(payload)
