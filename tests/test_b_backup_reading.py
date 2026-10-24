"""Harness repair B (ROUND-B.md): a backup reading by the same model is a reading, not a provisional hold.

All 26 replay errors that were "only the backup read it" came from the nemotron era (25 undecodable replies, one 502).
Today the check's own model is openai/gpt-4o-mini-2024-07-18 and the backup openai/gpt-4o-mini: the same model, so a
backup read is as good as the own read and is no longer held. Another model, or the compact schema, is still held.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import capability_check_call as call  # noqa: E402

TASK = "Run BONOBO on my expression matrix."
READING = {"s1": {"role": "background", "has": ["my expression matrix"], "about_methods": [], "asks": []}}


class Fails:
    def with_structured_output(self, schema, **kwargs):
        return self

    def invoke(self, messages):
        raise ValueError("Semantic structured output could not be decoded")


class Reads:
    def __init__(self):
        self.schemas = []

    def with_structured_output(self, schema, **kwargs):
        self.schemas.append(schema)
        return self

    def invoke(self, messages):
        return {"parsed": self.schemas[-1].model_validate(READING), "raw": None, "parsing_error": None}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(call, "_own_llm", lambda model, max_tokens: Fails())
    monkeypatch.setattr(call, "preflight_budget", lambda *args, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)


def _check(monkeypatch, own: str):
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", own)
    backup = Reads()
    context = SimpleNamespace(study_purpose_llm=backup, semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    proposal, _usage, _warnings, status = call.request_capability_check(
        context, {}, TASK, LLMUsage(budget_tokens=30000), [])
    return proposal, status, backup


def test_the_same_model_under_its_dated_name_reads_as_well_as_the_check_itself(monkeypatch):
    proposal, status, backup = _check(monkeypatch, "openai/gpt-4o-mini-2024-07-18")
    assert proposal is not None and status == "ok" and len(backup.schemas) == 1


def test_another_model_as_backup_is_still_held(monkeypatch):
    proposal, status, _ = _check(monkeypatch, "nvidia/nemotron-3-super-120b-a12b:free")
    assert proposal is not None and status == "fallback"


def test_a_backup_read_with_the_compact_schema_is_still_held(monkeypatch):
    monkeypatch.setattr(call, "_ENUM_LIMIT", 10)
    proposal, status, backup = _check(monkeypatch, "openai/gpt-4o-mini-2024-07-18")
    assert proposal is not None and status == "fallback"
    assert backup.schemas[0] is not proposal_model(1)  # the compact shape, not the one the own model read


@pytest.mark.parametrize("a,b,same", [
    ("openai/gpt-4o-mini", "openai/gpt-4o-mini-2024-07-18", True),
    ("OpenAI/GPT-4o-mini-2024-07-18", "openai/gpt-4o-mini", True),
    ("nvidia/nemotron-3-super-120b-a12b:free", "openai/gpt-4o-mini", False),
    ("openai/gpt-4o", "openai/gpt-4o-mini", False),
    (None, "openai/gpt-4o-mini", False),
    ("", "", False),
])
def test_one_model_is_its_alias_and_its_dated_snapshot(a, b, same):
    assert call.same_model(a, b) is same
