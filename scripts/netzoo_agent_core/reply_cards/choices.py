"""The question a reply asks, as ordered options.

Every builder here takes its candidates from the same typed decision and the
same registry helpers the reply renderer used, so a card never offers a
workflow the text did not. Options are ordered by, in turn:

1. a recommendation grounded in what the request stated -- the only option
   ever marked ``Recommended``;
2. how many typed dimensions of the request (regulators, scale, result) the
   workflow's registered output misses -- an option that misses none while
   every other misses one is marked ``Best match``;
3. whether it needs an input the request left out;
4. registry order.

Anything related that cannot run here is returned separately as unavailable,
with the reason, never mixed into the options.
"""

from __future__ import annotations

from workflow_registry import (
    EXTERNAL_REFERENCES, GUIDANCE_COMPOSITIONS, OUTPUT_CAPABILITIES, SELECTION_AXES, STATED_TAG_PHRASES,
)

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..routing.capability_compatibility import input_availability
from ..routing.clarification_planner import plan_clarification
from .contracts import ReplyChoices, ReplyOption
from .method_notes import condition_phrase, fit_notes, gives, highlight, missing_input_labels, needs_line
from .option_reasons import option_parts, per_sample_use
from .phrases import clip, join_names, primary_outcome, quote, result_phrase, workflow_name

__all__ = [
    "option_scale",
    "capability_gap_parts",
    "clarification_choices",
    "external_references",
    "hypothesis_parts",
    "method_choices",
    "present_inputs",
    "reading_parts",
]

# Three wrapped terminal lines: what you get, how it differs, when to pick it.
_DESCRIPTION_LIMIT = 200


def present_inputs(task: str, decision: TaskDecision) -> frozenset[str]:
    """Inputs the request says it has, from its wording and the typed readings."""
    present = set(input_availability(task).present)
    for item in decision.outcome_hypotheses:
        present.update(value for value in item.outcome.input_artifacts if value != "unknown")
    return frozenset(present)


def describe(parts, ranks=None) -> str:
    """Short fragments joined by ' · ' within a budget, shown in the order given.

    Fragments are kept in priority order: `ranks` (lower first, one per part),
    else the order given. A fragment that does not fit is skipped, and a
    shorter one after it may still fit.
    """
    texts = [" ".join((part or "").split()).rstrip(".") for part in parts]
    order = sorted(range(len(texts)), key=lambda i: (ranks[i] if ranks else 0, i))
    kept: list[int] = []
    for index in order:
        part = texts[index]
        if not part:
            continue
        if sum(len(texts[i]) + 3 for i in kept) + len(part) <= _DESCRIPTION_LIMIT:
            kept.append(index)
        elif not kept:
            texts[index] = clip(part, _DESCRIPTION_LIMIT)
            kept.append(index)
    return " · ".join(texts[i][:1].upper() + texts[i][1:] for i in sorted(kept))


def _stated_reasons(advice) -> list[str]:
    """Why the recommendation holds, in the registry's words, never the model's.

    A quote shows where the request said it; the reason is the condition it
    established. Folder-based advice (Log 154) says the named folder's files
    fit. The model's rationale describes the method ("BONOBO is designed to
    infer ..."), not what the user said, so it is never a reason here
    (Log 318); advice without a stated reason is not marked recommended.
    """
    reasons, folders = [], []
    for item in advice.conditions:
        condition = f"{item.axis}:{item.value}"
        if item.axis in SELECTION_AXES:
            reasons.append(condition_phrase(condition) or SELECTION_AXES[item.axis]["values"].get(item.value, condition))
        elif item.axis == "selection_tag" and item.value in STATED_TAG_PHRASES:
            reasons.append(STATED_TAG_PHRASES[item.value])
        elif item.axis == "inspected_inputs" and item.text_span:
            folders.append(item.text_span)
    if folders:
        reasons.append("the files in " + join_names(list(dict.fromkeys(folders)), "and") + " fit its inputs")
    return list(dict.fromkeys(reasons))


def _separating_conditions(candidates: list[str]) -> dict[str, list[str]]:
    """Each candidate's registry conditions that separate it from the others."""
    from ..graph.condition_recommender import condition_options

    labels: dict[str, list[str]] = {action: [] for action in candidates}
    for option in condition_options(candidates):
        phrase = condition_phrase(option.condition) or option.label
        for action in option.actions:
            labels.setdefault(action, []).append(phrase)
    return labels


