"""Bounded PUMA expression-header removal strategy."""

from __future__ import annotations

from pathlib import Path

from ...contracts import (
    EvaluationResult,
    InputEvidence,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    WorkflowPlan,
    WorkflowStep,
)
from ...contracts.results import PUMA_EXPRESSION_HEADER_UNSUPPORTED
from ..recovery_registry import RecoveryValidation

__all__ = ["PumaHeaderlessExpressionRecovery"]


class PumaHeaderlessExpressionRecovery:
    """Derive a headerless expression and retry one failed PUMA step."""

    name = "format_expression_headerless"
    applicable_actions = frozenset({"run_puma"})
    accepted_error_codes = frozenset({PUMA_EXPRESSION_HEADER_UNSUPPORTED})

    def accepts(self, *, action: str, error_code: str | None) -> bool:
        return (
            action in self.applicable_actions
            and error_code in self.accepted_error_codes
        )

    def apply(
        self,
        plan: WorkflowPlan,
        step_index: int,
        evaluation: EvaluationResult,
    ) -> tuple[WorkflowPlan, int]:
        decision = TaskDecision.model_validate(plan.decision)
        if (
            not self.accepts(
                action=decision.action,
                error_code=evaluation.recovery_error_code,
            )
            or not decision.expression_file
            or not decision.output_file
            or not 0 <= step_index < len(plan.steps)
            or plan.steps[step_index].action != "run_puma"
        ):
            return plan, step_index

        source = Path(decision.expression_file)
        output_parent = Path(decision.output_file).parent
        derived = str(output_parent / f"{source.stem}.puma-expression.tsv")
        decision.expression_file = derived
        plan.decision = decision.model_dump()
        expression_evidence = next(
            (item for item in plan.evidence if item.field == "expression_file"),
            None,
        )
        recovery_reason = (
            "The prior PUMA attempt rejected the expression header, so the bounded "
            "recovery derived a headerless expression file."
        )
        if expression_evidence is None:
            plan.evidence.append(
                InputEvidence(
                    field="expression_file",
                    status="derived",
                    value=derived,
                    reason=recovery_reason,
                    derived_from=str(source),
                )
            )
        else:
            expression_evidence.status = "derived"
            expression_evidence.value = derived
            expression_evidence.reason = recovery_reason
            expression_evidence.candidates = []
            expression_evidence.bundle_id = None
            expression_evidence.derived_from = str(source)

        recovery_steps = [
            WorkflowStep(
                action="format_expression",
                purpose=(
                    "Remove the expression header rejected by PUMA and create a "
                    "derived input file."
                ),
                arguments={
                    "expression_file": str(source),
                    "output_file": derived,
                    "genes_axis": "auto",
                    "with_header": False,
                },
            ),
            WorkflowStep(
                action="inspect_inputs",
                purpose=(
                    "Revalidate the repaired expression file against the prior and "
                    "PPI inputs."
                ),
            ),
            WorkflowStep(
                action="run_puma",
                purpose="Retry the PUMA workflow with the repaired input.",
            ),
        ]
        plan.steps = [*plan.steps[:step_index], *recovery_steps]
        plan.recovery_action = self.name
        plan.recovery_error_code = evaluation.recovery_error_code
        plan.recovery_step_index = step_index
        plan.recovery_attempt = min(
            plan.recovery_attempt + 1,
            MAX_RECOVERY_ATTEMPTS,
        )
        return plan, step_index

    def validate_evidence(
        self,
        plan: WorkflowPlan,
        decision: TaskDecision,
    ) -> list[str]:
        failures: list[str] = []
        expression_evidence = [
            item for item in plan.evidence if item.field == "expression_file"
        ]
        if len(expression_evidence) != 1 or expression_evidence[0].status != "derived":
            failures.append(
                "PUMA header-removal recovery requires exactly one derived "
                "expression input"
            )
            return failures

        derived = [item for item in plan.evidence if item.status == "derived"]
        if len(derived) != 1:
            failures.append("a recovery plan must contain exactly one derived input")
        item = expression_evidence[0]
        index = plan.recovery_step_index
        format_step = (
            plan.steps[index]
            if index is not None and 0 <= index < len(plan.steps)
            else None
        )
        if item.value != decision.expression_file:
            failures.append("derived expression does not match the plan decision")
        expected_arguments = {
            "expression_file": item.derived_from,
            "output_file": item.value,
            "genes_axis": "auto",
            "with_header": False,
        }
        arguments_match = (
            format_step is not None
            and format_step.action == "format_expression"
            and set(format_step.arguments) == set(expected_arguments)
            and format_step.arguments.get("expression_file")
            == expected_arguments["expression_file"]
            and format_step.arguments.get("output_file")
            == expected_arguments["output_file"]
            and format_step.arguments.get("genes_axis") == "auto"
            and format_step.arguments.get("with_header") is False
        )
        if not arguments_match:
            failures.append(
                "derived expression does not match the authorized recovery "
                "transformation"
            )
        return failures

    def validate(
        self,
        plan: WorkflowPlan,
        decision: TaskDecision,
        normal_steps: list[str],
    ) -> RecoveryValidation:
        index = plan.recovery_step_index
        metadata_ok = (
            plan.recovery_action == self.name
            and self.accepts(
                action=decision.action,
                error_code=plan.recovery_error_code,
            )
            and index is not None
            and 1 <= plan.recovery_attempt <= MAX_RECOVERY_ATTEMPTS
            and 0 <= index < len(normal_steps)
            and normal_steps[index] == "run_puma"
        )
        if not metadata_ok:
            return RecoveryValidation(
                ok=False,
                detail=(
                    "Recovery metadata does not identify a registered, bounded "
                    "PUMA repair."
                ),
                failures=["recovery metadata does not match this strategy"],
                expected_steps=normal_steps,
            )

        expected = [
            *normal_steps[:index],
            "format_expression",
            "inspect_inputs",
            "run_puma",
        ]
        evidence_failures = self.validate_evidence(plan, decision)
        sequence_ok = [step.action for step in plan.steps] == expected
        failures = list(evidence_failures)
        if not sequence_ok:
            failures.append(
                "recovery steps do not match the registered header-removal repair"
            )
        return RecoveryValidation(
            ok=not failures,
            detail=(
                "Recovery metadata and steps match the registered header-removal "
                "repair."
                if not failures
                else "; ".join(failures)
            ),
            failures=failures,
            expected_steps=expected,
        )
