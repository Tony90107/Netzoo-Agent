import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
CORE_ROOT = SCRIPTS_ROOT / "netzoo_agent_core"
CORE_PACKAGE = "netzoo_agent_core"


def _module_name(path: Path) -> str:
    relative = path.relative_to(CORE_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _internal_dependencies(path: Path, known_modules: set[str]) -> set[str]:
    module = _module_name(path)
    package = module.split(".") if path.name == "__init__.py" else module.split(".")[:-1]
    dependencies: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        candidates: list[str] = []
        if isinstance(node, ast.Import):
            candidates.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: max(0, len(package) - node.level + 1)]
                if node.module:
                    candidates.append(".".join((*base, *node.module.split("."))))
                else:
                    candidates.extend(".".join((*base, alias.name)) for alias in node.names)
            elif node.module:
                candidates.append(node.module)

        for candidate in candidates:
            if candidate == CORE_PACKAGE:
                candidate = ""
            elif candidate.startswith(f"{CORE_PACKAGE}."):
                candidate = candidate[len(CORE_PACKAGE) + 1 :]
            if candidate in known_modules:
                dependencies.add(candidate)

    return dependencies


def _dependency_graph() -> dict[str, set[str]]:
    paths = tuple(CORE_ROOT.rglob("*.py"))
    known_modules = {_module_name(path) for path in paths}
    return {
        _module_name(path): _internal_dependencies(path, known_modules)
        for path in paths
    }


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
            str(path.relative_to(CORE_ROOT)): len(
                path.read_text(encoding="utf-8").splitlines()
            )
            for path in CORE_ROOT.rglob("*.py")
            if len(path.read_text(encoding="utf-8").splitlines()) > 1_000
        }
        self.assertEqual(
            oversized,
            {},
            "Split a deep module at a real responsibility seam before it grows further.",
        )

    def test_internal_module_dependency_graph_is_acyclic(self):
        dependencies = _dependency_graph()

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

    def test_data_layer_does_not_depend_on_orchestration_layers(self):
        dependencies = _dependency_graph()
        forbidden = {"cli", "evaluation", "execution", "graph", "planning"}
        violations = {
            module: sorted(
                dependency
                for dependency in module_dependencies
                if dependency.split(".", 1)[0] in forbidden
            )
            for module, module_dependencies in dependencies.items()
            if module == "data" or module.startswith("data.")
        }
        violations = {
            module: module_dependencies
            for module, module_dependencies in violations.items()
            if module_dependencies
        }

        self.assertEqual(
            violations,
            {},
            "Keep neutral data behavior below planning, execution, evaluation, graph, and CLI.",
        )

    def test_recovery_returns_through_the_plan_evaluator(self):
        graph_source = (CORE_ROOT / "graph" / "topology.py").read_text(
            encoding="utf-8"
        )

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
