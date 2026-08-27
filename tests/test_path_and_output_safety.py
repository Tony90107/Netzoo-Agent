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

    def test_natural_language_data_phrases_do_not_become_file_paths(self):
        tasks = [
            "if i want to get sample specific mi-RNA network data, what tools do i need?",
            "Which workflow produces network results for each patient?",
            "Explain the expression data requirements for PUMA.",
        ]
        for task in tasks:
            with self.subTest(task=task):
                decision = agent.hydrate_router_decision(
                    agent.TaskDecision(
                        action="no_tool",
                        in_scope=True,
                        should_execute=False,
                        intent_type="answer_question",
                        confidence=0.9,
                        reason="guidance",
                    ),
                    task,
                )
                self.assertIsNone(decision.network_file)
                self.assertIsNone(decision.expression_file)

    def test_explicit_network_paths_survive_hydration(self):
        cases = [
            ("network_file=data/network.tsv", "data/network.tsv"),
            ("network: data/network.tsv", "data/network.tsv"),
            ("use data/network.tsv as the network", "data/network.tsv"),
        ]
        for task, expected in cases:
            with self.subTest(task=task):
                decision = agent.hydrate_router_decision(
                    agent.TaskDecision(
                        action="no_tool",
                        in_scope=True,
                        should_execute=False,
                        intent_type="answer_question",
                        confidence=0.9,
                        reason="guidance",
                    ),
                    task,
                )
                self.assertEqual(decision.network_file, expected)

    def test_paths_in_natural_language_are_not_truncated_by_filename_aliases(self):
        task = (
            "Run PANDA using data/official-toy/ToyExpressionData.txt, "
            "data/official-toy/ToyMotifData.txt, and "
            "data/official-toy/ToyPPIData.txt."
        )
        decision = agent.hydrate_router_decision(
            agent.TaskDecision(
                action="run_panda",
                in_scope=True,
                should_execute=True,
                intent_type="run_analysis",
                confidence=0.95,
                reason="explicit PANDA request",
                expression_file="data/official-toy/ToyExpressionData.txt",
                motif_file="data/official-toy/ToyMotifData.txt",
                ppi_file="data/official-toy/ToyPPIData.txt",
            ),
            task,
        )

        assert decision.expression_file == "data/official-toy/ToyExpressionData.txt"
        assert decision.motif_file == "data/official-toy/ToyMotifData.txt"
        assert decision.ppi_file == "data/official-toy/ToyPPIData.txt"

    def test_lioness_output_roles_must_be_distinct(self):
        task = (
            "run LIONESS coexpression with expression_file=data/lioness-toy/expression.tsv "
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
                expression_file="data/lioness-toy/expression.tsv",
                output_file="same.tsv",
                lioness_output="same.tsv",
            ),
            task,
        )

        verdict = agent.evaluate_workflow_plan(plan, task)

        self.assertEqual(verdict.status, "rejected")
        failed = {item.criterion for item in verdict.rubric if item.result == "fail"}
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
