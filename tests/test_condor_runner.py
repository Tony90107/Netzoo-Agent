import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_condor_runner():
    loader = importlib.machinery.SourceFileLoader(
        "netzoo_condor_runner",
        str(ROOT / "docker" / "run-condor"),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


condor = load_condor_runner()


class CondorRunnerTests(unittest.TestCase):
    def test_missing_target_membership_is_terminal_failure(self):
        obj = SimpleNamespace(
            reg_memb=pd.DataFrame({"node": ["TF1"], "community": [0]}),
            tar_memb=pd.DataFrame(),
        )

        with self.assertRaisesRegex(condor.CondorExecutionError, "tar_memb"):
            condor.required_memberships(obj)

    def test_method_errors_keep_context(self):
        candidates = (
            (
                "brim()",
                lambda: (_ for _ in ()).throw(ValueError("no convergence")),
            ),
            (
                "run()",
                lambda: (_ for _ in ()).throw(RuntimeError("fallback failed")),
            ),
        )

        with self.assertRaisesRegex(
            condor.CondorExecutionError,
            r"brim\(\).*ValueError.*no convergence",
        ):
            condor.run_first_supported("optimization", candidates)

    def test_happy_path_writes_all_required_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = condor.condor_artifact_paths(temporary, "trial-1")
            edges = pd.DataFrame(
                {"source": ["TF1", "TF2"], "target": ["GeneA", "GeneB"], "weight": [1.0, 1.0]}
            )
            obj = FakeCondor(edges, reg=[0, 1], tar=[0, 1])

            written = condor.write_outputs(
                obj,
                edges,
                paths,
                initialization_method="initial_community()",
                optimization_method="brim()",
            )

            self.assertEqual(set(written), set(paths.values()))
            self.assertTrue(all(path.is_file() for path in written))
            self.assertTrue(paths["reg_memb.tsv"].stat().st_size > 0)
            self.assertTrue(paths["tar_qscores.tsv"].stat().st_size > 0)

    def test_stand_in_without_matrices_cannot_claim_core_scores(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = condor.condor_artifact_paths(temporary, "trial-1")
            obj = SimpleNamespace(
                reg_memb=pd.DataFrame({"reg": ["TF1"], "community": [0]}),
                tar_memb=pd.DataFrame({"tar": ["GeneA"], "community": [0]}),
            )
            with self.assertRaisesRegex(condor.CondorExecutionError, "core scores"):
                condor.write_outputs(obj, pd.DataFrame(), paths,
                                     initialization_method="i", optimization_method="o")

    def test_regulators_follow_final_targets_and_core_scores_sum_to_one(self):
        # Two clear modules; netZooPy's brim keeps the initial regulator assignment,
        # so TF2 starts in the wrong community and must move.
        edges = pd.DataFrame({
            "source": ["TF1", "TF1", "TF2", "TF2", "TF3", "TF3", "TF4", "TF4"],
            "target": ["GeneA", "GeneB", "GeneA", "GeneB", "GeneC", "GeneD", "GeneC", "GeneD"],
            "weight": [1.0] * 8,
        })
        obj = FakeCondor(edges, reg=[0, 1, 1, 1], tar=[0, 0, 1, 1])
        scores = condor.final_scores(obj)
        self.assertEqual(list(scores["reg_memb"]["community"]), [0, 0, 1, 1])
        self.assertEqual(scores["reassigned_regulators"], 1)
        for frame in (scores["reg_qscores"], scores["tar_qscores"]):
            sums = frame.groupby("community")["qscore"].sum()
            self.assertTrue(np.allclose(sums, 0.5))
        self.assertAlmostEqual(scores["modularity"], 0.5)


class FakeCondor:
    """The netZooPy condor_object.matrices contract on a fixed edge list."""

    def __init__(self, edges, reg, tar):
        self.reg_names = sorted(set(edges["source"]))
        self.tar_names = sorted(set(edges["target"]))
        self.edges = edges
        self.reg_memb = pd.DataFrame({"reg": self.reg_names, "community": reg})
        self.tar_memb = pd.DataFrame({"tar": self.tar_names, "community": tar})

    def matrices(self, c, resolution):
        rg = {name: i for i, name in enumerate(self.reg_names)}
        gn = {name: i for i, name in enumerate(self.tar_names)}
        A = np.zeros((len(gn), len(rg)))
        for source, target, weight in self.edges.itertuples(index=False):
            A[gn[target], rg[source]] = weight
        ki, dj = A.sum(1, keepdims=True), A.sum(0, keepdims=True)
        m = float(ki.sum())
        B = A - resolution * (ki @ dj) / m
        T = np.zeros((len(gn), c))
        T[[gn[n] for n in self.tar_memb["tar"]], list(self.tar_memb["community"])] = 1
        R = np.zeros((len(rg), c))
        R[[rg[n] for n in self.reg_memb["reg"]], list(self.reg_memb["community"])] = 1
        return B, m, T, R, gn, rg


if __name__ == "__main__":
    unittest.main()
