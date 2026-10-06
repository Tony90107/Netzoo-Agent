"""Build the card for one finished turn.

Called by the conversation machine with the graph result, the next prompt it
just derived from that result, and the loaded policy. The reply text is left
alone; the card is what a driver may show first. When anything here fails the
turn is unaffected: the machine drops the card and the full text is shown, as
before cards existed.
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, RUN_ACTIONS

from ..interpretation.applicability import data_condition
from ..contracts import ProjectPolicySnapshot, TaskDecision, ToolExecutionResult, WorkflowPlan
from ..contracts.state import NextTurnPrompt
from ..outcomes import effective_results
from .choices import (
    describe,
    option_scale,
    capability_gap_parts,
    clarification_choices,
    external_references,
    hypothesis_parts,
    method_choices,
    present_inputs,
    reading_parts,
)
from .contracts import ReplyCard, ReplyChoices, ReplyOption
from .method_notes import highlight, needs_line, unmentioned_input_labels
from .next_steps import next_steps, plan_step
from ..interpretation.practical_notes import practical_notes
from .option_reasons import per_sample_use, scale_split, shared_points
from .phrases import artifact_noun, clip, input_phrase, join_names, primary_outcome, quote, result_phrase, workflow_name

__all__ = ["build_reply_card"]

_SINGLE_WORKFLOW_KINDS = {
    "verified_guidance", "scientific_guidance", "workflow_contract", "handoff_script",
    "handoff_boundary", "cobra_boundary", "algorithm_boundary",
}
_INPUT_FIELDS = {
    "expression_file", "motif_file", "ppi_file", "mirna_file", "coexpression_file", "design_file",
    "network_file", "mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file",
    "omics_layer_1", "omics_layer_2",
}
_OUTPUT_FIELDS = ("output_file", "lioness_output", "output_dir")
_MEASURED = frozenset({"expression_matrix", "mutation_matrix", "measurement_dataset", "coexpression_network",
                       "regulatory_network"})


def _understood(decision: TaskDecision, task: str) -> str:
    """What the agent took the request to ask for, so a misreading is visible."""
    outcome = primary_outcome(decision)
    if outcome is None or outcome.artifact_type == "unknown":
        return ""
    present = present_inputs(task, decision)
    # Priors alone are not what a result is computed "from"; naming only them misleads.
    inputs = input_phrase(sorted(present)) if present & _MEASURED else ""
    return f"Understood goal: {result_phrase(outcome)}" + (f" from {inputs}" if inputs else "") + "."


def _single_action(decision: TaskDecision, policy) -> str | None:
    for actions in (decision.matched_actions, decision.recommended_actions[-1:], decision.hypothesis_actions):
        found = [a for a in dict.fromkeys(actions) if a in policy.workflows]
        if len(found) == 1:
            return found[0]
    return None


def _produces(action: str) -> str:
    capability = OUTPUT_CAPABILITIES.get(action)
    if capability is None:
        return ""
    artifacts = sorted(capability.produced_artifacts or {capability.artifact_type})
    scales = set(capability.granularities)
    scale = (
        " (one per sample)" if scales == {"sample_specific"}
        else " (cohort-level and per-sample)" if {"aggregate", "sample_specific"} <= scales
        else " (one cohort-level result)" if scales == {"aggregate"}
        else ""
    )
    return join_names([artifact_noun(a) for a in artifacts], "and") + scale


def _base_not_first(policy, action: str) -> str:
    """A per-sample extension also writes its base's cohort network, so the base need not run first.

    The headline used to name the pair "PUMA → LIONESS-PUMA", which reads as two
    runs, while the composition card for the same pair says the opposite
    (Test 2, 2026-10-02). Said only when the registry gives both scales.
    """
    capability = OUTPUT_CAPABILITIES.get(action)
    if capability is None or not {"aggregate", "sample_specific"} <= set(capability.granularities):
        return ""
    bases = [workflow_name(policy, a) for a in capability.guidance_predecessors if a in policy.workflows]
    return (f"It also writes the cohort network, so {join_names(bases, 'and')} need not run first."
            if bases else "")


def _unmentioned(actions, task: str, decision: TaskDecision) -> str:
    """Inputs every listed workflow needs that the request does not name (Test 2, 2026-10-02).

    A request that names only expression data was led to a workflow needing a
    motif prior and a PPI network without a word about either.
    """
    present = present_inputs(task, decision)
    lists = [unmentioned_input_labels(action, task, present) for action in actions]
    shared = [label for label in lists[0] if all(label in other for other in lists[1:])] if lists else []
    if not shared:
        return ""
    names = join_names(shared, "and")
    return (f"Not mentioned in your request: {names}." if len(lists) == 1 else
            f"Every option also needs {names}, which your request does not mention.")


def _narrowed_from(decision, policy, task) -> tuple[str | None, list[str]]:
    """(the quote, the other candidates) when one method signal narrowed a tie.

    The discriminator turns a tie into one workflow when the request states a
    method signal (`match_basis == "registry_features"`). That can rest on a
    single word -- "convergence" alone picked OTTER over PANDA for a request
    that set two philosophies against each other -- so the card says which
    word decided it and which methods it set aside. The tie is recomputed by
    the same matcher with the signal removed; nothing here re-routes.
    """
    if decision.match_basis != "registry_features" or not decision.outcome_hypotheses:
        return None, []
    from ..routing.outcome_matching import match_semantic_request

    hypothesis = decision.outcome_hypotheses[0]
    spans = [item.text_span for item in hypothesis.evidence if item.dimension == "selection_tag" and item.text_span]
    bare = hypothesis.model_copy(update={
        "outcome": hypothesis.outcome.model_copy(update={"selection_tags": []}),
        "evidence": [item for item in hypothesis.evidence if item.dimension != "selection_tag"],
    })
    try:
        tie = match_semantic_request(task, [bare], request_mode="guidance")
    except Exception:  # noqa: BLE001 - an explanation, never a reason to fail the card
        return None, []
    others = [a for a in tie.hypothesis_actions if a in policy.workflows and a not in decision.matched_actions]
    return (spans[0] if spans else None), others


def _workflow_card(decision, policy, task, action, *, kind="workflow_guidance", base_note=True) -> ReplyCard:
    name = workflow_name(policy, action)
    outcome = primary_outcome(decision)
    if decision.capability_match_status == "fallback":
        headline = f"{name} is the closest registered match, but it is not a verified match for your request."
    elif (condition := data_condition(decision, action)) is not None:
        # Log 380 (plan item 4): not "fits your goal" while the data it needs is missing.
        headline = (f"{name} needs {condition[1]}, which you said you do not have."
                    if condition[0] == "ruled_out" else f"{name} fits your goal if you have {condition[1]}.")
    elif outcome is not None and outcome.artifact_type != "unknown":
        headline = f"{name} fits your goal: {result_phrase(outcome, article=False)}."
    elif _produces(action):
        produced = _produces(action)
        article = "an " if produced[:1] in "aeiou" else "a "
        headline = f"{name} produces {article}{produced}."
    else:
        headline = f"{name} is the registered workflow for this."
    from .choices import _producer_first

    first = _producer_first(action, present_inputs(task, decision), policy)
    said, others = _narrowed_from(decision, policy, task)
    narrowed = ""
    if others:
        names = join_names([workflow_name(policy, a) for a in others], "and")
        narrowed = (f"Picked from {len(others) + 1} fitting methods because you wrote {quote(said, 40)}; "
                    f"{names} also fit." if said else
                    f"Picked from {len(others) + 1} fitting methods by a method signal; {names} also fit.")
    points = [
        narrowed,
        f"{first}." if first else "",
        f"Method: {highlight(action)}." if highlight(action) else "",
        f"Needs: {needs_line(action)}." if needs_line(action) else "",
        *practical_notes(action, task, short=True),
        _unmentioned([action], task, decision),
        f"Produces: {_produces(action)}." if _produces(action) else "",
        _base_not_first(policy, action) if base_note else "",
    ]
    card = ReplyCard(kind=kind, headline=clip(headline, 300), points=[clip(p, 300) for p in points if p][:6])
    if first:
        producers = first.split("build it with ", 1)[1]
        card = card.model_copy(update={"next_steps": [ReplyOption(
            key="producer-first",
            label=clip(f"Build the network first ({producers})", 80),
            description=f"Plans the registered handoff into {workflow_name(policy, action)}; each step is approved on its own.",
            answer=clip(f"Build the network with {producers} first, then use it with "
                        f"{workflow_name(policy, action)} for this goal.", 600),
            resolution="follow_up",
        )]})
    if others:
        names = join_names([workflow_name(policy, a) for a in others], "and")
        compare = ReplyOption(
            key="compare-others",
            label=clip(f"Compare with {names}", 80),
            description="Explains how their assumptions differ and which fits your study; runs nothing.",
            answer=clip(f"Compare {workflow_name(policy, action)} with {names} for this goal. "
                        "How do their assumptions differ, and which fits my study?", 600),
            resolution="compare_workflows",
            compare_actions=[action, *others],
        )
        card = card.model_copy(update={"next_steps": [*card.next_steps, compare]})
    return card


_DIFFERENCES = {
    "artifact_type": "what they produce",
    "granularity": "scale (one cohort network or one per sample)",
    "regulator_type": "which regulators they model (TFs, miRNAs)",
    "required_input": "the inputs they need",
    "algorithm": "their modeling assumptions",
}


def _difference(actions, decision) -> str:
    """What separates the candidates most, by the planner's own ranking."""
    from ..routing.clarification_planner import plan_clarification

    plan = plan_clarification(actions, outcomes=[item.outcome for item in decision.outcome_hypotheses])
    return _DIFFERENCES.get(plan.dimension if plan else "algorithm", "their modeling assumptions")


