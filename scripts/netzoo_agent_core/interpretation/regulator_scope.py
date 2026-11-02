"""A tie between a TF-only workflow and its miRNA extension, settled by the data the request states.

NETZOO_REGULATOR_SCOPE=on.

"I have RNA-seq from 50 tumors, a TF motif prior and a PPI network. I want a
regulatory network for each patient." When the reading left the regulators
open, routing tied LIONESS-PANDA with LIONESS-PUMA and asked "Which regulator
type should the network model: transcription factors, miRNA regulators, or
both?" (app session 07a68476; 5 of 13 runs of that sentence on 2026-11-02, the
other 8 matched LIONESS-PANDA). The request had already said what its regulator
evidence is.

The data-facts call reads what the request says it has (model meaning, each
quote checked only for being in the request, Logs 376-381). Code then drops a
candidate whose regulators are another candidate's plus miRNAs -- the same
result, scale and inputs otherwise (PUMA beside PANDA, LIONESS-PUMA beside
LIONESS-PANDA) -- when:
- the request states TF priors (`priors` stated) and no miRNA data (`mirna`
  not stated);
- no reading of the result names miRNA regulators;
- the request has no miRNA wording (the regulator-class witness; a veto only,
  so a false hit keeps today's question);
- the workflow was not named by the user, and no earlier turn chose it.

A tie left with one workflow becomes its match; a larger tie keeps its
question, recomputed without the dropped extension. Nothing is ruled out: the
extension is only not offered for data the request did not describe.
"""

from __future__ import annotations

import os
import re

from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_AXES

from .checked_match import _produces_readings
from .unmapped_routes import is_unmapped

__all__ = ["applied", "enabled", "mirna_extensions", "narrow_regulator_scope"]

_USER_CHOSEN = ("workflow_name", "confirmed_context")


def enabled() -> bool:
    return os.environ.get("NETZOO_REGULATOR_SCOPE", "off").strip().lower() == "on"


def _same_but_regulators(extension, base) -> bool:
    return (extension.artifact_type == base.artifact_type
            and set(extension.produced_artifacts or ()) == set(base.produced_artifacts or ())
            and set(extension.granularities) == set(base.granularities)
            and set(extension.input_artifacts) == set(base.input_artifacts))


def mirna_extensions(candidates) -> dict[str, str]:
    """Each candidate that is another candidate plus miRNA regulators, mapped to that base."""
    found = {}
    for action in candidates:
        extension = OUTPUT_CAPABILITIES.get(action)
        if extension is None or "mirna" not in extension.regulator_types:
            continue
        for other in candidates:
            base = OUTPUT_CAPABILITIES.get(other)
            if (other != action and base is not None
                    and set(base.regulator_types) == set(extension.regulator_types) - {"mirna"}
                    and _same_but_regulators(extension, base)):
                found[action] = other
                break
    return found


def _readings(decision):
    return [*([decision.requested_outcome] if decision.requested_outcome is not None else []),
            *(item.outcome for item in decision.outcome_hypotheses)]


def narrow_regulator_scope(decision, task: str):
    """The decision without the miRNA extensions its stated data does not describe, and those dropped."""
    facts = decision.data_facts or {}
    candidates = list(decision.hypothesis_actions)
    if (decision.action != "no_tool" or decision.matched_actions or len(candidates) < 2
            or decision.stated_hypotheses or is_unmapped(decision) or decision.match_basis in _USER_CHOSEN
            or facts.get("priors") != "stated" or facts.get("mirna") == "stated"
            or any("mirna" in outcome.regulator_types for outcome in _readings(decision))
            or re.search(SELECTION_AXES["regulator_class"]["witness"], task, re.I)):
        return decision, []
    dropped = list(mirna_extensions(candidates))
    if not dropped:
        return decision, []
    kept = [action for action in candidates if action not in dropped]
    advice = decision.advisory_recommendation
    update = {
        "hypothesis_actions": kept,
        "recommended_actions": [action for action in decision.recommended_actions if action not in dropped],
        "alternative_actions": [action for action in decision.alternative_actions if action not in dropped],
        "advisory_recommendation": None if advice is not None and advice.action in dropped else advice,
    }
    if len(kept) == 1:
        action = kept[0]
        reading = {} if _produces_readings(action, decision) else {"requested_outcome": None, "outcome_hypotheses": []}
        update.update({
            "matched_actions": [action], "recommended_actions": [action], "hypothesis_actions": [],
            "alternative_actions": [], "advisory_recommendation": None, "clarification_question": None,
            "capability_match_status": "exact", **reading,
        })
    else:
        from ..routing.clarification_planner import plan_clarification
        from ..graph.condition_recommender import unrecommended_question

        narrowed = decision.model_copy(update=update)
        planned = plan_clarification(kept, outcomes=[item.outcome for item in decision.outcome_hypotheses])
        update["clarification_question"] = planned.question if planned else unrecommended_question(narrowed)
    return decision.model_copy(update=update), dropped


def applied(decision, task: str, record):
    """The routing decision under NETZOO_REGULATOR_SCOPE; `record` gets the event payload when a candidate is dropped."""
    if not enabled():
        return decision
    narrowed, dropped = narrow_regulator_scope(decision, task)
    if dropped:
        record({"dropped": dropped, "kept": list(narrowed.matched_actions or narrowed.hypothesis_actions),
                "data_facts": narrowed.data_facts})
    return narrowed
