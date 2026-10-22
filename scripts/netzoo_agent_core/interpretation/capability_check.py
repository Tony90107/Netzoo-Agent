"""Verify the capability check, cover every sentence, and say what was understood (Log 387).

The model proposes, sentence by sentence, what the request asks for and which
capability-sheet entries give it (`graph.capability_check_call`). Code then:

- keeps a requirement only when its quote is in the request (`_locate`);
- decides each result's status from the sheet alone: `available` when a direct
  produces entry gives it, `with_step` when only a with-step entry does,
  `not_available` when none does -- near misses never decide anything;
- covers every request sentence: one that no kept quote overlaps is listed as
  not checked, never silently dropped (the user's Q3, 2026-10-08: an omitted
  requirement that cannot be done turns the rest back into a false yes);
- calls a full gap only when there is at least one result, every result is
  not available, and no sentence was left unchecked.

The reply always opens with what was understood, so a misreading is visible.
"""

from __future__ import annotations

import re

from ..capability_sheet import data_units, entry, result_forms, sheet_entries
from .needed_facts import (
    applicable_unknowns, check_unknowns, fact_line, fact_update, file_checked_note, needed_fact_reply, resolve_unknowns,
    verified_unknown_domains, verified_unknown_scopes, verified_unknowns,
)
from ..contracts.capability_check import (
    CONDITIONS, CapabilityCheck, CheckedRequirement, full_gap as _full_gap, proposal_sentences, reading_version,
)
from .count_alternatives import (count_update, file_count_note, verified_count_alternatives, weigh_credited_counts,
                                 weigh_sample_doubts)
from .request_spans import _locate_tokens, _span, distinct_passages  # noqa: F401 -- research tools import _span
from .request_readings import only_inputs, ruled_out_inputs, stated_quotes, uncertain_quotes, verified_goal  # noqa: F401
from .method_conditions import (
    method_fitting, named_limits, request_method_for, request_method_limit, settings_apart, typed_setting,
    verified_method, with_request_method,
)
from .request_facts import FactRecord
from .required_conditions import quantity_note
from .sentence_ownership import owned_sentences, request_sentences
from .requirement_split import (
    ask_conditions, condition_requirements, delivery_requirements, form_condition_spans, split_additions, unmet,
)
from .stated_reasons import _form_reasons, claim_sentences, stated  # noqa: F401 -- research tools import _form_reasons
from .unconfirmed_routes import checked_body_result

__all__ = [
    "build_capability_check", "verified_conditions", "verified_method", "method_fitting", "stated_requirements",
    "condition_pairs",
    "apply_condition_answers", "redirect_pairs", "apply_redirect_answers",
    "workflow_description", "request_sentences", "understanding_paragraph", "full_gap_reply",
    "full_gap_result", "whole_check_result", "wait_on_asked",
    "with_capability_check_reply", "unavailable_rows", "second_opinion_pairs", "blank_requirement_pairs",
    "apply_second_opinion",
    "implied_actions", "requirement_for", "delivering_actions", "checked_route_lines", "checked_body_result",
]

def _status(delivered: list[str]) -> str:
    levels = {entry(key).level for key in delivered}
    if "direct" in levels:
        return "available"
    return "with_step" if levels else "not_available"


_TYPED = ("scale", "omics_layers", "data_unit", "regulator_kinds", "needs_sign", "input_network",
          "group_membership", "time_model", "spatial", "samples_matched", "mutation_origin", "value_type", "mirna_driver")
_UNSTATED_FORM = {"group_membership": "not_stated", "time_model": "not_dynamic", "spatial": "not_spatial"}
"""Each result form's value when the request's words do not state the form no registered workflow gives."""
RESULT_FORM_OFF = {name: CONDITIONS[name][1] for name in _UNSTATED_FORM}
"""The form value that rules results out (`CONDITIONS`): several_groups, dynamic, uses_neighbors."""


def verified_conditions(task: str, proposal) -> dict[str, str]:
    """Log 412: the request-level conditions that rule results out and whose words are in the request."""
    conditions = getattr(proposal, "conditions", None)
    found = {}
    for name, (_values, rules_out, _description) in CONDITIONS.items():
        quote = (getattr(conditions, f"{name}_quote", "") or "").strip()
        if getattr(conditions, name, None) == rules_out and quote and _span(task, quote) is not None:
            found[name] = rules_out
    count = getattr(conditions, "joint_layers", None)
    quote = getattr(conditions, "joint_layers_quote", "")
    from ..workflow_conditions import stated_numbers
    if count is not None and count > 0 and quote and _span(task, quote) is not None and count in stated_numbers(quote):
        found["joint_layers"] = str(count)
    return found


def _open_choices(task: str, proposal, conditions, place) -> tuple[list[CheckedRequirement], set]:
    """Verdict layer step 2b: each result choice whose options, fitted to the sheet, lead to different workflows.

    Options are asks the model reads and credits like any other; a choice the model types a methods choice
    (`differs_in` method) is left to routing's tie, and one whose options lead to the same workflows decides nothing.
    """
    known = sheet_entries()
    found, option_spans = [], set()
    for choice in getattr(getattr(proposal, "conditions", None), "open_choices", None) or ():
        placed = [(span, option) for option in choice.options if (span := place(option.quote)) is not None]
        if choice.differs_in != "result" or len({span for span, _ in placed}) < 2:
            continue
        outcomes = {task[a:b]: _fitting([k for k in option.delivered_by if known.get(k) and known[k].kind == "produces"],
                                        _with_conditions(option, conditions))
                    for (a, b), option in placed}
        led_to = {frozenset(entry(key).action for key in keys) for keys in outcomes.values()}
        if len(led_to) < 2 or not any(outcomes.values()):
            continue
        said = _span(task, choice.quote)
        quote = task[said[0]:said[1]] if said else " or ".join(outcomes)
        option_spans.update(span for span, _ in placed)
        found.append(CheckedRequirement(
            quote=quote, kind="result", status="needs_fact", depends_on="choice", outcomes=outcomes,
            unknown_quote=quote, delivered_by=list(dict.fromkeys(k for keys in outcomes.values() for k in keys))))
    return found, option_spans


