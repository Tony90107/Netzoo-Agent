"""What the request's own data can build, when no matched workflow can run on it (Log 312).

Test 2 of the ten-scenario doc: "microarray expression profiles from 40 heart
failure patients ... reconstruct a separate regulatory network for each
patient". Every matched workflow also needs inputs the request never names (a
motif prior and a PPI network; or, from an unquoted second reading, a second
omics layer), while two registered workflows build a per-sample network from
expression alone. The reply named neither of them and asked about miRNAs.

Registry data decides everything here. A workflow runs on the request's data
when every input role it requires is one the request names in some words
(`missing_input_labels` with the request, as the option notes use it); a role
the wording cannot judge, such as an omics layer, never counts as named. The
alternatives are the other network workflows that do run on it, at the scale
the reading asks for and with the regulator roles the request states: "a
TF-to-gene network" from expression alone is not offered a co-expression
network, which is not the result it asked for (replay, 2026-10-02). Nothing is matched or selected: the reply says what the
named data allows and asks whether the other inputs exist.
"""

from __future__ import annotations

from dataclasses import dataclass

from workflow_registry import OUTPUT_CAPABILITIES, RUN_ACTIONS

from ..reply_cards.method_notes import INPUT_ARTIFACTS, SHORT_INPUT_LABELS, input_fields, missing_input_labels
from ..routing.capability_compatibility import input_availability
from .request_integrity import regulatory_role_mentions

__all__ = [
    "InputAlternative", "alternative_phrases", "input_alternative", "render_input_alternative",
    "with_input_alternative", "with_input_alternative_reply",
]

_NETWORKS = frozenset({
    "regulatory_network", "coexpression_network", "signed_regulatory_effect_network", "multi_omic_network",
})
# How the reply names data the request states, by the artifact its wording establishes.
_DATA = {
    "expression_matrix": "expression data",
    "coexpression_network": "a co-expression matrix",
    "motif_prior": "a motif prior",
    "ppi_prior": "a PPI network",
    "mirna_prior": "a miRNA list",
    "regulatory_network": "a TF-gene network",
    "mutation_matrix": "mutation data",
}
_RESULTS = {
    "regulatory_network": ("regulator-to-gene network", ""),
    "coexpression_network": ("gene-gene co-expression network", " (genes only, no regulator roles)"),
    "signed_regulatory_effect_network": ("signed regulator-to-gene network", ""),
    "multi_omic_network": ("network across two omics layers", ""),
}
_SCALES = {"sample_specific": "one {} per sample", "aggregate": "one cohort-level {}"}
_NOT_INSPECTED = "No files were inspected and no analysis ran."
# Guidance replies that name workflows for the request's result; only these get the paragraph.
_REPLY_KINDS = frozenset({
    "outcome_clarification", "research_choices", "verified_guidance", "scientific_guidance",
    "workflow_contract", "composition",
})


@dataclass(frozen=True)
class InputAlternative:
    stated: tuple[str, ...]
    # (workflow, inputs it still needs, whether the wording could judge them):
    # a role the wording cannot judge (an omics layer) is listed as needed, not "also".
    lacking: tuple[tuple[str, tuple[str, ...], bool], ...]
    asked: tuple[str, ...]
    alternatives: tuple[str, ...]
    granularity: str


def _present(task: str, decision) -> frozenset[str]:
    present = set(input_availability(task).present)
    for item in decision.outcome_hypotheses:
        present.update(value for value in item.outcome.input_artifacts if value != "unknown")
    return frozenset(present)


def _runs_on(action: str, present: frozenset[str], task: str) -> bool:
    required, groups = input_fields(action)
    judged = (all(field in INPUT_ARTIFACTS for field in required)
              and all(any(field in INPUT_ARTIFACTS for field in group) for group in groups))
    return judged and not missing_input_labels(action, present, task)


def _primary(decision):
    if decision.requested_outcome is not None:
        return decision.requested_outcome
    return decision.outcome_hypotheses[0].outcome if decision.outcome_hypotheses else None


