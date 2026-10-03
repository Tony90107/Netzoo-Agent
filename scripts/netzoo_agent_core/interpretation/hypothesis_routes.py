"""One section per reading when a request's readings would collapse (Log 248).

A request that states two hypotheses can reach the reply with both readings
validated and still be answered with one workflow: the matcher returns the one
exact capability both readings accept, or the only reading that has a workflow
(Log 245). The readings are then listed on their own, each with the registered
workflows that fit it -- their algorithmic premises and inputs -- and the reply
asks which to start with. Nothing here routes: every candidate list is the
registry's deterministic match of one validated reading, and a tie reply that
already covers every reading is left exactly as it was.
"""

from __future__ import annotations

import re

from workflow_registry import GUIDANCE_COMPOSITIONS, OUTPUT_CAPABILITIES

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text_with_user_data, user_data_token
from ..routing.method_rejections import rejected_methods_for
from ..routing.outcome_matching import match_requested_outcome, match_semantic_request
from .concept_answers import _GRANULARITY_LABELS, _artifact_label, _candidate_details, _network_family_label
from .research_choices import render_research_choices
from .scientific_guidance import method_paragraphs
from .inspected_answers import with_inspection_footer
from .tie_guidance import method_families

__all__ = ["render_hypothesis_routes"]

_NOT_INSPECTED = "No files were inspected and no analysis ran."
# Evidence that says what a reading is about, in the order it is quoted.
_QUOTED_DIMENSIONS = ("artifact_type", "granularity", "regulator_type", "operation", "input_artifact")
# More workflows than this for one reading are listed one line each.
_FULL_DETAILS = 3


def _input_only_artifacts(policy: ProjectPolicySnapshot) -> frozenset[str]:
    consumed, produced = set(), set()
    for spec in policy.workflows.values():
        capability = spec.output_capability
        consumed.update(capability.input_artifacts)
        produced.update(capability.produced_artifacts)
        produced.add(capability.artifact_type)
    return frozenset(consumed - produced)


def _signature(outcome):
    return (outcome.artifact_type, frozenset(outcome.regulator_types), outcome.granularity)


def _readings(decision: TaskDecision, policy: ProjectPolicySnapshot) -> list:
    """Distinct scientific readings: not an input restated as the result, not a
    reading that only lacks inputs another reading of the same result states."""
    excluded = _input_only_artifacts(policy) | {"unknown"}
    candidates = [
        item for item in decision.outcome_hypotheses
        if item.outcome.artifact_type not in excluded
    ]
    readings = []
    for item in candidates:
        inputs = set(item.outcome.input_artifacts)
        if any(
            other is not item
            and _signature(other.outcome) == _signature(item.outcome)
            and inputs < set(other.outcome.input_artifacts)
            for other in candidates
        ):
            continue
        key = (_signature(item.outcome), frozenset(inputs))
        if key not in {(_signature(r.outcome), frozenset(r.outcome.input_artifacts)) for r in readings}:
            readings.append(item)
    return readings


def _candidates(task: str, reading, request_mode: str) -> list[str]:
    match = match_semantic_request(task, [reading], request_mode=request_mode)
    if match.status in {"exact", "fallback"}:
        return list(match.matched_actions)
    if match.status == "ambiguous":
        return list(match.hypothesis_actions or match.matched_actions)
    return []


def _spans(reading, task: str) -> list[str]:
    """The reading's explicit quotes that the request really contains, in order.

    A quote may end in a period where the request goes on after a comma; Test 4
    (r5) titled its reading "RNA-seq" because its two result quotes did.
    """
    folded = task.casefold()
    spans = []
    for dimension in _QUOTED_DIMENSIONS:
        for item in reading.evidence:
            if item.dimension != dimension or item.source != "explicit":
                continue
            whole = (item.text_span or "").strip()
            span = next((text for text in (whole, whole.rstrip(".,;:!?").rstrip())
                         if text and text.casefold() in folded), None)
            if span is not None and span not in spans:
                spans.append(span)
    return spans


def _quote(reading, others, task: str) -> str | None:
    """A quote only this reading gives, so two titles never read the same."""
    shared = {span for other in others for span in _spans(other, task)}
    return next((span for span in _spans(reading, task) if span not in shared), None)


def _input_label(value: str) -> str:
    return value.replace("_", " ")


