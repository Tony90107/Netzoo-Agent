"""granularity-unknown-2026-10-28: on the last attempt, a reading whose only issue is a contradicted granularity is
kept with granularity `unknown` (j5 W01); any other issue keeps the failure."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph import semantic_attempts  # noqa: E402
from netzoo_agent_core.graph.semantic_attempts import granularity_left_unknown  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/granularity_unknown/j5_w01.json").read_text())


def _w01():
    interpretation = SemanticInterpretation.model_validate(FIXTURE["interpretation"])
    return interpretation, validate_outcome_hypotheses(FIXTURE["task"], interpretation.outcome_hypotheses,
                                                       interpretation.request_mode)


def test_the_recorded_w01_reading_is_kept_with_an_unknown_granularity():
    interpretation, validation = _w01()
    assert list(validation.issues) == ["hypothesis[0].granularity_contradicts_request:aggregate"]
    after, revalidated, changed = granularity_left_unknown(FIXTURE["task"], interpretation, validation)
    assert revalidated.valid and changed == [0]
    assert after.outcome_hypotheses[0].outcome.granularity == "unknown"
    assert after.outcome_hypotheses[0].outcome.artifact_type == interpretation.outcome_hypotheses[0].outcome.artifact_type


def test_any_other_issue_keeps_the_failure():
    interpretation, _ = _w01()
    mixed = SimpleNamespace(valid=False, issues=["hypothesis[0].granularity_contradicts_request:aggregate",
                                                 "hypothesis[0].ungrounded_evidence:artifact_type=x"])
    assert granularity_left_unknown(FIXTURE["task"], interpretation, mixed) == (interpretation, mixed, [])
    other = SimpleNamespace(valid=False, issues=["hypothesis[0].granularity_contradicts_request:aggregate",
                                                 "hypothesis[1].ungrounded_evidence:artifact_type=x"])
    assert granularity_left_unknown(FIXTURE["task"], interpretation, other)[2] == []
    unscoped = SimpleNamespace(valid=False, issues=["granularity_contradicts_request:aggregate"])
    assert granularity_left_unknown(FIXTURE["task"], interpretation, unscoped)[2] == []


def test_only_the_last_attempt_keeps_the_reading():
    """An earlier attempt is retried with the issue, as before: the call sits under the last-attempt branch."""
    tree = ast.parse(Path(semantic_attempts.__file__).read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.If)
             and "MAX_SEMANTIC_ATTEMPTS" in ast.unparse(node.test)
             and any(isinstance(inner, ast.Call) and ast.unparse(inner.func) == "granularity_left_unknown"
                     for inner in ast.walk(node))]
    assert len(calls) == 1 and ast.unparse(calls[0].test) == "attempt + 1 >= MAX_SEMANTIC_ATTEMPTS"
