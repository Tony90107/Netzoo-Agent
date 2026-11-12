"""Chat-layer gaps found by driving the seven new methods through the CLI (2026-11-09 tests, fixed 2026-11-10)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scorpion_io  # noqa: E402
from netzoo_agent_core.cli.clarification import (  # noqa: E402
    ClarificationInputError, clarification_continuation, parse_clarification_assignments,
)
from netzoo_agent_core.contracts import FollowUpContext, InputEvidence, NextTurnPrompt, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine  # noqa: E402
from netzoo_agent_core.engine.task_updates import after_turn  # noqa: E402
from netzoo_agent_core.interpretation.extraction import _task_path  # noqa: E402
from netzoo_agent_core.prior_request import prior_decision  # noqa: E402
from netzoo_agent_core.reply_cards.answer_buttons import ask_choices  # noqa: E402
from netzoo_agent_core.routing.path_tokens import output_directory, tenx_directories  # noqa: E402

SCORPION_PROSE = (
    "I have single-cell RNA-seq counts in data/scorpion-toy/counts_10x with cell metadata "
    "data/scorpion-toy/cell_metadata.tsv. Build one gene regulatory network per donor and region with motif "
    "data/scorpion-toy/motif_prior.tsv and PPI data/scorpion-toy/ppi.tsv, then compare tumour (region T) against "
    "normal (region N). Output to tmp/x/scorpion"
)


# --- 1. a 10x directory named in prose is the single-cell matrix; the metadata stays metadata -------------------------

def test_a_10x_directory_in_prose_binds_as_the_cell_matrix():
    assert tenx_directories(SCORPION_PROSE, ROOT) == ["data/scorpion-toy/counts_10x"]
    assert _task_path(SCORPION_PROSE, "cell_expression_file") == "data/scorpion-toy/counts_10x"
    assert _task_path(SCORPION_PROSE, "cell_metadata_file") == "data/scorpion-toy/cell_metadata.tsv"


def test_a_folder_without_a_matrix_is_not_read_as_10x(tmp_path):
    (tmp_path / "plain").mkdir()
    assert tenx_directories("counts in plain/ and in missing/dir", tmp_path) == []


def test_a_metadata_table_given_as_the_matrix_says_so():
    errors = scorpion_io.scan_cell_matrix(ROOT / "data" / "scorpion-toy" / "cell_metadata.tsv").errors
    assert errors and "looks like a cell metadata" in errors[0] and "finite" not in errors[0]


# --- 3. "output to <folder>" is the output folder ----------------------------------------------------------------------

def test_output_to_a_folder_is_read_for_every_workflow():
    porcupine = ("Run PORCUPINE on the sample-specific networks in data/n.txt with the pathways in data/p.gmt, "
                 "output to tmp/a/porcupine")
    assert _task_path(porcupine, "output_dir") == "tmp/a/porcupine"
    assert _task_path(porcupine, "output_file") is None  # one folder, not also a file (live r7: output roles collided)
    assert _task_path("Run PANDA on data/e.tsv, output to tmp/x/panda.tsv", "output_file") == "tmp/x/panda.tsv"
    assert output_directory("Find pathways. Save the results to tmp/a/porcupine") == "tmp/a/porcupine"
    assert output_directory("Run PANDA and write it to /data/out/panda.tsv") is None  # a file, not a folder
    sponge = prior_decision("Build the motif and PPI priors with SPONGE for the TFs MYC, MAX and SOX2, output to tmp/a/sponge")
    assert sponge.output_dir == "tmp/a/sponge"


# --- 4. PORCUPINE: answers keep the request's files; a yes is not a path; an answer button binds ---------------------

def _porcupine_plan():
    decision = TaskDecision(action="run_porcupine", in_scope=True, should_execute=True, intent_type="run_analysis",
                            confidence=0.9, reason="Run PORCUPINE.")
    return WorkflowPlan(workflow="PORCUPINE", objective="Run PORCUPINE.", decision=decision.model_dump(),
                        status="needs_input", missing_inputs=["output_dir"], evidence=[
        InputEvidence(field="sample_network_file", status="provided", value="data/n.txt", reason="given"),
        InputEvidence(field="pathway_file", status="discovered", value="data/p.gmt", reason="named, role inferred"),
        InputEvidence(field="output_dir", status="missing", reason="Give the path of output_dir"),
    ])


def test_answering_the_output_folder_keeps_the_files_the_request_gave():
    task = clarification_continuation(_porcupine_plan(), {"output_dir": "tmp/a/porcupine"})
    assert "sample_network_file is data/n.txt" in task and "pathway_file is data/p.gmt" in task
    assert "output_dir is tmp/a/porcupine" in task
    assert "CARRIED_DISCOVERED_FIELD=pathway_file." in task  # still awaiting its content confirmation
    assert "CARRIED_DISCOVERED_FIELD=sample_network_file" not in task


def test_a_yes_or_no_is_never_a_path():
    for reply in ("y", "No", "yes."):
        try:
            parse_clarification_assignments(_porcupine_plan(), reply, selected={}, target_field="output_dir")
        except ClarificationInputError as error:
            assert "needs a path" in str(error)
        else:
            raise AssertionError(f"{reply!r} was accepted as a path")


def test_typing_no_on_a_yes_no_card_binds_the_answer(monkeypatch):
    """Live 2026-11-09 e6: a typed "no" matched the "No" button and went on unbound; the confirm was asked again."""
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    confirm = FactQuestion(question="Before I go ahead, please confirm: is the data you will use a co-expression "
                                    "matrix? (yes or no)", workflows=["PORCUPINE"],
                           contract_quote="PORCUPINE incompatible_input_artifacts: coexpression_network",
                           depends_on="jev:condition")
    core = CoreDecision(kind="ASK", basis="jev_condition", facts=[confirm], workflows=["PORCUPINE"])
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    recorder = Mock()
    recorder.start_run.return_value = "7f0e9a2c-0000-4000-8000-000000000001"
    runtime = bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()), project_policy=Mock(),
        session_id="s", resume_id=None, conversation=[], pending_plan=None, active_usage=None, run_id=None,
        recorder=recorder, trace_store=Mock(), ensure_trace_sync=lambda _run_id: None, app=object(),
        input_func=Mock(), invoke_graph_turn_func=Mock(), reply_resolver=Mock())
    machine = ConversationMachine(SimpleNamespace(task=None), runtime)
    state = machine.state
    state.task_state = after_turn(None, {"decision": {"core": core.model_dump(mode="json")}}, "Find pathways ...")
    state.next_prompt = NextTurnPrompt(kind="clarify_outcome", question=confirm.question)
    state.follow_up_context = FollowUpContext(prior_user_goal="Find pathways ...", prompt_kind="clarify_outcome",
                                              prompt_question=confirm.question)
    state.reply_card = {"choices": ask_choices(core).model_dump(mode="json")}
    machine._submit_main("no")
    assert [(fact.what, fact.value) for fact in state.task_state.facts] == [("jev:condition", "no")]
    assert state.pending_task  # the turn goes on with the answer
    assert recorder.start_run.called and recorder.append.call_args[0][0] == state.run_id  # live e6 rerun: run_id was None


# --- SCORPION: groups and comparison stated in words, read against the metadata -----------------------------------

def test_scorpion_groups_and_comparison_are_read_from_words():
    from netzoo_agent_core.data.scorpion_grouping import stated_grouping
    meta = "data/scorpion-toy/cell_metadata.tsv"
    assert stated_grouping(SCORPION_PROSE, meta) == {
        "group_by": ["donor", "region"], "compare_by": "region", "group1": "T", "group2": "N"}
    assert stated_grouping("One network for each cell type.", meta) == {"group_by": ["cell_type"]}
    # Words that name no column or value are never guessed into one.
    assert stated_grouping("Build networks per patient and compare tumor versus normal.", meta) == {}
    assert stated_grouping("Build one network from all cells.", meta) == {}
    assert stated_grouping(SCORPION_PROSE, None) == {}


def test_scorpion_decision_carries_the_stated_groups():
    from netzoo_agent_core.interpretation.hydration import hydrate_router_decision
    decision = TaskDecision(action="run_scorpion", in_scope=True, should_execute=True, intent_type="run_analysis",
                            confidence=0.9, reason="Run SCORPION.")
    hydrated = hydrate_router_decision(decision, SCORPION_PROSE)
    assert (hydrated.group_by, hydrated.compare_by, hydrated.group1, hydrated.group2) == (
        ["donor", "region"], "region", "T", "N")
    explicit = hydrate_router_decision(decision, SCORPION_PROSE + " group_by=donor")
    assert explicit.group_by == ["donor"]  # an assignment wins over the words


# --- a request that says where to save its results asks for them now ------------------------------------------------

def test_saving_results_to_a_folder_is_a_run_request():
    from netzoo_agent_core.routing.capability import reconcile_request_mode
    goal = ("Find which pathways vary coherently across my sample-specific networks in data/n.txt, using the pathways "
            "in data/p.gmt. Save the results to tmp/a/porcupine")
    assert reconcile_request_mode(goal, "answer") == "execute"
    assert reconcile_request_mode("How do I save the results to tmp/x?", "answer") == "answer"
    assert reconcile_request_mode("Find pathways and save the results.", "answer") == "answer"  # no location


# --- a failed tool says why ------------------------------------------------------------------------------------------

def test_a_crash_reports_its_reason_not_a_generic_failure():
    from netzoo_agent_core.routing.results import crash_reason
    raw = ("Command: `run-sponge`\nExit code: 1\n\nSTDERR:\nTraceback (most recent call last):\n  File \"x\", line 1\n"
           "ValueError: No objects to concatenate\nException ignored in: <function f>\n"
           "Traceback (most recent call last):\n  File \"y\"\nFileNotFoundError: [Errno 2] fingerprint.yaml\n")
    assert crash_reason(raw) == "ValueError: No objects to concatenate"
    assert crash_reason("Exit code: 1\n\nSTDERR:\nSPONGE did not create: motif_prior.tsv\n") == \
        "SPONGE did not create: motif_prior.tsv"
    assert crash_reason("Exit code: 0\n") is None


def test_sponge_skips_a_tf_track_with_no_site_at_the_threshold(monkeypatch):
    import types
    import pandas as pd
    calls = []
    fake = types.ModuleType("sponge.modules.utils.tfbs_filtering")
    fake.process_motif = lambda motif_df, bed_df, n_processes=1: calls.append(len(motif_df)) or pd.DataFrame(
        {"score": [500], "transcript": ["t1"]})
    for name, module in (("sponge", types.ModuleType("sponge")), ("sponge.modules", types.ModuleType("sponge.modules")),
                         ("sponge.modules.utils", types.ModuleType("sponge.modules.utils")),
                         ("sponge.modules.utils.tfbs_filtering", fake)):
        monkeypatch.setitem(sys.modules, name, module)
    sys.modules["sponge.modules.utils"].tfbs_filtering = fake
    import run_sponge
    skipped = run_sponge._skip_empty_tracks()
    empty = fake.process_motif(pd.DataFrame(columns=["chrom", "start", "end", "score"]), pd.DataFrame())
    assert empty.empty and list(empty.columns) == ["score", "transcript"] and len(skipped) == 1 and calls == []
    assert len(fake.process_motif(pd.DataFrame({"chrom": ["chr1"], "start": [1], "end": [2], "score": [500]}),
                                  pd.DataFrame())) == 1 and calls == [1]


def test_the_scorpion_plan_says_which_networks_it_builds():
    from netzoo_agent_core.data.scorpion_grouping import scorpion_plan_lines
    assert scorpion_plan_lines({"group_by": ["donor", "region"], "compare_by": "region", "group1": "T",
                                "group2": "N"}) == [
        "- One network per donor x region (cell metadata columns)",
        "- Compared: region T vs N (testEdges; log2 fold change is the first minus the second)"]
    assert scorpion_plan_lines({}) == ["- One network from all cells (no grouping column set)"]


def test_a_tf_without_edges_is_reported_as_a_warning(tmp_path):
    import json
    from netzoo_agent_core.data.artifacts import validate_output_artifacts
    (tmp_path / "motif_prior.tsv").write_text("MYC\tNPM1\t1\n")
    (tmp_path / "ppi_prior.tsv").write_text("MYC\tMYC\t1.0\n")
    (tmp_path / "manifest.json").write_text(json.dumps({"summary": {
        "motif_edges": 1, "requested_tfs_without_motif_edges": ["MAX"]}}))
    decision = TaskDecision(action="build_priors", in_scope=True, should_execute=True, intent_type="prepare_input",
                            confidence=1.0, reason="SPONGE", output_dir=str(tmp_path))
    check = validate_output_artifacts("build_priors", decision)
    assert check.ok and any("MAX" in warning and "JASPAR motif" in warning for warning in check.warnings)
