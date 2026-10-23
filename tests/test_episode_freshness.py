"""Harness repair P4 (ROUND-P4.md, spec 9, A16 and A19): which files an episode used, and whether they still are.

A reused path is a candidate, never an earlier result: its reason says what is the same (by sha256 only), what changed
(content, the input checks, the contract or the policy), what was never fingerprinted, and what was checked now.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.memory import Episode, InputRevision  # noqa: E402
from netzoo_agent_core.data.artifact_revision import freshness, revision, step_revisions  # noqa: E402
from netzoo_agent_core.interpretation.episode_reuse import reusable_episode_inputs  # noqa: E402
from netzoo_agent_core.memory.normalization import compact_episode_payload  # noqa: E402

POLICY = SimpleNamespace(policy_hash="p1", workflows={})


@pytest.fixture()
def files(tmp_path):
    expression = tmp_path / "expr.tsv"
    design = tmp_path / "design.tsv"
    expression.write_text("gene\ts1\ts2\ts3\nA\t1\t2\t3\n")
    design.write_text("sample\tgroup\ns1\ta\ns2\tb\ns3\ta\n")
    return expression, design


def _same_size_edit(path: Path) -> None:
    """New content, same size, mtime put back: only the sha256 can tell."""
    stat = path.stat()
    text = path.read_text()
    path.write_text(text.replace("1", "9", 1))
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert path.stat().st_size == stat.st_size and path.stat().st_mtime_ns == stat.st_mtime_ns


def test_the_same_path_with_other_content_is_changed_even_at_the_same_size_and_mtime(files):
    expression, _ = files
    old = revision(expression.resolve(), "run_cobra", POLICY)
    assert freshness(old, str(expression), "run_cobra", POLICY)[0] == "unchanged"
    _same_size_edit(expression)
    assert freshness(old, str(expression), "run_cobra", POLICY) == ("changed", "its content changed since")


def test_a_changed_check_contract_or_policy_makes_the_earlier_check_stale(files):
    expression, _ = files
    old = revision(expression.resolve(), "run_cobra", POLICY)
    assert freshness(old, str(expression), "run_cobra", SimpleNamespace(policy_hash="p2", workflows={})) == (
        "rules_changed", "the content is the same, but the project policy changed since")
    stale_check = old.model_copy(update={"validator_hash": "an older input check"})
    assert "the input checks" in freshness(stale_check, str(expression), "run_cobra", POLICY)[1]
    spec = SimpleNamespace(model_dump_json=lambda: '{"action": "run_cobra", "version": 2}')
    assert "the workflow contract" in freshness(old, str(expression), "run_cobra",
                                                SimpleNamespace(policy_hash="p1", workflows={"run_cobra": spec}))[1]


def test_no_fingerprint_is_unverified_and_a_gone_file_is_missing(files):
    expression, _ = files
    old = revision(expression.resolve(), "run_cobra", POLICY)
    assert freshness(None, str(expression), "run_cobra", POLICY)[0] == "unverified"
    expression.unlink()
    assert freshness(old, str(expression), "run_cobra", POLICY)[0] == "missing"


def test_a_step_fingerprints_its_existing_input_files_and_never_outputs(files):
    expression, design = files
    decision = SimpleNamespace(expression_file=str(expression), design_file=str(design), output_dir="cobra_out",
                               taxon="human")
    found = step_revisions("run_cobra", decision, POLICY)
    assert sorted(found) == ["design_file", "expression_file"]
    assert found["expression_file"].path == str(expression.resolve()) and len(found["expression_file"].sha256) == 64


def _episode(files, *, status="completed", revisions=True) -> Episode:
    expression, design = files
    return Episode(episode_id="e1234567abcd", profile_id="p", task_summary="t", workflow="COBRA", action="run_cobra",
                   status=status, inputs={"expression_file": str(expression), "design_file": str(design)},
                   input_revisions={field: revision(path.resolve(), "run_cobra", POLICY)
                                    for field, path in (("expression_file", expression), ("design_file", design))}
                   if revisions else {})


def test_an_unchanged_reuse_says_so_and_never_claims_a_check_this_module_did_not_run(files):
    values, reason = reusable_episode_inputs("run_cobra", [_episode(files)], POLICY)
    assert values == {"expression_file": str(files[0]), "design_file": str(files[1])}
    assert "the files are the ones that run used (same sha256) and the rules are unchanged" in reason
    assert "they were not checked here; the plan's input checks run on them" in reason
    assert "Reused validated inputs" not in reason


def test_a_changed_file_is_still_offered_but_its_reason_says_what_changed(files):
    episode = _episode(files)
    _same_size_edit(files[0])
    _, reason = reusable_episode_inputs("run_cobra", [episode], POLICY)
    assert "expression_file: its content changed since" in reason and "design_file" not in reason


def test_an_episode_from_before_p4_keeps_its_candidate_as_unverified(files):
    """A19: no fingerprints -- still a candidate, never presented as checked then."""
    _, reason = reusable_episode_inputs("run_cobra", [_episode(files, revisions=False)], POLICY)
    assert reason.count("no fingerprint was recorded for it then") == 2


def test_dry_run_and_failed_episodes_are_never_reused_and_a_gone_file_is_not_offered(files):
    for status in ("dry_run", "failed"):
        assert reusable_episode_inputs("run_cobra", [_episode(files, status=status)], POLICY) is None
    episode = _episode(files)
    files[1].unlink()
    assert reusable_episode_inputs("run_cobra", [episode], POLICY) is None


def test_an_episode_saved_before_p4_loads_and_the_inspect_view_shows_the_fingerprints(files):
    old = Episode.model_validate({"episode_id": "e", "profile_id": "p", "task_summary": "t", "workflow": "COBRA",
                                  "status": "completed", "inputs": {"expression_file": "expr.tsv"}})
    assert old.input_revisions == {} and compact_episode_payload(old)["input_revisions"] == {}
    shown = compact_episode_payload(_episode(files))["input_revisions"]["expression_file"]
    assert len(shown["sha256"]) == 12 and shown["size"] == files[0].stat().st_size


def test_the_store_records_each_fields_fingerprint_from_the_execute_gate(files, tmp_path):
    from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan
    from netzoo_agent_core.contracts.planning import WorkflowStep
    from netzoo_agent_core.contracts.results import EvaluationResult, ToolExecutionResult
    from netzoo_agent_core.memory import EpisodeStore

    expression, design = files
    decision = TaskDecision(action="run_cobra", in_scope=True, should_execute=True, confidence=0.9, reason="r",
                            expression_file=str(expression), design_file=str(design), output_dir="cobra_out")
    plan = WorkflowPlan(workflow="COBRA", objective="o", decision=decision.model_dump(), status="ready",
                        steps=[WorkflowStep(action="run_cobra", purpose="p")])
    gate = {item.path: item.model_dump(mode="json") for item in step_revisions("run_cobra", decision, POLICY).values()}
    result = ToolExecutionResult(action="run_cobra", status="success", summary="ok")
    episode = EpisodeStore(root=tmp_path / "episodes").record(
        "p", "Run COBRA.", plan, [result], EvaluationResult(status="completed", reason="done"), input_revisions=gate)
    assert sorted(episode.input_revisions) == ["design_file", "expression_file"]
    assert isinstance(episode.input_revisions["design_file"], InputRevision)
