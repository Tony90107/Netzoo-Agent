from __future__ import annotations

import shutil
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.data.demo_provenance import (  # noqa: E402
    bundled_demo_authority_note,
    is_verified_bundled_demo,
)


PROJECT_ROOT = Path(__file__).parents[1]
LIONESS_ROOT = PROJECT_ROOT / "data" / "lioness-toy"


def _lioness_panda_inputs(root: Path = LIONESS_ROOT) -> dict[str, str]:
    return {
        "expression_file": str(root / "expression.tsv"),
        "motif_file": str(root / "motif-panda.tsv"),
        "ppi_file": str(root / "ppi.tsv"),
    }


def test_only_registered_files_with_matching_hashes_are_trusted(tmp_path):
    registered = _lioness_panda_inputs()
    assert is_verified_bundled_demo("run_lioness_panda", registered) is True

    copied_root = tmp_path / "lioness-toy"
    shutil.copytree(LIONESS_ROOT, copied_root)
    assert (
        is_verified_bundled_demo(
            "run_lioness_panda", _lioness_panda_inputs(copied_root)
        )
        is False
    )

    missing = dict(registered)
    missing.pop("ppi_file")
    assert is_verified_bundled_demo("run_lioness_panda", missing) is False


def test_bundled_demo_note_does_not_claim_biological_authority():
    note = bundled_demo_authority_note()

    assert "SHA-256" in note
    assert "demonstration only" in note
    assert "not biological evidence" in note


def test_registered_cobra_and_coexpression_demos_are_verified():
    assert is_verified_bundled_demo(
        "run_cobra",
        {
            "expression_file": "data/cobra-toy/expression.tsv",
            "design_file": "data/cobra-toy/design.tsv",
        },
    )
    assert is_verified_bundled_demo(
        "run_lioness_coexpression",
        {"expression_file": "data/lioness-toy/expression.tsv"},
    )


def test_offline_planner_can_select_the_registered_lioness_demo(monkeypatch, tmp_path):
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    decision = agent.TaskDecision(
        action="run_lioness_panda",
        in_scope=True,
        should_execute=True,
        confidence=0.99,
        reason="Run the bundled LIONESS-PANDA demo.",
    )

    plan = agent.build_workflow_plan(decision, "Run a LIONESS-PANDA demo once")

    assert plan.status == "needs_confirmation"
    assert plan.decision["expression_file"] == "data/lioness-toy/expression.tsv"
    assert plan.decision["motif_file"] == "data/lioness-toy/motif-panda.tsv"
    assert plan.decision["ppi_file"] == "data/lioness-toy/ppi.tsv"


def test_offline_runtime_accepts_only_the_registered_lioness_demo(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))

    result = agent.run_lioness_panda.invoke(
        {
            **_lioness_panda_inputs(),
            "output_file": "outputs/lioness-toy/panda.tsv",
            "lioness_output": "outputs/lioness-toy/lioness-panda.txt",
        }
    )

    assert "run-lioness panda" in result
    assert bundled_demo_authority_note() in result