def _result_line(outcome, *, after=None) -> str:
    inputs = [_input_label(value) for value in outcome.input_artifacts if value != "unknown"]
    granularity = _GRANULARITY_LABELS.get(outcome.granularity, "")
    line = "Result: " + _artifact_label(outcome.artifact_type)
    if granularity:
        line += f" ({granularity})"
    if after is not None:
        # A later step works on the previous step's result (Log 329).
        return line + f", from the {_artifact_label(after.outcome.artifact_type)} of the previous step."
    line += ", from " + (" and ".join(inputs) if inputs else "inputs the request does not state")
    return line + "."


# Words that put one thing after another. Without one, readings that could
# feed each other are still alternatives: "One camp wants the most accurate
# TF-gene regulatory network; the other wants to split the network into
# functional modules" (tests/test_hypothesis_routes.py).
_SEQUENCE = re.compile(
    r"\bthen\b|\bafter(?:wards|\s+that)?\b|\bnext\b|\bfollowed\s+by\b|\bsubsequently\b|然後|接著|之後",
    re.I,
)


def step_order(readings, policy: ProjectPolicySnapshot, task: str = ""):
    """The readings in the order they run, when each one's result feeds the next (Log 329).

    "Patient-specific networks ... then the gene modules inside each patient's
    network" is two steps, not two readings: CONDOR, which produces the
    modules, takes a regulatory network, the first result. The registry's
    inputs and outputs decide the order; the request must also say one comes
    after the other. None means the readings are alternatives.
    """
    if not 2 <= len(readings) <= 3 or not _SEQUENCE.search(task or ""):
        return None

    def produced(spec) -> set[str]:
        return set(spec.output_capability.produced_artifacts) | {spec.output_capability.artifact_type}

    def feeds(first, then) -> bool:
        return any(then.outcome.artifact_type in produced(spec)
                   and first.outcome.artifact_type in spec.output_capability.input_artifacts
                   for spec in policy.workflows.values())

    from itertools import permutations

    for order in permutations(readings):
        if all(feeds(order[i], order[i + 1]) for i in range(len(order) - 1)):
            return list(order)
    return None


def _accepting_workflows(outcome, policy: ProjectPolicySnapshot) -> list[str]:
    inputs = {value for value in outcome.input_artifacts if value != "unknown"}
    if not inputs:
        return []
    found = []
    for spec in policy.workflows.values():
        capability = spec.output_capability
        if inputs <= set(capability.input_artifacts):
            produced = capability.produced_artifacts or {capability.artifact_type}
            outputs = ", ".join(sorted(_artifact_label(a) for a in produced))
            found.append(f"**{spec.workflow}** ({outputs})")
    return sorted(set(found))


def _covered(decision: TaskDecision, routes: list[tuple]) -> bool:
    shown = set(decision.hypothesis_actions)
    return (
        decision.capability_match_status == "ambiguous"
        and len(shown) >= 2
        and all(actions and set(actions) <= shown for _, actions in routes)
    )


def _alone_candidates(task: str, reading, value: str) -> list[str]:
    """The registry's match for one input, minus methods rejected for that input.

    `match_semantic_request` checks every current input the request states, so
    SAMBAR is rejected for "mutations or expression" as a whole; what one input
    supports on its own is the capability match alone.
    """
    match = match_requested_outcome(reading.outcome)
    actions = (
        list(match.matched_actions) if match.status in {"exact", "fallback"}
        else list(match.hypothesis_actions or match.matched_actions) if match.status == "ambiguous"
        else []
    )
    rejected = {item.action for item in rejected_methods_for(task, [value], actions=actions)}
    return [action for action in actions if action not in rejected]


def _splits(task: str, reading) -> list[tuple[str, list[str]]]:
    """Log 250: each stated input on its own, when no workflow takes them together.

    Only a reading with no candidate and two or more inputs is split, and only
    when some input alone has a candidate -- otherwise the split says nothing
    the reading does not. The inputs are the reading's own; none is added.
    """
    inputs = [value for value in reading.outcome.input_artifacts if value != "unknown"]
    if len(inputs) < 2:
        return []
    def alone(value):
        # The other inputs' evidence goes with them, or the match reads it as
        # an input the outcome dropped.
        return reading.model_copy(update={
            "outcome": reading.outcome.model_copy(update={"input_artifacts": [value]}),
            "evidence": [item for item in reading.evidence
                         if item.dimension != "input_artifact" or item.value == value],
        }, deep=True)
    splits = [(value, _alone_candidates(task, alone(value), value)) for value in inputs]
    # An input that has a workflow first; otherwise the reading's own order.
    splits.sort(key=lambda item: not item[1])
    return splits if any(actions for _, actions in splits) else []