def wait_on_asked(check: CapabilityCheck, pairs) -> CapabilityCheck:
    """Verdict layer step 2: a fact the user said they do not know decides among the workflows the second opinion
    weighed, when the first reading credited none.

    Live check 2026-10-13: B30 ("partial-correlation networks linking my omics layers ... never said whether there
    are two layers or more") and F46 ("請跑 CONDOR ... 我不確定節點角色") credited nothing; the second opinion was asked
    about DRAGON/LIONESS-DRAGON and CONDOR, answered part/none, and the turn was refused -- though the unknown layer
    count and node roles are exactly what decide those workflows.
    """
    if not check.unknowns:
        return check
    known = sheet_entries()
    asked: dict[int, list[str]] = {}
    for index, _action, keys in pairs:
        asked.setdefault(index, []).extend(k for k in keys if known.get(k) and known[k].kind == "produces")
    requirements = list(check.requirements)
    for index, keys in asked.items():
        item = requirements[index]
        if item.status not in ("not_available", "available", "with_step"):
            continue
        unknowns = check_unknowns(check, item.quote)
        if not unknowns:
            continue
        possible, analyses = resolve_unknowns(_fitting, list(dict.fromkeys(keys)),
                                             {**item.attrs, "_method": item.method}, unknowns)
        update = fact_update(possible, analyses, _status, check.unknown_domains)
        if update is not None:
            requirements[index] = item.model_copy(update=update)
    if requirements == check.requirements:
        return check
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, check.unchecked)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})


_CHECKED_ABOUT = ("how_computed", "what_it_contains")


def stated_requirements(task: str, proposal, check: CapabilityCheck, own_sentence: bool = False) -> list[str]:
    """Log 414: the other requirements to check against credited workflows, as quoted in the request.

    Kept only when they say how a result is computed or what it must contain (never a file format, a name,
    or which samples to use), their words are in the request, and they lie outside every asked-for result's
    own words -- an ask's own words were already read with it.

    `own_sentence` (M2, user decision): those in a sentence that asks for a result, outside its words, which were
    dropped (a24b N35 "in which the miRNA-gene edge weights are driven by our ... miRNA expression levels", MX14 "set
    it to re-run automatically every Monday"). They are checked too, and one no credited workflow meets is a
    requirement of its own (`requirement_split.apply_own_sentence_answers`), so the result it sits beside stands.
    """
    conditions = getattr(proposal, "conditions", None)
    asked = [span for item in check.results() if (span := _span(task, item.quote)) is not None]
    # Pre-measure (Log 414): "from expression, motifs and PPI", inside the sentence that asks for the network, was
    # filed as how_computed and once answered "violates" for a supported result (heldout16 PC4). A requirement
    # stated outside the asks is a sentence of its own: one that holds no asked-for result's words.
    asking = [(s, e) for s, e in request_sentences(task) if any(a < e and s < b for a, b in asked)]
    kept = []
    for other in getattr(conditions, "other_requirements", None) or []:
        span = _span(task, other.quote) if other.about in _CHECKED_ABOUT and other.quote.strip() else None
        if span is None or any(s < span[1] and span[0] < e for s, e in asking) != own_sentence:
            continue
        if own_sentence and any(a <= span[0] and span[1] <= b for a, b in asked):
            continue  # an ask's own words were read with it
        kept.append(task[span[0]:span[1]])
    return list(dict.fromkeys(kept))


def condition_pairs(check: CapabilityCheck, stated: list[str]) -> list[tuple[int, str, list[str], str]]:
    """(requirement index, workflow action, its entries, stated requirement) for every workflow the check
    credited a result to (Log 414).

    The workflow is shown with all of its produces entries that fit the ask's typed attributes, not only the
    credited one: a stated "each edge needs an adjusted p-value" beside a network credited to DRAGON's network
    entry is met by DRAGON's p-value entry, and showing the network alone would invite a false "violates".

    Round m3 (P08): words that are a setting the check already verified for that workflow are not asked about again
    (`method_conditions.typed_setting`); the setting's own rules judged them.
    """
    from types import SimpleNamespace

    known = sheet_entries()
    pairs = []
    for index, item in enumerate(check.requirements):
        if item.kind != "result" or item.status not in ("available", "with_step", "partial"):
            continue
        for action in dict.fromkeys(entry(key).action for key in item.delivered_by):
            produces = [key for key, found in known.items() if found.kind == "produces" and found.action == action]
            keys = (_fitting(produces, SimpleNamespace(**item.attrs)) if item.attrs else produces) or produces
            workflow = entry(keys[0]).workflow
            pairs += [(index, action, keys, quote) for quote in stated
                      if not typed_setting(item.method, workflow, quote)]
    return pairs


def workflow_description(keys: list[str]) -> str:
    """One workflow's results as the condition check reads them: each result, how to read it, what it needs."""
    known = sheet_entries()
    needs = next((known[key].inputs for key in keys if known[key].inputs), ())
    if not needs:
        action = known[keys[0]].action
        needs = next((item.inputs for item in known.values() if item.action == action and item.inputs), ())
    described = " ".join(" ".join(filter(None, (known[key].text, known[key].reading))) for key in keys)
    return described + (f" Computed from: {'; '.join(needs)}." if needs else "")


def redirect_pairs(check: CapabilityCheck, candidates: list[str]) -> list[tuple[int, str, list[str], str]]:
    """Log 414: for a result every credited workflow was removed from, the other offered workflows to ask about.

    Pre-measure, seen heldout17 KP3: "the hospital effect should be separated from the co-expression" removed
    LIONESS-COEXPRESSION, rightly, while COBRA -- which routing offered -- gives exactly that. Without asking the
    other offered workflows the supported request was refused.
    """
    from types import SimpleNamespace

    known = sheet_entries()
    pairs = []
    for index, item in enumerate(check.requirements):
        if item.kind != "result" or item.status != "not_available" or not item.violations:
            continue
        quotes = list(dict.fromkeys(reason.split(' does not meet "', 1)[1].rstrip('"') for reason in item.violations))
        removed = {reason.split(" does not meet ", 1)[0] for reason in item.violations}
        for action in candidates:
            produces = [key for key, found in known.items() if found.kind == "produces" and found.action == action]
            keys = _fitting(produces, SimpleNamespace(**item.attrs)) if item.attrs else produces
            keys = method_fitting(item.method, keys)[0]  # M1: the named method, its settings, the data size
            if keys and known[keys[0]].workflow not in removed:
                pairs += [(index, action, keys, quote) for quote in quotes]
    return pairs


def apply_redirect_answers(check: CapabilityCheck, pairs: list[tuple[int, str, list[str], str]],
                           answers: list) -> CapabilityCheck:
    """Credit an offered workflow answered `satisfies` for every stated requirement it was asked about."""
    verdicts: dict[tuple[int, str], list] = {}
    for (index, action, keys, _quote), answer in zip(pairs, answers):
        verdicts.setdefault((index, action), [keys, True])[1] &= answer == "satisfies"
    requirements = [item.model_copy() for item in check.requirements]
    for (index, _action), (keys, satisfied) in verdicts.items():
        if satisfied:
            item = requirements[index]
            delivered = list(dict.fromkeys([*item.delivered_by, *keys]))
            requirements[index] = item.model_copy(update={"delivered_by": delivered, "status": _status(delivered)})
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, check.unchecked)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})


