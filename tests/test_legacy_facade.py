import stat
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ENTRYPOINT = ROOT / "scripts" / "netzoo_agent.py"
sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent as agent  # noqa: E402


class LegacyFacadeTests(unittest.TestCase):
    def test_entrypoint_is_executable(self):
        mode = stat.S_IMODE(ENTRYPOINT.stat().st_mode)
        self.assertTrue(mode & stat.S_IXUSR)

    def test_historical_tool_imports_remain_available(self):
        self.assertTrue(hasattr(agent, "explain_panda_puma_io"))
        self.assertTrue(hasattr(agent, "TOOLS"))
        names = {tool.name for tool in agent.TOOLS}
        self.assertEqual(
            names,
            {
                "explain_panda_puma_io",
                "inspect_netzoo_inputs",
                "run_panda",
                "run_puma",
            },
        )

    def test_historical_explanation_tool_is_deterministic(self):
        summary = agent.explain_panda_puma_io.invoke({"topic": "overview"})

        self.assertIn("PANDA needs", summary)
        self.assertIn("PUMA needs", summary)
        self.assertIn("Requested topic: overview", summary)


if __name__ == "__main__":
    unittest.main()
