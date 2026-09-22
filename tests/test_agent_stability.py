import sys
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch


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

    def test_successful_recovery_records_completed_episode_without_old_error(self):
        results = self.recovered_results()
        results[0].errors = ["expression header rejected"]
        with tempfile.TemporaryDirectory() as tmp:
            store = agent.EpisodeStore(Path(tmp))

            episode = store.record(
                profile_id="researcher",
                task="run PUMA",
                plan=self.recovered_plan(),
                results=results,
                evaluation=agent.EvaluationResult(
                    status="completed",
                    reason="recovered",
                ),
                replan_count=1,
            )

        self.assertEqual(episode.status, "completed")
        self.assertIsNone(episode.error_signature)


class DatasetBundleTests(unittest.TestCase):
    def setUp(self):
        self.source = Path(__file__).parents[1] / "data" / "lioness-toy"
        # These bundle fixtures intentionally use GeneA/TF1-style labels. The
        # tests exercise atomic discovery/provenance, not biological authority.
        mode = patch.object(agent.settings, "TEST_DATA_MODE", True)
        mode.start()
        self.addCleanup(mode.stop)

    def copy(self, directory: Path, name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.source / name, directory / name)

    @staticmethod
    def puma_decision(expression_file: str):
        return agent.TaskDecision(
            action="run_puma",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="explicit PUMA request",
            expression_file=expression_file,
        )

    def test_incomplete_directories_do_not_form_one_autonomous_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.copy(root / "study-a", "expression.tsv")
            for name in ("prior-puma.tsv", "ppi.tsv", "mirna.txt"):
                self.copy(root / "study-b", name)

            bundle = agent.discover_coherent_bundle("run_puma", root, {})

        self.assertIsNone(bundle)

    def test_one_complete_validated_directory_is_selected_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "study-a"
            for name in (
                "expression.tsv",
                "prior-puma.tsv",
                "ppi.tsv",
                "mirna.txt",
            ):
                self.copy(study, name)

            bundle = agent.discover_coherent_bundle("run_puma", root, {})

        self.assertIsNotNone(bundle)
        self.assertEqual(
            Path(bundle.bundle_id.removeprefix("directory:")),
            study.resolve(),
        )
        self.assertEqual(
            set(bundle.values),
            {"expression_file", "motif_file", "ppi_file", "mirna_file"},
        )

    def test_planner_does_not_fill_an_anchored_request_from_other_datasets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expression = root / "study-a" / "expression.tsv"
            self.copy(expression.parent, expression.name)
            for name in ("prior-puma.tsv", "ppi.tsv", "mirna.txt"):
                self.copy(root / "study-b", name)
            task = f"run PUMA with expression_file={expression}"

            plan = agent.build_workflow_plan(
                self.puma_decision(str(expression)),
                task,
            )

        self.assertEqual(plan.status, "needs_input")
        self.assertIn("motif_file", plan.missing_inputs)
        self.assertIn("ppi_file", plan.missing_inputs)
        self.assertIn("mirna_file", plan.missing_inputs)

    def test_planner_applies_one_valid_bundle_with_shared_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study-a"
            for name in (
                "expression.tsv",
                "prior-puma.tsv",
                "ppi.tsv",
                "mirna.txt",
            ):
                self.copy(study, name)
            expression = study / "expression.tsv"
            task = f"run PUMA with expression_file={expression}"

            plan = agent.build_workflow_plan(
                self.puma_decision(str(expression)),
                task,
            )

        self.assertEqual(plan.status, "needs_confirmation")
        discovered = [
            item for item in plan.evidence if item.status == "discovered"
        ]
        self.assertEqual(
            {item.bundle_id for item in discovered},
            {f"directory:{study.resolve()}"},
        )


if __name__ == "__main__":
    unittest.main()
