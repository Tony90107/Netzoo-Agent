from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.routing.error_adapters import (  # noqa: E402
    PUMA_EXPRESSION_HEADER_UNSUPPORTED,
    ToolErrorContext,
    adapt_tool_error,
    extract_reported_error_codes,
)
from netzoo_agent_core.routing.results import structure_tool_result  # noqa: E402


def _puma_decision() -> TaskDecision:
    return TaskDecision(
        action="run_puma",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
    )


def test_machine_error_code_is_extracted_independently_of_message():
    raw = "Error code: PUMA_EXPRESSION_HEADER_UNSUPPORTED\nerror: wording changed"

    assert extract_reported_error_codes(raw) == [
        PUMA_EXPRESSION_HEADER_UNSUPPORTED
    ]


def test_puma_adapter_maps_stable_code_to_recovery():
    diagnosis = adapt_tool_error(
        ToolErrorContext(
            action="run_puma",
            reported_error_codes=[PUMA_EXPRESSION_HEADER_UNSUPPORTED],
            errors=["arbitrary human wording"],
        )
    )

    assert diagnosis is not None
    assert diagnosis.error_code == PUMA_EXPRESSION_HEADER_UNSUPPORTED
    assert diagnosis.retryable is True
    assert diagnosis.recovery_action == "format_expression_headerless"


def test_human_phrase_without_machine_code_does_not_grant_recovery():
    result = structure_tool_result(
        "run_puma",
        _puma_decision(),
        "error: legacy netZooPy PUMA does not accept an expression header",
    )

    assert result.status == "failed"
    assert result.error_code is None
    assert result.retryable is False
    assert result.recovery_hint is None


def test_unknown_machine_code_stops_without_recovery():
    result = structure_tool_result(
        "run_puma",
        _puma_decision(),
        "Error code: PUMA_UNKNOWN_FAILURE\nerror: unknown",
    )

    assert result.status == "failed"
    assert result.error_code is None
    assert result.retryable is False
    assert result.recovery_hint is None