def apply_condition_answers(check: CapabilityCheck, pairs: list[tuple[int, str, list[str], str]],
                            answers: list) -> CapabilityCheck:
    """Remove each credited workflow answered `violates`; satisfies, unrelated and not_about_results change nothing
    (Log 414; items 4-5 c2: a name for the output files is never a reason to remove a workflow).

    Nothing is ever made unconfirmed here: a result keeps its verdict unless a workflow is found unable to meet
    a stated requirement, and only that workflow is removed.
    """
    removed: dict[int, dict[str, list[str]]] = {}
    for (index, action, keys, quote), answer in zip(pairs, answers):
        if answer == "violates":
            removed.setdefault(index, {}).setdefault(action, [])
            if quote not in removed[index][action]:
                removed[index][action].append(quote)
    requirements = [item.model_copy() for item in check.requirements]
    for index, actions in removed.items():
        item = requirements[index]
        delivered = [key for key in item.delivered_by if entry(key).action not in actions]
        names = {action: entry(keys[0]).workflow for _index, action, keys, _quote in pairs}
        reasons = [unmet(names[action], quote) for action, quotes in actions.items() for quote in quotes]
        status = ("partial" if delivered else "not_available") if item.status == "partial" else _status(delivered)
        requirements[index] = item.model_copy(update={
            "delivered_by": delivered, "status": status, "violations": list(dict.fromkeys(reasons))})
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, check.unchecked)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})


def _with_conditions(item, conditions: dict[str, str]):
    """The ask with each request-level condition it does not state itself (Log 412).

    A condition never overrides what the ask's own words say: a data unit the ask states (pseudo-bulk
    profiles are bulk samples) stands, and overlapping membership concerns only an ask about groups (by
    its own form or the grouping entries it was credited to), matched samples only an ask over two or
    more omics layers.
    """
    update = {}
    if conditions.get("data_unit") and item.data_unit == "not_stated":
        update["data_unit"] = conditions["data_unit"]
    known = sheet_entries()
    # Log 413 (heldout18 CK4, CK6): "communities" and "patient subtypes" were read as not about groups, so
    # the ask's own form missed them; a result the sheet says puts each item in one group is about groups.
    grouping = any(known[key].groups for key in item.delivered_by if key in known)
    if conditions.get("group_membership") and (getattr(item, "group_membership", None) in ("one_group", "not_stated")
                                               or grouping):
        update["group_membership"] = conditions["group_membership"]
    for name in ("spatial", "time_model"):
        if conditions.get(name):
            update[name] = conditions[name]
    # 2026-10-22 (user decision): an ask's form rules a workflow out only with the request's own words for it. The
    # ask's typed form has no quote; gpt-4o-mini typed "split the tumors into 2-5 subtypes" several_groups with an
    # empty request-level quote (h5 Q26, J22, M45) and SAMBAR or CONDOR was refused (subtypes-regression-2026-10-22).
    for name, neutral in _UNSTATED_FORM.items():
        if getattr(item, name, None) == RESULT_FORM_OFF[name] and conditions.get(name) != RESULT_FORM_OFF[name]:
            update.setdefault(name, neutral)
    for name in ("mutation_origin", "value_type", "mirna_driver"):
        if conditions.get(name) and getattr(item, name, "not_stated") == "not_stated":
            update[name] = conditions[name]
    if conditions.get("joint_layers") and item.omics_layers == 0:
        update["omics_layers"] = int(conditions["joint_layers"])
    if conditions.get("samples_matched") and update.get("omics_layers", item.omics_layers) >= 2:
        update["samples_matched"] = conditions["samples_matched"]
    return item.model_copy(update=update) if update else item


def _fitting(keys: list[str], item) -> list[str]:
    """The delivered entries that fit the ask's typed attributes (Logs 388-389).

    Data unit, regulator kinds, sign, layers, input network and a stated scale can rule every entry
    out -- no registered workflow takes single cells, models lncRNA regulators, signs
    PANDA's edges, joins three omics layers, partitions a gene-gene network, or gives a per-patient network from
    PANDA or OTTER. An unstated scale rules nothing out.

    Item 3 (2026-10-14): until now a scale only narrowed the list and never emptied it (Log 388: a misread scale must
    not turn a deliverable result into a gap), so a per-patient network credited to OTTER alone stayed OTTER's. On the
    recorded checks the empties were not misreads of the request but sheet labels too narrow for a label or test read
    per sample and reported for the cohort (33 of 35 distinct asks: "patient subtypes" typed per sample, "a test
    between responders and non-responders" typed whole-cohort, all supported); those entries now carry both scales
    (`capability_sheet.yaml`), and on the 654 recorded asks with a typed scale the hard rule changes 2, both already
    misread as DRAGON (`docs/research-log/scale-hard-2026-10-14`).
    """
    known = sheet_entries()
    if item.data_unit != "not_stated" and item.data_unit not in data_units():
        return []
    if any(getattr(item, form, None) not in (None, *allowed) for form, allowed in result_forms().items()):
        return []  # Log 402: overlapping groups, dynamics or spatial neighbours
    wanted = set(item.regulator_kinds)
    # Log 412: a multi-omic entry models layers measured on the same samples (its inputs: "same samples").
    unmatched = any(getattr(item, name, None) == "different_samples" for name in ("samples_matched", "sample_alignment"))
    keys = [k for k in keys
            if (known[k].layers is None or (item.omics_layers <= known[k].layers and not unmatched))
            and (known[k].regulators is None or wanted <= known[k].regulators)
            and not (item.needs_sign and known[k].signed is False)
            and (known[k].input_network is None
                 or getattr(item, "input_network", "none") in ("none", "not_stated", known[k].input_network))]
    from workflow_registry import ACTION_DEFINITIONS
    def data_fits(key):
        definition = ACTION_DEFINITIONS.get(known[key].action)
        modalities = definition.output_capability.accepted_input_modalities if definition and definition.output_capability else ()
        if "somatic_mutation" in modalities and getattr(item, "mutation_origin", None) == "germline":
            return False
        if "multi_omic_continuous" in modalities and getattr(item, "value_type", None) == "binary":
            return False
        if known[key].regulators and "mirna" in known[key].regulators and getattr(item, "mirna_driver", None) == "measured_expression":
            return False
        samples = getattr(item, "fact_sample_count", None)
        if samples is not None:
            method = {**getattr(item, "_method", {}), "samples": samples}
            return bool(method_fitting(method, [key])[0])
        return True
    keys = [key for key in keys if data_fits(key)]
    want = {"per_sample": "sample_specific", "whole_cohort": "aggregate"}.get(item.scale)
    return [k for k in keys if want is None or want in known[k].granularity]