def _method_card(decision, policy, task, choices: ReplyChoices) -> ReplyCard:
    count = len(choices.options)
    outcome = primary_outcome(decision)
    actions = [option.action for option in choices.options if option.action]
    difference = _difference(actions, decision)
    if scale_split(actions, outcome) and difference != _DIFFERENCES["granularity"]:
        # A per-sample extension also writes the cohort network, so the planner
        # does not count scale as a difference; to the reader it is the first one.
        difference = "scale (one network for all samples or one per sample) and " + (
            "in their modeling assumptions" if difference == _DIFFERENCES["algorithm"] else difference)
    if outcome is not None and outcome.artifact_type != "unknown" and difference.endswith(_DIFFERENCES["algorithm"]):
        headline = f"{count} registered methods can build {result_phrase(outcome)}; they differ in {difference}."
    else:
        headline = f"{count} registered workflows fit your request; they differ in {difference}."
    points = [_understood(decision, task), _unmentioned(actions, task, decision),
              *shared_points(actions, outcome, task, policy)]
    recommended = next((option for option in choices.options if option.badge == "Recommended"), None)
    best = next((option for option in choices.options if option.badge == "Best match"), None)
    if recommended is not None:
        points.append(f"Recommended: {recommended.label}, from what you said.")
    elif best is not None:
        points.append(f"Best match: {best.label} is the only one whose output matches everything you asked for.")
    else:
        points.append("Nothing you said favours one method yet; each option says when to pick it.")
    if decision.addressed_concerns:
        points.append("Your stated concern is answered per method in the full explanation.")
    points = [clip(p, 300) for p in points if p]
    # The generic note goes first when the shared points would pass the card's six.
    picking = "Picking an option explains it for your data and what it needs; nothing runs."
    if len(points) < 6:
        points.insert(len(points) - bool(decision.addressed_concerns), picking)
    return ReplyCard(kind="method_choice", headline=clip(headline, 300), points=points[:6], choices=choices)


