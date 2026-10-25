"""ROUND-26 2a (collab/ROUND-26-PLAN.md 3.1-3.2): the request's words linked to the settings of its candidate workflows.

The reading picks each setting from one enum of all 34 (`setting_names`), every description in one long text. Against
the field gold (ROUND-26 phase 0) it left 61 of 236 setting phrases unlinked -- "genes on rows", "from 2 to 8
subtypes", "sparsify switched on", "log2-transformed" -- and linked 9 to another setting (Q42 "keep the full matrices"
as keep_in_memory). Text-to-SQL on large schemas links each phrase against a narrowed column list (DIN-SQL, CHESS).

So one focused read lists only the candidate workflows' own settings -- the workflows the request names and the ones
the reading credits, never narrowed by another typed field (Q10's scale would have dropped the right result) -- as flat
required pairs: the words that set each, and the words of its value (VAREX, Round 4: a small model leaves object lists
empty). Where the contract declares output modes for a combination of controls (BONOBO's `conditional_outputs`), one
enum offers the valid modes by their semantics. Code keeps a link only when its words are in the request; a mode
becomes the controls it turns on, named by its words. The links join the reading's request-level settings before the
check is built, so the workflows' own rules judge every value (`method_fitting`), never the model.

Merging is asymmetric (the CC1 lesson): a link adds a setting or replaces the reading's link over the same words --
the same setting, an unregistered one, or (a mode only) another setting of the same workflow whose own field the read
left empty -- and an empty field removes nothing.

ROUND-27 B1 (docs/research-log/round27-b1-2026-10-25/ROUND.md) changes five things and nothing else: candidates are the
credited workflows only; free-text settings (sample names, CONDOR's prefix) are never linked; a setting the user is
unsure of is held, not merged; an empty link never replaces the reading's valued item for the same setting; and a link
whose merge adds a limit or violation to the check is held too (`guarded_links`). A held link is asked to confirm when
the call is a DO (`held_core`); it never refuses.
"""

from __future__ import annotations

import copy
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from workflow_registry import ACTION_DEFINITIONS

from ..capability_sheet import sheet_entries
from ..method_names import UNREGISTERED, registered_workflows
from ..workflow_conditions import boolean_value, conditions_for, stated_numbers
from .request_spans import _span

__all__ = ["LINKS_INSTRUCTIONS", "guarded_links", "held_core", "link_workflows", "links_model", "links_text",
           "merged_reading", "reading_doubts", "verified_links", "without_emptier"]

LINKS_INSTRUCTIONS = (
    "Return only the SettingsLinks structure. You are given a user's request and the settings of the workflows it "
    "may run. For each setting, copy the exact words of the request that set it, and the exact words that give its "
    "value (they may be the same words); leave both empty when the request does not set it. Words describing the "
    "user's data set a setting that declares that property of the data. When the user does not know a value, copy "
    "the words that set it and leave the value empty. For an output mode, choose the mode the request asks for by "
    "what it wants kept or saved, with the words that ask for it; not_stated when the request does not say. Mark a "
    "setting unsure when the user says they are not sure whether or how to set it."
)
EXCLUDED = frozenset({"BONOBO.sample_names", "CONDOR.prefix"})  # B1 change 2: free text, never linked
_NOT_STATED = "not_stated"


def _key(workflow: str) -> str:
    return workflow.replace("-", "_")


def _controls(workflow: str) -> list:
    """The workflow's controls it passes to its executor (`SettingLimit.wired`)."""
    conditions = conditions_for(workflow)
    action = registered_workflows().get(workflow)
    if conditions is None or action is None:
        return []
    return [control for control in ACTION_DEFINITIONS[action].controls
            if (limit := conditions.settings.get(control.name)) is not None and limit.wired
            and f"{workflow}.{control.name}" not in EXCLUDED]


