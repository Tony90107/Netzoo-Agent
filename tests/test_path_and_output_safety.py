import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402


class PathAndOutputSafetyTests(unittest.TestCase):
    def test_quoted_path_with_spaces_round_trips(self):
        task = 'run PANDA with expression_file="/tmp/My Study/表現 matrix.tsv"'

        self.assertEqual(
            agent._extract_named_path(task, ("expression_file",)),
            "/tmp/My Study/表現 matrix.tsv",
        )

    def test_lioness_output_roles_must_be_distinct(self):
        task = (
            "run LIONESS coexpression with expression_file=expression.tsv "
            "output_file=same.tsv lioness_output=same.tsv"
        )
        plan = agent.build_workflow_plan(
            agent.TaskDecision(
                action="run_lioness_coexpression",
                in_scope=True,
                should_execute=True,
                intent_type="run_analysis",
                confidence=1.0,
                reason="explicit LIONESS coexpression request",
                expression_file="expression.tsv",
                output_file="same.tsv",
                lioness_output="same.tsv",
            ),
            task,
        )

        verdict = agent.evaluate_workflow_plan(plan, task)

        self.assertEqual(verdict.status, "rejected")
        failed = {
            item.criterion for item in verdict.rubric if item.result == "fail"
        }
        self.assertIn("output_role_uniqueness", failed)

    def test_condor_prefix_cannot_escape_output_directory(self):
        with self.assertRaisesRegex(ValueError, "prefix"):
            agent.condor_artifact_paths("/tmp/out", "../victim")

    def test_condor_artifacts_remain_under_output_directory(self):
        paths = agent.condor_artifact_paths("/tmp/out", "trial-1")
        root = Path("/tmp/out").resolve()

        self.assertEqual(
            set(paths),
            {"edges.tsv", "reg_memb.tsv", "tar_memb.tsv", "summary.txt"},
        )
        self.assertTrue(all(path.is_relative_to(root) for path in paths.values()))


if __name__ == "__main__":
    unittest.main()
