"""Bounded retries and a preflight reservation for evidence-backed fact checks.

The reservation changes projected optional-call cost, never the shared allowance
or the usage ledger. A skipped optional read therefore cannot spend the turn.
"""
from __future__ import annotations

import os

from ..contracts import HumanMessage, SystemMessage
from ..contracts.fact_check import FactProposals
from ..interpretation.fact_check import FACT_INSTRUCTIONS, fact_candidates, fact_messages_text
from ..llm import _estimated_tokens
from .structured_calls import _serialized_structured_input


def retryable_check_error(error: BaseException) -> bool:
    """Retry structured decoding or temporary transport/provider errors, once.

    Configuration, authentication and programmer errors do not become retries.
    Provider exception classes are checked without requiring a particular SDK.
    """
    code = getattr(error, "status_code", None)
    if isinstance(code, int):
        return code in (408, 409, 429) or 500 <= code <= 599
    if isinstance(error, (ValueError, TimeoutError, ConnectionError)):
        return True
    return bool({base.__name__ for base in type(error).__mro__} & {
        "APITimeoutError", "APIConnectionError", "TimeoutException", "TransportError",
    })


def capability_max_tokens(model) -> int:
    """The check model's output cap: OPENROUTER_CAPABILITY_MAX_TOKENS when set; else 4,000 for OpenAI's gpt-4o family
    and 16,000 for any other model (sized for nemotron's reasoning, up to 12,906, Log 414). check-reserve (2026-10-28):
    gpt-4o-mini's largest of 840 checks was 2,258, and the 16,000 reserve refused 65 optional calls."""
    given = os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS")
    if given:
        return int(given)
    return 4000 if str(model or "").startswith("openai/gpt-4o") else 16000


def check_output_reserve(context, llm) -> int:
    """Match the output cap actually bound by the check-model factory."""
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if llm is not getattr(context, "study_purpose_llm", None) and own:
        return capability_max_tokens(own)
    return context.router_max_tokens


def fact_check_input(task: str, actions: list[str], policy) -> tuple[list, str]:
    """The same serialized prompt for reservation, preflight and actual use."""
    messages = [SystemMessage(content=FACT_INSTRUCTIONS),
                HumanMessage(content=fact_messages_text(task, actions, policy))]
    return messages, _serialized_structured_input(messages, FactProposals)


def required_fact_check_reserve(context, user_task: str, decision, proposal=None, *, fact_llm=None) -> int:
    """Reserve one fact read only for an independently witnessed deciding doubt.

    A registered candidate alone does not require a fact call. When the early
    reading is supplied, use only its code-validated quotes to establish a doubt.
    """
    policy = getattr(context, "project_policy", None)
    llm = fact_llm if fact_llm is not None else getattr(context, "study_purpose_llm", None)
    if policy is None or llm is None:
        return 0
    check = decision.capability_check
    if proposal is not None:
        from ..interpretation.capability_check import build_capability_check

        check, _ = build_capability_check(user_task, proposal)
        decision = decision.model_copy(update={"capability_check": check})
    if check is None or not (check.uncertain_quotes or check.needed_facts()):
        return 0
    actions = fact_candidates(decision, policy)
    if not actions:
        return 0
    _, text = fact_check_input(user_task, actions, policy)
    output_reserve = check_output_reserve(context, llm)
    # The routing caller supplies its selected fact LLM. Older direct callers
    # can still reserve conservatively from config without importing call nodes.
    own = os.environ.get("OPENROUTER_CAPABILITY_MODEL")
    if (fact_llm is None and os.environ.get("NETZOO_FACT_MODEL", "router") == "check"
            and own and own != getattr(context, "semantic_model_name", None)):
        output_reserve = capability_max_tokens(own)
    return _estimated_tokens(text) + output_reserve
