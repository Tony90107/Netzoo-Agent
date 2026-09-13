import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from workflow_registry import (  # noqa: E402
    ACTION_DEFINITIONS,
    ACTION_NAMES,
    get_controls,
    resolve_conditional_output,
)


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

    def test_controls_are_typed_and_non_bonobo_workflows_do_not_leak_bonobo_controls(self):
        bonobo_controls = get_controls("run_bonobo")
        self.assertIn("sample_names", {item.name for item in bonobo_controls})
        for item in bonobo_controls:
            self.assertTrue(item.executor_argument)
            self.assertIn(
                item.control_type,
                {"boolean", "integer", "number", "string", "string_list", "enum"},
            )
        panda_controls = get_controls("run_panda")
        self.assertEqual([item.name for item in panda_controls], ["with_header"])

    def test_selection_tags_filter_only_registry_declared_controls(self):
        sample_controls = get_controls("run_bonobo", {"sample_specific"})
        sparse_controls = get_controls(
            "run_bonobo", {"sparse_pvalue_coexpression"}
        )
        self.assertIn("sample_names", {item.name for item in sample_controls})
        self.assertNotIn("save_pvals", {item.name for item in sample_controls})
        self.assertIn("save_pvals", {item.name for item in sparse_controls})
        self.assertNotIn("sample_names", {item.name for item in sparse_controls})

    def test_bonobo_conditional_output_is_machine_resolvable(self):
        rule = resolve_conditional_output(
            "run_bonobo", {"sparsify": True, "save_pvals": True}
        )
        self.assertIsNotNone(rule)
        self.assertEqual(
            rule.produced_artifacts,
            frozenset({"coexpression_network", "pvalue_matrix"}),
        )
        self.assertIn("full co-expression matrix", rule.semantics)
        self.assertIn("p-value matrix", rule.semantics)


if __name__ == "__main__":
    unittest.main()
