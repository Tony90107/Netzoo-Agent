"""The slim reading (spec docs/superpowers/specs/2026-10-19-slim-reading-fields-design.md, S1): a request's words ->
`SlimReading` -> the decision table's `MenuReading`.

Step 1, the core read (`core_model`, `from_core`): A1 what each thing asked says, A2 the role of each registered name
code finds, A3 the data the user has or lacks, A4 run or ask -- and the C and D facts the user states, as a list of
stated facts. Nothing unstated is written; each fact's value is checked by code against its field's menu (plain
strings, so no schema nears OpenAI's 1000-enum limit; phase 1, v7).

Step 2, code (`slim_needs`): the candidates' contracts choose the B fields the focused read reads
(`menu_decision.b_fields`): B1-B3 per thing asked, B4 per candidate workflow; B5 (the candidates' controls) and B6
(counts, when a candidate limits one) whenever step 3 runs.

Step 3, the focused read (`focus_model`, `merge_focus`): one cell per chosen B1-B4 field (stated, unsure between
values, or not said) and two lists, B5 settings and B6 counts. Each field is read once: what step 1 read is never
re-read, and an answer fills its field.

`to_menu` turns a `SlimReading` into the `MenuReading` that `decide_menu` judges; `to_slim` turns a `MenuReading`
into the slim shape (phase-0 gold readings, recorded phase-1 reads); `wire_payloads` writes the payloads the two
reads would send for a reading, to count the values written. Offline: nothing in the live path calls this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..capability_sheet import sheet_entries
from ..contracts.capability_check import CONDITIONS
from ..contracts.menu_reading import Count, MenuReading, Requirement, Said, SettingAsked, Wanted
from ..contracts.slim_reading import RESULT_SAID, ResultItem, SlimReading, Stated
from ..judgment_defaults import judgment_defaults
from ..method_names import LIONESS_FAMILY, UNREGISTERED, registered_workflows, workflows_in
from ..workflow_conditions import all_conditions
from .menu_decision import b_fields, decide_menu
from .menu_focus import focus_limits
from .menu_reader import (
    _CONDITION_MEANS, _DATA_MEANS, _EDGE, _IDENTIFIER, _LIONESS_VERSION, Layout, ReadReport, _norm, _strict, name_key,
    quote_in, request_layout,
)

__all__ = ["FACTS", "MAX_FOCUS", "Needs", "SLIM_SHAPE", "chosen", "core_model", "core_text", "focus_model",
           "focus_text", "from_core", "merge_focus", "slim_needs", "split_b", "to_menu", "to_slim", "wire_payloads",
           "wire_values"]

SLIM_SHAPE = "s1"
MAX_FOCUS = 6
"""More candidates than this: the result is still open, and the B fields wait for it (as phase 1's focused re-read)."""
_FORBID = ConfigDict(extra="forbid")

# --- the fields ------------------------------------------------------------------------------------------------------

# Step-1 facts: wire field -> (slim field, dimension, the values the model may write).
FACTS = {
    "claim": ("C2", "claims", ("causal", "prediction")),
    "outside_action": ("C3", "delivery", ()),
    "special_data": ("C4", "", ("single_cells", "binary_values", "dynamic_model", "spatial_neighbors",
                                "overlapping_groups")),
    "groups": ("D1", "groups", ()),
    "comparison": ("D2", "compare", ("later", "describe", "test")),
    "sign": ("D3", "signed", ("signed", "unsigned")),
    "requirement": ("D4", "requirements", ("how_computed", "what_it_contains")),
    "raw_files": ("D5", "data_stage", ()),
    "file_doubt": ("D6", "unsure_files", ()),
    "covariate": ("D7", "covariates", ("batch", "site", "other")),
}
_FACT_MEANS = {
    "claim": "causal: proof that one thing causes another; prediction: a trained model that predicts an outcome.",
    "outside_action": "something done outside the analysis: results sent, uploaded, published, a dashboard or app, a "
                      "schedule (value empty).",
    "special_data": "single_cells: each profile is a single cell; binary_values: 0/1 calls to be modeled; "
                    "dynamic_model: a model of change from one time point to the next; spatial_neighbors: results "
                    "that use where samples sit or which are neighbours; overlapping_groups: an item allowed in "
                    "several groups. When the user is unsure, values: the special value and its plain counterpart "
                    "(bulk_samples, continuous_values, time_points_separately, samples_independent, one_group_each).",
    "groups": "words naming groups or conditions among the samples (AD and controls; value empty).",
    "comparison": "later: a comparison the user will make afterwards (a purpose); describe: results put side by side "
                  "as part of what is asked; test: a statistical test of the difference as part of what is asked.",
    "sign": "signed: whether regulators activate or repress (a sign per edge); unsigned: weights without a sign.",
    "requirement": "how_computed: how the result must be computed (a convex solution); what_it_contains: what the "
                   "result must contain (a p-value for every edge). A setting, a property of the data or a file "
                   "format is no requirement.",
    "raw_files": "raw files that need processing first: FASTQ, BAM, peak or signal files (value empty).",
    "file_doubt": "the user doubts what a named file holds: which export, which matrix (value empty).",
    "covariate": "a covariate or confounder the user mentions: batch, site (a site or centre), or other (age, sex, "
                 "treatment); one fact each.",
}
# C4: a special data situation and its plain counterpart, as the condition and its value.
_SPECIAL = {"single_cells": ("data_unit", "single_cells"), "bulk_samples": ("data_unit", "bulk_samples"),
            "binary_values": ("value_type", "binary"), "continuous_values": ("value_type", "continuous"),
            "dynamic_model": ("time_model", "dynamic"), "time_points_separately": ("time_model", "not_dynamic"),
            "spatial_neighbors": ("spatial", "uses_neighbors"), "samples_independent": ("spatial", "not_spatial"),
            "overlapping_groups": ("group_membership", "several_groups"),
            "one_group_each": ("group_membership", "one_group")}
_SPECIAL_OF = {pair: word for word, pair in _SPECIAL.items()}
_C4 = ("data_unit", "time_model", "spatial", "group_membership")
"""Conditions read only as C4; value_type is C4 when binary is in play, else B4 (DRAGON's continuous values)."""

# Step-3 cells: B1-B3 intents and B4 conditions, the values the model picks, and what each means.
_CELL_VALUES = {
    "granularity": ("whole_cohort", "per_group", "per_sample"),
    "regulators": ("tf", "tf_and_mirna_prior", "mirna_expression_driven", "other_regulators"),
    "layers": ("joint_two_layers", "per_layer", "three_or_more_jointly"),
}
_CELL_MEANS = {
    "granularity": "whole_cohort: one result for all samples together; per_group: one for each group or condition; "
                   "per_sample: a separate result for each sample (each patient).",
    "regulators": "tf: transcription factors only; tf_and_mirna_prior: transcription factors and miRNAs from a "
                  "miRNA-target prior; mirna_expression_driven: miRNA-gene links driven by measured miRNA expression; "
                  "other_regulators: lncRNAs, RNA-binding proteins, splicing factors, ceRNA or sponge networks.",
    "layers": "joint_two_layers: one model linking two omics layers to each other; per_layer: a separate result for "
              "each layer; three_or_more_jointly: three or more layers that must all be in one model.",
}
# Cell value -> [(dimension, value)].
_REGULATORS = {"tf": [("regulators", "tf")], "tf_and_mirna_prior": [("regulators", "tf_mirna")],
               "mirna_expression_driven": [("regulators", "tf_mirna"), ("mirna_driver", "measured_expression")],
               "other_regulators": [("regulators", "off_menu")]}
_LAYERS = {"joint_two_layers": [("integration", "joint")], "per_layer": [("integration", "per_layer")],
           "three_or_more_jointly": [("integration", "joint"), ("layers", "three_or_more_jointly")]}
_B_OF = {"granularity": "B1", "regulators": "B2", "mirna_driver": "B2", "integration": "B3", "layers": "B3"}
_ITEM_DIMENSIONS = ("granularity", "regulators", "integration", "layers", "compare", "signed", "requirements")


def _b4_values(name: str) -> tuple[str, ...]:
    if name.startswith("setting:"):
        return ("true", "false")
    if name in CONDITIONS:
        return tuple(v for v in CONDITIONS[name][0] if v != "not_stated")
    return tuple(judgment_defaults().dimensions[name].values)


# --- SlimReading <-> MenuReading -------------------------------------------------------------------------------------

def _said_of(fact: Stated) -> Said:
    if fact.values:
        return Said(status="unsure", values=list(fact.values), quotes=[fact.quote] if fact.quote else [])
    return Said(status="stated", value=fact.value, basis=fact.basis, quotes=[fact.quote or fact.value])


def _count_of(fact: Stated) -> Count:
    quotes = [fact.quote] if fact.quote else []
    if fact.values:
        return Count(status="conflicting", values=[int(v) for v in fact.values], quotes=quotes)
    return Count(status="stated", value=int(fact.value), quotes=quotes)


def to_menu(slim: SlimReading) -> MenuReading:
    """The decision table's state for a slim reading (structure only: quotes were checked when it was read)."""
    if slim.status == "failed":
        return MenuReading(status="failed")
    wanted: list[Wanted] = []
    for result in slim.results:
        quote, said = result.quote, result.said
        if said == "question_to_us":
            wanted.append(Wanted(quote=quote, form="question_to_us"))
        elif said == "purpose_or_topic":
            wanted.append(Wanted(quote=quote, form="purpose"))
        elif said in ("menu_result", "kind_of_result"):
            wanted.append(Wanted(quote=quote, artifact=Said(status="stated", value=result.value, basis="explicit",
                                                            quotes=[quote])))
        elif said == "off_menu_result":
            wanted.append(Wanted(quote=quote, outside_name=result.outside_name, artifact=Said(
                status="stated", value="off_menu", basis="explicit", quotes=[quote])))
        elif said == "unsure_between_results":
            wanted.append(Wanted(quote=quote, artifact=Said(status="unsure", values=list(result.values),
                                                            quotes=[quote])))
        elif said == "method_choice":
            wanted.append(Wanted(quote=quote, method_choice=[quote]))
        else:  # workflow_only: a run or a workflow, no result named
            wanted.append(Wanted(quote=quote))
    deliverable = [i for i, w in enumerate(wanted) if w.form == "deliverable"]
    conditions: dict[str, Said] = {}
    parts: dict = {"claims": Said(), "delivery": Said(), "groups": [], "settings": [], "unsure_files": [], "covariates": [],
                   "sample_count": Count(), "feature_count": Count(), "single_feature_count": None}
    purposes = []
    for fact in slim.stated:
        name = fact.name
        if name in _ITEM_DIMENSIONS:
            if name == "compare" and fact.value == "later":
                if not any(w.quote == fact.quote for w in wanted):
                    purposes.append(Wanted(quote=fact.quote, form="purpose"))
                continue
            targets = [fact.item] if 0 <= fact.item < len(wanted) else deliverable
            for index in targets:
                w = wanted[index]
                if name == "requirements":
                    update = {"requirements": [*w.requirements, Requirement(quote=fact.quote, verdicts=dict(
                        fact.verdicts), must=fact.must)]}
                else:
                    update = {name: _said_of(fact)}
                wanted[index] = w.model_copy(update=update)
        elif name in ("claims", "delivery"):
            parts[name] = _said_of(fact)
        elif name == "groups":
            parts["groups"].append(fact.value or fact.quote)
        elif name == "unsure_files":
            parts["unsure_files"].append(fact.quote)
        elif name == "covariates":
            parts["covariates"].append(fact.value)
        elif name in ("sample_count", "feature_count"):
            parts[name] = _count_of(fact)
        elif name == "single_feature_count":
            if fact.values:
                parts["features_one_type"] = True
            else:
                parts["single_feature_count"] = int(fact.value)
        elif fact.field in ("B4", "B5") and (name.startswith("setting:") or fact.field == "B5"):
            control = name.split(":", 1)[1] if name.startswith("setting:") else name
            parts["settings"].append(SettingAsked(quote=fact.quote, workflow=fact.workflow, control=control,
                                                  value="" if fact.values else fact.value, unsure=bool(fact.values),
                                                  values=list(fact.values)))
        elif name:  # a condition: B2 mirna_driver, B4, C4, D5 data_stage
            conditions[name] = _said_of(fact)
    background = [name for name, role in slim.roles.items() if role == "background"]
    choices = [name for name, role in slim.roles.items() if role == "choice"]
    if len(choices) >= 2:
        # Two or more names typed as a choice, on an item naming no result: the user is choosing between methods.
        for index in deliverable:
            w = wanted[index]
            if w.artifact.status == "not_stated" and not w.method_choice and any(n in w.quote for n in choices):
                wanted[index] = w.model_copy(update={"method_choice": [w.quote]})
    return MenuReading(
        wanted=[*wanted, *purposes], context_mentions=background, unregistered_methods=list(slim.unregistered_methods),
        claims=parts["claims"], delivery=parts["delivery"], conditions=conditions,
        data=[d.name for d in slim.data if d.value == "has"], data_absent=[d.name for d in slim.data if d.value == "lacks"],
        only_data=slim.only_these, groups=parts["groups"], sample_count=parts["sample_count"],
        feature_count=parts["feature_count"], single_feature_count=parts["single_feature_count"],
        settings=parts["settings"], unsure_files=parts["unsure_files"], run_requested=slim.run == "run",
        covariates=parts["covariates"], features_one_type=bool(parts.get("features_one_type")))


def _fact_of(field: str, name: str, said: Said, item: int = -1) -> Stated:
    values = [str(v) for v in said.values] if said.status in ("unsure", "conflicting") else []
    return Stated(field=field, name=name, value="" if values else str(said.value), values=values,
                  quote=(said.quotes or [""])[0], item=item, basis=said.basis or "explicit")


def to_slim(reading: MenuReading) -> SlimReading:
    """A `MenuReading` in the slim shape (phase-0 gold readings, recorded phase-1 reads). Values the slim reading never
    writes are left out: plain defaults (bulk samples, processed tables, association, files in the output folder)."""
    if reading.status == "failed":
        return SlimReading(status="failed")
    results, stated = [], []
    for w in reading.wanted:
        if w.form in ("context", "data_description"):
            continue  # words describing the data or the context are no A1 item: the slim reading does not write them
        index, a = len(results), w.artifact
        if w.form == "question_to_us":
            results.append(ResultItem(quote=w.quote, said="question_to_us"))
        elif w.form == "purpose":
            results.append(ResultItem(quote=w.quote, said="purpose_or_topic"))
        elif w.method_choice:
            results.append(ResultItem(quote=w.quote, said="method_choice"))
        elif a.status == "stated" and a.value == "off_menu":
            results.append(ResultItem(quote=w.quote, said="off_menu_result", outside_name=w.outside_name))
        elif a.status == "stated":
            said = "kind_of_result" if a.value in judgment_defaults().generic else "menu_result"
            results.append(ResultItem(quote=w.quote, said=said, value=str(a.value)))
        elif a.status in ("unsure", "conflicting"):
            results.append(ResultItem(quote=w.quote, said="unsure_between_results", values=list(a.values)))
        else:
            results.append(ResultItem(quote=w.quote, said="workflow_only"))
        for name in ("granularity", "regulators", "integration", "layers", "compare", "signed"):
            said = getattr(w, name)
            if said.status != "not_stated":
                field = _B_OF.get(name) or {"compare": "D2", "signed": "D3"}[name]
                stated.append(_fact_of(field, name, said, index))
        for requirement in w.requirements:
            stated.append(Stated(field="D4", name="requirements", value="how_computed", quote=requirement.quote,
                                 item=index, verdicts=dict(requirement.verdicts), must=requirement.must))
    defaults = {"data_unit": "bulk_samples", "data_stage": "processed_matrix", "time_model": "not_dynamic",
                "spatial": "not_spatial", "group_membership": "one_group"}
    for name, said in reading.conditions.items():
        if said.status == "not_stated" or (name in defaults and said.known() == defaults[name]):
            continue
        if name == "mirna_driver":
            field = "B2"
        elif name in _C4 or (name == "value_type" and ("binary" in said.values or said.known() == "binary")):
            field = "C4"
        elif name == "data_stage":
            field = "D5"
        else:
            field = "B4"
        stated.append(_fact_of(field, name, said))
    if reading.claims.known() in ("causal", "prediction") or reading.claims.status in ("unsure", "conflicting"):
        stated.append(_fact_of("C2", "claims", reading.claims))
    if reading.delivery.known() == "outside_netzoo" or reading.delivery.status in ("unsure", "conflicting"):
        stated.append(_fact_of("C3", "delivery", reading.delivery))
    stated += [Stated(field="D1", name="groups", value=group, quote=group) for group in reading.groups]
    stated += [Stated(field="D6", name="unsure_files", quote=quote) for quote in reading.unsure_files]
    stated += [Stated(field="D7", name="covariates", value=value, quote=value) for value in reading.covariates]
    for name in ("sample_count", "feature_count"):
        count = getattr(reading, name)
        if count.status == "stated":
            stated.append(Stated(field="B6", name=name, value=str(count.value), quote=(count.quotes or [""])[0]))
        elif count.status in ("unsure", "conflicting"):
            stated.append(Stated(field="B6", name=name, values=[str(v) for v in count.values],
                                 quote=(count.quotes or [""])[0]))
    if reading.single_feature_count is not None:
        stated.append(Stated(field="B6", name="single_feature_count", value=str(reading.single_feature_count)))
    b4 = {(workflow, name.split(":", 1)[1]) for workflow, names in judgment_defaults().b4_conditions.items()
          for name in names if name.startswith("setting:")}
    for s in reading.settings:
        is_b4 = any(control == s.control and s.workflow in (workflow, "") for workflow, control in b4)
        stated.append(Stated(field="B4" if is_b4 else "B5", name=f"setting:{s.control}" if is_b4 else s.control,
                             workflow=s.workflow, value=s.value, values=list(s.values) if s.unsure else [],
                             quote=s.quote))
    data = [Stated(field="A3", name=kind, value="has") for kind in reading.data]
    data += [Stated(field="A3", name=kind, value="lacks") for kind in reading.data_absent]
    roles = {name: "background" for name in reading.context_mentions}
    return SlimReading(results=results, roles=roles, unregistered_methods=list(reading.unregistered_methods),
                       data=data, only_these=reading.only_data, run="run" if reading.run_requested else "ask",
                       stated=stated)


# --- step 2: the B fields the candidates' contracts choose --------------------------------------------------------

@dataclass(frozen=True)
class Needs:
    """What the focused read (step 3) reads: B1-B3 cells per thing asked, B4 cells, the candidates (whose controls are
    B5's menu) and the counts a candidate limits (B6)."""

    intents: tuple[tuple[int, str], ...] = ()
    conditions: tuple[str, ...] = ()
    candidates: tuple[str, ...] = ()
    counts: tuple[str, ...] = ()
    groups: bool = False

    @property
    def runs(self) -> bool:
        return bool(self.candidates)

    def cells(self) -> list[tuple[str, int, str]]:
        """(key, item, dimension) per cell; B3 is one cell for integration and layers."""
        found, seen = [], set()
        for item, dimension in self.intents:
            dimension = "layers" if dimension == "integration" else dimension
            if (item, dimension) not in seen:
                seen.add((item, dimension))
                found.append((f"item{item + 1}_{_CELL_KEY[dimension]}", item, dimension))
        found += [(_condition_key(name), -1, name) for name in self.conditions]
        return found


_CELL_KEY = {"granularity": "scale", "regulators": "regulators", "layers": "layers"}


def _condition_key(name: str) -> str:
    if name.startswith("setting:"):
        workflow, control = name.split(":", 1)[1].split(".", 1)
        return re.sub(r"[^a-z0-9]+", "_", f"{workflow}_{control}".casefold())
    return name


def slim_needs(slim: SlimReading, task: str = "") -> Needs:
    """Step 2: none when the core read failed, its call is CLARIFY (the result is asked first) or UNCHECKED, or more
    than `MAX_FOCUS` candidates are left. A DECLINE at step 1 still reads the B fields: one may rest on a B field's
    plain value, and a field not read never refuses (spec 4.2; S2: LIONESS-PUMA named, regulators plain TF)."""
    if slim.status == "failed":
        return Needs()
    menu = to_menu(slim)
    if decide_menu(menu, task).kind in ("CLARIFY", "UNCHECKED"):
        return Needs()
    intents, conditions, candidates = b_fields(menu, task)
    if not candidates or len(candidates) > MAX_FOCUS:
        return Needs()
    counts = tuple(focus_limits(tuple(candidates))["counts"])
    return Needs(intents=tuple(intents), conditions=tuple(conditions), candidates=tuple(candidates), counts=counts,
                 groups=bool(menu.groups))


def split_b(slim: SlimReading) -> tuple[SlimReading, list[Stated]]:
    """The core read's part of a reading, and its B facts (what step 3 reads)."""
    core = [f for f in slim.stated if not f.field.startswith("B")]
    return slim.model_copy(update={"stated": core}), [f for f in slim.stated if f.field.startswith("B")]


def chosen(fact: Stated, needs: Needs) -> bool:
    """Whether step 3 reads the B fact's field for these needs (B5 whenever it runs, B6 when a candidate limits it)."""
    if not needs.runs:
        return False
    if fact.field == "B5":
        return True
    if fact.field == "B6":
        return ("feature_count" if fact.name == "single_feature_count" else fact.name) in needs.counts
    if fact.field == "B4":
        if fact.name.startswith("setting:"):
            control = fact.name.split(":", 1)[1]
            return any(n.startswith("setting:") and n.endswith(f".{control}") for n in needs.conditions)
        return fact.name in needs.conditions
    dimension = {"integration": "layers", "mirna_driver": "regulators"}.get(fact.name, fact.name)
    cells = {(item, dim) for _key, item, dim in needs.cells()}
    return any(dim == dimension and (fact.item in (-1, item)) for item, dim in cells)


# --- step 1: the core read -------------------------------------------------------------------------------------------

_ASKS = (
    "menu_result: a result on the menu, asked for or asked about (result); kind_of_result: only a kind of result -- "
    "network, regulation (result); workflow_only: a registered workflow or a run, and no result; method_choice: a "
    "choice between two or more methods, and no result; purpose_or_topic: no result -- only why they want it, a "
    "topic, or what can be done; off_menu_result: a result no registered workflow gives (outside_name); "
    "unsure_between_results: two or more results and the user does not know which (results).")
_WIRE_ASKS = tuple(value for value in RESULT_SAID if value != "question_to_us")
"""S2 (dev, 10 items): a question to us typed apart from the result it asks about ("Can PANDA give per-sample
networks?") named no result, and each went to CLARIFY -- v5's lesson again; the spec's A1 has no such value."""


@lru_cache(maxsize=1)
def core_text() -> str:
    """Step 1's menu: the results, the workflows, the data kinds and the facts -- from the defaults table and the
    capability sheet, nothing written here. No B field is shown: step 3 reads those."""
    table, sheet = judgment_defaults(), sheet_entries()
    lines = ["RESULTS ON THE MENU (items[].result, asks menu_result):"]
    lines += [f"- {name}: {table.artifacts[name].means}" for name in table.dimensions["artifact"].values]
    lines.append("KINDS OF RESULT (items[].result, asks kind_of_result): " + "; ".join(
        f"{word} = one of {', '.join(names)}" for word, names in table.generic.items()))
    lines += ["", "REGISTERED WORKFLOWS AND THE RESULTS THEY GIVE:"]
    for workflow in sorted(registered_workflows()):
        results = list(dict.fromkeys(table.by_entry[key] for key, entry in sheet.items()
                                     if entry.kind == "produces" and entry.workflow == workflow
                                     and table.by_entry[key] != "comparison"))
        lines.append(f"- {workflow}: {', '.join(results)}")
    lines += ["", f"WHAT AN ITEM ASKS (items[].asks): {_ASKS}"]
    lines += ["", "DATA KINDS (data[].kind):"]
    lines += [f"- {value}: {_DATA_MEANS[value]}" for value in table.dimensions["data_available"].values]
    lines += ["", "STATED FACTS (facts[].field: values):"]
    lines += [f"- {name}: {_FACT_MEANS[name]}" for name in FACTS]
    lines += ["", "OFF THE MENU (from the capability sheet), and where it is written:"]
    recorded: dict[str, list[str]] = {}
    for key, (dimension, value) in table.ruled_by.items():
        entry = sheet.get(key)
        label = {"artifact": "items[].asks off_menu_result", "claims": f"facts claim {value}",
                 "delivery": "facts outside_action", "data_available": "data mutation_calls lacks"}.get(dimension)
        if dimension in ("data_unit", "time_model") and value == CONDITIONS[dimension][1]:
            label = f"facts special_data {_SPECIAL_OF[(dimension, value)]}"
        off = value in table.dimensions[dimension].off_menu or (
            dimension in CONDITIONS and value == CONDITIONS[dimension][1])
        if entry is None or not off or label is None:
            continue
        texts = recorded.setdefault(label, [])
        if entry.text not in texts:
            texts.append(entry.text)
    lines += [f"- {label}: {' | '.join(texts)}" for label, texts in recorded.items()]
    lines.append(f"- unregistered_methods: a method or variant to use that is none of "
                 f"{', '.join(sorted(registered_workflows()))}.")
    return "\n".join(lines)


@lru_cache(maxsize=64)
def core_model(names: tuple[str, ...] = ()) -> type[BaseModel]:
    """Step 1's strict schema: lists of what was said -- nothing is written for what was not."""
    item = create_model(
        "SlimItem", __config__=_FORBID,
        quote=(str, Field(description="The user's exact words for this thing.")),
        asks=(Literal[_WIRE_ASKS], Field(description=_ASKS)),  # type: ignore[valid-type]
        result=(str, Field(description="menu_result: the result's name; kind_of_result: network or regulation; "
                                       "empty otherwise.")),
        results=(list[str], Field(description="unsure_between_results: the results the words leave open.")),
        outside_name=(str, Field(description="off_menu_result: the user's exact words naming the result.")),
    )
    data = create_model(
        "SlimData", __config__=_FORBID,
        kind=(str, Field(description="A kind from DATA KINDS.")),
        status=(Literal["has", "lacks"], Field(description="has: the user has it; lacks: they say they do not.")),
        quote=(str, Field(description="The user's exact words.")),
    )
    fact = create_model(
        "SlimFact", __config__=_FORBID,
        field=(Literal[tuple(FACTS)], Field(description="The fact, from STATED FACTS.")),  # type: ignore[valid-type]
        value=(str, Field(description="The fact's value from STATED FACTS; empty for facts without values.")),
        values=(list[str], Field(description="When the user is unsure: the values the words leave open.")),
        quote=(str, Field(description="The user's exact words.")),
    )
    fields: dict[str, tuple] = {
        "items": (list[item], Field(description=(
            "Each thing the request asks or asks about, one per quote. Words that only describe the data or give "
            "context are no item."))),
    }
    if names:
        role = create_model("SlimRole", __config__=_FORBID, role=(Literal["target", "choice", "background"], Field(
            description="target: the workflow the user asks to run or asks about; choice: one of two or more "
                        "workflows the user is choosing between; background: mentioned only as background (an "
                        "earlier run, where an input came from).")))
        fields["names"] = (create_model("SlimNames", __config__=_FORBID, **{
            name_key(name): (role, Field(description=name)) for name in names}), Field(description=(
                "Each registered name listed after the request, with its role.")))
    fields.update({
        "data": (list[data], Field(description="Each kind of data the user says they have or lack.")),
        "only_these": (str, Field(description="The user's exact words saying the data they list are all they have; "
                                              "empty when not said.")),
        "run": (Literal["run", "ask"], Field(description="run: the user asks to run it now; ask: anything else.")),
        "run_quote": (str, Field(description="run: the user's exact words asking to run it; empty otherwise.")),
        "facts": (list[fact], Field(description="Each fact of STATED FACTS the user states.")),
        "unregistered_methods": (list[str], Field(description=(
            "The user's exact words naming a method or variant to use that no registered workflow is."))),
    })
    return _strict(create_model("SlimCoreWire", __config__=_FORBID, **fields))


def _as_dict(payload) -> dict:
    return payload.model_dump(mode="json") if isinstance(payload, BaseModel) else dict(payload or {})


def _verified(quote, task: str, where: str, report: ReadReport) -> str:
    if quote_in(quote or "", task):
        return str(quote)
    if str(quote or "").strip():
        report.dropped.append(f"{where}: quote not in the request: {quote!r}")
    return ""


def _item_of(quote: str, results: list[ResultItem]) -> int:
    """The thing asked a fact's words belong to: the item whose words hold it, or hold most of it; -1 for all."""
    words = _norm(quote)
    deliverable = [i for i, r in enumerate(results) if r.said not in ("question_to_us", "purpose_or_topic")]
    for index in deliverable:
        item = _norm(results[index].quote)
        if words and (words in item or item in words):
            return index
    return -1


def from_core(payload, task: str, layout: Layout | None = None) -> tuple[SlimReading, ReadReport]:
    """The slim reading step 1 says, every quote checked against the request and every value against its menu."""
    raw, report, table = _as_dict(payload), ReadReport(), judgment_defaults()
    layout = layout or request_layout(task)
    menu_results, kinds = set(table.dimensions["artifact"].values), set(table.generic)
    results: list[ResultItem] = []
    for index, entry in enumerate(raw.get("items") or []):
        where = f"items[{index}]"
        quote = _verified(entry.get("quote"), task, where, report)
        asks = entry.get("asks") or "workflow_only"
        if not quote:
            report.dropped.append(f"{where}: dropped, its words are not the request's")
            continue
        value, values, outside = str(entry.get("result") or "").strip(), [], ""
        if asks in ("menu_result", "kind_of_result"):  # the value says which: a result on the menu or a kind
            asks = "menu_result" if value in menu_results else "kind_of_result" if value in kinds else asks
        if asks == "menu_result" and value not in menu_results or asks == "kind_of_result" and value not in kinds:
            report.dropped.append(f"{where}: {asks} {value!r} is not on the menu -> no result named")
            asks, value = "workflow_only", ""
        elif asks == "unsure_between_results":
            values = [v for v in dict.fromkeys(entry.get("results") or []) if v in menu_results | kinds]
            if len(values) < 2:
                report.dropped.append(f"{where}: unsure between fewer than two results on the menu")
                asks, values = "workflow_only", []
        elif asks == "off_menu_result":
            outside = next((n for n in (entry.get("outside_name"), quote) if n and quote_in(n, task)), "")
            if not outside or workflows_in(outside) or _IDENTIFIER.search(outside):
                # A registered name is on the menu, and a file name or identifier names no result (phase 1, d1, d5).
                report.dropped.append(f"{where}: off_menu_result without words naming a result off the menu")
                asks, outside = "workflow_only", ""
        if asks not in ("menu_result", "kind_of_result"):
            value = ""
        results.append(ResultItem(quote=quote, said=asks, value=value, values=values, outside_name=outside))
    roles = {}
    for name in layout.names:
        role = ((raw.get("names") or {}).get(name_key(name)) or {}).get("role")
        if role:
            roles[name] = role
    data, seen = [], set()
    for index, entry in enumerate(raw.get("data") or []):
        kind = str(entry.get("kind") or "")
        if kind not in table.dimensions["data_available"].values:
            report.dropped.append(f"data[{index}]: {kind!r} is no data kind")
            continue
        quote = _verified(entry.get("quote"), task, f"data[{index}]", report)
        if quote and kind not in seen:
            seen.add(kind)
            data.append(Stated(field="A3", name=kind, value=entry.get("status") or "has", quote=quote))
    only = _verified(raw.get("only_these"), task, "only_these", report)
    run_quote = _verified(raw.get("run_quote"), task, "run_quote", report) if raw.get("run") == "run" else ""
    stated = []
    for index, entry in enumerate(raw.get("facts") or []):
        fact = _fact(entry, task, f"facts[{index}]", report, results)
        if fact is not None:
            stated.append(fact)
    registered = {_norm(name) for name in (*registered_workflows(), LIONESS_FAMILY)}
    unregistered = [name for index, name in enumerate(raw.get("unregistered_methods") or [])
                    if _verified(name, task, f"unregistered_methods[{index}]", report)
                    and _norm(name).strip(_EDGE) not in registered]
    for match in _LIONESS_VERSION.finditer(task):
        if match.group() not in registered_workflows() and match.group() not in unregistered:
            unregistered.append(match.group())  # a LIONESS version not registered names none
    return SlimReading(results=results, roles=roles, unregistered_methods=unregistered, data=data,
                       only_these=bool(only), only_quote=only, run="run" if run_quote else "ask",
                       run_quote=run_quote, stated=stated), report


def _fact(entry: dict, task: str, where: str, report: ReadReport, results: list[ResultItem]) -> Stated | None:
    name = entry.get("field")
    if name not in FACTS:
        report.dropped.append(f"{where}: {name!r} is no fact")
        return None
    field, dimension, menu = FACTS[name]
    quote = _verified(entry.get("quote"), task, where, report)
    if not quote:
        report.dropped.append(f"{where}: {name} without verified words")
        return None
    value = str(entry.get("value") or "").strip()
    values = [str(v) for v in dict.fromkeys(entry.get("values") or []) if str(v).strip()]
    item = _item_of(quote, results) if dimension in ("compare", "signed", "requirements") else -1
    if name == "special_data":
        pairs = [_SPECIAL[v] for v in (values or [value]) if v in _SPECIAL]
        conditions = {condition for condition, _ in pairs}
        if len(conditions) != 1:
            report.dropped.append(f"{where}: special_data {value or values!r} names no one condition")
            return None
        condition = conditions.pop()
        chosen_values = list(dict.fromkeys(v for _, v in pairs))
        if values:
            if len(chosen_values) < 2:  # unsure about one special value: between it and its plain counterpart
                chosen_values = [v for v in (CONDITIONS[condition][0] if condition in CONDITIONS else ())
                                 if v != "not_stated"]
                report.filled.append(f"{where}: unsure {condition} -> every value")
            return Stated(field="C4", name=condition, values=chosen_values, quote=quote)
        if chosen_values[0] != CONDITIONS[condition][1]:
            report.dropped.append(f"{where}: {value} is a plain value, not a special situation")
            return None
        return Stated(field="C4", name=condition, value=chosen_values[0], quote=quote)
    if menu:
        if values:
            kept = [v for v in values if v in menu]
            if len(kept) >= 2:
                return Stated(field=field, name=dimension, values=kept, quote=quote, item=item)
            value = kept[0] if kept else value
        if value not in menu:
            report.dropped.append(f"{where}: {name} value {value!r} is not on its menu")
            return None
    if name == "outside_action":
        value = "outside_netzoo"
    elif name == "raw_files":
        value = "raw_files"
    elif name == "groups":
        value = quote
    elif name == "file_doubt":
        value = ""
    return Stated(field=field, name=dimension, value=value, quote=quote, item=item)


# --- step 3: the focused read -----------------------------------------------------------------------------------------

def _controls(candidates: tuple[str, ...], conditions: tuple[str, ...]) -> dict[str, list[tuple[str, object]]]:
    """B5's menu: each candidate's controls, less those a B4 cell reads (BONOBO's declared transform)."""
    b4 = {name.split(":", 1)[1] for name in conditions if name.startswith("setting:")}
    found = {}
    for workflow in candidates:
        limits = all_conditions().get(workflow)
        if limits is not None:
            found[workflow] = [(name, limit) for name, limit in limits.settings.items()
                               if f"{workflow}.{name}" not in b4]
    return found


def focus_text(needs: Needs, slim: SlimReading) -> str:
    from workflow_registry import ACTION_DEFINITIONS

    table = judgment_defaults()
    lines = [f"CANDIDATE WORKFLOWS: {', '.join(needs.candidates)}", ""]
    things = [(i, r.quote) for i, r in enumerate(slim.results)]
    if any(item >= 0 for _key, item, _dim in needs.cells()):
        lines += ["THINGS ASKED:", *(f"- item{i + 1}: \"{quote}\"" for i, quote in things), ""]
    lines.append("FIELDS (cells: stated, unsure between values, or not_said):")
    for key, item, dimension in needs.cells():
        if item >= 0:
            means = _CELL_MEANS[dimension]
            if dimension == "granularity" and not needs.groups:
                means = means.replace("per_group: one for each group or condition; ", "")
            lines.append(f"- {key} (item{item + 1}): {means}")
        elif dimension.startswith("setting:"):
            workflow, control = dimension.split(":", 1)[1].split(".", 1)
            lines.append(f"- {key}: whether the user's data for {workflow} are declared {control.replace('_', ' ')} "
                         f"(true or false).")
        else:
            options = table.dimensions[dimension].options if dimension in table.dimensions else {}
            values = "; ".join(f"{v}: {options.get(v, v)}" for v in _b4_values(dimension))
            lines.append(f"- {key}: {_CONDITION_MEANS.get(dimension, '')} Values: {values}.")
    lines += ["", "CONTROLS (settings[]: workflow, control and value; a setting none of these takes is control "
                  "unregistered):"]
    controls = _controls(needs.candidates, needs.conditions)
    for workflow, found in controls.items():
        if not found:
            lines.append(f"- {workflow}: no settings (runs with package defaults).")
            continue
        action = registered_workflows()[workflow]
        descriptions = {c.name: c.description for c in ACTION_DEFINITIONS[action].controls}
        for name, limit in found:
            if limit.control_type == "enum":
                kind = "one of " + ", ".join(map(str, limit.allowed_values))
            elif limit.control_type in ("number", "integer"):
                kind = limit.control_type + "".join(f" {word} {value:g}" for word, value in (
                    ("min", limit.minimum), ("max", limit.maximum)) if value is not None)
            else:
                kind = "true or false" if limit.control_type == "boolean" else limit.control_type.replace("_", " ")
            lines.append(f"- {workflow} {name} ({kind}): {descriptions.get(name, '')}")
    if needs.counts:
        limits = focus_limits(tuple(needs.candidates))["counts"]
        lines += ["", "COUNTS (counts[]: what, layer, number):"]
        lines += [f"- {name}: {'; '.join(limits[name]) or 'the total number of samples'}" for name in needs.counts]
    return "\n".join(lines)


@lru_cache(maxsize=64)
def focus_model(needs: Needs) -> type[BaseModel]:
    """Step 3's strict schema: one cell per chosen B1-B4 field, and the B5 and B6 lists."""

    def cell(key: str, values: tuple[str, ...]):
        Value = Literal[values]  # type: ignore[valid-type]
        # The quote first, as every field of phase 1's v2+ shape (d1): S2 wrote a scale "stated" on words naming none.
        return create_model(
            f"Cell_{key}", __config__=_FORBID,
            quote=(str, Field(description="The user's exact words that say it; empty when not said.")),
            status=(Literal["not_said", "stated", "unsure"], Field(description=(
                "not_said; stated: the words give the value; unsure: the user does not know, or gives several "
                "(values)."))),
            value=(Value | None, Field(description="stated: the value.")),
            values=(list[Value], Field(description="unsure: the values the words leave open.")),
        )

    fields: dict[str, tuple] = {}
    for key, item, dimension in needs.cells():
        if item >= 0:
            values = _CELL_VALUES[dimension]
            if dimension == "granularity" and not needs.groups:
                values = tuple(v for v in values if v != "per_group")
        else:
            values = _b4_values(dimension)
        fields[key] = (cell(key, values), Field(description=f"{key}"))
    setting = create_model(
        "SlimSetting", __config__=_FORBID,
        quote=(str, Field(description="The user's exact words giving the setting.")),
        workflow=(str, Field(description="The candidate workflow it is for; empty when the words do not say.")),
        control=(str, Field(description="The control from CONTROLS, or unregistered when none takes it.")),
        value=(str, Field(description="The value as the control's allowed values spell it; empty when none.")),
        values=(list[str], Field(description="When the user is unsure: the values the words leave open.")),
        asks_to_set=(bool, Field(description="true when the user asks to run with it; false when the words only "
                                             "describe their data or where results go.")),
    )
    fields["settings"] = (list[setting], Field(description="Each setting the user gives."))
    if needs.counts:
        count = create_model(
            "SlimCount", __config__=_FORBID,
            what=(Literal["samples", "features"], Field(description="samples: the number of samples; features: the "
                                                                   "number of features of one layer.")),
            layer=(str, Field(description="features: the layer they belong to (expression, protein, ...).")),
            value=(int | None, Field(description="The number; null when the user gives several.")),
            values=(list[int], Field(description="When the user is unsure: the numbers the words leave open.")),
            quote=(str, Field(description="The user's exact words.")),
        )
        fields["counts"] = (list[count], Field(description="Each number of samples or features the user gives."))
    return _strict(create_model("SlimFocusWire", __config__=_FORBID, **fields))


def _cell_facts(key: str, item: int, dimension: str, entry: dict, quote: str, report: ReadReport) -> list[Stated]:
    status = entry.get("status")
    values = [str(v) for v in dict.fromkeys(entry.get("values") or [])]
    value = str(entry.get("value") or "")
    if item < 0:
        menu = _b4_values(dimension)
        if status == "unsure":
            values = [v for v in values if v in menu]
            if len(values) < 2:
                values = list(menu)
                report.filled.append(f"focus.{key}: unsure with fewer than two values -> every value")
        elif value not in menu:
            report.dropped.append(f"focus.{key}: {value!r} is not a value")
            return []
        if dimension.startswith("setting:"):
            workflow, control = dimension.split(":", 1)[1].split(".", 1)
            return [Stated(field="B4", name=f"setting:{control}", workflow=workflow, quote=quote,
                           value="" if status == "unsure" else value, values=values if status == "unsure" else [])]
        return [Stated(field="B4", name=dimension, quote=quote, value="" if status == "unsure" else value,
                       values=values if status == "unsure" else [])]
    menu = _CELL_VALUES[dimension]
    mapping = {"granularity": {v: [("granularity", v)] for v in menu}, "regulators": _REGULATORS,
               "layers": _LAYERS}[dimension]
    chosen_values = [v for v in (values if status == "unsure" else [value]) if v in mapping]
    if not chosen_values:
        report.dropped.append(f"focus.{key}: {value or values!r} is not a value")
        return []
    if status == "unsure" and len(chosen_values) < 2:
        chosen_values = list(menu)
        report.filled.append(f"focus.{key}: unsure with fewer than two values -> every value")
    by_dimension: dict[str, list[str]] = {}
    for v in chosen_values:
        for name, mapped in mapping[v]:
            by_dimension.setdefault(name, [])
            if mapped not in by_dimension[name]:
                by_dimension[name].append(mapped)
    # A dimension only some of the values in play speak to is not written: unsure between TFs alone and miRNA links
    # driven by expression says nothing yet about what drives miRNA links (S2 smoke, accept24:U01).
    by_dimension = {name: mapped for name, mapped in by_dimension.items()
                    if all(any(n == name for n, _m in mapping[v]) for v in chosen_values)}
    facts = []
    for name, mapped in by_dimension.items():
        many = status == "unsure" and len(mapped) >= 2
        facts.append(Stated(field=_B_OF[name], name=name, item=item, quote=quote,
                            value="" if many else mapped[0], values=mapped if many else []))
    return facts


def _quoted_values(values, quote: str, limit=None) -> list[str]:
    """A setting's alternatives as the user gave them (hybrid spec 3.4; h3 L28, L02): a number counts only when the
    setting's own words hold it, a word only when they say it -- never the control's whole allowed range. A boolean's
    two values are its doubt."""
    found = [str(v).strip() for v in dict.fromkeys(values) if str(v).strip()]
    if limit is not None and limit.control_type == "boolean":
        return [v for v in found if v.casefold() in ("true", "false")]
    numbers = {n.value for n in request_layout(quote).numbers}
    words = _norm(quote)

    def said(value: str) -> bool:
        try:
            return float(value) in numbers
        except ValueError:
            return re.search(rf"(?<![\w.]){re.escape(_norm(value))}(?![\w])", words) is not None

    return [v for v in found if said(v)]


def merge_focus(slim: SlimReading, payload, task: str, needs: Needs) -> tuple[SlimReading, ReadReport]:
    """The core reading with the B facts the focused read states, every quote and value checked."""
    raw, report = _as_dict(payload), ReadReport()
    facts: list[Stated] = []
    for key, item, dimension in needs.cells():
        entry = raw.get(key) or {}
        if entry.get("status", "not_said") == "not_said":
            continue
        quote = _verified(entry.get("quote"), task, f"focus.{key}", report)
        if not quote:
            report.dropped.append(f"focus.{key}: {entry.get('status')} without verified words")
            continue
        facts += _cell_facts(key, item, dimension, entry, quote, report)
    controls = _controls(needs.candidates, needs.conditions)
    names = {name.casefold(): name for found in controls.values() for name, _limit in found}
    limits = {name: limit for found in controls.values() for name, limit in found}
    read_before = [_norm(q) for q in (*(r.quote for r in slim.results), *(d.quote for d in slim.data)) if q]
    workflows = {w.casefold(): w for w in needs.candidates}
    for index, entry in enumerate(raw.get("settings") or []):
        where = f"focus.settings[{index}]"
        quote = _verified(entry.get("quote"), task, where, report)
        if not quote:
            continue
        control = str(entry.get("control") or "").strip().casefold()
        workflow = workflows.get(str(entry.get("workflow") or "").strip().casefold(), "")
        if control == UNREGISTERED:
            if entry.get("asks_to_set") is False:
                report.dropped.append(f"{where}: describes the data, not a setting to use")
                continue
            if _IDENTIFIER.search(quote):
                report.dropped.append(f"{where}: names a file or field, not a setting")  # phase 1, d8 m3:U18
                continue
            if any(words in _norm(quote) for words in read_before):
                # Words step 1 read as a thing asked or as data are read once (spec 4.4): no setting (S2: "Run SAMBAR
                # using the provided four reference/data files" refused SAMBAR as a setting it lacks).
                report.dropped.append(f"{where}: holds words step 1 read as a thing asked or data, not a setting")
                continue
            control = UNREGISTERED
        elif control in names:
            control = names[control]
        else:
            report.dropped.append(f"{where}: {entry.get('control')!r} is no candidate's control")
            continue
        value = str(entry.get("value") or "").strip()
        values = [] if value else _quoted_values(entry.get("values") or [], quote, limits.get(control))
        if len(values) == 1:
            value, values = values[0], []
        facts.append(Stated(field="B5", name=control, workflow=workflow, quote=quote, value=value,
                            values=values if control != UNREGISTERED else []))
    samples, layers = [], {}
    for index, entry in enumerate(raw.get("counts") or []):
        quote = _verified(entry.get("quote"), task, f"focus.counts[{index}]", report)
        numbers = sorted({int(v) for v in entry.get("values") or []}) or (
            [int(entry["value"])] if entry.get("value") is not None else [])
        if not quote or not numbers:
            continue
        if entry.get("what") == "samples":
            samples.append((numbers, quote))
        else:
            layers.setdefault(str(entry.get("layer") or "features").casefold(), []).append((numbers, quote))
    if "sample_count" in needs.counts and samples:
        doubtful = [n for n, _q in samples if len(n) >= 2]
        if doubtful:
            facts.append(Stated(field="B6", name="sample_count", values=[str(v) for v in doubtful[0]],
                                quote=samples[0][1]))
        else:  # the largest stated number is the total
            facts.append(Stated(field="B6", name="sample_count", value=str(max(n[0] for n, _q in samples)),
                                quote=samples[0][1]))
    if "feature_count" in needs.counts and layers:
        per_layer = [sorted({v for numbers, _q in found for v in numbers}) for found in layers.values()]
        quote = next(q for found in layers.values() for _n, q in found)
        totals = {0}
        for options in per_layer:
            totals = {total + option for total in totals for option in options}
        if len(totals) == 1:
            facts.append(Stated(field="B6", name="feature_count", value=str(totals.pop()), quote=quote))
        else:
            facts.append(Stated(field="B6", name="feature_count", values=[str(v) for v in sorted(totals)],
                                quote=quote))
        if len(per_layer) == 1 and len(per_layer[0]) == 1:
            facts.append(Stated(field="B6", name="single_feature_count", value=str(per_layer[0][0]), quote=quote))
        elif len(per_layer) == 1:  # one data type, unsure: its count is the one COBRA's genes > samples reads (h3 L40)
            facts.append(Stated(field="B6", name="single_feature_count", values=[str(v) for v in per_layer[0]],
                                quote=quote))
    return slim.model_copy(update={"stated": [*slim.stated, *facts]}), report


# --- the values written ----------------------------------------------------------------------------------------------

def wire_payloads(slim: SlimReading, needs: Needs, names: tuple[str, ...] = ()) -> tuple[dict, dict | None]:
    """The payloads steps 1 and 3 would send for this reading -- to count the values written (spec 6.1, S1/S2)."""
    core: dict = {"items": [{"quote": r.quote, "asks": r.said, "result": r.value, "results": list(r.values),
                             "outside_name": r.outside_name} for r in slim.results]}
    if names:
        core["names"] = {name_key(name): {"role": slim.roles.get(name, "target")} for name in names}
    core["data"] = [{"kind": d.name, "status": d.value, "quote": d.quote} for d in slim.data]
    core["only_these"] = slim.only_quote
    core["run"], core["run_quote"] = slim.run, slim.run_quote
    wire_of = {dimension: name for name, (_field, dimension, _menu) in FACTS.items() if dimension}
    facts = []
    for f in slim.stated:
        if f.field in ("C4",):
            values = [_SPECIAL_OF.get((f.name, v), v) for v in f.values]
            facts.append({"field": "special_data", "value": "" if values else _SPECIAL_OF.get((f.name, f.value), f.value),
                          "values": values, "quote": f.quote})
        elif f.field in ("C2", "C3", "D1", "D2", "D3", "D4", "D5", "D6", "D7"):
            name = wire_of[f.name]
            value = "" if name in ("outside_action", "raw_files", "groups", "file_doubt") else f.value
            facts.append({"field": name, "value": value, "values": list(f.values), "quote": f.quote})
    core["facts"] = facts
    core["unregistered_methods"] = list(slim.unregistered_methods)
    if not needs.runs:
        return core, None
    focus: dict = {}
    for key, item, dimension in needs.cells():
        focus[key] = {"status": "not_said", "value": None, "values": [], "quote": ""}
    for f in slim.stated:
        if not f.field.startswith("B") or f.field in ("B5", "B6") or not chosen(f, needs):
            continue
        for key, item, dimension in needs.cells():
            same = (dimension == {"integration": "layers", "mirna_driver": "regulators"}.get(f.name, f.name)
                    and f.item in (-1, item)) or (dimension.startswith("setting:") and f.name.startswith("setting:")
                                                 and dimension.endswith(f".{f.name.split(':', 1)[1]}"))
            if same:
                focus[key] = {"status": "unsure" if f.values else "stated", "value": None if f.values else f.value,
                              "values": list(f.values), "quote": f.quote}
    focus["settings"] = [{"quote": f.quote, "workflow": f.workflow, "control": f.name, "value": f.value,
                          "values": list(f.values), "asks_to_set": True} for f in slim.stated if f.field == "B5"]
    if needs.counts:
        focus["counts"] = [{"what": "samples" if f.name == "sample_count" else "features", "layer": "",
                            "value": None if f.values else int(f.value), "values": [int(v) for v in f.values],
                            "quote": f.quote} for f in slim.stated
                           if f.field == "B6" and f.name != "single_feature_count" and chosen(f, needs)]
    return core, focus


_EMPTY = (None, "", "not_stated", "not_mentioned", "not_said", "none", False, "unspecified", "nothing")


def wire_values(payload) -> tuple[int, int]:
    """(values written, values with content) of a payload: every leaf, an empty list counting once (phase 1's count:
    56 bench items x 2 reads, median 207.5 and 25)."""
    leaves = []

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            if not node:
                leaves.append([])
            for value in node:
                walk(value)
        else:
            leaves.append(node)

    walk(payload or {})
    return len(leaves), sum(1 for v in leaves if v != [] and v not in _EMPTY)