def method_choices(decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str) -> ReplyChoices | None:
    """Tied workflows for one request, best-supported first."""
    candidates = [a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows]
    if len(candidates) < 2:
        return None
    outcome = primary_outcome(decision)
    present = present_inputs(task, decision)
    advice = decision.advisory_recommendation
    recommended = (advice.action if advice is not None and advice.action in candidates and _stated_reasons(advice)
                   else None)
    conditions = _separating_conditions(candidates)
    fits = {action: fit_notes(action, outcome) for action in candidates}
    missing = _differential_missing(candidates, present, task)
    order = sorted(candidates, key=lambda action: (
        action != recommended, len(fits[action][1]), bool(missing[action]), candidates.index(action),
    ))
    clean = [action for action in candidates if not fits[action][1]]
    best = clean[0] if len(clean) == 1 and recommended is None else None
    options = []
    for index, action in enumerate(order):
        matches, mismatches = fits[action]
        name = workflow_name(policy, action)
        if action == recommended:
            lead = ["Fits what you said: " + "; ".join(_stated_reasons(advice))]
        else:
            lead = []
        got, use = option_parts(action, candidates, outcome, policy, before=order[:index])
        when = ([] if action == recommended else
                ["Pick it if " + " or ".join(conditions[action])] if conditions.get(action) else [])
        needs = ["Also needs " + ", ".join(missing[action])] if missing[action] else []
        # Read as: what you get, how it fits your request, what it lets you do
        # and costs, when to pick it, what it needs. When over budget, what the
        # option gives and misses is kept first, then what it needs and when to
        # pick it; a cost is never shown without the use it pays for.
        ranked = [(0, part) for part in lead] + [(1, part) for part in got] + [(5, part) for part in matches] \
            + [(2, part) for part in mismatches] + ([(6, " · ".join(use))] if use else []) \
            + [(4, part) for part in when] + [(3, part) for part in needs]
        badge = "Recommended" if action == recommended else "Best match" if action == best else ""
        options.append(ReplyOption(
            key=action,
            label=name,
            description=describe([part for _, part in ranked], [rank for rank, _ in ranked]),
            answer=f"Use {name}",
            recommended=action == recommended,
            badge=badge,
            action=action,
            granularity=option_scale(action, outcome.granularity if outcome else None),
            resolution="confirm_workflow",
        ))
    if recommended:
        ordering = "Recommended first, from what you said."
    elif best:
        ordering = "The option that matches everything you asked for comes first."
    elif len({len(fits[a][1]) for a in candidates}) > 1 or any(missing.values()):
        ordering = "Options that match more of what you asked for, and use only data you mentioned, come first."
    else:
        ordering = "Nothing you said favours one of them; each line says when to pick it."
    return ReplyChoices(header="Method", question="Which method fits your study?", options=options, ordering=ordering)


def option_scale(action: str | None, requested: str | None = None) -> str | None:
    """The scale a workflow option means: the requested one it offers, else its own."""
    capability = OUTPUT_CAPABILITIES.get(action or "")
    if capability is None or len(capability.granularities) < 2:
        return None
    if requested in capability.granularities:
        return requested
    # A per-sample extension (LIONESS) is chosen for its per-sample result.
    return "sample_specific" if capability.guidance_predecessors else None


def _differential_missing(candidates: list[str], present, task: str = "") -> dict[str, list[str]]:
    """Inputs one option needs that the others do not, and the request never mentions.

    Wording only detects inputs imperfectly, so an input every candidate needs is
    never reported: it cannot separate them, and a missed mention would read as
    a false "you lack this". What remains is the choice-relevant difference,
    such as the miRNA list PUMA needs and PANDA does not. An input every
    candidate accepts, alone or as one alternative ("expression matrix or
    adjusted co-expression matrix"), separates nothing either (Test 1,
    2026-10-02: four options each said "Also needs expression matrix").
    """
    missing = {action: missing_input_labels(action, present, task) for action in candidates}
    common = set.intersection(*(_accepted(action) for action in candidates)) if candidates else set()
    return {action: [label for label in labels if not set(_alternatives(label)) & common]
            for action, labels in missing.items()}


def _alternatives(label: str) -> list[str]:
    return [part.strip() for part in label.split(" or ") if part.strip()]


def _accepted(action: str) -> set[str]:
    """Every input label the workflow takes, each alternative of a one-of group included."""
    return {item for label in _needed(action) for item in _alternatives(label)}


