import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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
                {"source": ["TF1"], "target": ["GeneA"], "weight": [1.0]}
            )
            obj = SimpleNamespace(
                reg_memb=pd.DataFrame({"node": ["TF1"], "community": [0]}),
                tar_memb=pd.DataFrame({"node": ["GeneA"], "community": [0]}),
                modularity=0.5,
            )

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
            self.assertTrue(paths["tar_memb.tsv"].stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
