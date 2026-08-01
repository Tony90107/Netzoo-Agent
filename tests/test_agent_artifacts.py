import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def decision(self, action: str, **values) -> agent.TaskDecision:
        return agent.TaskDecision(
            action=action,
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="artifact test",
            **values,
        )

    def test_zero_byte_puma_output_fails(self):
        output = self.write("puma.tsv", "")
        result = agent.validate_output_artifacts(
            "run_puma",
            self.decision("run_puma", output_file=str(output)),
        )

        self.assertFalse(result.ok)
        self.assertIn("empty", " ".join(result.errors))

    def test_zero_exit_with_invalid_artifact_is_structured_as_failure(self):
        output = self.write("panda.tsv", "")
        decision = self.decision("run_panda", output_file=str(output))

        result = agent.structure_tool_result(
            "run_panda",
            decision,
            "Command: `run-panda`\nExit code: 0",
        )

        self.assertEqual(result.status, "failed")
        self.assertIn("empty", " ".join(result.errors))

    def test_malformed_lioness_text_fails(self):
        aggregate = self.write("aggregate.tsv", "TF1\tGene1\t1.0\n")
        lioness = self.write("lioness.tsv", "not-a-network\n")
        result = agent.validate_output_artifacts(
            "run_lioness_panda",
            self.decision(
                "run_lioness_panda",
                output_file=str(aggregate),
                lioness_output=str(lioness),
            ),
        )

        self.assertFalse(result.ok)
        self.assertIn("LIONESS", " ".join(result.errors))

    def test_condor_requires_both_memberships(self):
        self.write("trial-edges.tsv", "source\ttarget\tweight\nTF1\tGene1\t1\n")
        self.write("trial-reg_memb.tsv", "node\tcommunity\nTF1\t0\n")
        self.write("trial-summary.txt", "CONDOR trial summary\n")
        result = agent.validate_output_artifacts(
            "run_condor",
            self.decision(
                "run_condor",
                output_dir=str(self.root),
                prefix="trial",
            ),
        )

        self.assertFalse(result.ok)
        self.assertIn("tar_memb", " ".join(result.errors))

    def test_valid_text_artifacts_pass(self):
        expression = self.write("formatted.tsv", "Gene1\t1\t2\nGene2\t3\t4\n")
        coexpression = self.write(
            "coexpression.tsv",
            "gene\tGene1\tGene2\nGene1\t1\t0.5\nGene2\t0.5\t1\n",
        )
        aggregate = self.write("aggregate.tsv", "TF1\tGene1\t1.0\n")
        lioness = self.write(
            "lioness.tsv",
            "TF\tgene\ts1\ts2\nTF1\tGene1\t0.1\t0.2\n",
        )

        checks = [
            agent.validate_output_artifacts(
                "format_expression",
                self.decision("format_expression", output_file=str(expression)),
            ),
            agent.validate_output_artifacts(
                "convert_expression",
                self.decision("convert_expression", output_file=str(coexpression)),
            ),
            agent.validate_output_artifacts(
                "run_panda",
                self.decision("run_panda", output_file=str(aggregate)),
            ),
            agent.validate_output_artifacts(
                "run_lioness_panda",
                self.decision(
                    "run_lioness_panda",
                    output_file=str(aggregate),
                    lioness_output=str(lioness),
                ),
            ),
        ]

        self.assertTrue(all(check.ok for check in checks), checks)

    def test_valid_lioness_npy_passes(self):
        aggregate = self.write("puma.tsv", "TF1\tGene1\t1.0\n")
        lioness = self.root / "lioness.npy"
        np.save(lioness, np.ones((1, 1, 3), dtype=float))

        result = agent.validate_output_artifacts(
            "run_lioness_puma",
            self.decision(
                "run_lioness_puma",
                output_file=str(aggregate),
                lioness_output=str(lioness),
            ),
        )

        self.assertTrue(result.ok, result.errors)

    def test_full_condor_artifacts_pass(self):
        self.write("trial-edges.tsv", "source\ttarget\tweight\nTF1\tGene1\t1\n")
        self.write("trial-reg_memb.tsv", "node\tcommunity\nTF1\t0\n")
        self.write("trial-tar_memb.tsv", "node\tcommunity\nGene1\t0\n")
        self.write("trial-summary.txt", "CONDOR trial summary\n")

        result = agent.validate_output_artifacts(
            "run_condor",
            self.decision(
                "run_condor",
                output_dir=str(self.root),
                prefix="trial",
            ),
        )

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(len(result.artifacts), 4)


if __name__ == "__main__":
    unittest.main()