def build_capability_check(
    task: str, proposal, verified_claims: dict[str, str] | frozenset[str] = frozenset(),
    counted_samples: tuple[int, str] | None = None,
) -> tuple[CapabilityCheck, list[dict]]:
    """The verified check for one proposal, and what was rejected.

    A registry-wide reason (no causal proof, no prediction) is kept only when the
    study-purpose reader verified that claim with its cue words: the smoke run cited
    both for a splicing request. Given with the claims' words, the reply says one only for a
    result in a sentence holding them (ROUND-20, `stated_reasons.claim_sentences`).

    A passage asked for several times is one requirement; when one reading names an
    entry and another names none (Log 387 dev round: a network and a forecast quoted as
    one sentence twice) it is `partial`, never `available`.

    `counted_samples` (ROUND-07): (samples, path) counted in the named expression file (`weigh_sample_doubts`).
    """
    known = sheet_entries()
    rejected, spans, asks, other = [], [], {}, {}
    conditions = verified_conditions(task, proposal)
    unknown_scopes = verified_unknown_scopes(task, proposal)
    unknown_domains = verified_unknown_domains(task, proposal)
    form_spans = form_condition_spans(task, proposal, conditions)  # M2: conditions on the result's form
    # ROUND-03: every count and setting the reading writes is one record; methods and candidates are compiled from it.
    record = FactRecord(task)
    whole = record.read_request(proposal)
    scoped = reading_version(proposal) == 2
    sentences, ownership_rejected = owned_sentences(task, proposal_sentences(proposal))  # before any read of them
    alternatives, unknowns = record.read_doubts(proposal, verified_unknowns(task, proposal),
                                               unknown_domains, unknown_scopes, sentences)

    def place(quote: str):
        span = _span(task, quote)
        if span is None:
            rejected.append({"quote": quote, "reason": "quote_not_in_request"})
        else:
            spans.append(span)
        return span

    rejected.extend(ownership_rejected)
    asked = [found for sentence in sentences for item in sentence.asks
             if (found := _span(task, item.quote)) is not None]
    for sentence in sentences:
        for kind, quotes in (("context", sentence.has), ("about_methods", sentence.about_methods)):
            for quote in quotes:
                if (span := place(quote)) is not None:
                    other.setdefault(span, kind)
        for item in sentence.asks:
            if (span := place(item.quote)) is None:
                continue
            question = getattr(item, "asked_as", "request") == "question"
            if ((sentence.role == "background" or sentence.role == "methods_question" and not question)
                    and not (item.delivered_by or item.not_by)):
                # The model's own role rules out an ask it matched to nothing (Log 387 dev round 3:
                # "We have expression from 50 kidney samples ..." filed as an ask); an ask it
                # matched to an entry stands. The words still count as read. Log 403: an ask the
                # model says was asked as a question about which method gives it is a result asked
                # for, whatever the sentence's role (o10 SN6, heldout8 QU2-QU8: never checked).
                other.setdefault(span, "context" if sentence.role == "background" else "about_methods")
            else:
                kept, item = ask_conditions(item, conditions, form_spans, asked)
                asks.setdefault(span, []).append(_with_conditions(item, kept))
    asks, additions = split_additions(task, asks, request_sentences(task))  # M2: what an ask adds to a result
    # Phase 5b (m3 U12 trace): only results some workflow is credited with count as several; an uncredited row
    # ("I need a capability judgment that waits for the size fact") kept the count off the one real result.
    credited_results = distinct_passages(span for span, items in asks.items() if any(  # overlapping words: one result
        known.get(k) and known[k].kind == "produces" for item in items for k in item.delivered_by))
    requirements, apart = [], {}
    for span, items in asks.items():
        # M1: each reading is held to the method, settings and data size it states.
        applicable = applicable_unknowns(unknowns, unknown_scopes, unknown_domains, task[span[0]:span[1]],
                                         credited_results <= 1)
        result = task[span[0]:span[1]]
        own = [record.read_method(item, "result", result) for item in items]
        methods = own
        workflows = [{known[k].workflow for k in item.delivered_by if known.get(k)} for item in items]
        applied = None
        if len(asks) == 1 and whole:  # live m1a F1: the request's own method and settings, for its one result
            applied = [whole] * len(items)
        elif whole:  # M2: with several results, only what names a workflow a result is credited to
            applied = [request_method_for(whole, found) for found in workflows]
        if scoped:  # ROUND-04, shape 2: the counts and settings are the request's, each with its scope
            applied = [{**{key: given[key] for key in ("named", "named_quote") if key in given},
                        **record.scoped_method(span, result, len(asks) == 1, found)}
                       for given, found in zip(applied or [{}] * len(items), workflows)]
        if applied is not None:
            methods = [with_request_method(method, given) for method, given in zip(own, applied)]
            for mine, given, merged in zip(own, applied, methods):
                record.note_conflicts(result, mine, given, merged)
        # ROUND-07: a sample count the user is unsure of -- answered by the named file, or else set aside
        methods, applicable, here = weigh_sample_doubts(record, result, methods, applicable, alternatives,
                                                        counted_samples if credited_results <= 1 else None)
        # Round m3 (MX12): a setting no credited workflow can use, stated apart from every asked result, is a
        # requirement of its own; the result is read without it.
        for index, (item, method) in enumerate(zip(items, methods)):
            credited = [k for k in item.delivered_by if known.get(k) and known[k].kind == "produces"]
            methods[index], found = settings_apart(task, method, credited, list(asks))
            apart.update((row.quote, row) for row in found)
        pre = [_fitting([k for k in item.delivered_by if known.get(k) and known[k].kind == "produces"], item)
               for item in items]  # the credits before the data size is judged
        fitted = [method_fitting(method, keys) for method, keys in zip(methods, pre)]
        readings = [keys for keys, *_rest in fitted]
        limits = list(dict.fromkeys(reason for _keys, reasons, *_rest in fitted for reason in reasons))
        instead = list(dict.fromkeys(key for _keys, _limits, others, _defaults in fitted for key in others))
        defaults = list(dict.fromkeys(key for *_rest, own in fitted for key in own))
        blocks = list(dict.fromkeys(known[k].workflow for keys, (kept, _r, others, _d) in zip(pre, fitted)
                                    for k in keys if k not in kept and k not in others))  # ROUND-17: run limits
        method = next((found for found in methods if found), {})
        if not any(pre) and (named_reasons := named_limits(method)):  # ROUND-18: why the named one cannot run
            limits, blocks = limits or named_reasons, blocks or [method["named"]]
        delivered = list(dict.fromkeys(k for keys in readings for k in keys))
        not_by = list(dict.fromkeys(
            k for item in items for k in item.not_by
            if known.get(k) and (known[k].kind == "near_miss"
                                 or (known[k].kind == "registry_wide" and known[k].claim in verified_claims))))
        status = "partial" if delivered and not all(readings) else _status(delivered)
        attrs = {key: getattr(items[0], key) for key in _TYPED if hasattr(items[0], key)}
        if "samples_matched" not in attrs and items[0].omics_layers >= 2:
            attrs["samples_matched"] = "not_stated"
        blank = not any(item.delivered_by or item.not_by for item in items)
        asked_as = "question" if all(getattr(item, "asked_as", "request") == "question" for item in items) \
            else "request"
        waiting = {}
        # Verdict layer step 2: a fact the user said they do not know, on which this result's workflows differ.
        read = method_fitting(method, list(dict.fromkeys(k for item in items for k in item.delivered_by
                                                         if known.get(k) and known[k].kind == "produces")))[0]
        fit_attrs = {name: getattr(items[0], name) for name in (*_TYPED, "samples_matched") if hasattr(items[0], name)}
        fit_attrs["_method"] = method
        if applicable:
            possible, analyses = resolve_unknowns(_fitting, read, fit_attrs, applicable)
            update = fact_update(possible, analyses, _status, unknown_domains)
            if update is not None:
                status, delivered = update.pop("status"), update.pop("delivered_by")
                waiting = update
        if here and (found := count_update(task, here, method, list(dict.fromkeys(
                k for keys in pre for k in keys)), task[span[0]:span[1]], credited_results <= 1)) is not None:
            record.note_set_aside(result, method, found["method"])  # ROUND-07 (G2): the doubt, not the one number
            method, limits = found.pop("method"), found.pop("limits")  # phase 5b: each candidate judged in code
            status, delivered, waiting = found.pop("status"), found.pop("delivered_by"), found
        fact_ids = record.ids_for(method, waiting.get("unknown_quote", "") if waiting.get("by_code") else "")
        requirements.append(CheckedRequirement(quote=task[span[0]:span[1]], kind="result", status=status,
                                               delivered_by=delivered, not_by=not_by, attrs=attrs, blank=blank,
                                               asked_as=asked_as, method=method, limits=limits, instead=instead,
                                               defaults=defaults, fact_ids=fact_ids, blocks=blocks, **waiting))
    requirements += [item.model_copy(update={"fact_ids": record.ids_for(item.method)}) for item in apart.values()]
    spans += [found for item in apart.values() if (found := _span(task, item.quote)) is not None]
    choices, option_spans = _open_choices(task, proposal, conditions, place)
    requirements = [item for item in requirements if _span(task, item.quote) not in option_spans] + choices
    requirements += [CheckedRequirement(quote=task[span[0]:span[1]], kind=kind, status="not_checked")
                     for span, kind in other.items() if span not in asks]
    if whole and not any(item.kind == "result" for item in requirements):
        stated = getattr(proposal, "conditions", None)
        said = {name: task[found[0]:found[1]] for name in conditions
                if (quote := (getattr(stated, f"{name}_quote", "") or "").strip())
                and (found := _span(task, quote)) is not None}
        if (found := request_method_limit(whole, conditions, said, task)) is not None:
            requirements.append(found.model_copy(update={"fact_ids": record.ids_for(found.method)}))
    covered = [*asks, *(found for item in additions if (found := _span(task, item.quote)) is not None)]
    requirements += additions + condition_requirements(task, conditions, form_spans, covered)
    spans += [span for span in form_spans.values() if not any(a <= span[0] and span[1] <= b for a, b in asks)]
    deliveries = delivery_requirements(task, proposal, [item for item in requirements if item.kind == "result"])
    requirements += deliveries
    spans += [span for item in deliveries if (span := _span(task, item.quote)) is not None]
    # Log 392 (B): the schema has one field per numbered sentence, so a sentence the model
    # gave a background or methods-question role was read even when it quoted nothing
    # (TEST_PROMPTS r9: such background sentences were listed as "Not checked").
    read = {index for index, sentence in enumerate(proposal_sentences(proposal))
            if sentence.role in ("background", "methods_question")}
    unchecked = [task[s:e].strip() for index, (s, e) in enumerate(request_sentences(task))
                 if index not in read and not any(a < e and s < b for a, b in spans)]
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, unchecked)
    goal, goal_quote = verified_goal(task, proposal)
    return CapabilityCheck(requirements=requirements, unchecked=unchecked, full_gap=full_gap,
                           conditions=conditions, unknowns=[list(item) for item in unknowns], unknown_scopes=unknown_scopes,
                           unknown_domains=unknown_domains, goal=goal, goal_quote=goal_quote,
                           stated_quotes=stated_quotes(task, proposal),
                           uncertain_quotes=uncertain_quotes(task, proposal),
                           ruled_out=ruled_out_inputs(task, proposal),
                           claim_sentences=claim_sentences(task, verified_claims, deliveries),
                           count_alternatives=[{k: v for k, v in item.items() if k not in ("span", "read_by")}
                                               for item in alternatives],
                           facts=record.facts_list(), fact_conflicts=list(record.conflicts),
                           **dict(zip(("only_inputs", "only_inputs_quote"), only_inputs(task, proposal)))), rejected