def _clarification_card(decision, policy, task, choices: ReplyChoices) -> ReplyCard:
    count = len([a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows])
    headline = f"{count} registered workflows fit; one detail about your study decides between them."
    points = [_understood(decision, task), _unmentioned(
        [a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows], task, decision)]
    return ReplyCard(kind="clarification", headline=clip(headline, 300),
                     points=[clip(p, 300) for p in points if p], choices=choices)


def _composition_card(decision, policy, task) -> ReplyCard | None:
    """A base workflow and its per-sample extension (render_workflow_composition_guidance)."""
    chain = [a for a in decision.recommended_actions if a in policy.workflows]
    if len(chain) < 2:
        return _workflow_card(decision, policy, task, chain[0]) if chain else None
    base, final = chain[0], chain[-1]
    outcome = primary_outcome(decision)
    if outcome is not None and outcome.granularity == "sample_specific":
        card = _workflow_card(decision, policy, task, final, base_note=False)
        return card.model_copy(update={
            "kind": "composition",
            "headline": f"{workflow_name(policy, final)} gives the per-sample result you asked for; "
                        f"it also writes the cohort network, so {workflow_name(policy, base)} need not run first.",
        })
    choices = ReplyChoices(
        header="Scale",
        question="Do you need one network per sample, or only the cohort network?",
        options=[
            ReplyOption(key=final, label=f"One network per sample ({workflow_name(policy, final)})",
                        description=describe([*per_sample_use(final, policy)[:1], "Also writes the cohort network",
                                              *per_sample_use(final, policy)[1:]]),
                        answer=f"Use {workflow_name(policy, final)}", action=final,
                        granularity=option_scale(final, "sample_specific"), resolution="confirm_workflow"),
            ReplyOption(key=base, label=f"Cohort network only ({workflow_name(policy, base)})",
                        description=describe([f"A single {workflow_name(policy, base)} run, so faster",
                                              "It will not show how samples differ"]),
                        answer=f"Use {workflow_name(policy, base)}", action=base,
                        granularity=option_scale(base, "aggregate"), resolution="confirm_workflow"),
        ],
        ordering="Both use the same inputs.",
    )
    return ReplyCard(
        kind="composition",
        headline=(f"{workflow_name(policy, final)} gives one network per sample and also the cohort network; "
                  f"{workflow_name(policy, base)} alone gives only the cohort network."),
        points=[p for p in (f"Needs: {needs_line(final)}.", _unmentioned([final], task, decision)) if p],
        choices=choices,
    )


