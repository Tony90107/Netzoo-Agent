from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.planning as planning  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402


def _plan_digest(plan) -> str:
    payload = json.dumps(
        plan.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


PLANNING_CASES = (
    (
        "respond_only",
        TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=0.99,
            reason="Explain PANDA.",
        ),
        "Explain PANDA.",
        "8a90e5eb0ae7412dd492867b4e4f62b16a10c0c364ce181813dc55f95ffffade",
    ),
    (
        "retrieval",
        TaskDecision(
            action="web_search",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Find current PANDA references.",
            web_query="current PANDA references",
        ),
        "Search the web for current PANDA references.",
        "3002acd9eebcce0114110e98620a1f6c0b74f82f2a28c72ff28c4cc906ee486b",
    ),
    (
        "explicit_panda",
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Run supplied PANDA inputs.",
        ),
        (
            "Run PANDA with expression_file=data/study/expression.tsv "
            "motif_file=data/study/motif.tsv ppi_file=data/study/ppi.tsv "
            "output_file=outputs/study/panda.tsv"
        ),
        "14e28c7aef73fdaa791174ba182b4d7037cc033429b9217fa35434d0d2541bd6",
    ),
)


@pytest.mark.parametrize(("case_name", "decision", "task", "expected"), PLANNING_CASES)
def test_planning_model_dump_is_characterized(case_name, decision, task, expected):
    before = decision.model_dump(mode="json")
    plan = planning.build_workflow_plan(decision, task)

    assert _plan_digest(plan) == expected, case_name
    assert decision.model_dump(mode="json") == before


PUBLIC_EXPORTS = ["build_workflow_plan", "render_plan"]


def test_planning_is_responsibility_oriented_package():
    assert hasattr(planning, "__path__")
    for module_name in ("builder", "rendering"):
        importlib.import_module(f"netzoo_agent_core.planning.{module_name}")


def test_planning_public_surface_is_preserved():
    assert planning.__all__ == PUBLIC_EXPORTS
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(planning, name)
