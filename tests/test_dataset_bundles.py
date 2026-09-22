import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402


class DatasetBundlePlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        # This suite uses placeholder IDs to isolate coherent-bundle behavior.
        mode = patch.object(agent.settings, "TEST_DATA_MODE", True)
        mode.start()
        self.addCleanup(mode.stop)

    @staticmethod
    def write(directory: Path, name: str, text: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_expression(self, directory: Path) -> Path:
        return self.write(
            directory,
            "expression.tsv",
            "GeneA\t1\t2\t3\nGeneB\t3\t2\t1\n",
        )

    def write_puma_priors(self, directory: Path) -> None:
        self.write(
            directory,
            "prior-puma.tsv",
            "TF1\tGeneA\t1\nTF2\tGeneB\t1\nmiR-1\tGeneA\t1\n",
        )
        self.write(directory, "ppi.tsv", "TF1\tTF2\t1\nTF2\tTF1\t1\n")
        self.write(directory, "mirna.txt", "miR-1\n")

    def write_complete_puma_bundle(self, directory: Path) -> Path:
        self.write_expression(directory)
        self.write_puma_priors(directory)
        return directory

    @staticmethod
    def puma_decision(expression_file: str) -> agent.TaskDecision:
        return agent.TaskDecision(
            action="run_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=1.0,
            reason="explicit PUMA request",
            expression_file=expression_file,
        )

    def test_anchored_expression_does_not_pull_inputs_from_other_datasets(self):
        expression = self.write_expression(self.root / "study-a")
        self.write_puma_priors(self.root / "study-b")

        plan = agent.build_workflow_plan(
            self.puma_decision(str(expression)),
            f"run PUMA with expression_file={expression}",
        )

        self.assertEqual(plan.status, "needs_input")
        self.assertIn("motif_file", plan.missing_inputs)
        self.assertIn("ppi_file", plan.missing_inputs)
        self.assertIn("mirna_file", plan.missing_inputs)

    def test_one_complete_directory_is_applied_with_one_bundle_id(self):
        study = self.write_complete_puma_bundle(self.root / "study-a")
        expression = study / "expression.tsv"

        plan = agent.build_workflow_plan(
            self.puma_decision(str(expression)),
            f"run PUMA with expression_file={expression}",
        )

        discovered = [item for item in plan.evidence if item.status == "discovered"]
        self.assertEqual(plan.status, "needs_confirmation")
        self.assertEqual(
            {item.bundle_id for item in discovered},
            {f"directory:{study.resolve()}"},
        )

    def test_content_validation_accepts_a_uniquely_verified_misnamed_motif_file(self):
        study = self.root / "study-a"
        expression = self.write_expression(study)
        self.write(
            study,
            "motfi.tsv",
            "TF1\tGeneA\t1\nTF2\tGeneB\t1\nmiR-1\tGeneA\t1\n",
        )
        self.write(study, "ppi.tsv", "TF1\tTF2\t1\nTF2\tTF1\t1\n")
        self.write(study, "mirna.txt", "miR-1\n")

        plan = agent.build_workflow_plan(
            self.puma_decision(str(expression)),
            f"run PUMA with expression_file={expression}",
        )

        motif = next(item for item in plan.evidence if item.field == "motif_file")
        self.assertEqual(plan.status, "needs_confirmation")
        self.assertEqual(Path(motif.value).name, "motfi.tsv")
        self.assertIn("verified from file contents", motif.reason)

    def test_one_partial_bundle_lists_found_files_and_only_requests_missing_input(self):
        study = self.root / "data" / "study-a"
        self.write_expression(study)
        self.write(
            study,
            "prior-puma.tsv",
            "TF1\tGeneA\t1\nTF2\tGeneB\t1\nmiR-1\tGeneA\t1\n",
        )
        self.write(study, "ppi.tsv", "TF1\tTF2\t1\nTF2\tTF1\t1\n")
        decision = agent.TaskDecision(
            action="run_lioness_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=1.0,
            reason="Use locally available inputs.",
            recommended_actions=["run_puma", "run_lioness_puma"],
        )

        with patch(
            "netzoo_agent_core.planning.evidence.PROJECT_ROOT",
            self.root,
        ):
            plan = agent.build_workflow_plan(
                decision,
                "Continue the trusted workflow using available local data.",
            )

        self.assertEqual(plan.status, "needs_input")
        self.assertEqual(plan.missing_inputs, ["mirna_file"])
        self.assertEqual(plan.input_bundle_options, [])
        self.assertIn(str(study), plan.question)
        self.assertIn("expression.tsv", plan.question)
        self.assertIn("prior-puma.tsv", plan.question)
        self.assertIn("ppi.tsv", plan.question)
        self.assertIn("mirna_file", plan.question)
        rendered_prompt = agent.clarification_prompt(plan)
        self.assertIn("I found this partial input bundle", rendered_prompt)
        self.assertIn("prior-puma.tsv", rendered_prompt)
        self.assertIn("mirna_file", rendered_prompt)
        self.assertIn("wizard will ask only for these missing fields", rendered_prompt)
        self.assertNotIn("choose another input bundle", rendered_prompt)
        discovered = {
            item.field: item for item in plan.evidence if item.status == "discovered"
        }
        self.assertEqual(
            set(discovered),
            {"expression_file", "motif_file", "ppi_file"},
        )
        self.assertEqual(
            {item.bundle_id for item in discovered.values()},
            {f"directory:{study.resolve()}"},
        )

        supplied_mirna = self.write(
            self.root / "provided",
            "mirna.txt",
            "miR-1\n",
        )
        selections = agent.parse_clarification_assignments(
            plan,
            str(supplied_mirna),
            target_field="mirna_file",
        )
        continuation = agent.clarification_continuation(plan, selections)
        self.assertIn("CARRIED_DISCOVERED_FIELD=expression_file", continuation)
        self.assertIn("CARRIED_DISCOVERED_FIELD=motif_file", continuation)
        self.assertIn("CARRIED_DISCOVERED_FIELD=ppi_file", continuation)

        repaired = agent.repair_router_decision(
            agent.TaskDecision(
                action="no_tool",
                in_scope=True,
                should_execute=False,
                confidence=0.95,
                reason="Continue the accepted workflow.",
            ),
            continuation,
        )
        with patch(
            "netzoo_agent_core.planning.evidence.PROJECT_ROOT",
            self.root,
        ):
            replanned = agent.build_workflow_plan(repaired, continuation)

        self.assertEqual(replanned.status, "needs_confirmation")
        self.assertEqual(replanned.missing_inputs, [])

    def test_complete_bundles_are_atomic_unless_user_enters_custom_mode(self):
        first = self.write_complete_puma_bundle(self.root / "data" / "study-a")
        second = self.write_complete_puma_bundle(self.root / "data" / "study-b")
        decision = agent.TaskDecision(
            action="run_lioness_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=1.0,
            reason="Use locally available inputs.",
            recommended_actions=["run_puma", "run_lioness_puma"],
        )

        with patch(
            "netzoo_agent_core.planning.evidence.PROJECT_ROOT",
            self.root,
        ):
            plan = agent.build_workflow_plan(
                decision,
                "Continue the trusted workflow using available local data.",
            )

        self.assertEqual(plan.status, "needs_input")
        self.assertEqual(len(plan.input_bundle_options), 2)
        expression_evidence = next(
            item for item in plan.evidence if item.field == "expression_file"
        )
        self.assertEqual(
            expression_evidence.candidate_bundle_ids,
            [
                f"directory:{first.resolve()}",
                f"directory:{second.resolve()}",
            ],
        )
        self.assertEqual(
            [item.bundle_id for item in plan.input_bundle_options],
            expression_evidence.candidate_bundle_ids,
        )
        prompt = agent.clarification_prompt(plan)
        self.assertIn("Choose one complete input bundle", prompt)
        self.assertIn("custom", prompt)
        self.assertNotIn("Select input 1 of 4", prompt)

        continuation = agent.bundle_clarification_continuation(plan, "1")
        for field_name, filename in (
            ("expression_file", "expression.tsv"),
            ("motif_file", "prior-puma.tsv"),
            ("ppi_file", "ppi.tsv"),
            ("mirna_file", "mirna.txt"),
        ):
            self.assertIn(
                f"{field_name} is {(first / filename).resolve()}", continuation
            )
            self.assertIn(f"SELECTED_FIELD={field_name}", continuation)
            self.assertNotIn(str((second / filename).resolve()), continuation)

        with self.assertRaisesRegex(
            agent.ClarificationInputError,
            "no complete bundle numbered 3",
        ):
            agent.bundle_clarification_continuation(plan, "3")

        repaired = agent.repair_router_decision(
            agent.TaskDecision(
                action="no_tool",
                in_scope=True,
                should_execute=False,
                confidence=0.95,
                reason="Continue the selected bundle.",
            ),
            continuation,
        )
        with patch(
            "netzoo_agent_core.planning.evidence.PROJECT_ROOT",
            self.root,
        ):
            replanned = agent.build_workflow_plan(repaired, continuation)
        self.assertEqual(replanned.status, "ready")
        selected_inputs = {
            item.field: item.status
            for item in replanned.evidence
            if item.field
            in {"expression_file", "motif_file", "ppi_file", "mirna_file"}
        }
        self.assertEqual(set(selected_inputs.values()), {"selected"})
        self.assertEqual(
            agent.evaluate_workflow_plan(replanned, continuation).status,
            "approved",
        )

        custom_prompt = agent.custom_clarification_prompt(plan)
        self.assertIn("Custom input composition", custom_prompt)
        self.assertIn("Select input 1 of 4", custom_prompt)

    def test_plan_evaluator_rejects_conflicting_discovered_bundle_ids(self):
        study = self.write_complete_puma_bundle(self.root / "study-a")
        expression = study / "expression.tsv"
        task = f"run PUMA with expression_file={expression}"
        plan = agent.build_workflow_plan(
            self.puma_decision(str(expression)),
            task,
        )
        discovered = [item for item in plan.evidence if item.status == "discovered"]
        discovered[-1].bundle_id = "directory:/forged-study"

        verdict = agent.evaluate_workflow_plan(plan, task)

        self.assertEqual(verdict.status, "deferred")


if __name__ == "__main__":
    unittest.main()
