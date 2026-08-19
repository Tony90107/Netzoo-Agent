import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.data.resource_inventory import (  # noqa: E402
    inventory_workspace_resources,
)


class DatasetBundlePlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

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
        self.assertEqual(plan.status, "ready")
        self.assertEqual(
            {item.bundle_id for item in discovered},
            {f"directory:{study.resolve()}"},
        )

    def test_inventory_and_planning_choose_the_same_complete_bundle(self):
        self.write_complete_puma_bundle(self.root / "study-a")

        inventory = inventory_workspace_resources(self.root, ["run_puma"])
        bundle = agent.discover_coherent_bundle("run_puma", self.root, {})

        self.assertIsNotNone(bundle)
        planning_inputs = {
            role: Path(path).resolve().relative_to(self.root.resolve()).as_posix()
            for role, path in bundle.values.items()
        }
        self.assertEqual(planning_inputs, inventory.validated_bundles[0].inputs)

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

        self.assertEqual(verdict.status, "rejected")
        failed = {item.criterion for item in verdict.rubric if item.result == "fail"}
        self.assertIn("dataset_bundle_provenance", failed)


if __name__ == "__main__":
    unittest.main()