def _modes(workflow: str) -> list[tuple[str, dict, str]]:
    """(id, when, semantics) of each valid output mode the contract declares for a combination of the controls."""
    action = registered_workflows().get(workflow)
    capability = getattr(ACTION_DEFINITIONS.get(action), "output_capability", None) if action else None
    rules = [rule for rule in getattr(capability, "conditional_outputs", ()) or () if rule.valid]
    return [(f"mode_{index}", dict(rule.when), " ".join(rule.semantics.split())) for index, rule in enumerate(rules, 1)]


def _sentences(reading: dict) -> list[dict]:
    return [value for name, value in reading.items() if name[1:].isdigit() and isinstance(value, dict)]


def link_workflows(task: str, reading: dict) -> list[str]:
    """The candidate workflows with settings: those the reading credits (B1 change 1 -- 2a also took the workflows the
    request names and the reading's named methods, and linked DRAGON's output format into a LIONESS-DRAGON request)."""
    known = sheet_entries()
    found = []
    for sentence in _sentences(reading):
        for ask in sentence.get("asks") or []:
            found += [known[key].workflow for key in ask.get("delivered_by") or []
                      if key in known and known[key].kind == "produces"]
    workflows = registered_workflows()
    return [name for name in dict.fromkeys(found) if name in workflows and _controls(name)]


def links_text(workflows: list[str]) -> str:
    """The candidate workflows' settings and output modes as the read is shown them."""
    lines = []
    for workflow in workflows:
        lines.append(f"{workflow}:")
        for control in _controls(workflow):
            values = f" Values: {', '.join(map(str, control.allowed_values))}." if control.allowed_values else ""
            lines.append(f"- {control.name} ({control.control_type}): {control.description}{values}")
        for mode, when, semantics in _modes(workflow):
            settings = ", ".join(f"{name}={str(value).lower()}" for name, value in when.items())
            lines.append(f"- output mode {mode} ({settings}): {semantics}")
    return "\n".join(lines)


@lru_cache(maxsize=32)
def links_model(workflows: tuple[str, ...]) -> type[BaseModel]:
    fields: dict = {}
    for workflow in workflows:
        key = _key(workflow)
        for control in _controls(workflow):
            described = (control.description or control.name).rstrip(".")
            fields[f"{key}__{control.name}_words"] = (str, Field(description=(
                f"The request's exact words that set {workflow}'s {control.name} ({described}); empty when the "
                "request does not set it.")))
            fields[f"{key}__{control.name}_value_words"] = (str, Field(description=(
                f"The request's exact words giving the value of {workflow}'s {control.name}; empty when none is "
                "given.")))
            fields[f"{key}__{control.name}_unsure"] = (bool, Field(description=(
                f"Whether the user says they are not sure whether or how to set {workflow}'s {control.name}.")))
        if modes := _modes(workflow):
            fields[f"{key}__output_mode"] = (Literal[(_NOT_STATED, *(mode for mode, _when, _s in modes))], Field(
                description=f"The {workflow} output mode the request asks for; {_NOT_STATED} when it does not say."))
            fields[f"{key}__output_mode_words"] = (str, Field(description=(
                f"The request's exact words asking for that {workflow} output mode; empty when not_stated.")))
    return create_model("SettingsLinks", __config__=ConfigDict(extra="forbid"), **fields)


def _overlap(a, b) -> bool:
    return a is not None and b is not None and a[0] < b[1] and b[0] < a[1]


def reading_doubts(task: str, reading: dict) -> list[tuple[int, int]]:
    """Where the reading found the user unsure: its unknown facts and open choices (`request_readings.uncertain_quotes`)."""
    conditions = reading.get("conditions") or {}
    quotes = [item.get("quote", "") for name in ("unknown_facts", "open_choices")
              for item in conditions.get(name) or [] if isinstance(item, dict)]
    return [span for quote in quotes if (quote or "").strip() and (span := _span(task, quote.strip())) is not None]