def _gap_card(decision, policy, task) -> ReplyCard:
    headline, alternatives, unavailable = capability_gap_parts(decision, policy, task)
    points = []
    if alternatives:
        points.append("A registered workflow produces a related result; choose it below if that is what you meant.")
    else:
        supported = sorted({result_phrase(_Outcome(spec.output_capability), article=False)
                            for spec in policy.workflows.values()})
        points.append(clip("Registered results: " + ", ".join(supported) + ".", 300))
    choices = (ReplyChoices(header="Instead", question="Did you mean a supported result?",
                            options=alternatives, ordering="The closest supported result first.")
               if alternatives else None)
    return ReplyCard(kind="capability_gap", headline=clip(headline, 300), points=points,
                     choices=choices, unavailable=unavailable)


class _Outcome:
    """Adapter so a registry capability reads like a typed outcome for phrasing."""

    def __init__(self, capability):
        self.artifact_type = capability.artifact_type
        self.granularity = "unknown"
        self.regulator_types = list(capability.regulator_types)


def _method_gap_card(decision, policy, task) -> ReplyCard:
    """A requested modeling principle no qualified workflow implements (Log 257)."""
    from ..interpretation.advisory_answers import _related_gap_actions

    gap = decision.advisory_capability_gap
    principle = join_names(sorted(tag.replace("_", " ") for tag in gap.selection_tags), "and")
    headline = f"No registered workflow implements the {principle} approach you asked for."
    ranked = [action for action, _ in _related_gap_actions(decision, policy)]
    options = [
        ReplyOption(
            key=action,
            label=workflow_name(policy, action),
            description=clip(highlight(action), 250),
            answer=f"Use {workflow_name(policy, action)}",
            action=action,
            resolution="confirm_workflow",
        )
        for action in ranked
    ]
    choices = (ReplyChoices(header="Relax it", question="Would one of these, without that requirement, work for you?",
                            options=options, ordering="Closest to the result you asked for first.")
               if len(options) >= 1 else None)
    points = [_understood(decision, task),
              "The registered alternatives do not fulfil the requested modeling requirement."]
    return ReplyCard(kind="capability_gap", headline=clip(headline, 300),
                     points=[clip(p, 300) for p in points if p], choices=choices,
                     unavailable=external_references(decision))


