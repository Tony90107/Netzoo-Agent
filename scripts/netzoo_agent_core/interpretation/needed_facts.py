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

__all__ = ["DIMENSIONS", "decisive_outcomes", "fact_line", "fact_questions", "needed_fact_reply", "waiting_decision"]

# dimension: (what it is about, the question, ((value, label), ...)); a value is set on the ask's typed attributes.
DIMENSIONS = {
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


def _typed(about: str, value: str):
    if about == "regulator_kinds":
        return list(value.split("+"))
    if about == "omics_layers":
        return int(value)
    return value


def decisive_outcomes(fitting, keys: list[str], attrs: dict, about: str) -> dict[str, list[str]] | None:
    """For each value of `about`, the entries that give the result; None when every value gives the same ones."""
    if about not in DIMENSIONS or not keys:
        return None
    if about == "regulator_kinds" and not attrs.get("regulator_kinds"):
        return None  # a result with no regulators (co-expression, communities) cannot depend on which they are
    outcomes = {}
    for value, _label in DIMENSIONS[about][2]:
        typed = _typed(about, value)
        if about == "regulator_kinds":
            typed = sorted({*(kind for kind in attrs["regulator_kinds"] if kind != "mirna"), *typed})
        item = SimpleNamespace(**{**attrs, about: typed})
        outcomes[value] = fitting(list(keys), item)
    return outcomes if len({frozenset(found) for found in outcomes.values()}) > 1 else None


def _workflows(keys: list[str]) -> str:
    names = list(dict.fromkeys(entry(key).workflow for key in keys))
    if not names:
        return "no registered workflow gives this"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def fact_line(item) -> str:
    """The understanding line of a result waiting on a fact."""
    about, _question, values = DIMENSIONS[item.depends_on]
    said = f' ("{item.unknown_quote}")' if item.unknown_quote else ""
    answers = "; ".join(f"if {label}: {_workflows(item.outcomes.get(value, []))}" for value, label in values)
    return f'"{item.quote}" -- depends on {about}, which you said you do not know{said}: {answers}.'


def fact_questions(check) -> list[str]:
    return list(dict.fromkeys(DIMENSIONS[item.depends_on][1] for item in check.needed_facts()))


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
