import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, ACTION_NAMES  # noqa: E402


class WorkflowRegistryTests(unittest.TestCase):
    def test_registry_covers_every_typed_action_exactly_once(self):
        self.assertEqual(set(ACTION_DEFINITIONS), set(ACTION_NAMES))

    def test_local_executor_registry_matches_local_action_registry(self):
        self.assertEqual(
            set(agent.LOCAL_TOOL_EXECUTORS),
            set(agent.LOCAL_EXECUTION_ACTIONS),
        )

    def test_run_registry_derivations_remain_consistent(self):
        for action in agent.RUN_ACTIONS:
            with self.subTest(action=action):
                definition = ACTION_DEFINITIONS[action]
                self.assertTrue(definition.run)
                self.assertEqual(
                    tuple(agent.REQUIRED_INPUTS[action]),
                    definition.required_inputs,
                )
                self.assertEqual(
                    agent.CODE_VALIDATION_STEPS[action],
                    list(definition.validation_steps),
                )


if __name__ == "__main__":
    unittest.main()