def _run_card(plan: WorkflowPlan, results: list[ToolExecutionResult], evaluation: dict | None) -> ReplyCard | None:
    runs = [item for item in results if item.action.startswith("run_")]
    if not runs:
        return None
    workflow = plan.workflow
    if any(item.status == "dry_run" for item in runs) and not any(item.status == "success" for item in runs):
        values = {item.field: item.value for item in plan.evidence if item.value}
        inputs = [str(values[field]).rsplit("/", 1)[-1] for field in values if field in _INPUT_FIELDS]
        outputs = [str(values[field]) for field in _OUTPUT_FIELDS if field in values]
        points = [
            clip("Inputs: " + ", ".join(inputs) + ".", 300) if inputs else "",
            clip("Will write: " + ", ".join(outputs) + ".", 300) if outputs else "",
            "Execution needs your explicit approval, and runs once.",
        ]
        return ReplyCard(kind="plan_ready", headline=f"Your {workflow} plan passed validation. Nothing has run yet.",
                         points=[p for p in points if p])
    failed = [item for item in runs if item.status == "failed"]
    if failed or (evaluation or {}).get("status") == "failed":
        errors = [error for item in failed for error in item.errors][:2]
        points = [clip("Error: " + error, 300) for error in errors]
        hint = next((item.recovery_hint for item in failed if item.recovery_hint), None)
        if hint:
            points.append(clip("Suggested fix: " + hint, 300))
        points.append("No unfinished step is reported as completed.")
        return ReplyCard(kind="run_failed", headline=f"{workflow} did not finish.", points=points, ran_nothing=False)
    artifacts = [path for item in runs for path in item.artifacts]
    shown = [path.removeprefix("/work/") for path in artifacts[:3]]
    points = [clip("Outputs: " + ", ".join(shown) + (f" (+{len(artifacts) - 3} more)" if len(artifacts) > 3 else "") + ".", 300)]
    points.extend(clip("Warning: " + warning, 300) for item in runs for warning in item.warnings[:1])
    return ReplyCard(kind="run_completed", headline=f"{workflow} finished and passed its result checks.",
                     points=points[:5], ran_nothing=False)