def _needed(action: str) -> list[str]:
    return [part.strip() for part in needs_line(action).split(",") if part.strip()]


_SCALE_LABELS = {
    "aggregate": "One cohort-wide network",
    "sample_specific": "One network per sample",
}
_REGULATOR_LABELS = {
    ("tf",): "Transcription factors only",
    ("mirna",): "miRNAs only",
    ("mirna", "tf"): "Both TFs and miRNAs",
}


def _dimension_label(dimension: str, option) -> str:
    """A short answer label; the planner's labels are written for a sentence."""
    from .phrases import artifact_noun

    values = tuple(value for value in option.value.split("|") if value)
    if dimension == "granularity":
        label = _SCALE_LABELS["sample_specific" if "sample_specific" in values else "aggregate"]
        return label + (" (plus the cohort network)" if {"aggregate", "sample_specific"} <= set(values) else "")
    if dimension == "regulator_type":
        return _REGULATOR_LABELS.get(tuple(sorted(values)), option.label)
    if dimension == "artifact_type":
        text = " + ".join(artifact_noun(value) for value in values)
        return text[:1].upper() + text[1:]
    return option.label[:1].upper() + option.label[1:]


def clarification_choices(decision: TaskDecision, policy: ProjectPolicySnapshot, *,
                          task: str = "") -> ReplyChoices | None:
    """The planner's question about the result itself, when that is what the reply asks.

    The planner is a pure function of the candidates and readings, so running
    it again yields the options behind the question the reply printed. It is
    used only when the questions are identical, and never for the algorithm
    dimension, whose options are the methods themselves. Answers are ordered
    as the method options are (rules 2-4 above). The planner lists its values
    alphabetically, so "Both TFs and miRNAs" ("mirna|tf") used to come first
    and was the default even for a request that named only expression data
    (Test 2, 2026-10-02); registry order now breaks the tie.
    """
    question = decision.clarification_question
    candidates = [a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows]
    if not question or len(candidates) < 2:
        return None
    plan = plan_clarification(candidates, outcomes=[item.outcome for item in decision.outcome_hypotheses])
    if plan is None or plan.dimension == "algorithm" or plan.question != question:
        return None
    outcome = primary_outcome(decision)
    missing = _differential_missing(candidates, present_inputs(task, decision), task)
    ranked = []
    for index, option in enumerate(plan.options, start=1):
        actions = [a for a in option.candidate_actions if a in policy.workflows]
        if not actions:
            continue
        label = _dimension_label(plan.dimension, option)
        single = actions[0] if len(actions) == 1 else None
        values = option.value.split("|")
        scale = (("sample_specific" if "sample_specific" in values else "aggregate")
                 if plan.dimension == "granularity" else outcome.granularity if outcome else None)
        mismatches = fit_notes(single, outcome)[1] if single else []
        # Only what every workflow behind this answer needs counts against it.
        lacking = [need for need in missing.get(actions[0], [])
                   if all(need in missing.get(action, []) for action in actions[1:])]
        first = min(candidates.index(action) for action in actions)
        if not single:
            got = []
        elif plan.dimension != "granularity":
            got = [gives(single)]
        else:
            # The answer already names the scale; say what that scale is for.
            got = per_sample_use(single, policy) if scale == "sample_specific" else []
        ranked.append((len(mismatches), bool(lacking), first, index, ReplyOption(
            key=f"{plan.dimension}-{index}",
            label=clip(label, 80),
            description=describe([f"Leads to {join_names([workflow_name(policy, a) for a in actions])}",
                                  *got, *mismatches,
                                  *(["Also needs " + ", ".join(lacking)] if lacking else [])],
                                 [0, *([3] * len(got)), *([1] * len(mismatches)), *([2] if lacking else [])]),
            answer=clip(label, 200),
            action=single,
            granularity=option_scale(single, scale) if single else None,
            resolution="confirm_workflow" if single else "follow_up",
        )))
    options = [option for *_, option in sorted(ranked, key=lambda item: item[:4])]
    if len(options) < 2:
        return None
    header = {"artifact_type": "Result", "granularity": "Scale", "regulator_type": "Regulators",
              "required_input": "Inputs"}.get(plan.dimension, "Choice")
    return ReplyChoices(header=header, question=question, options=options,
                        ordering="Each answer lists the workflows it leads to.")