def verified_links(task: str, workflows: list[str], read, doubts=()) -> tuple[list[dict], set[str]]:
    """(links whose words are in the request, settings whose words field the read left empty).

    A link is {name, quote, value_quote, span, workflow}; its value words are kept only when they are in the request
    and, for a number, state one. A mode adds each control it turns on, named by the mode's words with no value words
    (a boolean named so is on -- `boolean_value`), unless the read linked that control itself or the words read as off.
    No link is made over words the reading found the user unsure of (`doubts`): a request-level setting's words are
    stated words (R4), so the doubt's question would go unasked -- smoke C50 "I can't tell whether the values were
    log-transformed" linked to log_transformed with no value, which a boolean reads as on.
    """
    links, empty = [], set()
    for workflow in workflows:
        key = _key(workflow)
        for control in _controls(workflow):
            name = f"{workflow}.{control.name}"
            words = (getattr(read, f"{key}__{control.name}_words", "") or "").strip()
            if not words:
                empty.add(name)
                continue
            if (span := _span(task, words)) is None or any(_overlap(span, doubt) for doubt in doubts):
                continue
            said = (getattr(read, f"{key}__{control.name}_value_words", "") or "").strip()
            found = _span(task, said) if said else None
            if found is not None and any(_overlap(found, doubt) for doubt in doubts):
                continue
            value = task[found[0]:found[1]] if found is not None else ""
            if control.control_type in ("number", "integer") and not stated_numbers(value):
                value = ""
            links.append({"name": name, "quote": task[span[0]:span[1]], "value_quote": value, "span": span,
                          "workflow": workflow,
                          "unsure": bool(getattr(read, f"{key}__{control.name}_unsure", False))})  # B1 change 3
        mode = getattr(read, f"{key}__output_mode", _NOT_STATED)
        words = (getattr(read, f"{key}__output_mode_words", "") or "").strip()
        when = next((found for found_mode, found, _s in _modes(workflow) if found_mode == mode), None)
        if when is None or not words or (span := _span(task, words)) is None \
                or any(_overlap(span, doubt) for doubt in doubts):
            continue
        quote = task[span[0]:span[1]]
        if boolean_value("", quote) is not True:
            continue
        linked = {link["name"] for link in links}
        links += [{"name": f"{workflow}.{control}", "quote": quote, "value_quote": "", "span": span,
                   "workflow": workflow, "mode": mode}
                  for control, on in when.items() if on is True and f"{workflow}.{control}" not in linked]
    return links, empty


def _replaced(task: str, item: dict, links: list[dict], empty: set[str]) -> bool:
    """Whether a link over the same words replaces the reading's setting item: the same setting, an unregistered one,
    or -- only for a contract output mode, whose words the contract gives a meaning -- another setting of the same
    workflow whose own field the read left empty. A plain link to another setting removes nothing: its words may be
    wider than the setting it sets ("log2-transformed, mean-centered per gene" for centered alone)."""
    place = _span(task, item.get("quote", "")) if (item.get("quote") or "").strip() else None
    name = item.get("name", "")
    return any(_overlap(place, link["span"]) and (
        name in (link["name"], UNREGISTERED)
        or ("mode" in link and name.split(".", 1)[0] == link["workflow"] and name in empty))
        for link in links)


def merged_reading(task: str, reading: dict, links: list[dict], empty: set[str], *, add: bool = True) -> dict:
    """The reading (a proposal or re-read, as a dict) with the settings the links replace taken out and, with `add`,
    the links added as request-level settings (`conditions.settings`)."""
    merged = copy.deepcopy(reading)
    conditions = merged.get("conditions")
    if isinstance(conditions, dict):
        conditions["settings"] = [item for item in conditions.get("settings") or []
                                  if not _replaced(task, item, links, empty)]
    for sentence in _sentences(merged):
        for ask in sentence.get("asks") or []:
            if isinstance(ask.get("settings"), list):
                ask["settings"] = [item for item in ask["settings"] if not _replaced(task, item, links, empty)]
    if add and isinstance(conditions, dict):
        scoped = "sample_counts" in conditions  # ROUND-04's version 2 scopes each request-level setting
        conditions["settings"] += [{"name": link["name"], "quote": link["quote"], "value_quote": link["value_quote"],
                                    **({"applies_to": None} if scoped else {})} for link in links]
    return merged