def _core_card(kind: str, decision: TaskDecision, policy, task: str) -> ReplyCard | None:
    if kind in {"hypothesis_routes", "research_choices"}:
        choices, unavailable, stated = hypothesis_parts(decision, policy, task=task)
        if choices is not None:
            approaches = len({item.text_span for item in decision.stated_hypotheses})
            workflows = len(choices.options)
            headline = (f"You described {approaches} approaches; {workflows} registered workflows fit them."
                        if approaches != workflows else
                        f"You described {approaches} approaches; each is tested with a different registered workflow.")
            return ReplyCard(
                kind="hypothesis_choice", headline=headline,
                points=[], choices=choices, unavailable=unavailable,
            )
        if len(stated) == 1:
            return _workflow_card(decision, policy, task, stated[0]).model_copy(update={"unavailable": unavailable})
        if kind == "hypothesis_routes":
            choices, unavailable = reading_parts(decision, policy, task=task)
            if choices is not None:
                readings = {option.key.split("-")[1] for option in [*choices.options, *unavailable]}
                chained = all("→" in option.label for option in choices.options)
                missing = [option.label.split(":")[0] for option in unavailable if option.key.startswith("reading-")]
                headline = ((f"Your request has {len(readings)} steps, one after the other"
                             + (f"; {' and '.join(missing).lower()} {'has' if len(missing) == 1 else 'have'} "
                                "no registered workflow." if missing else "."))
                            if choices.header == "Step" else
                            f"Your request can be read {len(readings)} ways, and they lead to different workflows."
                            if len(readings) > 1 else
                            "No single registered workflow gives this from your inputs; a registered two-step handoff does."
                            if chained else
                            "No single registered workflow takes every stated input together.")
                return ReplyCard(kind="reading_choice", headline=headline, points=[],
                                 choices=choices, unavailable=unavailable)
        if kind == "research_choices":
            if (method := method_choices(decision, policy, task=task)) is not None and len(method.options) <= 6:
                return _method_card(decision, policy, task, method)
            if (action := _single_action(decision, policy)) is not None:
                return _workflow_card(decision, policy, task, action)
        return None
    if kind == "capability_gap":
        return _gap_card(decision, policy, task)
    if kind == "outcome_clarification":
        if decision.advisory_capability_gap is not None:
            return _method_gap_card(decision, policy, task)
        if (clarification := clarification_choices(decision, policy, task=task)) is not None:
            return _clarification_card(decision, policy, task, clarification)
        if (method := method_choices(decision, policy, task=task)) is not None:
            return _method_card(decision, policy, task, method)
    if kind == "composition" and decision.recommended_actions:
        return _composition_card(decision, policy, task)
    if kind in _SINGLE_WORKFLOW_KINDS | {"outcome_clarification"}:
        if (action := _single_action(decision, policy)) is not None:
            return _workflow_card(decision, policy, task, action)
    if kind == "outcome_clarification" and decision.clarification_question:
        return ReplyCard(kind="clarification",
                         headline="I need one more detail before choosing a workflow.",
                         points=[clip(decision.clarification_question, 300)])
    if kind == "unresolved":
        return ReplyCard(
            kind="unresolved",
            headline="I could not validate an interpretation of this request, so nothing was selected.",
            points=["This does not mean your question is unclear; restating the result you want usually helps."],
        )
    return None


_INPUT_ALTERNATIVE_CARDS = frozenset({"clarification", "method_choice", "workflow_guidance", "composition"})
_UNMENTIONED_POINTS = ("Not mentioned in your request:", "Every option also needs ")


