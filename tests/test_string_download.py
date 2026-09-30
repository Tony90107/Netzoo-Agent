"""STRING acquisition intent, clarification, and atomic curl boundaries."""

from __future__ import annotations

import gzip
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace

from netzoo_agent_core import settings
from netzoo_agent_core.cli.clarification import (
    clarification_continuation,
    clarification_prompt,
    parse_clarification_assignments,
)
from netzoo_agent_core.contracts import OutcomeEvidence, OutcomeHypothesis, RequestedOutcome
from netzoo_agent_core.contracts import LLMUsage
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.evaluation import evaluate_workflow_plan
from netzoo_agent_core.planning import build_workflow_plan
from netzoo_agent_core.routing.capability import reconcile_request_mode
from netzoo_agent_core.string_download import (
    continued_string_download_decision,
    download_string,
    requested_network_kind,
    requested_species,
    string_download_decision,
)


def _interpretation(operation: str = "acquire", mode: str = "execute") -> SemanticInterpretation:
    return SemanticInterpretation(
        request_mode=mode,
        semantic_goal="Get an existing STRING network",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=RequestedOutcome(operation=operation, artifact_type="regulatory_network", granularity="unknown"),
            confidence=0.9,
        )],
    )


def test_string_acquisition_routes_by_semantic_operation() -> None:
    task = "我想要下載gene regulatory network (string)"
    decision = string_download_decision(task, _interpretation())
    assert decision is not None
    assert decision.action == "download_string"
    assert decision.taxon is None
    assert decision.string_network_type == "regulatory"
    recovered = string_download_decision(task, _interpretation("infer"))
    assert recovered is not None and recovered.action == "download_string"
    assert recovered.requested_outcome.operation == "acquire"
    assert string_download_decision(task, _interpretation(mode="guidance")) is None
    assert string_download_decision("download a regulatory network", _interpretation()) is None
    assert string_download_decision("Download STRING protein sequences", _interpretation()) is None
    assert string_download_decision("下載 STRING 物種清單", _interpretation()) is None
    assert string_download_decision("How do I download a STRING network?", _interpretation()) is None
    assert string_download_decision("I do not want to download a STRING network", _interpretation()) is None
    assert reconcile_request_mode("How do I download a STRING network?", "guidance") == "guidance"


def test_graph_selects_string_acquisition_before_scientific_workflow_match(monkeypatch) -> None:
    from netzoo_agent_core.graph import router_invocation
    from netzoo_agent_core.policy import ProjectPolicyLoader
    from netzoo_agent_core.tracing import NullTraceRecorder

    def semantic(_context, _state, _task, usage):
        return _interpretation(), usage, [], None, frozenset()

    monkeypatch.setattr(router_invocation, "_invoke_semantic_interpreter", semantic)
    context = SimpleNamespace(
        task_token_budget=20_000,
        project_policy=ProjectPolicyLoader(settings.PROJECT_ROOT).load(),
        recorder=NullTraceRecorder(),
    )
    result = router_invocation.invoke_router(
        context, {"token_usage": LLMUsage().model_dump()},
        "我想要下載gene regulatory network (string)",
    )
    assert result.decision.action == "download_string"
    assert result.decision.matched_actions == ["download_string"]
    assert result.decision.should_execute

    monkeypatch.setattr(router_invocation, "_invoke_semantic_interpreter",
                        lambda _context, _state, _task, usage: (
                            _interpretation("infer"), usage, [], None, frozenset(),
                        ))
    recovered = router_invocation.invoke_router(
        context, {"token_usage": LLMUsage().model_dump()},
        "我想要下載gene regulatory network (string)",
    )
    assert recovered.decision.action == "download_string"
    assert recovered.decision.requested_outcome.operation == "acquire"


def test_router_recovers_live_acquisition_reading_and_asks_missing_details(monkeypatch) -> None:
    from netzoo_agent_core.graph import router_invocation
    from netzoo_agent_core.policy import ProjectPolicyLoader
    from netzoo_agent_core.tracing import NullTraceRecorder

    task = "我要下載 STRING 網路"
    live_reading = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Download STRING network data",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=RequestedOutcome(
                operation="acquire", artifact_type="unknown",
                granularity="not_applicable",
            ),
            confidence=1.0,
            evidence=[OutcomeEvidence(
                dimension="operation", source="explicit", value="acquire",
                text_span=task,
                rationale="The user wants to download existing data.",
            )],
        )],
    )

    monkeypatch.setattr(
        router_invocation, "_invoke_semantic_interpreter",
        lambda _context, _state, _task, usage: (
            live_reading, usage, [], None, frozenset(),
        ),
    )
    context = SimpleNamespace(
        task_token_budget=20_000,
        project_policy=ProjectPolicyLoader(settings.PROJECT_ROOT).load(),
        recorder=NullTraceRecorder(),
    )

    result = router_invocation.invoke_router(
        context, {"token_usage": LLMUsage().model_dump()}, task,
    )

    assert result.decision.action == "download_string"
    assert result.decision.requested_outcome.operation == "acquire"
    plan = build_workflow_plan(result.decision, task)
    assert plan.status == "needs_input"
    assert plan.missing_inputs == ["taxon", "string_network_type"]


