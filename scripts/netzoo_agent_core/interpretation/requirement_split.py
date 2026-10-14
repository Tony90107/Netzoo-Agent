"""M2 (2026-10-14): which words make a requirement of their own, so a part that cannot be done never takes the
doable part with it.

Final acceptance a24b, false refusals and silent omissions:
- MX10 "Run CONDOR ... to get TF-gene communities, and allow genes to sit in more than one community": the overlap,
  stated outside the ask's words, was applied to it (Log 412-413), so the communities were refused too. A condition
  on the result's form stated outside an ask's words is a requirement of its own -- heldout18 CK3-CK6's gold judges
  just that sentence -- and the ask keeps its own words' reading.
- MX02 "then put the per-sample networks into an interactive dashboard": the delivery holds the result's words, so
  it was dropped as part of the ask; a delivery is dropped only when it lies within an ask's words.
- S138 (P30) "Outputs can go to /registry/sambar_run1" was read as a delivery and refused; where result files are
  written is not one.
"""

from __future__ import annotations

import re

from ..capability_sheet import sheet_entries
from ..contracts.capability_check import CheckedRequirement
from .input_bindings import _DIRECTORY_TOKEN
from .discovery import _UNLABELED_PATH_RE
from .request_spans import _span

__all__ = ["FORM_CONDITIONS", "ask_conditions", "condition_requirements", "delivery_requirements",
           "form_condition_spans", "split_additions", "apply_own_sentence_answers"]

FORM_CONDITIONS = ("group_membership", "spatial", "time_model")
"""Conditions on the result's form; the others (data unit, matched samples) are facts about the user's data, and
rule a workflow out for every ask they concern."""

_PERMISSIVE = {"group_membership": "one_group", "spatial": "not_spatial", "time_model": "not_dynamic"}
_PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
          "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
          "time_model": "not_dynamic", "spatial": "not_spatial"}


def _within(inner: tuple[int, int], outer: tuple[int, int]) -> bool:
    return outer[0] <= inner[0] and inner[1] <= outer[1]


def form_condition_spans(task: str, proposal, conditions: dict[str, str]) -> dict[str, tuple[int, int]]:
    """Where in the request each verified result-form condition is stated."""
    stated = getattr(proposal, "conditions", None)
    found = {}
    for name in FORM_CONDITIONS:
        quote = (getattr(stated, f"{name}_quote", "") or "").strip() if name in conditions else ""
        if quote and (span := _span(task, quote)) is not None:
            found[name] = span
    return found


def ask_conditions(item, conditions: dict[str, str], form_spans: dict[str, tuple[int, int]],
                   asked: list[tuple[int, int]]):
    """The conditions that apply to one ask, and the ask itself.

    A result-form condition stated outside every ask's words is left to its own requirement; where an ask's own form
    only repeats it (a24b MX10: "TF-gene communities" typed several_groups from the next clause), the ask is read by
    its own words. One stated within an ask's words is that ask's, and applies as before (Log 412; a24b N04: "with a
    time delay" in one ask, "how long that delay is" in the next).
    """
    outside = {name for name, span in form_spans.items() if not any(_within(span, ask) for ask in asked)}
    kept = {name: value for name, value in conditions.items() if name not in outside}
    reset = {name: _PERMISSIVE[name] for name in outside if getattr(item, name, None) == conditions[name]}
    return kept, (item.model_copy(update=reset) if reset else item)


def condition_requirements(task: str, conditions: dict[str, str], form_spans: dict[str, tuple[int, int]],
                           asked: list[tuple[int, int]]) -> list[CheckedRequirement]:
    """A not-available result for each result-form condition stated outside every ask's words.

    No registered workflow gives such a form (`capability_sheet.result_forms`), and the line says why
    (`capability_check._form_reasons`).
    """
    return [CheckedRequirement(quote=task[span[0]:span[1]].strip().rstrip(" .;,!?"), kind="result",
                               status="not_available", attrs={**_PLAIN, name: conditions[name]})
            for name, span in form_spans.items() if not any(_within(span, ask) for ask in asked)]


def _names_a_folder(words: str) -> bool:
    """A file path or folder, and no web address or e-mail: where result files are written (a24b S138)."""
    if "://" in words or "@" in words or "www." in words.casefold():
        return False
    return bool(_UNLABELED_PATH_RE.search(words) or _DIRECTORY_TOKEN.search(words))


def delivery_requirements(task: str, proposal, results: list[CheckedRequirement]) -> list[CheckedRequirement]:
    """Items 4-5 (2026-10-14): each delivery the request states, as a result no registered workflow gives.

    Every registered workflow writes result files and stops (`capability_sheet.yaml`, `delivery`), so a delivery is
    never available -- it is not a property of the result to check against a workflow (Log 414's condition check
    would wrongly remove the network that is to be e-mailed). Kept when its words are in the request and do not lie
    within an asked-for result's own words, which were read with it (M2: a delivery that names the result, "put the
    per-sample networks into a dashboard", is still one), and when it is more than a folder for the files.
    """
    asked = [span for item in results if (span := _span(task, item.quote)) is not None]
    found = []
    for other in getattr(getattr(proposal, "conditions", None), "other_requirements", None) or []:
        span = _span(task, other.quote) if other.about == "delivery" and other.quote.strip() else None
        if span is None or any(_within(span, ask) for ask in asked) or _names_a_folder(task[span[0]:span[1]]):
            continue
        found.append(CheckedRequirement(quote=task[span[0]:span[1]].strip().rstrip(" .;,!?"), kind="result",
                                        status="not_available", not_by=["delivery"]))
    return list({item.quote: item for item in found}.values())


