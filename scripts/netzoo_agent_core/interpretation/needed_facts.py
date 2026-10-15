"""Verdict layer step 2: a result that waits on a fact the user said they do not know.

Blind set heldout416b (2026-10-12, independent writer): of 10 requests whose result was clear but a deciding property
of the data was unknown to the user ("I never checked whether its nodes are regulators plus genes, or genes only";
"its columns could be individual cells from a 10x run or ordinary bulk libraries"), none was asked about: most were
given a workflow, and the feasibility eval refused F46 ("CONDOR ... gene-gene or TF-gene, I am not sure").

The model only reads what the user says they do not know, typed to a dimension code already compares with the sheet
(`contracts.capability_check.UnknownAbout`). Code decides whether it matters: the result's workflows are fitted once
per value of that dimension (`capability_check._fitting`); only when the fits differ does the result wait on it
(status `needs_fact`), so an unknown that changes nothing is never asked about. Such a turn selects, refuses and runs
nothing, and asks one question per fact, with what each answer leads to.
"""

from __future__ import annotations

from types import SimpleNamespace

from ..capability_sheet import entry
from .request_spans import _span

__all__ = ["DIMENSIONS", "FILE_CHECKED", "decisive_outcomes", "fact_line", "fact_questions", "file_checked",
           "file_checked_note", "needed_fact_reply", "waiting_decision"]

# dimension: (what it is about, the question, ((value, label), ...)); a value is set on the ask's typed attributes.
DIMENSIONS = {
    "sample_count": ("how many independent samples are available",
                     "How many independent biological samples are available for this result?", ()),
    "mutation_origin": ("whether the variants are somatic or germline",
                        "Are these acquired somatic mutations, or inherited germline variants?",
                        (("somatic", "somatic mutations"), ("germline", "germline variants"))),
    "value_type": ("whether the measurements are continuous or binary",
                   "Are the omics measurements continuous values, or binary indicators?",
                   (("continuous", "continuous measurements"), ("binary", "binary indicators"))),
    "mirna_driver": ("what must drive the miRNA links",
                     "Should miRNA links use a target prior and miRNA list, or must they be estimated from measured miRNA expression?",
                     (("target_prior", "a target prior and miRNA list"), ("measured_expression", "measured miRNA expression"))),
    "sample_alignment": ("whether the tables' sample IDs align",
                         "Do both tables identify the same biological samples with matching sample IDs?",
                         (("same_samples", "matching sample IDs"), ("different_samples", "different sample IDs"))),
    "data_unit": ("whether each unit of your data is a single cell or a bulk sample",
                  "Is each sample in your data a single cell, or a bulk sample (a tissue, a patient, a cell line, or "
                  "cells pooled into a pseudo-bulk profile)?",
                  (("bulk_samples", "bulk samples"), ("single_cells", "single cells"))),
    "input_network": ("whether your network links regulators to genes or genes to genes",
                      "Does your network link regulators (such as TFs) to their target genes, or genes to genes?",
                      (("regulator_gene", "regulators to genes"), ("gene_gene", "genes to genes"))),
    "samples_matched": ("whether the omics tables come from the same samples",
                        "Were the different omics tables measured on the same samples?",
                        (("same_samples", "the same samples"), ("different_samples", "different samples"))),
    "regulator_kinds": ("whether your regulators include miRNAs",
                        "Do your regulators (or your prior) include miRNAs, or TFs only?",
                        (("tf", "TFs only"), ("tf+mirna", "TFs and miRNAs"))),
    "omics_layers": ("how many omics data types you have",
                     "How many omics data types do you have?",
                     (("2", "two"), ("3", "three or more"))),
    "scale": ("whether you want one result for all samples or one per sample",
              "Do you want one result for all your samples together, or one per sample?",
              (("whole_cohort", "one for all samples"), ("per_sample", "one per sample"))),
}


