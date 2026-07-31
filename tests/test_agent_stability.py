import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402


class OutcomeContractTests(unittest.TestCase):
    @staticmethod
    def recovered_plan():
        decision = agent.TaskDecision(
            action="run_puma",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="explicit PUMA request",
            expression_file="expression.tsv",
            motif_file="prior.tsv",
            ppi_file="ppi.tsv",
            mirna_file="mirna.txt",
            output_file="puma.tsv",
        )
        return agent.WorkflowPlan(
            workflow="PUMA",
            objective="Run PUMA",
            decision=decision.model_dump(),
            status="ready",
        )

    @staticmethod
    def recovered_results():
        return [
            agent.ToolExecutionResult(
                action="run_puma",
                status="failed",
                summary="header rejected",
                superseded=True,
                superseded_reason="recovered by attempt 1",
            ),
            agent.ToolExecutionResult(
                action="run_puma",
                status="success",
                summary="recovered",
                attempt_id=1,
            ),
        ]

    def test_legacy_tool_result_defaults_to_effective_attempt_zero(self):
        result = agent.ToolExecutionResult(
            action="run_puma",
            status="failed",
            summary="legacy payload",
        )

        self.assertEqual(result.attempt_id, 0)
        self.assertFalse(result.superseded)
        self.assertIsNone(result.superseded_reason)

    def test_effective_results_excludes_superseded_failure(self):
        results = [
            agent.ToolExecutionResult(
                action="run_puma",
                status="failed",
                summary="header rejected",
                superseded=True,
                superseded_reason="recovered by attempt 1",
            ),
            agent.ToolExecutionResult(
                action="run_puma",
                status="success",
                summary="recovered",
                attempt_id=1,
            ),
        ]

        effective = agent.effective_results(results)

        self.assertEqual([item.status for item in effective], ["success"])

    def test_successful_recovery_renders_terminal_completion(self):
        rendered = agent.render_compact_execution_response(
            self.recovered_plan(),
            self.recovered_results(),
            agent.EvaluationResult(status="completed", reason="recovered"),
        )

        self.assertIn("PUMA · COMPLETED", rendered)
        self.assertNotIn("PUMA · FAILED", rendered)

    def test_successful_recovery_selects_completed_next_prompt(self):
        state = {
            "plan": self.recovered_plan().model_dump(),
            "tool_results": [
                item.model_dump() for item in self.recovered_results()
            ],
            "evaluation": {
                "status": "completed",
                "reason": "recovered",
            },
        }

        prompt = agent.build_next_turn_prompt(state)

        self.assertEqual(prompt.kind, "completed")

    def test_recovery_supersedes_only_latest_effective_failure(self):
        results = [
            agent.ToolExecutionResult(
                action="inspect_inputs",
                status="success",
                summary="valid",
            ),
            agent.ToolExecutionResult(
                action="run_puma",
                status="failed",
                summary="header rejected",
            ),
        ]

        superseded = agent.supersede_triggering_failure(results, next_attempt=1)

        self.assertFalse(superseded[0].superseded)
        self.assertTrue(superseded[1].superseded)
        self.assertEqual(
            superseded[1].superseded_reason,
            "superseded by recovery attempt 1",
        )

    def test_structured_tool_result_records_recovery_attempt(self):
        decision = agent.TaskDecision(
            action="inspect_inputs",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="inspect",
        )

        result = agent.structure_tool_result(
            "inspect_inputs",
            decision,
            "inspection completed",
            attempt_id=2,
        )

        self.assertEqual(result.attempt_id, 2)


if __name__ == "__main__":
    unittest.main()