_TYPED = ("scale", "omics_layers", "data_unit", "regulator_kinds", "needs_sign", "input_network",
          "group_membership", "time_model", "spatial")


def _core_span(task: str, span: tuple[int, int], added: list[tuple[int, int]]) -> tuple[int, int]:
    """The ask's words before what it adds, cut at the last comma or semicolon before it; the whole ask otherwise."""
    end = min(start for start, _end in added)
    if any(start < end for start, _end in added) or end <= span[0]:
        return span
    head = task[span[0]:end]
    cut = max(head.rfind(","), head.rfind(";"))
    if cut >= 0 and len(head[cut + 1:].split()) <= 4:
        head = head[:cut]
    head = head.rstrip(" ,;:-")
    return (span[0], span[0] + len(head)) if len(head.split()) >= 3 else span


def split_additions(task: str, asks: dict, sentences: list[tuple[int, int]] = ()) -> tuple[dict, list[CheckedRequirement]]:
    """Each ask that adds to a result it also names on its own, as that result and, apart, each addition (M2).

    a24b MX03 typed the two-layer network with the third layer as one ask of three layers, and MX09 the TF and miRNA
    network with lncRNAs; both were refused whole. The result without its additions has the ask's typed attributes
    less what they add -- a layer each, the regulator classes no registered workflow models, overlapping groups --
    and is credited to the entries the reading credited or to the workflows whose near miss it cited (the model's
    "DRAGON does not give three layers" names DRAGON), then fitted as any ask. Each addition is a result of its own
    with the whole ask's attributes and citations, so it is refused with the reason the whole was.
    """
    from .method_conditions import verified_method
    from ..method_names import UNREGISTERED, named_workflows

    known = sheet_entries()
    offered = set().union(*(item.regulators for item in known.values() if item.kind == "produces" and item.regulators))
    found, extra = {}, []
    for span, items in asks.items():
        first = items[0]
        # live m2a G1: "add our lncRNAs as a further class of regulators" sat in the ask's sentence, beside the words
        # "aggregate PANDA network" rather than inside them.
        sentence = next((found_ for found_ in sentences if _within(span, found_)), span)
        added = [(item, where) for item in getattr(first, "adds", None) or []
                 if item.adds != "other" and item.quote.strip() and (where := _span(task, item.quote)) is not None
                 and _within(where, sentence) and where != span and not _within(span, where)]
        if not added:
            found.setdefault(span, []).extend(items)
            continue
        kinds = [item.adds for item, _where in added]
        inside = [where for _item, where in added if _within(where, span)]
        core = _core_span(task, span, inside) if inside else span
        owners = {known[key].workflow for key in first.not_by if key in known and known[key].kind == "near_miss"}
        if (named := verified_method(task, first).get("named")) not in (None, UNREGISTERED):
            owners |= set(named_workflows(named))  # a method the request names for this result
        update = {"quote": task[core[0]:core[1]], "adds": [], "delivered_by": list(dict.fromkeys([
            *first.delivered_by, *(key for key, entry in known.items()
                                   if entry.kind == "produces" and entry.level == "direct" and entry.workflow in owners)]))}
        if "omics_layer" in kinds:
            update["omics_layers"] = max(1, first.omics_layers - kinds.count("omics_layer"))
        if "regulator_class" in kinds:
            update["regulator_kinds"] = [kind for kind in first.regulator_kinds if kind in offered]
        if "group_overlap" in kinds:
            update["group_membership"] = "one_group"
        found.setdefault(core, []).extend(item.model_copy(update=update) for item in items)
        attrs = {key: getattr(first, key) for key in _TYPED if hasattr(first, key)}
        extra += [CheckedRequirement(quote=task[where[0]:where[1]].strip().rstrip(" .;,!?"), kind="result",
                                     status="not_available", attrs=attrs,
                                     not_by=[key for key in first.not_by if key in known and known[key].kind != "produces"])
                  for _item, where in added]
    return found, extra


def apply_own_sentence_answers(check, pairs: list[tuple[int, str, list[str], str]], answers: list):
    """Each requirement stated beside an ask in its sentence that a credited workflow cannot meet and none meets, as a
    not-available result of its own; the result beside it keeps its verdict (M2).

    A check that could not answer adds nothing: these words were dropped before M2, and a held run for every request
    that names its inputs ("from expression, motifs and PPI") would be worse.
    """
    from ..capability_sheet import entry

    verdicts: dict[str, dict[str, list[str]]] = {}
    for (_index, _action, keys, quote), answer in zip(pairs, answers):
        verdicts.setdefault(quote, {}).setdefault(answer, []).append(entry(keys[0]).workflow)
    added = [CheckedRequirement(quote=quote.strip().rstrip(" .;,!?"), kind="result", status="not_available",
                                limits=[f'{name} does not meet "{quote.strip().rstrip(" .;,!?")}"'
                                        for name in dict.fromkeys(found["violates"])])
             for quote, found in verdicts.items() if found.get("violates") and not found.get("satisfies")]
    return check.model_copy(update={"requirements": [*check.requirements, *added]}) if added else check

