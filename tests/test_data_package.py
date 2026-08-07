from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent_core.artifact_validation as artifact_validation  # noqa: E402
import netzoo_agent_core.bundles as bundles  # noqa: E402
import netzoo_agent_core.execution as execution  # noqa: E402
import netzoo_agent_core.path_safety as path_safety  # noqa: E402
import netzoo_agent_core.preparation as preparation  # noqa: E402
import netzoo_agent_core.validation as validation  # noqa: E402


OWNER_EXPORTS = {
    "table_validation": (
        validation,
        [
            "TableCheck",
            "_resolve_user_path",
            "_read_expression_source",
            "_looks_numeric",
            "_drop_common_header",
            "_read_checked_table",
            "_validate_expression",
            "_validate_edge_or_bed",
            "_validate_mirna_list",
            "_identifier_overlap_report",
            "_inspect_panda_inputs_impl",
            "inspect_netzoo_inputs",
        ],
    ),
    "bundles": (bundles, ["BundleDiscovery", "discover_coherent_bundle"]),
    "preparation": (
        preparation,
        ["format_expression_for_netzoo", "convert_expression_to_coexpression"],
    ),
    "artifacts": (
        artifact_validation,
        ["ARTIFACT_WRITE_ACTIONS", "validate_output_artifacts"],
    ),
    "paths": (
        path_safety,
        [
            "condor_artifact_paths",
            "resolved_output_collisions",
            "validate_output_basename",
        ],
    ),
}


def test_data_is_a_package_with_final_owners():
    data = importlib.import_module("netzoo_agent_core.data")
    assert hasattr(data, "__path__")
    for name in (
        "paths",
        "table_validation",
        "inspection",
        "bundles",
        "preparation",
        "artifacts",
    ):
        importlib.import_module(f"netzoo_agent_core.data.{name}")


def test_legacy_data_facades_use_single_implementation_owners():
    for module_name, (facade, names) in OWNER_EXPORTS.items():
        owner = importlib.import_module(f"netzoo_agent_core.data.{module_name}")
        assert facade.__all__ == names
        for name in names:
            assert getattr(facade, name) is getattr(owner, name)


def test_executor_reexports_moved_inspection_names():
    inspection = importlib.import_module("netzoo_agent_core.data.inspection")
    assert execution._expression_sample_count is inspection.expression_sample_count
    assert (
        execution._inspect_condor_inputs_impl
        is inspection.inspect_condor_inputs_impl
    )


def test_data_modules_do_not_depend_on_orchestration_or_executor():
    forbidden = {"execution", "planning", "evaluation", "graph", "cli"}
    for module_name in (
        "paths",
        "table_validation",
        "inspection",
        "bundles",
        "preparation",
        "artifacts",
    ):
        module = importlib.import_module(f"netzoo_agent_core.data.{module_name}")
        tree = ast.parse(inspect.getsource(module))
        relative_imports = {
            (node.module or "").split(".", 1)[0]
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.level >= 1
        }
        assert relative_imports.isdisjoint(forbidden), module_name