def input_alternative(decision, task: str) -> InputAlternative | None:
    """The workflows the request's named data runs, when none of the decision's does."""
    candidates = [
        action for action in dict.fromkeys(
            [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions])
        if action in OUTPUT_CAPABILITIES and action in RUN_ACTIONS
    ]
    outcome = _primary(decision)
    stated = input_availability(task).present
    if not candidates or outcome is None or outcome.artifact_type not in _NETWORKS or not stated:
        return None
    present = _present(task, decision)
    if any(_runs_on(action, present, task) for action in candidates):
        return None
    scale = outcome.granularity
    roles = {mention.regulator_type for mention in regulatory_role_mentions(task)}
    alternatives = tuple(
        action for action, capability in OUTPUT_CAPABILITIES.items()
        if action in RUN_ACTIONS and action not in candidates and capability.artifact_type in _NETWORKS
        and (scale not in _SCALES or scale in capability.granularities)
        and roles <= set(capability.regulator_types)
        and _runs_on(action, present, task)
    )
    if not alternatives:
        return None
    lacking = tuple(
        (action, tuple(labels), True) if (labels := missing_input_labels(action, present, task)) else
        (action, tuple(SHORT_INPUT_LABELS[field] for field in input_fields(action)[0]), False)
        for action in candidates
    )
    asked = next((tuple(missing_input_labels(action, present, task)) for action in candidates
                  if missing_input_labels(action, present, task)), ())
    if not asked:
        return None
    return InputAlternative(
        stated=tuple(_DATA.get(artifact, artifact.replace("_", " ")) for artifact in sorted(stated)),
        lacking=lacking, asked=asked, alternatives=alternatives, granularity=scale,
    )


def _join(items, word="and") -> str:
    items = list(dict.fromkeys(items))
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" {word} " + items[-1]


def _article(label: str) -> str:
    return label if label.startswith(("a ", "an ")) else ("an " if label[:1] in "aeiou" else "a ") + label


def _result(found: InputAlternative) -> str:
    kinds = {_RESULTS.get(OUTPUT_CAPABILITIES[action].artifact_type, ("network", "")) for action in found.alternatives}
    noun, note = kinds.pop() if len(kinds) == 1 else ("network", "")
    template = _SCALES.get(found.granularity)
    return (template.format(noun) if template else _article(noun)) + note


def alternative_names(policy, found: InputAlternative) -> str:
    return _join([policy.workflows[action].workflow if action in policy.workflows else action
                  for action in found.alternatives], "or")


def alternative_phrases(found: InputAlternative, policy) -> dict[str, str]:
    """The pieces a reply card reuses, worded as the paragraph words them."""
    asked = set(found.asked)
    keeps = [policy.workflows[action].workflow if action in policy.workflows else action
             for action, labels, judged in found.lacking if judged and set(labels) <= asked]
    return {
        "stated": _join(found.stated),
        "asked": _join([_article(label) for label in found.asked]),
        "alternatives": alternative_names(policy, found),
        "result": _result(found),
        "keeps": _join(keeps, "or") if keeps else "",
    }


def render_input_alternative(found: InputAlternative, policy) -> str:
    def name(action):
        return policy.workflows[action].workflow if action in policy.workflows else action

    groups: dict[tuple[tuple[str, ...], bool], list[str]] = {}
    for action, labels, judged in found.lacking:
        groups.setdefault((labels, judged), []).append(name(action))
    needs = "; ".join(
        f"{_join(names)} {'also ' if judged else ''}{'needs' if len(names) == 1 else 'need'} "
        + _join([_article(label) if judged else label for label in labels])
        for (labels, judged), names in groups.items()
    )
    return (
        f"**What your data allows.** Your request names only {_join(found.stated)}. {needs}. "
        f"With {_join(found.stated)} alone, {alternative_names(policy, found)} builds {_result(found)} instead. "
        f"Do you also have {_join([_article(label) for label in found.asked])}?"
    )


def with_input_alternative(text: str, decision, task: str, policy) -> str:
    """Add the paragraph above the reply's closing line, when it applies."""
    found = input_alternative(decision, task)
    if found is None or not text:
        return text
    block = render_input_alternative(found, policy)
    if _NOT_INSPECTED in text:
        return text.replace(_NOT_INSPECTED, block + "\n\n" + _NOT_INSPECTED, 1)
    return text + "\n\n" + block


def with_input_alternative_reply(result: dict, state, policy, reply) -> dict:
    """`respond()`'s last step: the same reply, with the paragraph when it applies."""
    from ..contracts import TaskDecision
    from ..llm import latest_user_task

    if policy is None or result.get("reply_kind") not in _REPLY_KINDS:
        return result
    text = str(result["messages"][-1].content)
    updated = with_input_alternative(
        text, TaskDecision.model_validate(state["decision"]), latest_user_task(state["messages"]), policy)
    return result if updated == text else reply(updated, result["reply_kind"])