FILE_CHECKED = {
    "sample_alignment": ("same_samples", frozenset({"run_dragon", "run_lioness_dragon"}),
                        "before it runs, {names} checks that both tables list exactly the same sample IDs and pairs their "
                        "rows by ID, so their order does not matter; unequal IDs stop the check. Matching IDs do not "
                        "establish biological identity: the tables must actually describe the same samples"),
}
"""File alignment can be checked; biological identity cannot be inferred from matching identifiers.

dimension: (the value the check confirms, the workflows whose input check settles it, what the reply says). Every
multi-omic workflow loads its layers with `data.dragon.load_and_align_dragon_layers`, which requires exactly the same
sample IDs and reorders layer 2 to layer 1 by ID. Feasibility eval F41 ("I do not know whether their columns are in the
same sample order") was asked "Were the different omics tables measured on the same samples?" -- a question the
files answer, about an order that never matters. Node roles (CONDOR) are not here: its input check only warns when
source and target IDs overlap, so a gene-gene network would still run, and B03 is still asked.
"""


def file_checked(about: str, outcomes: dict[str, list[str]]) -> bool:
    """Whether every workflow the confirmed value leads to settles `about` from the files before it runs."""
    if about not in FILE_CHECKED:
        return False
    value, actions, _note = FILE_CHECKED[about]
    keys = outcomes.get(value) or []
    return bool(keys) and all(entry(key).action in actions for key in keys)


def file_checked_note(item) -> str:
    """The sentence a result with a file-checked unknown is said with."""
    _value, _actions, note = FILE_CHECKED[item.file_checked]
    names = list(dict.fromkeys(entry(key).workflow for key in item.delivered_by))
    return f'You said "{item.unknown_quote}": ' + note.format(names=" or ".join(names) or "the workflow") + "."


def _typed(about: str, value: str):
    if about == "regulator_kinds":
        return list(value.split("+"))
    if about in ("omics_layers", "sample_count"):
        return int(value)
    return value


