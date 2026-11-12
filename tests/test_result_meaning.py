"""The result reading shown in Description: curated per workflow, files named from the run's own records."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.bootstrap import load_project_policy  # noqa: E402
from netzoo_agent_core.framework_compat import HumanMessage  # noqa: E402
from netzoo_agent_core.operation_summary import build_operation_summary  # noqa: E402
from netzoo_agent_core.result_meaning import MEANINGS, describe_files, meaning_for, next_analyses  # noqa: E402
from workflow_registry import RUN_ACTIONS  # noqa: E402


def test_every_run_workflow_has_a_reading_with_a_source():
    for action in RUN_ACTIONS:
        meaning = MEANINGS[action]
        assert meaning.about and meaning.read and meaning.limits, action
        assert meaning.sources and all(url.startswith("https://") for _, url in meaning.sources), action


def test_names_from_the_contracts_find_their_reading():
    policy = load_project_policy()
    for action, spec in policy.workflows.items():
        assert meaning_for(spec.workflow) == (action, MEANINGS[action]), spec.workflow


def test_next_analyses_come_from_the_contracts():
    policy = load_project_policy()
    panda = next_analyses("run_panda", policy)
    assert {"workflow": "CONDOR", "relation": "can take this result as input",
            "description": policy.workflows["run_condor"].description} in panda
    assert any(item["workflow"] == "LIONESS-PANDA" and item["relation"].startswith("per-sample") for item in panda)
    assert next_analyses("run_panda", None) == []


def test_a_written_file_is_named_by_its_plan_role_and_its_header_is_read(tmp_path):
    network = tmp_path / "toy-panda.tsv"
    network.write_text("tf\tgene\tmotif\tforce\nAHR\tA1\t1.0\t2.9\n", encoding="utf-8")
    evidence = [{"field": "output_file", "value": str(network), "status": "defaulted"}]
    [entry] = describe_files("run_panda", [str(network)], evidence, planned=False)
    assert entry["title"] == "Cohort TF-to-gene network"
    assert entry["written"] is True and entry["bytes"] > 0
    assert entry["columns"][3] == {"name": "force", "meaning": "PANDA edge score"}
    assert entry["columns"][2]["meaning"] == "1 if the edge was in the motif prior, 0 if not"


def test_a_headerless_file_shows_its_first_row_not_fake_columns(tmp_path):
    prior = tmp_path / "motif_prior.tsv"
    prior.write_text("SOX2\tGENE1\t1\nMYC\tGENE2\t1\n", encoding="utf-8")
    [entry] = describe_files("build_priors", [str(prior)], [], planned=False)
    assert entry["title"].startswith("Motif prior")
    assert entry["first_row"] == ["SOX2", "GENE1", "1"] and "columns" not in entry


def test_a_header_with_numeric_sample_names_is_still_a_header(tmp_path):
    table = tmp_path / "lioness.tsv"
    table.write_text("regulator\tgene\tprior_weight\t1\t2\nTF1\tGeneA\t1.0\t0.84\t0.92\n", encoding="utf-8")
    evidence = [{"field": "lioness_output", "value": str(table), "status": "provided"}]
    [entry] = describe_files("run_lioness_puma", [str(table)], evidence, planned=False)
    assert entry["title"].startswith("Sample-specific networks")
    assert [column["name"] for column in entry["columns"]] == ["regulator", "gene", "prior_weight", "1", "2"]


def test_fixed_names_and_unknown_files(tmp_path):
    files = describe_files("run_condor", ["out/condor-tar_memb.tsv", "out/manifest.json", "out/extra.bin"], [],
                           planned=False)
    assert [entry["title"] for entry in files] == [
        "Community of each target gene", "Run record: the inputs, settings and checks this run used",
        "CONDOR result file"]
    assert all("columns" not in entry for entry in files)  # not on disk: nothing is claimed about the content


def test_a_preview_lists_the_planned_paths_unwritten():
    evidence = [{"field": "output_file", "value": "outputs/a.tsv", "status": "defaulted"},
                {"field": "lioness_output", "value": "outputs/b.tsv", "status": "defaulted"},
                {"field": "expression_file", "value": "data/x.tsv", "status": "provided"}]
    files = describe_files("run_lioness_panda", [], evidence, planned=True)
    assert [(entry["path"], entry["written"]) for entry in files] == [("outputs/a.tsv", False), ("outputs/b.tsv", False)]
    assert files[0]["title"] == "Cohort PANDA network (all samples)"


def _state(tools, status="completed", plan_status="ready"):
    return {
        "messages": [HumanMessage(content="Run PANDA on the toy data")],
        "decision": {"action": "run_panda", "core": {"kind": "DO", "workflows": ["PANDA"]}},
        "plan": {"workflow": "PANDA", "status": plan_status, "steps": [{"action": "run_panda", "purpose": "Run."}],
                 "evidence": [{"field": "output_file", "value": "outputs/s/toy-panda.tsv", "status": "defaulted"}]},
        "tool_results": tools, "evaluation": {"status": status},
    }


def test_the_summary_carries_meaning_files_next_steps_and_caveats():
    policy = load_project_policy()
    tools = [{"action": "run_panda", "status": "success", "artifacts": ["/work/outputs/s/toy-panda.tsv"],
              "warnings": ["genes accepted as test-only identifiers because Synthetic Test mode is enabled."]}]
    summary = build_operation_summary(_state(tools), {}, policy)
    [meaning] = summary["meaning"]
    assert meaning["workflow"] == "PANDA" and meaning["role"] == "ran"
    assert meaning["sources"][0]["url"] == "https://netzoo.github.io/zooanimals/panda/panda/"
    assert any(item["workflow"] == "CONDOR" for item in meaning["next"])
    assert summary["files"][0]["path"] == "outputs/s/toy-panda.tsv"
    assert summary["files"][0]["title"] == "Cohort TF-to-gene network"
    assert summary["caveats"][0].startswith("Synthetic Test mode was on")
    assert summary["files"][0]["tags"] == ["method:PANDA", "result:network", "scale:cohort", "mode:synthetic test"]


def test_a_preview_explains_the_planned_files_and_says_nothing_was_written():
    tools = [{"action": "run_panda", "status": "dry_run", "artifacts": []}]
    summary = build_operation_summary(_state(tools), {}, load_project_policy())
    assert summary["meaning"][0]["role"] == "previewed"
    assert summary["files"] == [{"path": "outputs/s/toy-panda.tsv", "title": "Cohort TF-to-gene network",
                                 "read": "One row per TF-gene edge with its PANDA score.", "written": False,
                                 "workflow": "PANDA", "tags": ["method:PANDA", "result:network", "scale:cohort"]}]
    assert summary["caveats"] == ["Dry run: the files listed are where the run will write; nothing has been written yet."]


def test_a_choice_between_methods_explains_each_candidate_without_files():
    state = {"messages": [HumanMessage(content="Per-sample networks please")],
             "decision": {"action": "no_tool", "core": {"kind": "DO", "workflows": ["LIONESS-PANDA", "LIONESS-PUMA"]}},
             "plan": {"workflow": "none", "status": "respond_only", "steps": []}}
    summary = build_operation_summary(state, {"reply_kind": "outcome_clarification"}, load_project_policy())
    assert [(item["workflow"], item["role"]) for item in summary["meaning"]] == [
        ("LIONESS-PANDA", "considered"), ("LIONESS-PUMA", "considered")]
    assert summary["files"] == []


def test_answers_and_declines_carry_no_method_reading():
    state = {"messages": [HumanMessage(content="Predict drug response")],
             "decision": {"action": "no_tool", "core": {"kind": "DECLINE", "workflows": []}},
             "plan": {"workflow": "none", "status": "respond_only", "steps": []}}
    summary = build_operation_summary(state, {}, load_project_policy())
    assert summary["meaning"] == [] and summary["files"] == [] and summary["caveats"] == []


def test_a_run_waiting_on_its_inputs_has_its_method_selected_not_considered():
    state = _state([], status="", plan_status="needs_confirmation")
    summary = build_operation_summary(state, {"reply_kind": "input_confirmation"}, load_project_policy())
    assert summary["outcome"] == "needs_confirmation"
    assert [(item["workflow"], item["role"]) for item in summary["meaning"]] == [("PANDA", "selected")]
