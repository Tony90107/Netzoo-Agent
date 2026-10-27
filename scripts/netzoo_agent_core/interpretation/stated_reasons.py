"""ROUND-20 (user decision, 2026-10-21): a reply never gives wrong information. It says only the reasons code can verify,
and "not matched to any registered workflow" when it can verify none of a result's reasons -- since harness repair
P2 (2026-10-23) the layer-2 reason of `reason_layers`: what was checked, not why it cannot be done.

ROUND-19 measured the reasons in the 209 replies saying something cannot be done: 14 stated something false, from five
sources, each with its rule here --
- B, the condition check's answer (`requirement_split.model_judged`), is the model's judgment and never said: C40 p0,
  C32 p2 and C52 judged data descriptions unmet for doable requests.
- C, words naming no allowed choice (`UNCLEAR_CHOICE`), are unsettled words, not a run that cannot be done (C40).
- D, an input kind only an "only these" statement rules out (`ruled_out.rests_on_inference`, C44).
- A, "no setting for" words that are no setting (`_settable`: J20, C51, C57, C32 p5r).
- E, a registry-wide reason for a result its claim's words are not about (C07), and "none models other regulators"
  (`_form_reasons`: 0 right, 3 wrong and 4 misleading in ROUND-19).
The check's own fields, and so every decision, are unchanged; only what the reply says is.
"""

from __future__ import annotations

import re
from typing import Mapping

from ..capability_sheet import data_units, entry, result_forms, sheet_entries
from ..contracts.capability_check import CheckedRequirement
from ..routing.study_purpose_verify import _locate
from ..workflow_conditions import UNCLEAR_CHOICE, unpassed_setting
from .request_spans import _span
from .requirement_split import model_judged
from .ruled_out import rests_on_inference
from .sentence_ownership import request_sentences
from .setting_words import _settable, _unbound

__all__ = ["claim_sentences", "stated"]

# G6 (feasibility eval F23, F25): a typed attribute the registry rules out was the whole reason a result is not
# available, but only cited near misses were said, so "spatial ... borrowing signal from neighboring spots" and
# "overlapping communities" read "not matched to any registered workflow". The reasons are the capability sheet's
# own result_forms and data_units notes; each is said only when that attribute alone leaves no produces entry.
_FORM_REASONS = {
    ("spatial", "uses_neighbors"): (
        "No registered workflow uses where samples sit in space or which samples are neighbours; each sample is "
        "modelled on its own."),
    ("group_membership", "several_groups"): (
        "Registered grouping puts each item in exactly one group (CONDOR: one community per regulator or gene; "
        "SAMBAR: one subtype per sample); none returns overlapping memberships."),
    ("time_model", "dynamic"): (
        "No registered workflow models how the system changes from one time point to the next; time points can "
        "only be compared as separate results."),
    ("data_unit", "single_cells"): (
        "Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none "
        "models single cells."),
}
_REGULATOR_LABELS = {"tf": "TF", "mirna": "miRNA", "lncrna": "lncRNA"}


def _form_reasons(item: CheckedRequirement) -> list[str]:
    """Why the result's own typed attributes leave no registered result, from the capability sheet."""
    attrs, reasons = item.attrs, []
    doubted = set(getattr(item, "doubted_forms", ()) or ())  # jev-overlap ROUND-2: a form Jev found unasked
    for (name, value), text in _FORM_REASONS.items():
        allowed = data_units() if name == "data_unit" else result_forms().get(name, frozenset())
        if attrs.get(name) == value and value not in allowed and name not in doubted:
            reasons.append(text)
    # No layer-count reason: replayed over the recorded full gaps, 11 of 12 came from motif, PPI and expression
    # read as three omics layers (binding affinity, edge conservation), so it named a reason the request never raised.
    produces = [found for found in sheet_entries().values() if found.kind == "produces"]
    offered = set().union(*(found.regulators for found in produces if found.regulators))
    # ROUND-20 E: "other" regulators is the reading's word for what is no regulator class (methylation, metabolites,
    # cytokines): never the obstacle in ROUND-19 (causality was, M32 J31 H14), and false for a doable C07.
    if extra := sorted(set(attrs.get("regulator_kinds") or ()) - offered - {"other"}):
        reasons.append("Registered regulatory workflows contain "
                       + " and ".join(_REGULATOR_LABELS.get(kind, kind) for kind in sorted(offered))
                       + " regulators; none models " + ", ".join(_REGULATOR_LABELS.get(kind, kind) for kind in extra)
                       + " regulators.")
    return reasons


def stated(item: CheckedRequirement, check=None) -> CheckedRequirement | None:
    """The row with only the reasons code can verify, for the reply to say them.

    None when the row held reasons -- limits, or the condition check's answers -- and none can be said: a workflow was
    credited and then held, so neither a near miss nor "no registered workflow produces this" is true of it, and the
    reply says only that it matched no registered workflow (ROUND-19 C18 p1, J46: the right reason was the model's).
    """
    limits = [reason for reason in item.limits if _verifiable(reason, item, check)]
    if (item.limits or item.violations) and not limits:
        return None
    sentences = getattr(check, "claim_sentences", None) or {}
    # P5 r1 (h7 S04): a near miss ("W does not give it") rests on the model's reading of which result was asked, and
    # no near-miss entry names a claim code could verify, so only a registry-wide reason with its verified claim stays.
    not_by = [key for key in item.not_by
              if entry(key).kind == "registry_wide" and _about(item.quote, sentences.get(entry(key).claim) or ())]
    return item.model_copy(update={"limits": limits, "violations": [], "not_by": not_by})


def _verifiable(reason: str, item: CheckedRequirement, check) -> bool:
    if model_judged(reason) or reason.endswith(UNCLEAR_CHOICE) or rests_on_inference(check, reason):
        return False
    if any(re.search(rf"(?<![\w.]){re.escape(name.split('.', 1)[1])}(?![\w.])", reason) for name in _unbound(item)):
        return False  # harness repair P2 (b, spec A21): a premise is a setting bound to a control its words do not name
    if (found := unpassed_setting(reason)) is None:
        return True
    workflow, words = found
    # The reason quotes the setting's words; the value the user gave them is the row's (MX05: "its regularisation
    # lambda", 0.5).
    values = [setting.get("value") or "" for setting in item.method.get("settings") or []
              if setting.get("quote") == words]
    return _settable(workflow, " ".join([words, *values]))


def _about(quote: str, sentences) -> bool:
    """Whether the result's words lie in a sentence holding the claim's verified words."""
    words = quote.strip().strip(" .;,!?")
    return bool(words) and any(_locate(sentence, words) is not None for sentence in sentences)


def claim_sentences(task: str, claims: Mapping[str, str] | frozenset[str], deliveries=()) -> dict[str, list[str]]:
    """For each registry-wide claim, the request sentences holding its words (ROUND-20 E).

    `claims`: each study-purpose claim the reader verified, with its words (a bare set of claims carries none, and
    none of them is said). `deliveries`: the delivery results `requirement_split.delivery_requirements` located.
    """
    said = [*(claims.items() if isinstance(claims, Mapping) else ()), *(("delivery", item.quote) for item in deliveries)]
    sentences, found = request_sentences(task), {}
    for claim, quote in said:
        if (span := _span(task, quote)) is None:
            continue
        found.setdefault(claim, []).extend(task[s:e].strip() for s, e in sentences if s < span[1] and span[0] < e)
    return {claim: list(dict.fromkeys(items)) for claim, items in found.items()}