def decisive_outcomes(fitting, keys: list[str], attrs: dict, about: str, quote: str = "", domain: dict | None = None, *, include_uniform: bool = False) -> dict[str, list[str]] | None:
    """Different fits require a question; uniformly empty fits rule the result out; uniform positive fits need none."""
    if about not in DIMENSIONS or not keys:
        return None
    if about == "regulator_kinds" and not attrs.get("regulator_kinds"):
        return None  # a result with no regulators (co-expression, communities) cannot depend on which they are
    outcomes = {}
    values = DIMENSIONS[about][2]
    if about == "sample_count":
        from ..workflow_conditions import conditions_for, stated_numbers
        method = attrs.get("_method", {})
        thresholds = set()
        for key in keys:
            if not (found := conditions_for(entry(key).action)):
                continue
            if found.min_samples:
                thresholds.add(found.min_samples)
            for setting in method.get("settings", []):
                if setting["name"] == f"{found.workflow}.kmax":
                    thresholds.update(int(n) for n in stated_numbers(setting.get("value", "")) if n >= 1 and n == int(n))
            features = method.get("features")
            if features and found.max_values and found.size:
                per_sample = found.size(1, features)
                if per_sample > 0:
                    thresholds.add(found.max_values // per_sample + 1)
        if not thresholds:
            return None
        values = [(str(n), str(n)) for n in sorted({1, *thresholds, *(n - 1 for n in thresholds if n > 1)})]
    if about in ("omics_layers", "sample_count") and quote:
        from ..workflow_conditions import stated_numbers
        stated = (domain["values"] if domain else
                  sorted({int(n) for n in stated_numbers(quote) if n >= 1 and n == int(n)}))
        if domain and domain["kind"] == "choices":
            values = [(str(n), str(n)) for n in stated]
        elif len(stated) >= 2:
            # Range endpoints alone can both fail while interior counts fit. Legacy readings without
            # a typed domain conservatively retain internal runtime boundaries rather than inventing a gap.
            probes = {*stated, *(int(value) for value, _label in values if min(stated) <= int(value) <= max(stated))}
            values = [(str(n), str(n)) for n in sorted(probes)]
    for value, _label in values:
        typed = _typed(about, value)
        if about == "regulator_kinds":
            typed = sorted({*(kind for kind in attrs["regulator_kinds"] if kind != "mirna"), *typed})
        item = SimpleNamespace(**{**attrs, ({"sample_count": "fact_sample_count"}.get(about, about)): typed})
        outcomes[value] = fitting(list(keys), item)
    return outcomes if include_uniform or not any(outcomes.values()) or len({frozenset(found) for found in outcomes.values()}) > 1 else None


def _workflows(keys: list[str]) -> str:
    names = list(dict.fromkeys(entry(key).workflow for key in keys))
    if not names:
        return "no registered workflow gives this"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def fact_line(item) -> str:
    """The understanding line of a result waiting on a fact."""
    if item.depends_on == "choice":
        answers = "; ".join(f'if "{option}": {_workflows(keys)}' for option, keys in item.outcomes.items())
        return f'"{item.quote}" -- you have not chosen which result you want: {answers}.'
    about, _question, values = DIMENSIONS[item.depends_on]
    if item.depends_on == "omics_layers":
        values = [(value, f"{value} layers") for value in item.outcomes]
    if item.depends_on == "sample_count":
        values = [(value, f"{value} samples") for value in item.outcomes]
    said = f' ("{item.unknown_quote}")' if item.unknown_quote else ""
    answers = "; ".join(f"if {label}: {_workflows(item.outcomes.get(value, []))}" for value, label in values)
    return f'"{item.quote}" -- depends on {about}, which you said you do not know{said}: {answers}.'


def fact_questions(check) -> list[str]:
    return list(dict.fromkeys(_question(item) for item in check.needed_facts()))


def _question(item) -> str:
    if item.depends_on == "choice":
        options = [f'"{option}"' for option in item.outcomes]
        listed = options[0] if len(options) == 1 else ", ".join(options[:-1]) + " or " + options[-1]
        return f"Which result do you want: {listed}?"
    return DIMENSIONS[item.depends_on][1]


def waiting_decision(decision, check):
    """The turn's decision while results wait on facts: nothing selected, refused or run; one question per fact."""
    actions = list(dict.fromkeys(entry(key).action for item in check.needed_facts() for keys in item.outcomes.values()
                                 for key in keys if entry(key).action))
    return decision.model_copy(update={
        "action": "no_tool", "should_execute": False, "intent_type": "answer_question", "capability_check": check,
        "matched_actions": [], "recommended_actions": [], "alternative_actions": [], "advisory_recommendation": None,
        "hypothesis_actions": actions, "capability_match_status": "ambiguous",
        "clarification_question": " ".join(fact_questions(check)),
        "reason": "A result waits on a fact the user said they do not know; nothing is selected before it is known.",
    })


def needed_fact_reply(check, understanding: str) -> str:
    questions = fact_questions(check)
    ask = ("Before I choose a workflow, please tell me: " + questions[0] if len(questions) == 1 else
           "Before I choose a workflow, please tell me:\n" + "\n".join(f"- {question}" for question in questions))
    return "\n\n".join([understanding, ask, "No workflow has been selected and nothing runs before you answer.",
                        "No files were inspected and no analysis ran."])


def resolve_unknowns(fitting, keys: list[str], attrs: dict, unknowns: list[tuple]):
    """Counterfactuals share the same possible workflows, independent of unknown ordering.

    Each dimension is a conjunctive workflow constraint. Remove guesses for all unresolved dimensions,
    fit each one's possible values, then intersect the workflows possible under every other dimension.
    A uniformly empty one-dimensional probe is definitive only after the other guesses were removed.
    """
    neutral = dict(attrs)
    permissive = {"data_unit": "not_stated", "input_network": "none", "samples_matched": "not_stated",
                  "sample_alignment": "not_stated", "omics_layers": 0, "scale": "unstated",
                  "mutation_origin": "not_stated", "value_type": "not_stated", "mirna_driver": "not_stated"}
    for about, _quote, _domain in unknowns:
        if about in permissive:
            neutral[about] = permissive[about]
        elif about == "regulator_kinds":
            neutral[about] = [kind for kind in attrs.get(about, []) if kind != "mirna"]
        elif about == "sample_count":
            neutral["_method"] = {k: v for k, v in attrs.get("_method", {}).items() if k != "samples"}
    baseline = fitting(keys, SimpleNamespace(**neutral))
    analyses = []
    for about, quote, domain in unknowns:
        current = dict(neutral)
        if about == "regulator_kinds":
            current[about] = attrs.get(about, [])  # preserve whether this result has regulators at all
        outcomes = decisive_outcomes(fitting, baseline, current, about, quote, domain, include_uniform=True)
        if outcomes is not None:
            analyses.append((about, quote, outcomes))
    possible = set(baseline)
    for _about, _quote, outcomes in analyses:
        possible.intersection_update(key for found in outcomes.values() for key in found)
    adjusted = []
    for index, (about, quote, outcomes) in enumerate(analyses):
        other_possible = set(baseline)
        for other_index, (_other, _said, other) in enumerate(analyses):
            if other_index != index:
                other_possible.intersection_update(key for found in other.values() for key in found)
        adjusted.append((about, quote, {value: [k for k in found if k in other_possible]
                                        for value, found in outcomes.items()}))
    return [key for key in baseline if key in possible], adjusted


def verified_unknowns(task: str, proposal) -> list[tuple[str, str]]:
    """Verdict layer step 2: (dimension, the user's words) for each unknown fact whose words are in the request.

    Words that also state a result choice are that choice (step 2b), not a second unknown: pre-measure F37 ("I have
    not decided whether edges should mean TF regulation or gene-gene coexpression") was read as a choice and as an
    unknown omics-layer count, which would have asked how many omics data types the user has.
    """
    conditions = getattr(proposal, "conditions", None)
    chosen = [span for choice in getattr(conditions, "open_choices", None) or () if choice.differs_in == "result"
              for words in (choice.quote, *(option.quote for option in choice.options))
              if (span := _span(task, words)) is not None]
    found = []
    for fact in getattr(conditions, "unknown_facts", None) or ():
        span = _span(task, fact.quote)
        if (span is None or (fact.about, task[span[0]:span[1]]) in found
                or getattr(fact, "applies_to", None) == []
                or (getattr(fact, "applies_to", None) is not None
                    and not any(_span(task, words) is not None for words in fact.applies_to if words.strip()))
                or any(span[0] < end and start < span[1] for start, end in chosen)):
            continue
        found.append((fact.about, task[span[0]:span[1]]))
    return found


def verified_unknown_scopes(task: str, proposal) -> dict[str, list[str]]:
    scopes = {}
    for fact in getattr(getattr(proposal, "conditions", None), "unknown_facts", None) or ():
        applies = getattr(fact, "applies_to", None)
        where = _span(task, fact.quote)
        if applies is not None and where is not None:
            scopes[task[where[0]:where[1]]] = [task[a:b] for words in applies if words.strip()
                                            if (placed := _span(task, words)) is not None for a, b in [placed]]
    return scopes


def verified_unknown_domains(task: str, proposal) -> dict[str, dict]:
    from ..workflow_conditions import stated_numbers
    domains = {}
    for fact in getattr(getattr(proposal, "conditions", None), "unknown_facts", None) or ():
        kind, values = getattr(fact, "count_kind", "unspecified"), getattr(fact, "count_values", [])
        where = _span(task, fact.quote)
        if (fact.about in ("sample_count", "omics_layers") and where is not None
                and kind in ("choices", "range") and values and (kind != "range" or len(values) == 2)
                and all(n > 0 and n in stated_numbers(fact.quote) for n in values)):
            domains[task[where[0]:where[1]]] = {"kind": kind, "values": sorted(set(values))}
    return domains


def _unknown_applies(scopes, said: str, result: str) -> bool:
    return said not in scopes or any(_span(result, quote) is not None or _span(quote, result) is not None
                                     for quote in scopes[said])


def applicable_unknowns(unknowns, scopes, domains, quote):
    return [(about, said, domains.get(said)) for about, said in unknowns if _unknown_applies(scopes, said, quote)]


def fact_update(possible, analyses, status_for):
    if not analyses:
        return None
    if not possible:
        return {"status": "not_available", "delivered_by": [], "file_checked": None}
    checked = {}
    for about, said, outcomes in analyses:
        if len({frozenset(found) for found in outcomes.values()}) < 2:
            continue
        if file_checked(about, outcomes):
            checked = {"file_checked": about, "unknown_quote": said}
            continue
        return {"status": "needs_fact", "depends_on": about, "outcomes": outcomes, "unknown_quote": said,
                "file_checked": None, "delivered_by": possible}
    return {"status": status_for(possible), "delivered_by": possible, **checked}
