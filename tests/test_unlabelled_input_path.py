"""A file the request names without a role is the user's: it is bound or asked about, never replaced (2026-11-04).

"Run PANDA on /data/counts.tsv." bound nothing, because no role word ("expression", "motif", ...) labelled the path
and its name matched no role hint. The folder part of the path, `/data/`, was then read as a folder the user named,
so discovery searched it, found a partial bundle, and proposed `/data/log_expr.tsv` as the expression matrix -- a
file the user never named. A single named file fills the one role a workflow still lacks; otherwise the named files
are the only candidates offered and the user says which role each plays.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.cli.clarification import clarification_prompt  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings  # noqa: E402

VALID = ROOT / "data" / "auto-check-valid"
PANDA_INPUTS = ("expression_file", "motif_file", "ppi_file")


@pytest.fixture
def folder(tmp_path):
    """A folder holding the user's file next to a partial bundle that discovery would otherwise pick."""
    shutil.copy(VALID / "expression.tsv", tmp_path / "counts.tsv")
    shutil.copy(VALID / "expression.tsv", tmp_path / "log_expr.tsv")
    shutil.copy(VALID / "motif.tsv", tmp_path / "motif.tsv")
    shutil.copy(VALID / "ppi.tsv", tmp_path / "string_edges.tsv")
    return tmp_path


def _plan(task, action="run_panda"):
    decision = agent.TaskDecision(action=action, in_scope=True, should_execute=True, confidence=0.99,
                                  reason="formal run")
    plan = agent.build_workflow_plan(decision, task,
                                     profile=agent.UserProfile(profile_id="alice"),
                                     retrieved_episodes=[])
    return plan, {item.field: item for item in plan.evidence}


def _used(evidence):
    return {value for item in evidence.values() for value in [item.value, *item.candidates] if value}


def test_the_folder_of_a_named_file_is_not_a_folder_the_user_named(folder):
    selections = request_input_bindings(f"Run PANDA on {folder}/counts.tsv.")
    assert selections.values == {}
    assert selections.named_paths == (f"{folder}/counts.tsv",)
    assert selections.directory is None
    # A folder the request does name is still an anchor, also at the end of a sentence.
    assert request_input_bindings(f"Run PANDA on the files in {folder}/").directory == folder.resolve()
    assert request_input_bindings(f"Run PANDA on the files in {folder}/.").directory == folder.resolve()


def test_run_panda_on_one_unlabelled_path_asks_which_role_it_plays(folder):
    named = f"{folder}/counts.tsv"
    plan, evidence = _plan(f"Run PANDA on {named}.")
    assert plan.status == "needs_input"
    for field in PANDA_INPUTS:
        assert evidence[field].status == "missing" and evidence[field].value is None
        assert evidence[field].candidates == [named]
        assert f"names {named}; say whether it is {field}" in evidence[field].reason
    assert _used(evidence) - {evidence["output_file"].value} == {named}
    assert "log_expr.tsv" not in clarification_prompt(plan)


def test_two_unlabelled_paths_are_asked_about_not_guessed(folder):
    first, second = f"{folder}/counts.tsv", f"{folder}/string_edges.tsv"
    plan, evidence = _plan(f"Run PANDA on {first} and {second}.")
    assert plan.status == "needs_input"
    for field in PANDA_INPUTS:
        assert evidence[field].status == "missing" and evidence[field].value is None
        assert evidence[field].candidates == [first, second]
        assert "say which one is" in evidence[field].reason
    assert _used(evidence) - {evidence["output_file"].value} == {first, second}


def test_a_labelled_path_still_binds_and_anchors_discovery(folder):
    named = f"{folder}/counts.tsv"
    plan, evidence = _plan(f"Run PANDA with expression {named}.")
    assert (evidence["expression_file"].status, evidence["expression_file"].value) == ("provided", named)
    assert evidence["motif_file"].value == f"{folder}/motif.tsv"  # the provided file's folder is searched


def test_a_bare_name_resolved_to_the_same_folder_is_bound_not_pending(folder):
    expression = f"{folder}/counts.tsv"
    plan, evidence = _plan(f"Run PANDA with expression {expression}, and motif motif.tsv from the same folder.")
    assert evidence["motif_file"].value == f"{folder}/motif.tsv"
    assert not evidence["ppi_file"].reason.startswith("Your request names")  # the folder is still searched


def test_an_unlabelled_path_beside_a_labelled_one_stops_discovery(folder):
    expression, other = f"{folder}/counts.tsv", f"{folder}/string_edges.tsv"
    plan, evidence = _plan(f"Run PANDA with expression {expression} on {other}.")
    assert (evidence["expression_file"].status, evidence["expression_file"].value) == ("provided", expression)
    for field in ("motif_file", "ppi_file"):
        assert evidence[field].status == "missing" and evidence[field].candidates == [other]
    assert f"{folder}/motif.tsv" not in _used(evidence)


def test_one_unlabelled_path_fills_the_one_role_left_open(folder):
    expression, motif, other = (f"{folder}/{name}" for name in ("counts.tsv", "motif.tsv", "string_edges.tsv"))
    plan, evidence = _plan(f"Run PANDA with expression {expression} and motif {motif} on {other}.")
    assert (evidence["ppi_file"].status, evidence["ppi_file"].value) == ("provided", other)
    assert evidence["expression_file"].value == expression and evidence["motif_file"].value == motif


def test_a_demo_bundle_does_not_replace_an_unlabelled_path(folder):
    named = f"{folder}/counts.tsv"
    _plan_, evidence = _plan(f"Run a PANDA demo on {named}.")
    assert all(item.status != "demo_bundle" for item in evidence.values())
    assert all(evidence[field].value is None for field in PANDA_INPUTS)


def test_a_content_mapper_reads_only_the_named_file_and_its_role_awaits_confirmation(folder):
    named = folder / "counts.tsv"
    prompts = []

    class Mapper:
        def invoke(self, messages):
            prompts.append("\n".join(str(message.content) for message in messages))
            return {"assignments": [{"path": str(named), "role": "expression_file", "confidence": 0.9,
                                     "rationale": "Genes as rows, samples as columns."}]}

    decision = agent.TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=0.99,
                                  reason="formal run")
    plan = agent.build_workflow_plan(decision, f"Run PANDA on {named}.", profile=agent.UserProfile(profile_id="a"),
                                     retrieved_episodes=[], content_mapper=Mapper())
    evidence = {item.field: item for item in plan.evidence}
    assert len(prompts) == 1 and "counts.tsv" in prompts[0]
    assert all(name not in prompts[0] for name in ("log_expr.tsv", "motif.tsv", "string_edges.tsv"))
    assert evidence["expression_file"].value == str(named.resolve())
    assert evidence["expression_file"].status == "discovered"
    assert "Awaiting user confirmation" in evidence["expression_file"].reason
    for field in ("motif_file", "ppi_file"):
        assert evidence[field].status == "missing" and evidence[field].candidates == []
    assert plan.status == "needs_input"