def _with_input_alternative(card: ReplyCard, decision, policy, task: str, result: dict) -> ReplyCard:
    """Ask first whether the inputs exist when no option runs on the data the request names (Log 312)."""
    from ..interpretation.input_alternatives import alternative_phrases, asks_for_data, input_alternative

    found = input_alternative(decision, task, ask=asks_for_data(result, task))
    if found is None:
        return card
    words = alternative_phrases(found, policy)
    if not found.asked:
        # Log 380: everything missing is ruled out -- nothing to ask; say it.
        return card.model_copy(update={"points": [
            *(point for point in card.points if not point.startswith(_UNMENTIONED_POINTS)),
            clip(f"Needs {words['ruled_out']}, which you said you do not have.", 300)]})
    result = words["result"][:1].upper() + words["result"][1:] if words["result"] else ""
    options = [
        ReplyOption(
            key="inputs-named", label=clip(f"Only {words['stated']}", 80),
            description=describe([f"Leads to {words['alternatives']}", result] if words["alternatives"] else
                                 ["Ask what the data you named can give instead"]),
            answer=clip(f"I only have {words['stated']}. {result} is fine." if result else
                        f"I only have {words['stated']}.", 600),
            resolution="follow_up",
        ),
        ReplyOption(
            key="inputs-more", label=clip(f"I also have {words['asked']}", 80),
            description=describe([f"Leads to {words['keeps']}" if words["keeps"]
                                  else "Continues with the workflows this reply names"]),
            answer=clip(f"I also have {words['asked']}.", 600),
            resolution="follow_up",
        ),
    ]
    # A method or clarification card's other points describe the options this replaces.
    kept = card.points[:1] if card.kind in {"method_choice", "clarification"} else card.points
    points = [point for point in kept if not point.startswith(_UNMENTIONED_POINTS)]
    points.append(clip(f"Your request names only {words['stated']}; the matched workflows need more inputs, "
                       + (f"while {words['alternatives']} works from it alone." if words["alternatives"] else
                          "which the request does not mention."), 300))
    return card.model_copy(update={
        "points": points,
        "choices": ReplyChoices(header="Inputs", question=clip(f"Do you also have {words['asked']}?", 400),
                                options=options, ordering="The option that uses only the data you named comes first."),
    })


def _with_outside_steps(card: ReplyCard, decision, task: str) -> ReplyCard:
    """A step no registered workflow performs, as a "not available here" row (Log 320)."""
    from ..interpretation.outside_steps import outside_steps

    rows = [ReplyOption(key=f"outside-{step.key}", label=clip(step.name, 80), available=False,
                        resolution="none", reason=clip(step.reason, 260))
            for step in outside_steps(decision, task)]
    if not rows:
        return card
    return card.model_copy(update={"unavailable": [*card.unavailable, *rows][:8]})


def _with_study_purpose(card: ReplyCard, kind: str, decision, policy, task: str, state=None) -> ReplyCard:
    """The stated question as a point, and conclusions no workflow supports as rows (Log 342).

    Log 368: candidates that give one result for all the samples, asked about
    individuals, get a point naming the per-sample workflows for the same data
    (their planning steps are added by `_one_result_steps`).
    """
    from workflow_registry import UNSUPPORTED_CLAIMS

    from ..interpretation.study_purpose_notes import (
        CLAIM_LABELS, claim_cells, gap_claims, one_result_cells, purpose_from_state, question_claim,
    )

    purpose = purpose_from_state(state, task)
    gaps = gap_claims(purpose)
    if kind == "unresolved":
        if not gaps:
            return card
        label = UNSUPPORTED_CLAIMS[gaps[0][0]][2]
        return card.model_copy(update={
            "headline": clip(f"No registered workflow can do this: {label[:1].lower()}{label[1:]}.", 300),
            "points": [clip(UNSUPPORTED_CLAIMS[gaps[0][0]][3], 300)],
        })
    rows = [ReplyOption(key=f"purpose-{claim}", label=clip(UNSUPPORTED_CLAIMS[claim][2], 80), available=False,
                        resolution="none", reason=clip(UNSUPPORTED_CLAIMS[claim][3], 260))
            for claim, _ in gaps]
    points = list(card.points)
    cells = [(action, cell) for action, cell in claim_cells(decision, purpose) if cell.level != "one_result"]
    pooled = one_result_cells(decision, purpose)
    question = question_claim(purpose)
    if cells and question and len(points) < 6:
        names = join_names([workflow_name(policy, action) for action, _ in cells], "and")
        points.append(clip(f"Your question: {CLAIM_LABELS[question[0]]}; the reply says what {names} "
                           "give toward it and the step after each.", 300))
    if pooled and question and len(points) < 6:
        names = join_names([workflow_name(policy, action) for action, _ in pooled], "and")
        instead = list(dict.fromkeys(action for _, cell in pooled for action in cell.instead))
        alternatives = [workflow_name(policy, action) for action in instead]
        points.append(clip(
            f"{names} {'gives' if len(pooled) == 1 else 'give'} one result for all the samples: with one sample "
            f"per individual that cannot show {CLAIM_LABELS[question[0]]}; {join_names(alternatives, 'and')} "
            f"{'gives' if len(alternatives) == 1 else 'give'} one result per sample from the same data.", 300))
    if not rows and points == card.points:
        return card
    return card.model_copy(update={"points": points, "unavailable": [*card.unavailable, *rows][:8]})


