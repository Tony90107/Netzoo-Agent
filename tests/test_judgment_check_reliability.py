"""Required judgment calls retain bounded recovery and their own budget reservation."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement
from netzoo_agent_core.graph import capability_check_call as capability
from netzoo_agent_core.graph import fact_check_call as fact
from netzoo_agent_core.policy import ProjectPolicyLoader

TASK = "Run BONOBO. I don't know whether my expression values were centered."
DOUBT = "I don't know whether my expression values were centered"


class Answers:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = 0

    def with_structured_output(self, schema, **kwargs):
        return self

    def invoke(self, messages):
        answer = self.answers[self.calls]
        self.calls += 1
        if isinstance(answer, BaseException):
            raise answer
        return answer


@pytest.fixture
def policy():
    return ProjectPolicyLoader(Path(__file__).parents[1]).load()


@pytest.fixture(autouse=True)
def no_trace(monkeypatch):
    monkeypatch.delenv("OPENROUTER_CAPABILITY_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_CAPABILITY_EXTRA_TOKENS", raising=False)
    monkeypatch.delenv("NETZOO_FACT_MODEL", raising=False)
    monkeypatch.setattr(fact, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(capability, "record_event", lambda *a, **kw: None)


def context(policy, llm, budget=30000):
    return SimpleNamespace(study_purpose_llm=llm, semantic_model_name="openai/gpt-4o-mini",
                           router_max_tokens=1000, task_token_budget=budget, project_policy=policy,
                           price_catalog=None, recorder=SimpleNamespace(append=lambda *a: None))


def decision(uncertain=True):
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run BONOBO", kind="result", status="available", delivered_by=["bonobo.per_sample_networks"])],
        uncertain_quotes=[DOUBT] if uncertain else [])
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                        reason="r", matched_actions=["run_bonobo"], capability_check=check)


@pytest.mark.parametrize("error", [TimeoutError("temporary provider timeout"), ValueError("bad structure")])
def test_fact_check_retries_once_then_records_success(policy, error):
    llm = Answers(error, {"facts": []})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert checked.status == "checked" and llm.calls == 2
    assert [call.status for call in usage.calls] == ["failed", "success"]


def test_fact_check_never_retries_more_than_once(policy):
    llm = Answers(TimeoutError("first"), TimeoutError("second"), {"facts": []})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert checked.status == "failed" and llm.calls == 2
    assert checked.candidates == ["BONOBO"]
    assert len(usage.calls) == 2


def test_fact_check_permanent_provider_error_is_not_retried(policy):
    error = RuntimeError("unauthorized")
    error.status_code = 401
    llm = Answers(error, {"facts": []})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert checked.status == "failed" and llm.calls == 1
    assert checked.candidates == ["BONOBO"]


def test_fact_check_does_not_reopen_exhausted_usage(policy):
    llm = Answers({"facts": []})
    usage = LLMUsage(budget_tokens=60000, total_tokens=60000, budget_exhausted=True)  # A3: spent, not refused once
    checked, returned, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), usage, [])
    assert checked.status == "blocked" and checked.candidates == ["BONOBO"]
    assert returned is usage and llm.calls == 0


def test_fact_check_stops_retry_when_preflight_reservation_no_longer_fits(policy, monkeypatch):
    calls = []

    def preflight(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status="allowed" if len(calls) == 1 else "blocked"), []

    monkeypatch.setattr(fact, "preflight_budget", preflight)
    llm = Answers(ValueError("bad structure"), {"facts": []})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert checked.status == "blocked" and llm.calls == 1
    assert len(usage.calls) == 1 and usage.calls[0].status == "failed"


def test_capability_retry_cannot_reopen_usage_exhausted_by_first_attempt(policy, monkeypatch):
    def exhaust(usage, **kwargs):
        usage.total_tokens, usage.budget_exhausted = usage.budget_tokens, True  # A3: the first attempt spent the turn
        return usage

    monkeypatch.setattr(capability, "append_llm_usage", exhaust)
    monkeypatch.setattr(capability, "preflight_budget", lambda *a, **kw: (SimpleNamespace(status="allowed"), []))
    llm = Answers(ValueError("bad structure"), ValueError("must not call twice"))
    _, usage, _, status = capability.request_capability_check(context(policy, llm), {}, "Run BONOBO", LLMUsage(), [])
    assert status == "blocked" and usage.budget_exhausted and llm.calls == 1


def test_fact_check_fatal_cancellation_is_never_retried(policy):
    llm = Answers(KeyboardInterrupt(), {"facts": []})
    with pytest.raises(KeyboardInterrupt):
        fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert llm.calls == 1


def test_required_reserve_exists_only_with_verified_doubt_and_candidate(policy):
    from netzoo_agent_core.graph.required_check_budget import required_fact_check_reserve

    ctx = context(policy, Answers())
    reserve = required_fact_check_reserve(ctx, TASK, decision())
    assert ctx.router_max_tokens < reserve < ctx.task_token_budget
    assert required_fact_check_reserve(ctx, TASK, decision(uncertain=False)) == 0
    unrelated = decision().model_copy(update={"matched_actions": [], "capability_check": None})
    assert required_fact_check_reserve(ctx, TASK, unrelated) == 0
    assert required_fact_check_reserve(context(policy, None), TASK, decision()) == 0


@pytest.mark.parametrize("module_name, function_name", [
    ("study_purpose_call", "invoke_study_purpose"), ("data_facts_call", "invoke_data_facts")])
def test_reserved_required_check_skips_optional_read_without_spending_turn(policy, monkeypatch, module_name, function_name):
    from importlib import import_module
    from netzoo_agent_core.graph.required_check_budget import required_fact_check_reserve

    module = import_module("netzoo_agent_core.graph." + module_name)
    monkeypatch.setattr(module, "record_event", lambda *a, **kw: None)
    llm = Answers()
    ctx = context(policy, llm)
    reserve = required_fact_check_reserve(ctx, TASK, decision())
    # Leave room for the required fact check, not for it plus an advisory read.
    usage = LLMUsage(total_tokens=60000 - 1500 - reserve)
    _, usage, _ = getattr(module, function_name)(ctx, {"required_check_reserve": reserve}, TASK, usage, [])
    assert llm.calls == 0 and not usage.budget_exhausted and not usage.calls
    llm.answers = [{"facts": []}]
    checked, usage, _ = fact.request_fact_check(ctx, {}, TASK, decision(), usage, [])
    assert checked.status == "checked" and llm.calls == 1


@pytest.mark.parametrize("kind", ["capability", "fact"])
def test_invalid_provider_reply_retains_actual_usage_and_prevents_retry(policy, kind):
    raw = SimpleNamespace(usage_metadata={"input_tokens": 59999, "output_tokens": 1, "total_tokens": 60000},
                          response_metadata={}, tool_calls=[])
    llm = Answers({"parsed": None, "raw": raw, "parsing_error": ValueError("bad response")})
    ctx = context(policy, llm)
    if kind == "capability":
        _, usage, _, status = capability.request_capability_check(ctx, {}, "Run BONOBO", LLMUsage(), [])
    else:
        checked, usage, _ = fact.request_fact_check(ctx, {}, TASK, decision(), LLMUsage(), [])
        status = checked.status
    assert status == "blocked" and usage.budget_exhausted and llm.calls == 1
    assert usage.calls[0].usage_provenance == "actual" and usage.total_tokens == 60000


def test_fact_check_with_no_candidate_remains_optional(policy):
    llm = Answers()
    no_candidate = decision().model_copy(update={"matched_actions": [], "capability_check": None})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, no_candidate, LLMUsage(), [])
    assert checked.status == "not_run" and llm.calls == 0 and not usage.calls


def test_capability_transient_failure_retries_at_most_once(policy):
    llm = Answers(TimeoutError("first"), TimeoutError("second"), {})
    _, usage, _, status = capability.request_capability_check(context(policy, llm), {}, "Run BONOBO", LLMUsage(), [])
    assert status == "failed" and llm.calls == 2
    assert [call.status for call in usage.calls] == ["failed", "failed"]


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
def test_nontransient_provider_validation_or_auth_error_is_not_retried(policy, status_code):
    error = ValueError("invalid request or authentication")
    error.status_code = status_code
    llm = Answers(error, {"facts": []})
    checked, _, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), LLMUsage(), [])
    assert checked.status == "failed" and llm.calls == 1


def test_preflight_honors_own_models_actual_output_cap(policy, monkeypatch):
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "test/check")
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MAX_TOKENS", "16000")
    monkeypatch.setenv("NETZOO_FACT_MODEL", "check")
    own_llm = Answers({"facts": []})
    monkeypatch.setattr(capability, "_own_llm", lambda *a: own_llm)
    ctx = context(policy, Answers())
    # A 16k output reservation cannot fit in 15k remaining reading allowance.
    usage = LLMUsage(total_tokens=45000)
    checked, _, _ = fact.request_fact_check(ctx, {}, TASK, decision(), usage, [])
    assert checked.status == "blocked" and own_llm.calls == 0


def test_early_proposal_reserve_rejects_invented_unknown_quote(policy):
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.graph.required_check_budget import required_fact_check_reserve

    schema = proposal_model(2)
    reading = {"role": "background", "has": [], "about_methods": [], "asks": []}
    data = schema(s1=reading, s2=reading).model_dump()
    ctx = context(policy, Answers())
    data["conditions"]["unknown_facts"] = [{"quote": DOUBT, "about": "other"}]
    assert required_fact_check_reserve(ctx, TASK, decision(uncertain=False), schema.model_validate(data)) > 0
    data["conditions"]["unknown_facts"] = [{"quote": "I have no clue about cell types", "about": "other"}]
    assert required_fact_check_reserve(ctx, TASK, decision(), schema.model_validate(data)) == 0


def test_reservation_can_use_selected_check_llm_without_importing_call_nodes(policy, monkeypatch):
    from netzoo_agent_core.graph.required_check_budget import required_fact_check_reserve

    ctx = context(policy, Answers())
    ordinary = required_fact_check_reserve(ctx, TASK, decision())
    monkeypatch.setenv('NETZOO_FACT_MODEL', 'check')
    monkeypatch.setenv('OPENROUTER_CAPABILITY_MODEL', 'test/check')
    monkeypatch.setenv('OPENROUTER_CAPABILITY_MAX_TOKENS', '16000')
    selected = required_fact_check_reserve(ctx, TASK, decision(), fact_llm=Answers())
    assert selected - ordinary == 15000
    assert required_fact_check_reserve(ctx, TASK, decision()) == selected
