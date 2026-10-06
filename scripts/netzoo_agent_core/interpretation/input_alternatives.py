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

A workflow an outside-step note advises against for the request is never
offered: Test 4 (r1-r3, Log 334) was offered LIONESS-COEXPRESSION or BONOBO
for single-cell data whose note says per-cell LIONESS or BONOBO networks are
not advised.

Roles stated in the passive voice count too: "genes are regulated by
transcription factors ... and by microRNAs" (Test 6, r4-r5) was offered a
genes-only network, because the routing gate `regulatory_role_mentions` reads
only "TF-to-gene"-style phrases. This wider reading stays here, in the reply.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from workflow_registry import OUTPUT_CAPABILITIES, RUN_ACTIONS

from ..reply_cards.method_notes import INPUT_ARTIFACTS, SHORT_INPUT_LABELS, input_fields, missing_input_labels
from ..routing.capability_compatibility import input_availability
from .inspected_answers import above_closing
from .outside_steps import outside_steps
from .request_integrity import regulatory_role_mentions

__all__ = [
    "InputAlternative", "alternative_phrases", "asks_for_data", "input_alternative", "render_input_alternative",
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
# "genes are regulated by X and by Y": the rest of the sentence after "regulated by".
_PASSIVE_ROLES = re.compile(r"\bgenes?\b(?:(?!\b(?:not|never)\b)[^.;?!]){0,40}?\bregulated\s+by\b(?P<by>[^.;?!]*)", re.I)
_REGULATOR = re.compile(r"\bTFs?\b|\btranscription[- ]factors?\b|\bmi(?:cro)?[- ]?RNAs?\b|\bmiR\b", re.I)
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
    # Log 380: inputs the request rules out (the data-facts reading), with its words.
    # They are said, never asked about.
    ruled_out: tuple[str, ...] = ()
    ruled_out_quote: str = ""


def _present(task: str, decision) -> frozenset[str]:
    from .applicability import merge_inputs

    present = set(input_availability(task).present)
    for item in decision.outcome_hypotheses:
        present.update(value for value in item.outcome.input_artifacts if value != "unknown")
    # Log 380: kinds the data-facts call read are decided by that reading.
    return merge_inputs(present, decision.data_facts) if decision.data_facts else frozenset(present)


def _runs_on(action: str, present: frozenset[str], task: str) -> bool:
    required, groups = input_fields(action)
    judged = (all(field in INPUT_ARTIFACTS for field in required)
              and all(any(field in INPUT_ARTIFACTS for field in group) for group in groups))
    return judged and not missing_input_labels(action, present, task)


def _stated_roles(task: str) -> set[str]:
    roles = {mention.regulator_type for mention in regulatory_role_mentions(task)}
    for passive in _PASSIVE_ROLES.finditer(task):
        roles.update("tf" if word.casefold().startswith(("tf", "transcription")) else "mirna"
                     for word in _REGULATOR.findall(passive.group("by")))
    return roles


def _primary(decision):
    if decision.requested_outcome is not None:
        return decision.requested_outcome
    return decision.outcome_hypotheses[0].outcome if decision.outcome_hypotheses else None


def input_alternative(decision, task: str, *, ask: bool = True) -> InputAlternative | None:
    """The workflows the request's named data runs, when none of the decision's does.

    ``ask=False`` (Log 381): the request asks only for a conclusion no registered
    workflow supports, so no input is asked about; ruled-out data is still said.
    """
    candidates = [
        action for action in dict.fromkeys(
            [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions])
        if action in OUTPUT_CAPABILITIES and action in RUN_ACTIONS
    ]
    outcome = _primary(decision)
    present = _present(task, decision)
    judged = getattr(present, "judged", frozenset())
    # Log 380: with the data-facts reading, the stated data is that reading's, not the wording's.
    stated = (set(input_availability(task).present) - judged) | (set(present) & judged)
    if not candidates or outcome is None or not (stated or judged):
        return None
    if outcome.artifact_type not in _NETWORKS and not judged:
        return None
    if any(_runs_on(action, present, task) for action in candidates):
        return None
    scale = outcome.granularity
    roles = _stated_roles(task)
    advised_against = {action for step in outside_steps(decision, task) for action in step.advises_against}
    alternatives = tuple(
        action for action, capability in OUTPUT_CAPABILITIES.items()
        if action in RUN_ACTIONS and action not in candidates and action not in advised_against
        and outcome.artifact_type in _NETWORKS and capability.artifact_type in _NETWORKS
        and (scale not in _SCALES or scale in capability.granularities)
        and roles <= set(capability.regulator_types)
        and _runs_on(action, present, task)
    )
    # Log 380: a reading of the request's data lets the reply speak without an
    # alternative -- ask about what it left unstated (F3, Log 379: priors never
    # mentioned, GIRAFFE given as the answer), say what it ruled out.
    if not alternatives and not judged:
        return None
    absent = getattr(present, "absent", frozenset())
    ruled_out_fields = {field for field, artifact in INPUT_ARTIFACTS.items() if artifact in absent}
    ruled_out = tuple(dict.fromkeys(
        SHORT_INPUT_LABELS[field] for action in candidates for field in input_fields(action)[0]
        if field in ruled_out_fields))
    lacking = tuple(
        (action, tuple(labels), True) if (labels := missing_input_labels(action, present, task)) else
        (action, tuple(SHORT_INPUT_LABELS[field] for field in input_fields(action)[0]), False)
        for action in candidates
    )
    def askable(label: str) -> bool:
        # With a data-facts reading, only what it read as unstated is asked about:
        # a role only the wording judged ("mRNA plus small RNA" is expression) is not.
        if label in ruled_out:
            return False
        if not judged:
            return True
        return any(SHORT_INPUT_LABELS[field] == label and INPUT_ARTIFACTS.get(field) in judged
                   for field in INPUT_ARTIFACTS)

    # A workflow whose input is ruled out cannot be rescued by another one (Log 380):
    # PUMA with the priors ruled out is not worth a question about its miRNA list.
    open_candidates = [action for action in candidates
                       if not any(field in ruled_out_fields for field in input_fields(action)[0])]
    asked = next((tuple(label for label in missing_input_labels(action, present, task) if askable(label))
                  for action in open_candidates
                  if [label for label in missing_input_labels(action, present, task) if askable(label)]), ())
    if not ask:
        asked = ()
    if not asked and not (ruled_out and judged):
        return None
    quote = next((present.quotes.get(INPUT_ARTIFACTS[field], "") for field in ruled_out_fields
                  if getattr(present, "quotes", {}).get(INPUT_ARTIFACTS[field])), "")
    return InputAlternative(
        stated=tuple(_DATA.get(artifact, artifact.replace("_", " ")) for artifact in sorted(stated)),
        lacking=lacking, asked=asked, alternatives=alternatives, granularity=scale,
        ruled_out=ruled_out, ruled_out_quote=quote,
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
    if not found.alternatives:
        return ""
    return _join([policy.workflows[action].workflow if action in policy.workflows else action
                  for action in found.alternatives], "or")


def alternative_phrases(found: InputAlternative, policy) -> dict[str, str]:
    """The pieces a reply card reuses, worded as the paragraph words them."""
    asked = set(found.asked)
    keeps = [policy.workflows[action].workflow if action in policy.workflows else action
             for action, labels, judged in found.lacking if judged and set(labels) <= asked]
    return {
        "stated": _join(found.stated) if found.stated else "the data I described",
        "asked": _join([_article(label) for label in found.asked]) if found.asked else "",
        "alternatives": alternative_names(policy, found),
        "result": _result(found) if found.alternatives else "",
        "keeps": _join(keeps, "or") if keeps else "",
        "ruled_out": _join([_article(label) for label in found.ruled_out]) if found.ruled_out else "",
    }


def render_input_alternative(found: InputAlternative, policy) -> str:
    def name(action):
        return policy.workflows[action].workflow if action in policy.workflows else action

    ruled_out = set(found.ruled_out)
    groups: dict[tuple[tuple[str, ...], bool], list[str]] = {}
    for action, labels, judged in found.lacking:
        # Log 380: what the request rules out is said once below, not as "also needs".
        kept = tuple(label for label in labels if label not in ruled_out)
        if kept:
            groups.setdefault((kept, judged), []).append(name(action))
    needs = "; ".join(
        f"{_join(names)} {'also ' if judged else ''}{'needs' if len(names) == 1 else 'need'} "
        + _join([_article(label) if judged else label for label in labels])
        for (labels, judged), names in groups.items()
    )
    parts = [f"**What your data allows.** Your request names only {_join(found.stated)}." if found.stated
             else "**What your data allows.**"]
    if needs:
        parts.append(f"{needs}.")
    if found.ruled_out:
        users = _join([name(action) for action, labels, _ in found.lacking if ruled_out & set(labels)])
        said = f' ("{found.ruled_out_quote}")' if found.ruled_out_quote else ""
        parts.append(f"{users} {'needs' if ' and ' not in users else 'need'} "
                     f"{_join([_article(label) for label in found.ruled_out])}, which you said you do not have{said}.")
    data = _join(found.stated) if found.stated else "the data you describe"
    if found.alternatives:
        parts.append(f"With {data} alone, {alternative_names(policy, found)} builds {_result(found)} instead.")
    # Without an alternative nothing is claimed about "every registered workflow":
    # that would rest on routing's reading of the result (Log 380 dev, s18 T5).
    if found.asked:
        parts.append(f"Do you also have {_join([_article(label) for label in found.asked])}?")
    return " ".join(parts)


def asks_for_data(state, task: str) -> bool:
    """False when the request asks only for conclusions no registered workflow supports (Log 381).

    Log 380 F4 ("Could these profiles predict which patients will relapse?")
    was asked for a motif prior and a PPI network to run workflows that cannot
    answer it. The study purpose's claims decide: a prediction or causal claim
    with no claim a workflow works toward needs no input question.
    """
    from .study_purpose_notes import gap_claims, purpose_from_state, question_claim

    purpose = purpose_from_state(state, task)
    return not (gap_claims(purpose) and question_claim(purpose) is None)


def with_input_alternative(text: str, decision, task: str, policy, *, ask: bool = True) -> str:
    """Add the paragraph above the reply's closing line, when it applies."""
    found = input_alternative(decision, task, ask=ask)
    if found is None or not text:
        return text
    return above_closing(text, render_input_alternative(found, policy))


def with_input_alternative_reply(result: dict, state, policy, reply) -> dict:
    """`respond()`'s last step: the same reply, with the paragraph when it applies."""
    from ..contracts import TaskDecision
    from ..llm import latest_user_task

    decision = TaskDecision.model_validate(state["decision"])
    # Log 381: with a data-facts reading, the per-reading reply (Log 248) gets the
    # paragraph too (Log 380 G1: PANDA and OTTER with the priors unstated, never asked).
    kinds = _REPLY_KINDS | ({"hypothesis_routes"} if decision.data_facts else set())
    if policy is None or result.get("reply_kind") not in kinds:
        return result
    task = latest_user_task(state["messages"])
    text = str(result["messages"][-1].content)
    updated = with_input_alternative(text, decision, task, policy, ask=asks_for_data(state, task))
    return result if updated == text else reply(updated, result["reply_kind"])