def _one_result_steps(decision, policy, task: str, state, steps: list[ReplyOption]) -> list[ReplyOption]:
    """Log 368: planning steps for the per-sample workflows, added after the card's own steps.

    Only when no listed workflow has an answering cell for the stated question;
    nothing is removed -- an individual with many samples of their own can
    still plan the one-result workflow the reply was about.
    """
    from ..interpretation.study_purpose_notes import claim_cells, one_result_cells, purpose_from_state

    purpose = purpose_from_state(state, task)
    pooled = one_result_cells(decision, purpose)
    if not pooled or any(cell.level != "one_result" for _, cell in claim_cells(decision, purpose)):
        return steps
    planned = {step.action for step in steps}
    instead = dict.fromkeys(action for _, cell in pooled for action in cell.instead)
    return [*steps, *(plan_step(policy, action) for action in instead if action in RUN_ACTIONS and action not in planned)]


def build_reply_card(result: dict, prompt: NextTurnPrompt, policy, *, task: str) -> ReplyCard | None:
    """The card for a finished turn, or None when the turn is a wizard or not a policy run."""
    if not isinstance(policy, ProjectPolicySnapshot):
        return None
    plan = WorkflowPlan.model_validate(result["plan"])
    if plan.status in {"needs_input", "needs_confirmation"}:
        return None
    decision = TaskDecision.model_validate(plan.decision)
    results = effective_results([ToolExecutionResult.model_validate(item) for item in result.get("tool_results", [])])
    kind = str(result.get("reply_kind") or "")
    card = _run_card(plan, results, result.get("evaluation")) if kind == "execution" else None
    if card is None:
        card = _core_card(kind, decision, policy, task)
    if card is not None and card.kind in _INPUT_ALTERNATIVE_CARDS:
        card = _with_input_alternative(card, decision, policy, task, result)
    if card is not None and kind != "execution":
        card = _with_outside_steps(card, decision, task)
        card = _with_study_purpose(card, kind, decision, policy, task, result)
    outputs = [
        path.removeprefix("/work/")
        for item in results if item.action.startswith("run_") and item.status == "success"
        for path in item.artifacts
    ]
    steps = [*(card.next_steps if card else []),
             *next_steps(prompt, policy, outputs=outputs, has_choices=bool(card and card.choices))]
    if (card is not None and card.kind in {"workflow_guidance", "composition"} and not card.choices
            and prompt.kind == "completed" and prompt.allow_workflow_continuation
            and decision.capability_match_status == "exact"
            and not any(step.resolution == "plan_workflow" for step in steps)
            and (action := _single_action(decision, policy)) is not None and action in RUN_ACTIONS):
        # A verified single-workflow answer: planning it is the obvious next step,
        # through the same continuation the reply classifier would produce.
        steps.insert(len(card.next_steps), plan_step(policy, action))
    if card is not None and kind not in {"execution", "unresolved"}:
        steps = _one_result_steps(decision, policy, task, result, steps)
    chosen = {option.action for option in (card.choices.options if card and card.choices else []) if option.action}
    steps = [step for step in steps if not (step.resolution == "confirm_workflow" and step.action in chosen)]
    if card is None:
        if not steps:
            return None
        card = ReplyCard(kind="general", headline="", points=[])
    return card.model_copy(update={"next_steps": steps[:6]})