_MEASURED_INPUTS = frozenset({
    "expression_matrix", "coexpression_network", "mutation_matrix", "measurement_dataset",
})


def _stated_inputs(readings, task: str) -> frozenset[str]:
    """Measured inputs the request states, whichever reading the model gave them to.

    The primary patch assigns every current input to the primary reading
    (Log 245), so a second reading often carries none of its own.
    """
    from ..routing.capability_compatibility import input_availability

    stated = {value for reading in readings for value in reading.outcome.input_artifacts}
    stated |= set(input_availability(task).present)
    return frozenset(stated & _MEASURED_INPUTS)


def _handoff_routes(reading, stated: frozenset[str], policy: ProjectPolicySnapshot) -> list[tuple[str, str]]:
    """Registered producer -> consumer handoffs that reach a reading's result from the stated inputs.

    A result no single workflow produces from those inputs can still be one
    registered handoff away: CONDOR finds modules in a network, and PANDA,
    PUMA and OTTER declare CONDOR as their handoff target. Only registry
    `handoff_targets` count, never a guessed chain, and a producer that adds a
    regulator class the reading does not ask for (miRNA) is left out.
    """
    target = reading.outcome.artifact_type

    def produced(spec) -> set[str]:
        return set(spec.output_capability.produced_artifacts) | {spec.output_capability.artifact_type}

    # Only a gap in *kind* is bridged: when some workflow produces this result
    # straight from a stated input, the reading lacks a candidate for another
    # reason (a missing prior, say) that a handoff would not fix.
    if any(target in produced(spec) and stated & set(spec.output_capability.input_artifacts)
           for spec in policy.workflows.values()):
        return []
    requested = (set(reading.outcome.regulator_types) | set(reading.outcome.entity_types)) & {"tf", "mirna"}
    routes = []
    # Registry order, so the established base method is named first.
    for producer in [action for action in OUTPUT_CAPABILITIES if action in policy.workflows]:
        spec = policy.workflows[producer]
        capability = spec.output_capability
        if not stated & set(capability.input_artifacts):
            continue
        if "mirna" in capability.regulator_types and "mirna" not in requested:
            continue
        for consumer in capability.handoff_targets:
            consumer_spec = policy.workflows.get(consumer)
            if consumer_spec is not None and target in produced(consumer_spec):
                routes.append((producer, consumer))
    return routes


_SINGULAR = {
    "regulatory_network": "a regulatory network",
    "community_assignment": "its communities (modules)",
    "coexpression_network": "a co-expression network",
}


def _handoff_lines(routes, outcome, policy, stated=frozenset()) -> tuple[list[str], str]:
    lines = ["No single registered workflow produces this from the stated inputs; a registered "
             "handoff does, in two steps:"]
    for producer, consumer in routes:
        first, second = policy.workflows[producer], policy.workflows[consumer]
        used = sorted(stated & set(first.output_capability.input_artifacts))
        source = " and ".join(value.replace("_", " ") for value in used) or "stated inputs"
        lines.append(
            f"- **{first.workflow} → {second.workflow}** — {first.workflow} infers "
            f"{_SINGULAR.get(first.output_capability.artifact_type, _artifact_label(first.output_capability.artifact_type))} "
            f"from the {source}; {second.workflow} then takes that network and returns "
            f"{_SINGULAR.get(outcome.artifact_type, _artifact_label(outcome.artifact_type))}."
        )
    consumers = list(dict.fromkeys(consumer for _, consumer in routes))
    for consumer in consumers:
        lines.extend(
            line for line in _candidate_details(consumer, policy.workflows[consumer], policy)
            if line.startswith("  - Method premise:")
        )
    names = " or ".join(f"{policy.workflows[p].workflow} → {policy.workflows[c].workflow}" for p, c in routes)
    return lines, names


def _composition(outcome):
    """The Log 252 composition for a one-input result no workflow produces, if any."""
    inputs = [value for value in outcome.input_artifacts if value != "unknown"]
    if len(inputs) != 1:
        return None
    return GUIDANCE_COMPOSITIONS.get((outcome.artifact_type, inputs[0]))