def _reading_option(number, label, actions, policy, result, answer, scale=None) -> ReplyOption:
    single = actions[0] if len(actions) == 1 else None
    names = join_names([workflow_name(policy, a) for a in actions])
    return ReplyOption(
        key=f"reading-{number}",
        label=clip(label, 80),
        description=describe([f"{names}: {result}", highlight(single) if single else ""]),
        answer=clip(answer, 300),
        action=single,
        granularity=option_scale(single, scale) if single else None,
        resolution="confirm_workflow" if single else "follow_up",
    )


def reading_parts(decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str):
    """(choices, unavailable) for the per-reading and per-input replies (Logs 248, 250)."""
    from ..interpretation.hypothesis_routes import (
        _candidates, _composition, _handoff_routes, _quote, _readings, _splits, _stated_inputs,
    )

    readings = _readings(decision, policy)
    stated = _stated_inputs(readings, task)
    options, unavailable = [], []
    for number, reading in enumerate(readings, start=1):
        actions = [a for a in _candidates(task, reading, "guidance") if a in policy.workflows]
        said = _quote(reading, [other for other in readings if other is not reading], task)
        label = f"Reading {number}" + (f": {quote(said, 56)}" if said else "")
        answer = f"Start with reading {number}" + (f": {quote(said, 120)}" if said else "")
        result = result_phrase(reading.outcome)
        if actions:
            options.append(_reading_option(number, label, actions, policy, result, answer,
                                           reading.outcome.granularity))
            continue
        splits = _splits(task, reading)
        for value, input_actions in splits:
            source = value.replace("_", " ")
            input_actions = [a for a in input_actions if a in policy.workflows]
            key_label = (f"Reading {number}, from the {source}" if len(readings) > 1 else f"From the {source}")
            if input_actions:
                options.append(_reading_option(f"{number}-{value}", key_label, input_actions, policy,
                                               result, f"Use the {source} only", reading.outcome.granularity))
            else:
                unavailable.append(ReplyOption(
                    key=f"reading-{number}-{value}", label=clip(key_label, 80), available=False,
                    resolution="none", reason=f"No registered workflow produces {result} from the {source}.",
                ))
        if splits:
            continue
        composition = _composition(reading.outcome)
        if composition is not None:
            sources = [workflow_name(policy, a) for a, _ in composition.sources if a in policy.workflows]
            options.append(ReplyOption(
                key=f"reading-{number}", label=clip(label, 80),
                description=describe([f"A per-sample profile from {join_names(sources)}",
                                      "then clustering outside NetZoo"]),
                answer=clip(answer, 300),
            ))
            continue
        routes = _handoff_routes(reading, stated, policy)
        if routes:
            # A registered two-step handoff: each route starts with its producer,
            # which is planned and approved first; the consumer follows.
            for producer, consumer in routes:
                chain = f"{workflow_name(policy, producer)} → {workflow_name(policy, consumer)}"
                options.append(ReplyOption(
                    key=f"reading-{number}-{producer}",
                    label=clip((f"Reading {number}: " if len(readings) > 1 else "") + chain, 80),
                    description=describe([
                        f"{workflow_name(policy, producer)} builds the network, then "
                        f"{workflow_name(policy, consumer)} returns {result}",
                        highlight(consumer),
                    ]),
                    answer=f"Start with {workflow_name(policy, producer)}, then {workflow_name(policy, consumer)}",
                    action=producer,
                    resolution="confirm_workflow",
                ))
            continue
        unavailable.append(ReplyOption(
            key=f"reading-{number}", label=clip(label, 80), description=describe([f"Asks for {result}"]),
            available=False, resolution="none",
            reason="No registered workflow produces this from the stated inputs.",
        ))
    if not options:
        return None, unavailable
    return ReplyChoices(
        header="Reading", question="Which reading should we start with?", options=options,
        ordering="In the order your request states them.",
    ), unavailable