def _names(names: list[str]) -> str:
    names = list(dict.fromkeys(names))
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _workflows(keys: list[str]) -> str:
    return _names([entry(key).workflow for key in keys])


def _lower_first(text: str) -> str:
    """"The motif prior ..." -> "the motif prior ...", but "DRAGON returns ..." stays."""
    return text[:1].lower() + text[1:] if text[1:2].islower() else text


def _why_not(item: CheckedRequirement, check: CapabilityCheck | None = None) -> list[str]:
    if (item := stated(item, check)) is None:  # ROUND-20: only the reasons code can verify
        return []
    cited = []
    for key in item.not_by:
        found = entry(key)
        cited.append(found.why_not if found.kind == "registry_wide"
                     else f"{found.workflow} does not give it: {_lower_first(found.why_not)}")
    forms = _form_reasons(item) if item.status == "not_available" else []
    reasons = [*(f"{reason}." for reason in item.violations[:1]), *forms, *cited[:1]]
    if item.limits and item.status == "not_available":
        # M1: the method, a setting or the data size is the reason; another method is offered only as one.
        named = item.method.get("named_quote")
        alternative = ([f"{_workflows(item.defaults)} itself can still run, with its own settings instead -- an "
                        "alternative, not the setting you asked for."] if item.defaults else
                       [f'{_workflows(item.instead)} gives this result with its own method instead -- an alternative, '
                        f'not "{named}".'] if item.instead and named else [])
        reasons = [f"{item.limits[0]}.", *alternative, *(f"{reason}." for reason in item.limits[1:]), *reasons]
    return list(dict.fromkeys(reasons))[:2]