def _composition_lines(composition, policy) -> tuple[list[str], str]:
    lines = [composition.lead]
    names = []
    for action, gives in composition.sources:
        spec = policy.workflows.get(action)
        if spec is None:
            continue
        names.append(spec.workflow)
        lines.append(f"- **{spec.workflow}** gives {gives}.")
        # The premise and inputs of each source, as every other candidate shows them.
        lines.extend(
            line for line in _candidate_details(action, spec, policy)
            if line.startswith(("  - Method premise:", "  - Required inputs:"))
        )
    lines.append(composition.outside_step)
    lines.extend(composition.notes)
    return lines, "a profile from " + " / ".join(names) + ", then clustering outside NetZoo"


def _option_lines(outcome, actions, policy, *, single_input: bool, routes=(),
                  stated=frozenset()) -> tuple[list[str], str]:
    specs = [(action, policy.workflows[action]) for action in actions if action in policy.workflows]
    if len(specs) > _FULL_DETAILS:
        # Test 4 (r5, Log 331): six workflows with every premise and formula
        # buried the reply's point. One line each, as tie replies list them.
        _, sentence, listed = method_families([action for action, _ in specs], policy, _network_family_label)
        lines = [sentence] if sentence else []
        for label, members in listed:
            lines.extend([f"- {label}:", *("  " + line for line in members)] if len(listed) > 1 else members)
        return lines, " or ".join(spec.workflow for _, spec in specs)
    if specs:
        lines = [line for action, spec in specs for line in _candidate_details(action, spec, policy)]
        return lines, " or ".join(spec.workflow for _, spec in specs)
    composition = _composition(outcome)
    if composition is not None:
        return _composition_lines(composition, policy)
    if routes:
        return _handoff_lines(routes, outcome, policy, stated)
    if gap := scale_gap_note(outcome, policy):
        return [gap], "no registered workflow"
    lines = ["No registered workflow produces this result from "
             + ("this input." if single_input else "these inputs.")]
    accepting = _accepting_workflows(outcome, policy)
    if accepting:
        lines.append(
            "Registered workflows that accept " + ("it" if single_input else "these inputs")
            + ", and what they produce instead: " + "; ".join(accepting) + "."
        )
    return lines, "no registered workflow"


def scale_gap_note(outcome, policy) -> str:
    """What to do about a result at a scale the ontology does not give it (Log 327).

    The request stated the scale (Logs 294, 327 keep such a reading). The
    workflows that produce the result at its registered scale are named, and
    one that consumes a network is said to work on one network at a time, so
    "the modules inside each patient's network" gets CONDOR on each network.
    """
    rule = ARTIFACT_SEMANTICS.get(outcome.artifact_type)
    scale = _GRANULARITY_LABELS.get(outcome.granularity, "")
    if rule is None or rule.granularities is None or not scale or outcome.granularity in rule.granularities:
        return ""
    makers = [spec for spec in policy.workflows.values()
              if spec.output_capability.artifact_type == outcome.artifact_type]
    if not makers:
        return ""
    names = " or ".join(spec.workflow for spec in makers)
    label = _artifact_label(outcome.artifact_type)
    if any("regulatory_network" in spec.output_capability.input_artifacts for spec in makers):
        return (f"No registered workflow produces {scale} {label} in one step. {names} finds them in one "
                "network at a time: run it on each sample's network separately (outside this agent's "
                "registered workflows), or on the cohort network.")
    return f"No registered workflow produces {scale} {label}; {names} produces them for the whole cohort."


def _title(number, reading, readings, task, user_data, noun="Reading") -> str:
    quote = _quote(reading, [other for other in readings if other is not reading], task)
    if quote is not None:
        user_data.append(quote)
        return f'{noun} {number} -- "{user_data_token(len(user_data) - 1)}"'
    granularity = _GRANULARITY_LABELS.get(reading.outcome.granularity, "")
    return f"{noun} {number} -- " + " ".join(
        part for part in (granularity, _artifact_label(reading.outcome.artifact_type)) if part
    )


