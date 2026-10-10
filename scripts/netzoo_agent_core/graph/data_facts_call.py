"""The data-facts call: what the request says about its TF priors and miRNA data (Logs 376, 380).

Log 380 (plan item 4): asked after routing when a listed workflow needs a TF
motif prior and a PPI network, or miRNA data, that the request does not bind
as files. The model reads what the words mean; each quote is checked only for
being in the request (Logs 373-374: word lists judging meaning failed both
ways). When the call is not configured, blocked by the budget or fails,
nothing is read and every reader keeps the request's own words.
"""

from __future__ import annotations

import re
import time

from pydantic import BaseModel

from ..contracts import AgentState, LLMUsage
from ..contracts.data_facts import DataFactsProposal
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..contracts import HumanMessage, SystemMessage
from ..llm import append_llm_usage
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from ..routing.study_purpose_verify import _locate
from .capability_check_call import with_reading_allowance
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["DATA_FACTS_SYSTEM", "build_data_facts_messages", "invoke_data_facts", "verify_data_facts"]


# Log 376: its own small call, so the study-purpose prompt stays as it is. Log 380 adds miRNA;
# the prompt lives beside its call (llm.py reached its size bound).
DATA_FACTS_SYSTEM = (
    "Return only the DataFactsProposal structure for the user's request.\n\n"
    "priors -- whether the request says it has prior knowledge of transcription-factor binding (a motif or "
    "binding-site prior, a TF-target list) or of protein-protein interactions:\n"
    "- stated: it says it has them, or one of them.\n"
    "- ruled_out: it says it does not have them, or that it has only expression data.\n"
    "- unstated: it says neither.\n"
    "priors_span -- the words that say so, copied exactly from the request without translation; empty when "
    "unstated.\n\n"
    "mirna -- whether the request says it has microRNA data (a miRNA list, miRNA expression or miRNA-target "
    "predictions):\n"
    "- stated: it says it has them.\n"
    "- ruled_out: it says it does not have them, or that it has only other data.\n"
    "- unstated: it says neither.\n"
    "mirna_span -- the words that say so, copied exactly from the request without translation; empty when "
    "unstated."
)


def build_data_facts_messages(user_task: str) -> list:
    """Ask what the request says about its TF priors, with a quote (Log 376)."""
    return [
        SystemMessage(content=DATA_FACTS_SYSTEM),
        HumanMessage(content=user_task[-ROUTER_CONTEXT_MAX_CHARS:]),
    ]


def _in_own_current_words(task: str, span: str) -> bool:
    """Whether the quote lies in the user's own, current statement (Log 381).

    The authority-bearing text of plan item 1 (`admissible_request_text`)
    leaves out reported speech, quotations and what happened before. Log 380
    read a supervisor's "we need a motif prior" (T1) and another cohort's
    "JASPAR motifs and a STRING network" from last year (T2) as data the user
    has: the quote was in the request, but not in the user's own account of
    this data. Punctuation is ignored, because that text is split at commas.
    """
    from ..routing.request_scope import admissible_request_text

    words = re.findall(r"\w+", span)
    pattern = r"\W+".join(re.escape(word) for word in words)
    return bool(words) and re.search(pattern, admissible_request_text(task), re.IGNORECASE) is not None


def verify_data_facts(task: str, proposal: DataFactsProposal) -> tuple[dict, list[dict]]:
    """The state entry for a proposal: each reading stands when its quote is in the request, else unstated.

    A "stated" reading also needs its quote in the user's own, current words (Log 381).
    """
    entry, rejected = {"source": "model"}, []
    for field in ("priors", "mirna"):
        value, span = getattr(proposal, field), getattr(proposal, f"{field}_span")
        if value != "unstated" and _locate(task, span) is None:
            rejected.append({"field": field, "value": value, "reason": "quote_not_in_request"})
            value = "unstated"
        elif value == "stated" and not _in_own_current_words(task, span):
            rejected.append({"field": field, "value": value, "reason": "not_in_own_current_words"})
            value = "unstated"
        entry[field] = value
        entry[f"{field}_quote"] = span.strip() if value != "unstated" else ""
    return entry, rejected


def invoke_data_facts(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    usage: LLMUsage,
    budget_warnings: list[str],
) -> tuple[dict | None, LLMUsage, list[str]]:
    """The verified data facts of the request, or None when nothing read them."""
    # The same model as the study-purpose call, which the graph binds (`study_purpose_llm`).
    llm = getattr(context, "study_purpose_llm", None)
    if llm is None:
        return None, usage, budget_warnings
    messages = build_data_facts_messages(user_task)
    input_text = _serialized_structured_input(messages, DataFactsProposal)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    # Log 403: the reading allowance the check has (`with_reading_allowance`).
    budget, budget_warnings = preflight_budget(
        with_reading_allowance(context, usage), call_state, role="data_facts",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return None, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    result = None
    try:
        adapter = llm.with_structured_output(
            DataFactsProposal, method="function_calling", include_raw=True, strict=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        proposal = DataFactsProposal.model_validate(payload)
        output_text = proposal.model_dump_json()
        call_status = "success"
        result, rejected = verify_data_facts(user_task, proposal)
        record_event(context, state, "routing.data_facts_detected", "classify", {
            "proposal": proposal.model_dump(), "rejected": rejected, **result,
        })
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.data_facts_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
        })
    usage = append_llm_usage(
        usage, role="data_facts", model=context.semantic_model_name,
        response=raw, input_text=input_text, output_text=output_text,
        budget_tokens=context.task_token_budget,
        duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
        status=call_status, price_catalog=context.price_catalog,
    )
    return result, usage, budget_warnings