def _line(item: CheckedRequirement, provisional: bool = False, gap_unconfirmed: bool = False, check=None) -> str:
    line = _status_line(item, provisional, gap_unconfirmed, check)
    if item.file_checked and item.status in ("available", "with_step", "partial"):
        line = f"{line} {file_checked_note(item)}"
    return f"{line} {note}" if (note := file_count_note(item)) else line


def _status_line(item: CheckedRequirement, provisional: bool = False, gap_unconfirmed: bool = False,
                 check: CapabilityCheck | None = None) -> str:
    quote = f'"{item.quote}"'
    if item.status == "needs_fact":
        return fact_line(item)
    if item.status == "available":
        names = _workflows([k for k in item.delivered_by if entry(k).level == 'direct'])
        if provisional:  # phase 3 (round p3 C42, C43): what only the backup read is never said as available
            return f"{quote} -- the backup check matched {names} to this (not confirmed)."
        return f"{quote} -- available from {names}."
    if item.status == "partial":
        return (f"{quote} -- partly available: {_workflows(item.delivered_by)} gives part of it; no registered "
                "workflow produces the rest.")
    if item.status == "with_step":
        first = entry(item.delivered_by[0])
        return (f"{quote} -- available from {_workflows(item.delivered_by)}'s output plus a step you run "
                f"outside NetZoo: {first.step}")
    if provisional and item.status == "not_available":
        return f"{quote} -- {PROVISIONAL_NOT_MATCHED[0].lower()}{PROVISIONAL_NOT_MATCHED[1:]}"
    if gap_unconfirmed and item.status == "not_available":
        return f"{quote} -- {GAP_UNCONFIRMED_NOT_MATCHED[0].lower()}{GAP_UNCONFIRMED_NOT_MATCHED[1:]}"
    reasons = _why_not(item, check)
    if not reasons:
        return f"{quote} -- {NOT_MATCHED}"
    if item.limits:
        return " ".join([f"{quote} -- not available here as asked.", *reasons])
    return " ".join([f"{quote} -- not available here: no registered workflow produces this.", *reasons])


NOT_MATCHED = "not matched to any registered workflow."
"""A result row with no reason code can verify (ROUND-20); a reply built from such rows claims nothing more."""


def understanding_paragraph(check: CapabilityCheck, offers_methods: bool = True) -> str | None:
    """What the request was understood to ask for, one line per result, plus the unchecked sentences.

    `offers_methods`: False when the reply below lists no method (Log 403 part D), so the
    unconfirmed note does not point to methods that are not there.
    """
    results = check.results()
    if not results and not check.unchecked and not check.provisional:
        return None
    lines = ["What I understood you are asking for:"] if results else []
    lines += [f"{index}. {_line(item, check.provisional, check.gap_unconfirmed, check)}{quantity_note(check, item)}"
              for index, item in enumerate(results, 1)]  # ROUND-10: an unstated quantity condition is said
    lines += [f'Not checked against the registered workflows: "{sentence}"' for sentence in check.unchecked]
    if check.provisional:
        # Log 403 (o10 SN6): a backup reading with no result in it said nothing at all, and the
        # reply below read as checked.
        lines.append(PROVISIONAL_NOTE if offers_methods else PROVISIONAL_NOTE_SHORT)
    elif check.gap_unconfirmed:
        lines.append(GAP_UNCONFIRMED_NOTE if offers_methods else GAP_UNCONFIRMED_NOTE_SHORT)
    return "\n".join(lines)


def full_gap_reply(check: CapabilityCheck, *, with_note: bool = False) -> str:
    """The full-gap reply; `with_note` when an outside-step note follows (Log 393).

    TEST_PROMPTS r10 test4: "none is offered" read against the note's own "a registered
    route: pseudo-bulk ... then PANDA". The note's route is a different request (bulk, or a
    method not registered here), so the sentence says "as you asked" and points to it.
    """
    many = len(check.results()) > 1
    them, it = ("these", "them") if many else ("this", "it")
    said = any(_why_not(item, check) for item in check.results())  # ROUND-21: else no claim beyond "not matched"
    closing = (f"No registered workflow produces {them} as you asked {it}, so none is offered for {it} as asked. "
               "The note below describes the closest route." if with_note else
               # M1: the result exists, but not by the method, settings or data size asked for.
               f"No registered workflow can give {them} as you asked {it} (above), so none is offered as asked."
               if said and any(item.limits for item in check.results()) else
               f"No registered workflow produces {them}, so none is offered as the way to get {it}." if said else
               f"{'These were' if many else 'This was'} {NOT_MATCHED[:-1]}, so none is offered.")
    return "\n\n".join([
        understanding_paragraph(check) or "",
        closing,
        "No files were inspected and no analysis ran.",
    ])


# Log 401: what the backup model found is said as unconfirmed, and nothing is withdrawn for it.
PROVISIONAL_NOT_MATCHED = "The backup check matched no registered workflow to this (not confirmed)."
PROVISIONAL_NOTE = (
    "The usual capability check could not run this turn, so a backup model read the request; the lines above "
    "are not confirmed, and the methods below were not removed for them."
)

# Log 403: a full gap whose second opinion could not run is unconfirmed too, and acted on no more.
GAP_UNCONFIRMED_NOT_MATCHED = ("The check matched no registered workflow to this, but the second check that "
                               "confirms such a gap could not run (not confirmed).")
GAP_UNCONFIRMED_NOTE = (
    "The second check that confirms a gap could not run this turn, so the lines above are not confirmed, and "
    "the methods below were not removed for them."
)

# Log 403 part D: the same notes when the reply below lists no method.
PROVISIONAL_NOTE_SHORT = ("The usual capability check could not run this turn, so a backup model read the request; "
                          "nothing it found is confirmed.")
