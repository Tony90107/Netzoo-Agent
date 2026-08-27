from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    EvaluationResult,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
)
from netzoo_agent_core.contracts.results import (  # noqa: E402
    PUMA_EXPRESSION_HEADER_UNSUPPORTED,
)
from netzoo_agent_core.evaluation.plan_review import (  # noqa: E402
    evaluate_workflow_plan,
)
from netzoo_agent_core.evaluation.recovery import (  # noqa: E402
    recover_workflow_plan,
)
from netzoo_agent_core.evaluation.recovery_registry import (  # noqa: E402
    get_recovery_strategy,
)
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402


PUMA_TASK = (
    "run PUMA with expression_file=data/lioness-toy/expression.tsv, "
    "motif_file=data/lioness-toy/prior-puma.tsv, ppi_file=data/lioness-toy/ppi.tsv, "
    "mirna_file=data/lioness-toy/mirna.txt, output_file=outputs/puma.tsv"
)


def _ready_puma_plan():
    decision = TaskDecision(
        action="run_puma",
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=1.0,
        reason="run PUMA",
        expression_file="data/lioness-toy/expression.tsv",
        motif_file="data/lioness-toy/prior-puma.tsv",
        ppi_file="data/lioness-toy/ppi.tsv",
        mirna_file="data/lioness-toy/mirna.txt",
        output_file="outputs/puma.tsv",
    )
    return build_workflow_plan(decision, PUMA_TASK)


def _header_evaluation() -> EvaluationResult:
    return EvaluationResult(
        status="replan",
        reason="header rejected",
        recovery_action="format_expression_headerless",
        recovery_error_code=PUMA_EXPRESSION_HEADER_UNSUPPORTED,
    )


def test_unknown_recovery_name_is_not_registered():
    assert get_recovery_strategy("delete_inputs_and_retry") is None


def test_puma_strategy_rejects_wrong_error_code():
    strategy = get_recovery_strategy("format_expression_headerless")

    assert strategy is not None
    assert strategy.accepts(
        action="run_puma",
        error_code="PUMA_UNKNOWN_FAILURE",
    ) is False


def test_registered_strategy_builds_bounded_plan():
    recovered, next_step = recover_workflow_plan(
        _ready_puma_plan(),
        1,
        _header_evaluation(),
    )

    assert next_step == 1
    assert [step.action for step in recovered.steps] == [
        "inspect_inputs",
        "format_expression",
        "inspect_inputs",
        "run_puma",
    ]
    assert recovered.recovery_error_code == PUMA_EXPRESSION_HEADER_UNSUPPORTED
    expression = next(
        item for item in recovered.evidence if item.field == "expression_file"
    )
    assert expression.status == "derived"
    assert expression.derived_from == "data/lioness-toy/expression.tsv"


def test_missing_error_code_does_not_mutate_plan():
    plan = _ready_puma_plan()
    recovered, next_step = recover_workflow_plan(
        plan,
        1,
        EvaluationResult(
            status="replan",
            reason="missing provenance",
            recovery_action="format_expression_headerless",
        ),
    )

    assert recovered == plan
    assert next_step == 1


def test_wrong_action_does_not_mutate_plan():
    plan = _ready_puma_plan()
    plan.decision["action"] = "run_panda"
    recovered, next_step = recover_workflow_plan(plan, 1, _header_evaluation())

    assert recovered == plan
    assert next_step == 1


def test_exhausted_attempts_do_not_mutate_plan():
    plan = _ready_puma_plan()
    plan.recovery_attempt = MAX_RECOVERY_ATTEMPTS
    recovered, next_step = recover_workflow_plan(plan, 1, _header_evaluation())

    assert recovered == plan
    assert next_step == 1


def test_strategy_validation_rejects_modified_format_arguments():
    recovered, _ = recover_workflow_plan(
        _ready_puma_plan(),
        1,
        _header_evaluation(),
    )
    recovered.steps[1].arguments["with_header"] = True

    evaluation = evaluate_workflow_plan(recovered, PUMA_TASK)

    assert evaluation.status == "rejected"
    failed = {item.criterion for item in evaluation.rubric if item.result == "fail"}
    assert "evidence_provenance_contract" in failed


def test_strategy_validation_rejects_malformed_derived_evidence():
    recovered, _ = recover_workflow_plan(
        _ready_puma_plan(),
        1,
        _header_evaluation(),
    )
    expression = next(
        item for item in recovered.evidence if item.field == "expression_file"
    )
    expression.derived_from = None

    evaluation = evaluate_workflow_plan(recovered, PUMA_TASK)

    assert evaluation.status == "rejected"
    failed = {item.criterion for item in evaluation.rubric if item.result == "fail"}
    assert "evidence_provenance_contract" in failed
