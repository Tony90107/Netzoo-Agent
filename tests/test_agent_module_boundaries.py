import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
CORE_ROOT = SCRIPTS_ROOT / "netzoo_agent_core"


class AgentModuleBoundaryTests(unittest.TestCase):
    def test_legacy_entrypoint_remains_a_small_compatibility_facade(self):
        entrypoint = SCRIPTS_ROOT / "netzoo_agent.py"
        source = entrypoint.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_functions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.assertEqual(top_level_functions, [])
        self.assertLessEqual(
            len(source.splitlines()),
            150,
            "Move new behaviour into the owning netzoo_agent_core module.",
        )

    def test_core_modules_stay_reviewable(self):
        oversized = {
            path.name: len(path.read_text(encoding="utf-8").splitlines())
            for path in CORE_ROOT.glob("*.py")
            if len(path.read_text(encoding="utf-8").splitlines()) > 1_000
        }
        self.assertEqual(
            oversized,
            {},
            "Split a deep module at a real responsibility seam before it grows further.",
        )

    def test_internal_module_dependency_graph_is_acyclic(self):
        dependencies: dict[str, set[str]] = {}
        for path in CORE_ROOT.glob("*.py"):
            module = path.stem
            dependencies[module] = set()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                    dependencies[module].add(node.module)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module: str, trail: tuple[str, ...] = ()) -> None:
            if module in visiting:
                self.fail(
                    "Circular netzoo_agent_core dependency: "
                    + " -> ".join((*trail, module))
                )
            if module in visited:
                return
            visiting.add(module)
            for dependency in dependencies.get(module, ()):
                visit(dependency, (*trail, module))
            visiting.remove(module)
            visited.add(module)

        for module in dependencies:
            visit(module)

    def test_recovery_returns_through_the_plan_evaluator(self):
        graph_source = (CORE_ROOT / "graph.py").read_text(encoding="utf-8")

        self.assertIn(
            'graph.add_edge("recover", "evaluate_plan")',
            graph_source,
        )
        self.assertNotIn(
            'graph.add_edge("recover", "execute_tool")',
            graph_source,
        )


if __name__ == "__main__":
    unittest.main()