GAP_UNCONFIRMED_NOTE_SHORT = ("The second check that confirms a gap could not run this turn, so the lines above are "
                              "not confirmed.")
UNAVAILABLE_NOTE_SHORT = "This turn could not be checked against what the registered workflows produce."

UNAVAILABLE_NOTE = (
    "This turn could not be checked against what the registered workflows produce, so the methods "
    "below have not been confirmed to give what you asked for."
)


def full_gap_result(state, reply) -> dict | None:
    """The whole reply when nothing registered produces what was asked, else None."""
    from ..contracts import TaskDecision

    from ..llm import latest_user_task
    from .outside_steps import with_outside_steps

    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if check is None or not check.full_gap:
        return None
    # Log 392 (A): the verified outside-step notes (Log 320: SCORPION's pseudo-bulk route,
    # SPIDER, ALPACA) stay; TEST_PROMPTS r9 tests 4 and 8 lost them to the full gap.
    task = latest_user_task(state.get("messages") or [])
    plain = full_gap_reply(check)
    if with_outside_steps(plain, decision, task) != plain:
        return reply(with_outside_steps(full_gap_reply(check, with_note=True), decision, task), "capability_check_gap")
    return reply(plain, "capability_check_gap")


def whole_check_result(state, reply) -> dict | None:
    """The whole reply when the check alone answers the turn: a full gap (Log 387), a run it did not approve (items
    1-2, `run_hold`), or results waiting on facts the user said they do not know (verdict layer step 2)."""
    from ..contracts import TaskDecision
    from .ask_facts import ask_result
    from .clarify_goal import clarify_result
    from .run_hold import held_run_result

    if (clarify := clarify_result(state, reply)) is not None:  # core decision phase 1: the goal comes first
        return clarify
    if (asked := ask_result(state, reply)) is not None:  # core decision phase 2: the fact agent's questions
        return asked
    if (gap := full_gap_result(state, reply)) is not None:
        return gap
    if (held := held_run_result(state, reply, understanding_paragraph)) is not None:
        return held
    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if decision.action != "no_tool" or check is None or not check.needed_facts():
        return None
    return reply(needed_fact_reply(check, understanding_paragraph(check) or ""), "needs_fact")


def with_capability_check_reply(result: dict, state, reply) -> dict:
    """Open any other reply with what was understood (the full gap has its own reply)."""
    from ..contracts import TaskDecision

    decision = TaskDecision.model_validate(state["decision"])
    check = decision.capability_check
    if check is None or check.full_gap or result.get("reply_kind") in (None, "execution"):
        return result
    listed = result.get("reply_kind") not in ("unmapped_request", "capability_partial")
    paragraph = ((UNAVAILABLE_NOTE if listed else UNAVAILABLE_NOTE_SHORT) if check.unavailable
                 else understanding_paragraph(check, offers_methods=listed))
    if paragraph is None:
        return result
    text = str(result["messages"][-1].content)
    return {**reply(f"{paragraph}\n\n{text}", result["reply_kind"]),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}


def unavailable_rows(check: CapabilityCheck) -> list[tuple[str, str]]:
    """(label, reason) for each result not available here and each unchecked sentence."""
    rows = []
    for item in check.results():
        if item.status == "not_available":
            reasons = ([PROVISIONAL_NOT_MATCHED] if check.provisional else
                       [GAP_UNCONFIRMED_NOT_MATCHED] if check.gap_unconfirmed else _why_not(item, check))
            rows.append((item.quote, reasons[0] if reasons else "Not matched to any registered workflow."))
    rows += [(sentence, "Not checked against the registered workflows.") for sentence in check.unchecked]
    return rows


def requirement_for(check: CapabilityCheck | None, task: str, passages) -> CheckedRequirement | None:
    """The checked result the passages quote, or None (Log 403).

    Each renderer that says what one part of a request gets -- a reading, a step --
    reads the check's verdict on that part from here, so a part the check found
    available is never answered "no registered workflow" (heldout10 SC1: the check
    said the edge test is LIONESS-PANDA's output plus a step outside NetZoo, and the
    per-reading reply said no workflow produces it). A passage stands for the result
    whose words it shares, at least half of the shorter of the two. Passages are
    ordered by the caller: result evidence takes precedence over scale or input
    evidence. A passage spanning several results cannot stand for just one.
    """
    if check is None or check.unavailable:
        return None
    folded = task.casefold()

    def where(text: str):
        text = (text or "").strip().rstrip(".,;:!?").strip()
        start = folded.find(text.casefold()) if text else -1
        return None if start < 0 else (start, start + len(text))

    for passage in passages:
        said = where(passage)
        if said is None:
            continue
        matches = []
        for item in check.results():
            wanted = where(item.quote)
            if wanted is None:
                continue
            shared = min(wanted[1], said[1]) - max(wanted[0], said[0])
            if shared > 0 and shared >= 0.5 * min(wanted[1] - wanted[0], said[1] - said[0]):
                matches.append(item)
        if matches:
            return matches[0] if len(matches) == 1 else None
    return None


def delivering_actions(item: CheckedRequirement) -> list[str]:
    """The workflows a checked result names as giving it, direct ones first."""
    direct = [entry(key).action for key in item.delivered_by if entry(key).level == "direct"]
    stepped = [entry(key).action for key in item.delivered_by if entry(key).level != "direct"]
    return list(dict.fromkeys([*direct, *stepped]))


def checked_route_lines(item: CheckedRequirement, provisional: bool = False) -> tuple[list[str], str] | None:
    """What a part of the request gets by the check's verdict, when routing found it no workflow.

    None when the verdict delivers nothing. The text names the same workflows and the
    same outside step as the understanding line, so the two never disagree.
    """
    if item.status not in ("available", "with_step", "partial") or not item.delivered_by:
        return None
    unconfirmed = " (The backup check found this; it is not confirmed.)" if provisional else ""
    names = _workflows(item.delivered_by)
    if item.status == "with_step":
        first = entry(item.delivered_by[0])
        return ([f"No registered workflow gives this in one step: it comes from {names}'s output plus a step "
                 f"you run outside NetZoo. {first.step}{unconfirmed}"],
                f"{names}, then a step outside NetZoo")
    if item.status == "partial":
        return ([f"Partly available: {names} gives part of it; no registered workflow produces the rest."
                 f"{unconfirmed}"], f"partly {names}")
    return [f"Available from {names}.{unconfirmed}"], names