def test_species_and_network_clarification_returns_to_same_download() -> None:
    task = "我想要下載gene regulatory network (string)"
    decision = string_download_decision(task, _interpretation())
    plan = build_workflow_plan(decision, task)
    assert plan.status == "needs_input" and plan.missing_inputs == ["taxon"]
    continuation = clarification_continuation(plan, {"taxon": "Homo sapiens"})
    resumed = continued_string_download_decision(continuation)
    assert resumed is not None and resumed.taxon == "Homo sapiens"
    assert resumed.string_network_type == "regulatory"
    ready = build_workflow_plan(resumed, continuation)
    assert ready.status == "ready"
    assert evaluate_workflow_plan(ready, continuation).status == "approved"


def test_species_and_type_parsing_does_not_default_network_type() -> None:
    assert requested_species("下載 STRING 的人類調控網路") == "9606"
    assert requested_species("Download STRING for mouse") == "10090"
    assert requested_network_kind("Download STRING for mouse") is None
    assert requested_network_kind("Download STRING physical and regulatory") is None


def test_missing_network_type_asks_and_accepts_a_listed_choice() -> None:
    task = "Download STRING network for mouse"
    decision = string_download_decision(task, _interpretation())
    plan = build_workflow_plan(decision, task)
    assert plan.missing_inputs == ["string_network_type"]
    assert "functional, physical, or regulatory" in clarification_prompt(plan)
    selected = parse_clarification_assignments(plan, "2", target_field="string_network_type")
    resumed = continued_string_download_decision(clarification_continuation(plan, selected))
    assert resumed is not None and resumed.string_network_type == "physical"


def test_existing_local_file_skips_repeat_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    existing = tmp_path / "data" / "string" / "9606.protein.regulatory.links.v12.5.txt.gz"
    existing.parent.mkdir(parents=True)
    with gzip.open(existing, "wt", encoding="utf-8") as output:
        output.write("protein1 protein2 combined_score\n9606.ENSP1 9606.ENSP2 900\n")
    monkeypatch.setattr(settings, "EXECUTE_TOOLS", True)
    result = download_string.invoke({
        "taxon": "human", "string_network_type": "regulatory", "output_dir": str(tmp_path / "new"),
    })
    assert "already exists locally" in result
    assert str(existing) in result
    assert not (tmp_path / "new").exists()


def test_invalid_existing_file_is_reported_without_overwrite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(settings, "EXECUTE_TOOLS", True)
    existing = tmp_path / "data" / "9606.protein.links.v12.5.txt.gz"
    existing.parent.mkdir()
    existing.write_bytes(b"partial")
    result = download_string.invoke({
        "taxon": "9606", "string_network_type": "functional", "output_dir": str(existing.parent),
    })
    assert result.startswith("Error: A file named")
    assert existing.read_bytes() == b"partial"


def test_curl_download_is_atomic_and_validated(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(settings, "EXECUTE_TOOLS", True)
    from netzoo_agent_core import string_download as module

    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        assert command[0] == "curl"
        assert command[-1] == module._download_url("9606", "regulatory")
        target = Path(command[command.index("--output") + 1])
        with gzip.open(target, "wt", encoding="utf-8") as output:
            output.write("protein1 protein2 combined_score\n")
            output.write("9606.ENSP1 9606.ENSP2 900\n")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    result = download_string.invoke({
        "taxon": "9606", "string_network_type": "regulatory", "output_dir": str(tmp_path / "data"),
    })
    expected = tmp_path / "data" / "9606.protein.regulatory.links.v12.5.txt.gz"
    assert "Downloaded STRING regulatory" in result
    assert expected.is_file()
    assert commands and "--proto-redir" in commands[0]
    assert not list((tmp_path / "data").glob("*.part"))


def test_curl_failure_leaves_no_download_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(settings, "EXECUTE_TOOLS", True)
    from netzoo_agent_core import string_download as module

    monkeypatch.setattr(
        module.subprocess, "run",
        lambda command, **kwargs: CompletedProcess(command, 22, "", "HTTP 404"),
    )
    target = tmp_path / "data"
    result = download_string.invoke({
        "taxon": "9606", "string_network_type": "regulatory", "output_dir": str(target),
    })
    assert result.startswith("Error: STRING download failed")
    assert list(target.iterdir()) == []