def hypothesis_parts(decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str):
    """(choices, unavailable, actions) for stated hypotheses (Log 254)."""
    from ..graph.condition_recommender import _quote_grounded

    items = [
        item for item in decision.stated_hypotheses
        if _quote_grounded(task, item.text_span)
        and (item.basis == "unsupported" or item.basis in policy.workflows and item.basis in OUTPUT_CAPABILITIES)
    ]
    actions = list(dict.fromkeys(item.basis for item in items if item.basis != "unsupported"))
    stated = present_inputs(task, decision)
    options, unavailable, outside = [], [], []
    for action in actions:
        spans = list(dict.fromkeys(item.text_span for item in items if item.basis == action))
        targets = {item.target_artifact for item in items if item.basis == action}
        options.append(ReplyOption(
            key=action,
            label=clip(workflow_name(policy, action), 80),
            description=describe([
                ("For " + " and ".join(quote(span, 60) for span in spans)) if spans else "",
                _producer_first(action, stated, policy),
                highlight(action),
            ]),
            answer=f"Start with {workflow_name(policy, action)}",
            action=action,
            resolution="confirm_workflow",
        ))
        for (target, _), composition in GUIDANCE_COMPOSITIONS.items():
            if target in targets and action in dict(composition.sources):
                outside.append(composition.outside_step)
    for span in dict.fromkeys(item.text_span for item in items if item.basis == "unsupported"):
        unavailable.append(ReplyOption(
            key=f"gap-{len(unavailable) + 1}", label=clip(quote(span, 70), 80),
            available=False, resolution="none",
            reason="No registered workflow meets this; it needs a clearer measurement or an external method.",
        ))
    for step in dict.fromkeys(outside):
        unavailable.append(ReplyOption(
            key=f"outside-{len(unavailable) + 1}", label="Clustering the samples",
            available=False, resolution="none", reason=clip(step, 250),
        ))
    if len(options) < 2:
        return None, unavailable, actions
    return ReplyChoices(
        header="Hypothesis", question="Which hypothesis should we start with?", options=options,
        ordering="In the order your request states them; you can also pursue both.",
    ), unavailable, actions


def _producer_first(action: str, stated: frozenset[str], policy) -> str:
    """Say which registered workflow must run first when this one cannot take the stated data.

    CONDOR finds modules in a network, not in expression: for a request that
    has expression data it needs PANDA or OTTER first, through their
    registered handoff. Registry `handoff_targets` only.
    """
    capability = OUTPUT_CAPABILITIES.get(action)
    measured = stated & {"expression_matrix", "coexpression_network", "mutation_matrix", "measurement_dataset",
                         "regulatory_network"}
    if capability is None or not measured or measured & set(capability.input_artifacts):
        return ""
    producers = [
        producer for producer, cap in OUTPUT_CAPABILITIES.items()
        if action in cap.handoff_targets and producer in policy.workflows
        and measured & set(cap.input_artifacts) and "mirna" not in cap.regulator_types
    ]
    if not producers:
        return ""
    wanted = join_names(sorted(set(capability.input_artifacts)), "or").replace("_", " ")
    return f"Needs a {wanted} first: build it with {join_names([workflow_name(policy, p) for p in producers])}"


def capability_gap_parts(decision: TaskDecision, policy: ProjectPolicySnapshot):
    """(headline, alternatives, unavailable) for a result no workflow produces."""
    outcome = primary_outcome(decision)
    wanted = result_phrase(outcome)
    acquire = outcome is not None and outcome.operation == "acquire"
    unavailable = [ReplyOption(
        key="requested", label=clip(wanted[:1].upper() + wanted[1:], 80), available=False, resolution="none",
        reason=("Direct download supports only STRING protein networks (functional, physical, regulatory)."
                if acquire else "No registered workflow produces this."),
    )]
    alternatives = []
    for action in [a for a in decision.alternative_actions if a in policy.workflows][:2]:
        name = workflow_name(policy, action)
        alternatives.append(ReplyOption(
            key=action, label=f"Use {name} instead",
            description=describe([highlight(action), f"Needs {needs_line(action)}"]),
            answer=f"Use {name} instead", action=action, resolution="confirm_workflow",
        ))
    headline = (f"This agent cannot download {wanted}." if acquire
                else f"The registered workflows cannot produce {wanted}.")
    return headline, alternatives, unavailable


def external_references(decision: TaskDecision) -> list[ReplyOption]:
    """Published methods for a missing modeling principle (Log 267), reference only."""
    gap = decision.advisory_capability_gap
    if gap is None:
        return []
    outcome = primary_outcome(decision)
    artifact = outcome.artifact_type if outcome is not None else "unknown"
    return [
        ReplyOption(
            key=f"external-{index}", label=clip(ref.name, 80), description=clip(ref.summary, 250),
            available=False, resolution="none",
            reason=clip(f"Not runnable here ({ref.availability}); {ref.source}.", 250),
        )
        for index, ref in enumerate(EXTERNAL_REFERENCES, start=1)
        if ref.selection_tags & set(gap.selection_tags)
        and (artifact == "unknown" or artifact in ref.artifact_types)
    ]