def implied_actions(requirement: CheckedRequirement) -> list[str]:
    """The workflows a blank verdict's own typed attributes point to (Log 397).

    Only attributes that single out a few workflows count: two or more omics layers
    (the DRAGON family), a sign (GIRAFFE), miRNA regulators (the PUMA family) and a
    regulator-gene input network (CONDOR). TF regulators or a scale point to most of
    the registry and imply nothing, so a blank verdict on, say, copy-number calling has
    no workflow to ask and its gap stands. heldout6 NC6: a metabolite-lipid network
    came back blank with routing failed, omics_layers=2, and was gapped 3/3.
    """
    from types import SimpleNamespace

    attrs = SimpleNamespace(**requirement.attrs) if requirement.attrs else None
    if attrs is None or requirement.status != "not_available" or not requirement.blank:
        return []
    known = sheet_entries()
    def picks(item) -> bool:
        return ((attrs.omics_layers >= 2 and item.layers is not None)
                or (attrs.needs_sign and item.signed is True)
                or ("mirna" in attrs.regulator_kinds and item.regulators is not None and "mirna" in item.regulators)
                or (getattr(attrs, "input_network", "none") == "regulator_gene"
                    and item.input_network == "regulator_gene"))
    keys = [key for key, item in known.items() if item.kind == "produces" and picks(item)]
    return list(dict.fromkeys(known[key].action for key in _fitting(keys, attrs)))


def second_opinion_pairs(check: CapabilityCheck, actions: list[str]) -> list[tuple[int, str, list[str]]]:
    """(requirement index, workflow action, its fitting entry ids) to ask about (Log 390).

    Asked when a full gap would clear an exact routing match. Each not-available
    result is paired with each matched workflow, shown with all of its produces
    entries that fit the ask's typed attributes, because a request can need two
    of one workflow's outputs together (dev smoke: KC8's network with per-edge
    significance is DRAGON's network plus its p-values, and each alone was "no").
    A workflow the attributes rule out entirely is never asked about.
    """
    if not check.full_gap:
        return []
    return _pairs(check, lambda requirement: actions)


def blank_requirement_pairs(check: CapabilityCheck) -> list[tuple[int, str, list[str]]]:
    """Pairs for blank verdicts beside results the check did find (Log 404).

    Log 397 asks about the workflows a blank verdict's own typed attributes point to, but
    only when the whole request was a gap. heldout11 VC4s-2: communities were credited to
    CONDOR, "find each community's core genes" came back blank with a regulator-gene input
    network, and the reply said no workflow gives core genes while describing CONDOR's core
    score. A verdict with a reason (a cited near miss) is not asked again, nor a sibling's
    workflow: on heldout11 that would have asked about a dashboard, a narrative report and a
    differential expression table, all rightly refused.
    """
    if check.full_gap or check.unconfirmed():
        return []
    return _pairs(check, implied_actions)


def _pairs(check: CapabilityCheck, actions_for) -> list[tuple[int, str, list[str]]]:
    from types import SimpleNamespace

    known = sheet_entries()
    pairs = []
    for index, requirement in enumerate(check.requirements):
        # Log 414 / ROUND-10: one a stated requirement, or every candidate count of the user's, ruled out stays out.
        if (requirement.kind != "result" or requirement.status != "not_available" or not requirement.attrs
                or requirement.violations or requirement.unknown_quote and requirement.limits):
            continue
        for action in actions_for(requirement):
            produces = [key for key, item in known.items() if item.kind == "produces" and item.action == action]
            # M1: never a workflow outside the named method or one that cannot take the data; one that lacks only a
            # stated setting is asked about, and credited as itself with its own settings (m1b MX05).
            applicable = check_unknowns(check, requirement.quote)
            potential = (resolve_unknowns(_fitting, produces, {**requirement.attrs, "_method": requirement.method},
                                          applicable)[0] if applicable else
                         _fitting(produces, SimpleNamespace(**requirement.attrs)))
            kept, _limits, _instead, own = method_fitting(requirement.method, list(dict.fromkeys(potential)))
            fitting = kept or own
            if fitting:
                pairs.append((index, action, fitting))
    return pairs


def apply_second_opinion(check: CapabilityCheck, pairs: list[tuple[int, str, list[str]]],
                         answers: list, task: str = "") -> CapabilityCheck:
    """Credit a workflow's fitting entries for every pair answered all; the gap stands only if none was.

    Log 407: "part" no longer credits anything. Log 403 added it for one quote holding two results
    (heldout8 QP2-QP4: communities, then an interactive 3D view), but on the heldout11-14 recordings
    the check never quoted a supported and an unsupported result together (0 of 178 two-requirement
    sessions), while "part" was answered for single results only partly met -- each TF's sign in each
    tumor from GIRAFFE's cohort-level signs, enhancer-promoter loops from DRAGON -- 13 times on
    unsupported requests; the 4 times on supported ones another workflow was answered "all".
    `task`: the request, so a credited result's candidate counts are weighed (`weigh_credited_counts`).
    """
    requirements = [item.model_copy() for item in check.requirements]
    full, fitted = {}, {}
    for (index, _action, keys), answer in zip(pairs, answers):
        # "named": the words only ask to run this workflow ("請跑 PANDA"), naming no result -- its own results are
        # what is asked (10-13b F40, F46 were refused when the only choices were all/part/none).
        if {True: "all", False: "none"}.get(answer, answer) in ("all", "named"):
            full.setdefault(index, []).extend(keys)
    for index, keys in full.items():
        item = requirements[index]
        # A workflow that delivers the whole requirement replaces a partial reading of it.
        previous = item.delivered_by if item.status != "partial" else []
        from types import SimpleNamespace
        # Revalidate at the credit boundary, even if a caller supplied stale/unfiltered pairs.
        candidate = list(dict.fromkeys([*previous, *keys]))
        candidate = fitted[index] = _fitting(candidate, SimpleNamespace(**item.attrs)) if item.attrs else []
        kept, limits, _instead, own = method_fitting(item.method, candidate)
        previous = []
        delivered = list(dict.fromkeys([*previous, *kept]))
        requirements[index] = item.model_copy(update={
            "delivered_by": delivered, "status": _status(delivered), "second_opinion": True,
            "limits": list(dict.fromkeys([*item.limits, *limits])),
            "defaults": list(dict.fromkeys([*item.defaults, *own]))})
    requirements = weigh_credited_counts(task, check, requirements, fitted)
    results = [item for item in requirements if item.kind == "result"]
    full_gap = _full_gap(results, check.unchecked)
    return check.model_copy(update={"requirements": requirements, "full_gap": full_gap})
