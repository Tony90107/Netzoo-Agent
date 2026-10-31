"""A refusal that only says "couldn't match" asks the stated data condition first
(docs/research-log/declined-conditions-2026-10-31/ROUND.md). Off by default: NETZOO_DECLINED_CONDITIONS=shadow records
what it would do, =on applies it.

j9 A31 (DRAGON on layers from different patients), A39 (CONDOR on a gene-gene edge list): the capability check credits
nothing and records no reason, so the turn is DECLINE `full_gap` with the layer-2 line only, while the guard's typed
data check -- which names the real contract line -- runs only on a DO. Here, on such a DECLINE, the workflows the
request names (else Jev's result pick) go through the guard's own `check_typed_data`; when it rules them all out, the
turn becomes the guard's own data confirm (`conditioned_core`, built as for a DO). A bound "yes" then declines with the
confirmed line through the merged answer path (confirmed-reason-2026-10-30); a "no" leaves the next turn to the
pipeline. Code never writes the reason; nothing else changes; any failure leaves the DECLINE as it came.
"""

from __future__ import annotations

import os

from ..contracts.core_decision import CoreDecision
from ..interpretation.reason_layers import is_unmatched
from ..method_names import registered_workflows, workflows_in
from .context import record_event
from .jev_guard_call import (THRESHOLD, RESULT_NONE, asked_sentences, check_result, check_typed_data,
                             condition_asked, conditioned_core, result_menu)

__all__ = ["apply_declined_conditions", "declined_conditions_mode", "generic_decline", "named_candidates"]

BASES = ("full_gap", "all_results_not_available")


def declined_conditions_mode() -> str:
    mode = os.environ.get("NETZOO_DECLINED_CONDITIONS", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def generic_decline(core: CoreDecision) -> bool:
    """A result-level DECLINE whose every declined line is the layer-2 'couldn't match' one (no verified reason)."""
    return (core.kind == "DECLINE" and core.basis in BASES and bool(core.declined)
            and all(is_unmatched(part.line) for part in core.declined))


def named_candidates(task: str) -> list[str]:
    """The registered workflows the request names, in the registry's spelling (`method_names.workflows_in`)."""
    known = registered_workflows()
    return [name for name in workflows_in(task) if name in known]


def apply_declined_conditions(context, state, core: CoreDecision, user_task: str) -> CoreDecision:
    mode = declined_conditions_mode()
    if mode == "off" or not generic_decline(core) or condition_asked(state.get("task_state")):
        return core
    record = {"mode": mode, "kind_before": core.kind, "basis_before": core.basis}
    try:
        candidates, source = named_candidates(user_task), "named"
        if not candidates:
            pick = check_result(user_task)
            record["pick"] = pick
            name = pick.get("result")
            candidates = [name] if name in result_menu() and name not in RESULT_NONE \
                and pick.get("confidence", 0) >= THRESHOLD else []
            source = "jev_result"
        record |= {"candidates": candidates, "source": source}
        if not candidates:
            record["action"] = "no_candidate"
            record_event(context, state, "core.declined_conditions", "classify", record)
            return core
        typed = check_typed_data(user_task, candidates)
        as_do = core.model_copy(update={"kind": "DO", "workflows": list(candidates)})
        after, action = conditioned_core(as_do, typed, asked_sentences(state.get("task_state")))
        record |= {"typed": typed, "action": action}
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the DECLINE stands as it came
        record |= {"action": "not_run", "error": f"{type(error).__name__}: {error}"[:200]}
        record_event(context, state, "core.declined_conditions", "classify", record)
        return core
    if action != "ask":
        record_event(context, state, "core.declined_conditions", "classify", record)
        return core
    evidence = {**after.evidence, "jev_condition": {**after.evidence["jev_condition"], "kind_before": core.kind,
                                                    "basis_before": core.basis},
                "declined_conditions": {"declined": [part.model_dump() for part in core.declined]}}
    after = after.model_copy(update={"evidence": evidence})
    record |= {"applied": mode == "on", "question": after.facts[0].question,
               "contract": after.facts[0].contract_quote}
    record_event(context, state, "core.declined_conditions", "classify", record)
    return after if mode == "on" else core
