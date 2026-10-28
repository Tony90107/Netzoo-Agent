"""Harness repair A3 (ROUND-A.md): an optional call refused at preflight does not spend the turn for the required reads.

Live P5 M09 lost its capability check (A t3, E t1, E' t2: a refused selection-conditions call, discriminator or intent
router at 22.7-26.8k of 30k) or its fact check (D t3, E' t3: a refused second opinion at 42.6-44.7k of 60k). Each refusal
set `usage.budget_exhausted`, and the check and the fact check took that flag as a spent turn. They now look at what
the turn's calls spent (`spent`); a turn routing really spent still keeps its own budget (Log 394), and every call still
passes its own preflight.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph import capability_check_call as capability  # noqa: E402
from netzoo_agent_core.graph import fact_check_call as fact  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

TASK = "Run BONOBO. I don't know whether my expression values were centered."
DOUBT = "I don't know whether my expression values were centered"
READING = {"s1": {"role": "background", "has": [], "about_methods": [], "asks": []},
           "s2": {"role": "background", "has": ["my expression values"], "about_methods": [], "asks": []}}


class Answers:
    def __init__(self, *answers):
        self.answers, self.calls, self.schemas = list(answers), 0, []

    def with_structured_output(self, schema, **kwargs):
        self.schemas.append(schema)
        return self

    def invoke(self, messages):
        answer = self.answers[self.calls]
        self.calls += 1
        if answer == "reading":
            return {"parsed": self.schemas[-1].model_validate(READING), "raw": None, "parsing_error": None}
        return answer


@pytest.fixture
def policy():
    return ProjectPolicyLoader(Path(__file__).parents[1]).load()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for name in ("OPENROUTER_CAPABILITY_MODEL", "OPENROUTER_CAPABILITY_EXTRA_TOKENS", "NETZOO_FACT_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(fact, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(capability, "record_event", lambda *a, **kw: None)


def context(policy, llm):
    return SimpleNamespace(study_purpose_llm=llm, semantic_model_name="openai/gpt-4o-mini", router_max_tokens=1000,
                           task_token_budget=30000, project_policy=policy, price_catalog=None,
                           recorder=SimpleNamespace(append=lambda *a: None))


def decision():
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run BONOBO", kind="result", status="available", delivered_by=["bonobo.per_sample_networks"])],
        uncertain_quotes=[DOUBT])
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        matched_actions=["run_bonobo"], capability_check=check)


def refused(total: int, budget: int) -> LLMUsage:
    """A turn where an optional call was refused at preflight: flagged, not spent."""
    usage = LLMUsage(budget_tokens=budget, total_tokens=total)
    usage.budget_exhausted = True
    return usage


@pytest.mark.parametrize("total, budget, is_spent", [
    (26760, 30000, False), (30000, 30000, True), (42645, 75000, False), (75000, 75000, True), (0, 30000, False)])
def test_spent_is_what_the_calls_used_not_the_flag(total, budget, is_spent):
    assert capability.spent(refused(total, budget)) is is_spent


def test_a_refused_routing_call_leaves_the_check_to_run_with_its_allowance(policy, monkeypatch):
    budgets = []

    def preflight(ctx, state, **kwargs):
        budgets.append(ctx.task_token_budget)
        return SimpleNamespace(status="allowed"), []

    monkeypatch.setattr(capability, "preflight_budget", preflight)
    llm = Answers("reading")
    proposal, _, _, status = capability.request_capability_check(
        context(policy, llm), {}, TASK, refused(26760, 30000), [])  # M09 E t1
    assert proposal is not None and status == "ok" and llm.calls == 1 and budgets == [75000]


def test_routing_that_spent_the_turn_still_skips_the_check(policy):
    """Log 394 unchanged: the allowance never reopens a spent turn."""
    llm = Answers("reading")
    _, _, _, status = capability.request_capability_check(context(policy, llm), {}, TASK, refused(30000, 30000), [])
    assert status == "blocked" and llm.calls == 0
    assert capability.with_reading_allowance(context(policy, llm), refused(30000, 30000)).task_token_budget == 30000


def test_a_refused_second_opinion_leaves_the_fact_check_to_run(policy):
    llm = Answers({"facts": []})
    checked, usage, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), refused(42645, 75000), [])
    assert checked.status == "checked" and llm.calls == 1  # M09 E' t3
    assert usage.budget_tokens == 75000  # recorded against the allowance


def test_the_fact_check_still_passes_its_own_preflight(policy):
    """A flag no longer blocks it, but its own reservation does: 58k + its input + output exceeds 60k - 1.5k."""
    llm = Answers({"facts": []})
    checked, _, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), refused(73000, 75000), [])
    assert checked.status == "blocked" and llm.calls == 0


def test_a_turn_whose_allowance_was_spent_skips_the_fact_check(policy):
    llm = Answers({"facts": []})
    checked, _, _ = fact.request_fact_check(context(policy, llm), {}, TASK, decision(), refused(75000, 75000), [])
    assert checked.status == "blocked" and llm.calls == 0
