"""check-enum-limit-2026-10-28 (ROUND.md): the check's own model routed to OpenAI takes the compact schema over the
1,000-enum limit, as the backup always did."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.strict_schema import expanded_enum_values  # noqa: E402
from netzoo_agent_core.graph import capability_check_call as call  # noqa: E402

FIVE = " ".join(f"Sentence {index} asks for a TF-gene network." for index in range(1, 6))
FOUR = " ".join(f"Sentence {index} asks for a TF-gene network." for index in range(1, 5))


class Recording:
    def __init__(self, seen):
        self.seen = seen

    def with_structured_output(self, schema, **kwargs):
        self.seen.append(expanded_enum_values(schema.model_json_schema()))
        return self

    def invoke(self, messages):
        raise ValueError("Semantic structured output could not be decoded")


def _context(monkeypatch, own_model: str, seen: list):
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", own_model)
    monkeypatch.setattr(call, "_own_llm", lambda model, tokens: Recording(seen))
    monkeypatch.setattr(call, "preflight_budget", lambda context, state, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(call, "append_llm_usage", lambda usage, **kwargs: usage)
    return SimpleNamespace(study_purpose_llm=object(), semantic_model_name="openai/gpt-4o-mini",
                           router_max_tokens=1000, task_token_budget=30000, price_catalog=None)


def test_the_own_openai_model_reads_a_five_sentence_request_with_the_compact_schema(monkeypatch):
    seen = []
    context = _context(monkeypatch, "openai/gpt-4o-mini-2024-07-18", seen)
    call.request_capability_check(context, {}, FIVE, LLMUsage(budget_tokens=30000), [])
    assert seen and seen[0] <= 1000  # the first attempt, the one that failed live (6 of 6)


def test_a_short_request_and_a_model_not_on_openai_keep_the_full_schema(monkeypatch):
    seen = []
    context = _context(monkeypatch, "openai/gpt-4o-mini-2024-07-18", seen)
    call.request_capability_check(context, {}, FOUR, LLMUsage(budget_tokens=30000), [])
    assert seen[0] > 400  # four sentences: 907, under the limit, not compacted
    other = []
    context = _context(monkeypatch, "nvidia/nemotron-3-super-120b-a12b:free", other)
    call.request_capability_check(context, {}, FIVE, LLMUsage(budget_tokens=30000), [])
    assert other[0] > 1000


def test_the_reread_takes_the_compact_schema_over_the_limit(monkeypatch):
    seen = []
    context = _context(monkeypatch, "openai/gpt-4o-mini-2024-07-18", seen)
    passages = [f"Passage {index} asks for a network." for index in range(1, 9)]
    call.request_capability_reread(context, {}, " ".join(passages), passages, LLMUsage(budget_tokens=30000), [])
    assert seen and seen[0] <= 1000


# --- check-reserve-2026-10-28 (ROUND.md): the check model's output cap fits gpt-4o-mini ---------------------------

def test_the_output_cap_is_4000_for_gpt4o_and_unchanged_otherwise(monkeypatch):
    from netzoo_agent_core.graph.required_check_budget import capability_max_tokens, check_output_reserve

    monkeypatch.delenv("OPENROUTER_CAPABILITY_MAX_TOKENS", raising=False)
    assert capability_max_tokens("openai/gpt-4o-mini-2024-07-18") == 4000
    assert capability_max_tokens("nvidia/nemotron-3-super-120b-a12b:free") == 16000
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MAX_TOKENS", "9000")
    assert capability_max_tokens("openai/gpt-4o-mini-2024-07-18") == 9000
    monkeypatch.delenv("OPENROUTER_CAPABILITY_MAX_TOKENS")
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "openai/gpt-4o-mini-2024-07-18")
    context = SimpleNamespace(study_purpose_llm=object(), router_max_tokens=1200)
    assert check_output_reserve(context, object()) == 4000
    assert check_output_reserve(context, context.study_purpose_llm) == 1200


def test_the_own_llm_is_built_with_the_same_cap(monkeypatch):
    built = []
    monkeypatch.delenv("OPENROUTER_CAPABILITY_MAX_TOKENS", raising=False)
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "openai/gpt-4o-mini-2024-07-18")
    monkeypatch.setattr(call, "_own_llm", lambda model, tokens: built.append(tokens) or object())
    call._check_model(SimpleNamespace(study_purpose_llm=object(), semantic_model_name="openai/gpt-4o-mini"))
    assert built == [4000]
