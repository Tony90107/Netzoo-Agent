"""The first pass is judged against facts it was never shown.

Across 122 live trials with two semantic calls, the first pass validated once.
Its dominant failure is `missing_current_input` -- 132 occurrences in 118
rejected first passes -- which is exactly what the request witnesses locate in
the user's own text. Those witnesses already reach the reviewer inside
`request_facts`; the interpreter received only the prompt and the request.

This hands the first call the same observations, with their temporal role, so
that a historical or negated mention stays visibly non-current. It is not an
instruction and it fills nothing: the model still chooses every field, and the
same validator still judges the result.
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.llm import (  # noqa: E402
    build_semantic_interpreter_messages,
    build_semantic_interpreter_prompt,
)

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from test_routing_evaluation import FixtureProvider, run  # noqa: E402


PROMPT = build_semantic_interpreter_prompt()


def rendered(task):
    return "\n".join(str(m.content) for m in build_semantic_interpreter_messages(PROMPT, task))


def facts(task):
    text = rendered(task)
    block = text.split('"request_facts":', 1)[1]
    return json.loads("{" + '"request_facts":' + block.rsplit("}", 1)[0] + "}")["request_facts"]


def test_the_first_call_carries_the_spans_the_validator_will_use():
    task = next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1").prompt

    entries = facts(task)

    assert {"mutation_matrix"} == {item["artifact"] for item in entries}
    assert all(item["text_span"] in task for item in entries)
    assert {"current"} == {item["status"] for item in entries}


def test_a_historical_mention_keeps_its_role():
    """Handing over the spans must not read as handing over a list of inputs."""
    entries = facts("我之前用表現量矩陣跑過分析。現在我有體細胞突變矩陣。")

    by_artifact = {item["artifact"]: item["status"] for item in entries}
    assert by_artifact["expression_matrix"] == "historical"
    assert by_artifact["mutation_matrix"] == "current"


def test_a_negated_mention_keeps_its_role():
    entries = facts("These are expression measurements, not somatic mutations.")

    assert any(item["artifact"] == "mutation_matrix" and item["status"] == "negated"
               for item in entries)


def test_a_request_with_no_recognised_data_sends_no_facts():
    assert "request_facts" not in rendered("Which tool builds a regulatory network?")


def test_the_block_states_observations_rather_than_a_field_to_set():
    task = next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1").prompt

    text = rendered(task).casefold()

    assert "not instructions" in text
    assert "set input_artifacts" not in text


@pytest.mark.parametrize("case_id", ["original-q1", "original-q2", "original-q3"])
def test_production_routing_sends_them_on_the_first_call(case_id):
    case = next(item for item in load_scenarios(DEFAULT_SCENARIOS) if item.id == case_id)
    provider = FixtureProvider()

    run(provider, case)
    first_call = "\n".join(str(m.content) for m in provider.calls[0][1])

    assert '"request_facts"' in first_call
    assert '"mutation_matrix"' in first_call