def without_emptier(task: str, reading: dict, links: list[dict]) -> list[dict]:
    """B1 change 4: a link with no value words never replaces the reading's item for the same setting that has them
    (2a J41: the read gave ".parquet" no value and the format the reading had read vanished)."""
    valued = []
    for item in (reading.get("conditions") or {}).get("settings") or []:
        if (item.get("value_quote") or "").strip() and (item.get("quote") or "").strip():
            valued.append((item.get("name", ""), _span(task, item["quote"])))
    for sentence in _sentences(reading):
        for ask in sentence.get("asks") or []:
            for item in ask.get("settings") or []:
                if isinstance(item, dict) and (item.get("value_quote") or "").strip() and (item.get("quote") or "").strip():
                    valued.append((item.get("name", ""), _span(task, item["quote"])))
    return [link for link in links if link["value_quote"] or not any(
        name in (link["name"], UNREGISTERED) and _overlap(place, link["span"]) for name, place in valued)]


def _problems(check) -> set[str]:
    """Every limit and violation the check's requirement rows hold, as text."""
    found = set()
    for row in getattr(check, "requirements", []) or []:
        found.update(str(item) for item in (getattr(row, "limits", None) or []))
        found.update(str(item) for item in (getattr(row, "violations", None) or []))
    return found


def guarded_links(task: str, reading: dict, links: list[dict], empty: set[str], build) -> tuple[list[dict], list[dict]]:
    """(kept, held) -- B1 changes 3 and 5. `build(reading_dict)` makes the capability check (code only).

    A link the user is unsure of is held. Of the rest, a link whose merge adds a limit or violation the reading alone
    does not have is held, with the new problem as its reason: links are taken out one at a time, and one whose removal
    takes a new problem away is held. When a new problem stays and no single link explains it, every link is held."""
    held = [{**link, "reason": "unsure"} for link in links if link.get("unsure")]
    kept = [link for link in links if not link.get("unsure")]
    if not kept:
        return [], held
    before = _problems(build(reading))
    for _round in range(len(kept)):
        new = _problems(build(merged_reading(task, reading, kept, empty))) - before
        if not new:
            return kept, held
        culprit = None
        for link in kept:
            rest = [other for other in kept if other is not link]
            if len(_problems(build(merged_reading(task, reading, rest, empty))) - before) < len(new):
                culprit = link
                break
        if culprit is None:
            return [], held + [{**link, "reason": "; ".join(sorted(new))} for link in kept]
        reason = "; ".join(sorted(new - (_problems(build(merged_reading(
            task, reading, [other for other in kept if other is not culprit], empty))) - before)))
        held.append({**culprit, "reason": reason})
        kept = [other for other in kept if other is not culprit]
        if not kept:
            return [], held
    return kept, held


def _value_words(link: dict) -> str:
    return f' = "{link["value_quote"]}"' if link.get("value_quote") else ""


def held_core(core, held: list[dict]):
    """A DO with held links becomes an ASK with code's confirm questions (basis `setting_link_fact`); anything else,
    or nothing held, as it came. Never a refusal."""
    from ..contracts.core_decision import CoreDecision, FactQuestion
    if core.kind != "DO" or not held:
        return core
    facts = []
    for link in held:
        workflow, setting = link["name"].split(".", 1)
        if link.get("reason") == "unsure":
            question = f"Should {workflow}'s {setting} be set{_value_words(link)}? You were unsure."
        else:
            question = f"Did you mean {workflow}'s {setting}{_value_words(link)}? {link['reason']}."
        facts.append(FactQuestion(question=question.replace("..", "."), user_quote=link["quote"],
                                  workflows=[workflow]))
    evidence = {**core.evidence, "settings_held": [{k: v for k, v in link.items() if k != "span"} for link in held]}
    return CoreDecision(kind="ASK", basis="setting_link_fact", workflows=list(core.workflows), facts=facts,
                        declined=list(core.declined), evidence=evidence)