def render_hypothesis_routes(
    decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str,
) -> str | None:
    """The per-reading reply, or None when the existing reply already covers every reading."""
    if decision.action != "no_tool":
        return None
    # Explicit biological hypotheses survive even a single-endpoint classifier.
    if decision.stated_hypotheses:
        if choices := render_research_choices(decision, policy, task=task):
            return choices
    readings = _readings(decision, policy)
    if not readings:
        return None
    # Log 329: readings where each result is the next one's input are steps, in the order they run.
    steps = step_order(readings, policy, task)
    readings = steps or readings
    # Only a no-tool reply reaches here, so every reading is matched as guidance.
    routes = [(reading, _candidates(task, reading, "guidance")) for reading in readings]
    splits = [_splits(task, reading) if not actions else [] for reading, actions in routes]
    stated = _stated_inputs(readings, task)
    handoffs = [_handoff_routes(reading, stated, policy) if not actions and not split else []
                for (reading, actions), split in zip(routes, splits)]
    several = len(readings) >= 2 and not _covered(decision, routes)
    # Log 252: one reading with no workflow of its own but a registered composition.
    composed = any(not actions and _composition(reading.outcome) for reading, actions in routes)
    if not several and not any(splits) and not composed and not any(handoffs):
        return None
    unique_actions = {action for _, actions in routes for action in actions}
    if (len(unique_actions) == 1 and all(actions for _, actions in routes)
            and not any(splits) and not composed and not any(handoffs)):
        # Different requested artifacts may be outputs of the same method.
        # That is one workflow explanation, not a workflow-selection question.
        action = next(iter(unique_actions))
        text = "\n\n".join([*method_paragraphs(action, policy, task=task), _NOT_INSPECTED])
        return with_inspection_footer(text, decision.inspected_directories)
    user_data: list[str] = []
    sections = [
        f"Your request has {len(readings)} steps, one after the other: each step uses the result of the "
        "one before. Each step is listed with the registered workflows that fit it, their algorithmic "
        "premises and inputs:"
        if steps else
        "Your request describes more than one scientific reading. Each is listed with "
        "the registered workflows that fit it, their algorithmic premises and inputs:"
        if len(readings) >= 2 else
        "No single registered workflow produces this result from all the stated inputs "
        "together. Each stated input is listed on its own, with the registered workflows "
        "that fit it, their algorithmic premises and inputs:"
        if any(splits) else
        "Here is how registered workflows can reach this result, with their algorithmic "
        "premises and inputs:"
    ]
    choices = []
    for number, ((reading, actions), split, handoff) in enumerate(zip(routes, splits, handoffs), start=1):
        noun = "Step" if steps else "Reading"
        lines = [f"**{_title(number, reading, readings, task, user_data, noun)}**"] if len(readings) >= 2 else []
        lines.append(_result_line(reading.outcome, after=readings[number - 2] if steps and number > 1 else None))
        prefix = f"{number}: " if len(readings) >= 2 else ""
        if split:
            lines.append("Each stated input on its own:")
            for value, input_actions in split:
                single = reading.outcome.model_copy(update={"input_artifacts": [value]})
                option, names = _option_lines(single, input_actions, policy, single_input=True)
                lines.append(f"- From the {_input_label(value)}:")
                lines.extend("  " + line for line in option)
                choices.append(f"{prefix}the {_input_label(value)} ({names})")
        else:
            option, names = _option_lines(reading.outcome, actions, policy, single_input=False,
                                          routes=handoff, stated=stated)
            lines.extend(option)
            choices.append(f"{number} ({names})")
        sections.append("\n".join(lines))
    if steps:
        missing = [str(number) for number, (_, actions) in enumerate(routes, start=1) if not actions]
        first = choices[0].split(" (", 1)[1].rstrip(")")
        question = ((f"Should we start with step 1 ({first})? Each step is planned and approved on its own."
                     if routes[0][1] else "")
                    + (f" Step {', '.join(missing)} {'has' if len(missing) == 1 else 'have'} no registered "
                       "workflow; what to do instead is described above." if missing else "")).strip()
    elif len(readings) >= 2:
        question = ("Which reading should we start with: " + ", ".join(choices)
                    + "? If a reading should use different data, say which.")
    elif any(splits):
        question = ("Which should we start with: " + ", ".join(choices)
                    + "? If you meant a different result for one of the inputs, say which.")
    elif any(handoffs) and not composed:
        question = ("Should we start with " + choices[0].split(" (", 1)[1].rstrip(")")
                    + "? Each step is planned and approved on its own.")
    else:
        sources = [policy.workflows[action].workflow
                   for action, _ in _composition(readings[0].outcome).sources
                   if action in policy.workflows]
        question = ("Which per-sample profile should we start with: "
                    + ", ".join(sources[:-1]) + " or " + sources[-1] + "?")
    sections.append(question)
    sections.append(_NOT_INSPECTED)
    return _ui_text_with_user_data("\n\n".join(sections), user_data)
