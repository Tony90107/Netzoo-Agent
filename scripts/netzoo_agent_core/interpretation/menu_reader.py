"""The closed-menu reader (spec 2026-10-18, sections 3.1 and 6, phase 1): a request's words -> `MenuReading`.

The model is shown the closed menu -- every result on it and what it means, each registered workflow and the results
it gives, each dimension's values, each workflow's controls with their allowed values, and what is off the menu with
the field that records it -- and fills one strict-schema `MenuReadingWire`: what the user said, field by field, each
with the user's exact words. It never says whether anything can be done. Code then checks every quote against the
request and builds the `MenuReading` that `decide_menu` reads. A field whose words are not in the request is not
stated, and the report records it.

Shape (phase-1 dev rounds, `docs/research-log/closed-menu-phase1-2026-10-18/`):
- every field leads with one quote string (d1: gpt-4o-mini left quote lists empty, 100 quotes in 39/85 reads);
- what a wanted item names is typed first -- a result on the menu, a kind of result, only a workflow, a result off
  the menu, a doubt between results, nothing (d1: "Run LIONESS-PANDA" was read as an off-menu result);
- each kind of data has its own field -- has, lacks, not mentioned (d1: "We have X, Y and Z" was read as only data);
- code lists every number in the request and the model types each one -- a sample count, a feature count of a
  layer, a setting, or other; one of several possibilities or not (d1: counts and settings were mostly not read);
- code lists the sentences and the model says, for each, whether it states a doubt and about which field (d1: 5/41
  doubts read).
Code, not the model, does the arithmetic and the bookkeeping: feature counts are summed over layers, alternatives
become `conflicting` values, a doubt with too few values gets the dimension's values, registered names are counted
from the words (`named_workflows` stays None).

Phase 1: offline only; nothing in the live path calls it.
"""

from __future__ import annotations

import itertools
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..capability_sheet import sheet_entries
from ..contracts.capability_check import CONDITIONS
from ..contracts.menu_reading import Count, MenuReading, Requirement, Said, SettingAsked, Wanted
from ..contracts.strict_schema import strict_json_schema
from ..judgment_defaults import JudgmentDefaults, judgment_defaults
from ..method_names import LIONESS_FAMILY, UNREGISTERED, registered_workflows, workflows_in
from ..workflow_conditions import all_conditions
from .capability_check import request_sentences

__all__ = ["CONDITION_FIELDS", "DOUBT_ABOUT", "READER_SHAPE", "Layout", "NumberSpan", "ReadReport", "WANTED_FIELDS", "layout_text",
           "menu_text", "quote_in", "reader_model", "request_layout", "to_menu_reading"]

READER_SHAPE = "v7"
"""The schema shape the phase-1 rounds record (v1: quote lists, artifact enum with off_menu, a data list)."""
_FORBID = ConfigDict(extra="forbid")
Status = Literal["stated", "not_stated", "unsure", "conflicting"]
Basis = Literal["explicit", "implied"]
WireForm = Literal["asks", "purpose", "data_description", "context"]
"""v5: a question is not its own form -- d4 read "which method gives a separate TF-gene network for each sample?" as a
question naming nothing. Code calls an `asks` item naming no result and stating nothing a question to us."""
Names = Literal["menu_result", "kind_of_result", "workflow_only", "off_menu_result", "unsure_between_results",
                "nothing"]
Have = Literal["has", "lacks", "not_mentioned"]
RequirementAbout = Literal["how_computed", "what_it_contains", "another_result", "a_setting", "data_property",
                           "file_or_format", "other"]
# Only how the result is computed or what it holds is matched to contracts (d4: another result, a setting, a data
# property and a file format were each read as requirements and asked about).
_REQUIREMENT_KINDS = ("how_computed", "what_it_contains")

# The intent fields of a wanted item, in the order the menu shows them.
WANTED_FIELDS = ("integration", "granularity", "regulators", "layers", "signed", "compare")
# Request-level data conditions: CONDITIONS' typed conditions plus the two the defaults table adds.
CONDITION_FIELDS = ("data_unit", "data_stage", "mutation_origin", "value_type", "mirna_driver", "time_model",
                    "spatial", "group_membership", "input_network", "samples_matched")
DOUBT_ABOUT = ("none", "artifact", *WANTED_FIELDS, *CONDITION_FIELDS, "sample_count", "feature_count", "setting",
               "file_content", "other")
UNSPECIFIED = "unspecified"
MAX_SENTENCES = 16
MAX_NUMBERS = 16

# What counts as stated, per field: spec section 9.2 ("什麼才算有說"), drafts 3-5.
_STATED_WHEN = {
    "artifact": "What the item's words name: menu_result (a result on the menu: value), kind_of_result (only a kind "
                "of result -- network, regulation: kind), workflow_only (a registered workflow is named and no "
                "result), off_menu_result (a result no registered workflow gives: outside_name), "
                "unsure_between_results (the user does not know which result: values), nothing.",
    "integration": "stated only by words linking the layers to each other (between miRNAs and cytokines, within "
                   "and across the two layers, one integrated network across all layers) or asking for each layer "
                   "on its own; having two layers states nothing.",
    "granularity": "stated by words as clear as \"that patient's own network\", \"one network per diagnostic "
                   "group\", \"one network for the whole cohort\"; \"a network\" states nothing.",
    "regulators": "stated only when the user names the regulators (transcription factors, miRNAs, lncRNAs); "
                  "having a motif prior or miRNA data does not state it.",
    "layers": "for one joint model: two is exactly two omics layers; three_or_more_jointly is three or more "
              "layers that must all be in one model.",
    "signed": "signed when the user asks whether regulators activate or repress (a sign per edge); unsigned when "
              "they ask for edge weights without a sign.",
    "compare": "describe: results put side by side between groups, time points or samples; test: a statistical "
               "test of the difference; none: no comparison is asked for. A comparison said only as what the user "
               "will do later is a purpose, not this.",
}
_CONDITION_MEANS = {
    **{name: description for name, (_values, _off, description) in CONDITIONS.items()},
    "data_stage": "Whether the user's data are processed tables (matrices, counts) or raw files that need "
                  "processing first (FASTQ, BAM, peak or signal files).",
    "input_network": "What an existing network the user gives holds: regulator-to-gene edges or gene-gene edges.",
}
_DATA_MEANS = {
    "expression": "a gene expression table (RNA-seq counts, microarray, normalised expression)",
    "coexpression_matrix": "a gene-by-gene co-expression or correlation matrix",
    "motif_prior": "a TF-to-gene motif prior",
    "ppi": "a protein-protein (TF-TF) interaction network",
    "mirna_prior": "a miRNA-to-target-gene prior",
    "mutation_calls": "mutation calls or counts per gene and patient",
    "design_matrix": "a sample sheet or design matrix of covariates",
    "regulator_gene_network": "an existing regulator-to-gene network",
    "methylation": "a methylation layer",
    "protein": "a protein (proteomics) layer",
    "metabolite": "a metabolite (metabolomics) layer",
    "mirna_expression": "measured miRNA expression",
    "chromatin": "a chromatin layer (ATAC-seq, ChIP-seq)",
    "other_omics": "another omics layer (copy number, lipids, microbiome)",
}


def _values(table: JudgmentDefaults, name: str) -> tuple[str, ...]:
    dimension = table.dimensions[name]
    return (*dimension.values, *dimension.off_menu)


def _condition_values(table: JudgmentDefaults, name: str) -> tuple[str, ...]:
    if name in CONDITIONS:
        return tuple(value for value in CONDITIONS[name][0] if value != "not_stated")
    return tuple(table.dimensions[name].values)


def _controls() -> dict[str, dict]:
    return {workflow: dict(conditions.settings) for workflow, conditions in sorted(all_conditions().items())}


# --- what code finds in the request before the call -----------------------------------------------------------------

_DIGITS = re.compile(r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s?[kK](?![\w]))?(?![\w])"
                     r"|(?<![\w.])\.\d+(?![\w])")
# Number words from two up: "one" and "single" mostly mean a single result ("one network"), not a count.
_WORD_NUMBERS = {word: index for index, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split()) if index >= 2}
_WORD_NUMBERS.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
                      "ninety": 90, "hundred": 100})
_LIONESS_VERSION = re.compile(rf"(?<![A-Za-z0-9_-]){LIONESS_FAMILY}-[A-Z][A-Za-z0-9]*(?![A-Za-z0-9_-])")
# A file name (name.ext) or a snake_case identifier: the words name a file or a field, never a result.
_IDENTIFIER = re.compile(r"\b\w+\.[A-Za-z][A-Za-z0-9]{1,4}\b|\b[a-z0-9]+_[a-z0-9_]+\b")
_WORDS = re.compile(r"\b(" + "|".join(_WORD_NUMBERS) + r")\b", re.I)


@dataclass(frozen=True, slots=True)
class NumberSpan:
    text: str
    value: float
    start: int
    end: int
    context: str
    """The request's words around the number, verbatim."""


@dataclass(frozen=True, slots=True)
class Layout:
    sentences: tuple[str, ...]
    numbers: tuple[NumberSpan, ...]
    spans: tuple[tuple[int, int], ...] = ()
    """Each sentence's (start, end) in the request."""

    def sentence_of(self, number: NumberSpan) -> int:
        """The 1-based sentence the number is in (0 when none is)."""
        return next((i for i, (start, end) in enumerate(self.spans, 1) if start <= number.start < end), 0)


def _context(task: str, start: int, end: int, width: int = 40) -> str:
    left, right = max(0, start - width), min(len(task), end + width)
    while left > 0 and not task[left - 1].isspace():
        left -= 1
    while right < len(task) and not task[right].isspace():
        right += 1
    return task[left:right].strip()


def request_layout(task: str) -> Layout:
    """The request's sentences and the numbers in it, as code finds them; the model types each (one field each)."""
    spans = request_sentences(task) or [(0, len(task))]
    if len(spans) > MAX_SENTENCES:
        spans = [*spans[:MAX_SENTENCES - 1], (spans[MAX_SENTENCES - 1][0], spans[-1][1])]
    found = []
    for match in _DIGITS.finditer(task):
        raw = match.group().replace(",", "").replace(" ", "")
        try:
            value = float(raw.rstrip("kK")) * (1000 if raw[-1:] in "kK" else 1)
        except ValueError:
            continue
        found.append((match.start(), match.end(), match.group(), value))
    found += [(m.start(), m.end(), m.group(), float(_WORD_NUMBERS[m.group().casefold()])) for m in _WORDS.finditer(task)]
    numbers = tuple(NumberSpan(text, value, start, end, _context(task, start, end))
                    for start, end, text, value in sorted(found)[:MAX_NUMBERS])
    return Layout(sentences=tuple(task[s:e].strip() for s, e in spans), numbers=numbers, spans=tuple(spans))


def layout_text(layout: Layout) -> str:
    lines = ["Sentences (sentences.sN):", *(f"s{i}. {text}" for i, text in enumerate(layout.sentences, 1))]
    if layout.numbers:
        lines += ["", "Numbers (numbers.nN):"]
        lines += [f"n{i} = {number.text}: \"{number.context}\"" for i, number in enumerate(layout.numbers, 1)]
    return "\n".join(lines)


# --- the menu -------------------------------------------------------------------------------------------------------

def _control_line(name: str, limit, description: str) -> str:
    if limit.control_type == "enum":
        allowed = ", ".join(map(str, limit.allowed_values))
        aliases = "; ".join(f"{alias} = {value}" for alias, value in limit.value_names)
        kind = f"one of {allowed}" + (f" ({aliases})" if aliases else "")
    elif limit.control_type in ("number", "integer"):
        low = "" if limit.minimum is None else f"{limit.minimum:g}"
        high = "" if limit.maximum is None else f"{limit.maximum:g}"
        kind = f"{limit.control_type}" + (f" {low or '-inf'}..{high or 'inf'}" if low or high else "")
    elif limit.control_type == "boolean":
        kind = "true or false"
    else:
        kind = limit.control_type.replace("_", " ")
    default = "" if limit.default in (None, "", []) else f"; default {limit.default}"
    return f"  - {name} ({kind}{default}): {description}"


@lru_cache(maxsize=1)
def menu_text() -> str:
    """The closed menu, from the defaults table, the capability sheet and the registry -- nothing written here."""
    from workflow_registry import ACTION_DEFINITIONS

    table, sheet = judgment_defaults(), sheet_entries()
    lines = ["RESULTS ON THE MENU (wanted[].result.value):"]
    for name in table.dimensions["artifact"].values:
        lines.append(f"- {name}: {table.artifacts[name].means}")
    lines.append("KINDS OF RESULT (wanted[].result.kind, when the words name only the kind): " + "; ".join(
        f"{word} = one of {', '.join(names)}" for word, names in table.generic.items()))
    lines += ["", "REGISTERED WORKFLOWS AND THE RESULTS THEY GIVE:"]
    for workflow in sorted(registered_workflows()):
        results = list(dict.fromkeys(
            f"{table.by_entry[key]} ({'per sample' if entry.granularity == frozenset({'sample_specific'}) else 'per sample and cohort' if 'sample_specific' in entry.granularity else 'cohort'})"
            for key, entry in sheet.items() if entry.kind == "produces" and entry.workflow == workflow
            and table.by_entry[key] != "comparison"))
        lines.append(f"- {workflow}: {', '.join(results)}")
    lines += ["", "WANTED FIELDS (each: what states it; values):"]
    lines.append(f"- result: {_STATED_WHEN['artifact']}")
    for name in WANTED_FIELDS:
        dimension = table.dimensions[name]
        options = "; ".join(f"{value}: {text}" for value, text in dimension.options.items())
        values = ", ".join(_values(table, name))
        lines.append(f"- {name} ({values}): {_STATED_WHEN[name]}" + (f" Values: {options}" if options else ""))
    lines += ["", "DATA (data.<kind>: has, lacks or not_mentioned):"]
    lines += [f"- {value}: {_DATA_MEANS[value]}" for value in table.dimensions["data_available"].values]
    lines += ["", "DATA CONDITIONS (conditions.<name>; values):"]
    for name in CONDITION_FIELDS:
        lines.append(f"- {name} ({', '.join(_condition_values(table, name))}): {_CONDITION_MEANS[name]}")
    lines += ["", "WORKFLOW CONTROLS (settings, and numbers typed as a setting: workflow, control; a setting no "
                  "control below takes is control unregistered):"]
    for workflow, controls in _controls().items():
        action = registered_workflows()[workflow]
        descriptions = {control.name: control.description for control in ACTION_DEFINITIONS[action].controls}
        if not controls:
            lines.append(f"- {workflow}: no settings (runs with package defaults).")
            continue
        lines.append(f"- {workflow}:")
        lines += [_control_line(name, limit, descriptions.get(name, "")) for name, limit in controls.items()]
    lines += ["", "OFF THE MENU, AND THE FIELD THAT RECORDS IT (from the capability sheet):"]
    recorded: dict[str, list[str]] = {}
    for key, (dimension, value) in table.ruled_by.items():
        entry = sheet.get(key)
        # Only what no registered workflow gives: a near miss of one workflow (one network per sample is not
        # OTTER's, but is LIONESS-PANDA's) is on the menu.
        off = value in table.dimensions[dimension].off_menu or (
            dimension in CONDITIONS and value == CONDITIONS[dimension][1])
        if entry is None or not off:
            continue
        label = (f"conditions.{dimension}={value}" if dimension in CONDITION_FIELDS else
                 "data.mutation_calls=lacks" if dimension == "data_available" else
                 "result: off_menu_result" if dimension == "artifact" else f"{dimension}={value}")
        texts = recorded.setdefault(label, [])
        if entry.text not in texts:
            texts.append(entry.text)
    lines += [f"- {label}: {' | '.join(texts)}" for label, texts in recorded.items()]
    lines.append(f"- unregistered_methods: a method or variant to use that is none of "
                 f"{', '.join(sorted(registered_workflows()))}.")
    return "\n".join(lines)


# --- the wire schema ------------------------------------------------------------------------------------------------

_QUOTE = Field(description="The user's exact words that state it or show the doubt; empty when not stated.")


def _said(name: str, values: tuple[str, ...], description: str) -> tuple[type, object]:
    Value = Literal[values]  # type: ignore[valid-type]
    model = create_model(
        f"{name}Said", __config__=_FORBID,
        status=(Status, Field(description="stated, not_stated, unsure (the user does not know or has not decided) or "
                                          "conflicting (the words say two things).")),
        basis=(Basis | None, Field(description="When stated: explicit, or implied by words as clear as saying it.")),
        value=(Value | None, Field(description="The value, when stated.")),
        values=(list[Value], Field(description="When unsure or conflicting: the values the words leave open.")),
        quote=(str, _QUOTE),
    )
    return model, Field(description=description)


def _strict(model: type[BaseModel]) -> type[BaseModel]:
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def _enum(values) -> object:
    return Literal[tuple(values)]  # type: ignore[valid-type]


@lru_cache(maxsize=64)
def reader_model(sentences: int = 1, numbers: int = 0) -> type[BaseModel]:
    """The provider-facing schema for a request with this many sentences and numbers: every field required, every
    value an enum from the menu (strict mode), one field per sentence and per number so none is skipped."""
    table = judgment_defaults()
    results = table.dimensions["artifact"].values
    result = create_model(
        "ResultWire", __config__=_FORBID,
        quote=(str, _QUOTE),
        names=(Names, Field(description=_STATED_WHEN["artifact"])),
        value=(_enum(results) | None, Field(description="menu_result: the result.")),
        kind=(_enum(table.generic) | None, Field(description="kind_of_result: the kind.")),
        values=(list[_enum((*results, "off_menu"))], Field(description="unsure_between_results: the results the "
                                                                        "words leave open (off_menu for one off it).")),
        outside_name=(str, Field(description="off_menu_result: the user's exact words naming the result.")),
    )
    requirement = create_model(
        "RequirementWire", __config__=_FORBID,
        quote=(str, Field(description="The user's exact words.")),
        about=(RequirementAbout, Field(description="how_computed: how the result must be computed; "
                                                   "what_it_contains: what the result must contain; another_result: "
                                                   "a result of its own; a_setting: a workflow setting; data_property: "
                                                   "a property of the user's data; file_or_format: file names, "
                                                   "formats or folders; other.")),
    )
    wanted_fields: dict[str, tuple] = {
        "quote": (str, Field(description="The user's exact words for this item.")),
        "form": (WireForm, Field(description="asks: a request or a question about results or methods (a result to "
                                             "produce, whether or which method produces one, a workflow to run, "
                                             "which method to use, what can be done); purpose: why they want it or "
                                             "what they will do with it later; data_description: what their data "
                                             "is; context: anything else.")),
        "result": (result, Field(description="What the item's words name.")),
    }
    for name in WANTED_FIELDS:
        wanted_fields[name] = _said(name.capitalize(), _values(table, name), _STATED_WHEN[name])
    wanted_fields["requirements"] = (list[requirement], Field(description=(
        "Each requirement the user puts on this result (a convex solution, a p-value for every edge, edges weighted "
        "by our miRNA expression), typed by what it is about.")))
    wanted = create_model("WantedWire", __config__=_FORBID, **wanted_fields)

    have = create_model("HaveWire", __config__=_FORBID, status=(Have, ...), quote=(str, _QUOTE))
    data = create_model("DataWire", __config__=_FORBID, **{
        name: (have, Field(description=_DATA_MEANS[name])) for name in table.dimensions["data_available"].values})
    conditions = create_model("ConditionsWire", __config__=_FORBID, **{
        name: _said("".join(part.capitalize() for part in name.split("_")), _condition_values(table, name),
                    _CONDITION_MEANS[name])
        for name in CONDITION_FIELDS})
    controls = sorted({name for limits in _controls().values() for name in limits})
    workflow = _enum((*sorted(registered_workflows()), UNSPECIFIED))
    control = _enum((*controls, UNREGISTERED))
    layer = _enum((*sorted(table.omics_layers), UNSPECIFIED))
    number = create_model(
        "NumberWire", __config__=_FORBID,
        unit=(str, Field(description="The user's exact words for what the number counts or sets (genes, paired "
                                     "samples, lam, iterations).")),
        what=(Literal["sample_count", "feature_count", "setting", "layers_files_or_groups", "other"], Field(
            description=("sample_count: the total number of samples; feature_count: the number of features (genes, "
                         "proteins, ...) of one layer; setting: a value for a workflow control; "
                         "layers_files_or_groups: a number of layers, tables, files, groups or time points; other."))),
        layer=(layer, Field(description="feature_count: the layer the features belong to.")),
        # Plain strings that code checks against the registry: as enums, one per number and per sentence, a long
        # request passed OpenAI's 1000-enum-value limit for one schema (d6: m3:U12, 1020 values).
        workflow=(str, Field(description="setting: the workflow's name; unspecified when the words do not say.")),
        control=(str, Field(description="setting: the control's name from WORKFLOW CONTROLS, or unregistered.")),
        alternative=(bool, Field(description="The user gives this number as one of two or more possibilities "
                                             "(2 or 20) or does not know which applies.")),
    )
    sentence = create_model(
        "SentenceWire", __config__=_FORBID,
        doubt=(bool, Field(description="The sentence says the user does not know, is not sure or has not decided "
                                       "something, or gives two versions of it. A question to us is not a doubt.")),
        quote=(str, Field(description="doubt: the user's exact words of the doubt; empty otherwise.")),
        about=(_enum(DOUBT_ABOUT), Field(description="doubt: the field it is about (a wanted field, a data "
                                                     "condition, a count, a setting, what a named file holds, or "
                                                     "other); none otherwise.")),
        workflow=(str, Field(description="about setting: the workflow's name.")),
        control=(str, Field(description="about setting: the control's name; none otherwise.")),
        values=(list[str], Field(description="doubt: the values the words leave open, spelled as the field's values "
                                             "on the menu (numbers for counts).")),
    )
    setting = create_model(
        "SettingWire", __config__=_FORBID,
        quote=(str, Field(description="The user's exact words giving the setting.")),
        workflow=(workflow, Field(description="The workflow the setting is for; unspecified when the words do not "
                                              "say.")),
        control=(control, Field(description="The control from WORKFLOW CONTROLS, or unregistered when none takes "
                                            "it.")),
        value=(str, Field(description="The value as the control's allowed values spell it (true/false, a listed "
                                      "choice, a number); empty when the words give none.")),
        asks_to_set=(bool, Field(description="true when the user asks to run with it; false when the words only "
                                             "describe their data.")),
    )
    flag = create_model("Flag", __config__=_FORBID, value=(bool, ...), quote=(str, _QUOTE))
    names = _enum((*sorted(registered_workflows()), LIONESS_FAMILY))
    sentence_fields = create_model("SentencesWire", __config__=_FORBID, **{
        f"s{index}": (sentence, Field(description=f"Sentence {index}.")) for index in range(1, max(1, sentences) + 1)})
    number_fields = create_model("NumbersWire", __config__=_FORBID, **{
        f"n{index}": (number, Field(description=f"Number {index}.")) for index in range(1, numbers + 1)})
    fields: dict[str, tuple] = {
        "wanted": (list[wanted], Field(description=(
            "Each thing the request asks for or says, one item per quote. Words that only qualify an item (its "
            "scale, its layers, its regulators, its comparison) are fields of that item, not items of their own."))),
        "data": (data, Field(description="Each kind of data: whether the user says they have it or lack it.")),
        "groups": (list[str], Field(description="The user's exact words naming groups or conditions among the "
                                                "samples (AD and controls, responders and non-responders).")),
        "numbers": (number_fields, Field(description="Each number listed after the request, typed.")),
        "settings": (list[setting], Field(description="Every setting the user gives for a workflow without a "
                                                      "number (true/false, a listed choice, a list of samples).")),
        "conditions": (conditions, Field(description="DATA CONDITIONS, each as the user's words put it.")),
        "sentences": (sentence_fields, Field(description="Each sentence listed after the request: its doubt, if any.")),
        "unregistered_methods": (list[str], Field(description=(
            "The user's exact words naming a method or variant to use that no registered workflow is "
            "(TIGER, LIONESS-OTTER, DESeq2)."))),
        "background_methods": (list[names], Field(description=(
            "Registered names the user mentions only as background (a past run, where an input came from), never "
            "as the method to run or a choice."))),
        "claims": _said("Claims", _values(table, "claims"), "association: links between features; causal: proof of "
                                                             "causation; prediction: a trained predictive model."),
        "delivery": _said("Delivery", _values(table, "delivery"), "files: results written to the output folder; "
                                                                 "outside_netzoo: e-mailed, uploaded, published, a "
                                                                 "dashboard or a schedule."),
        "run_requested": (flag, Field(description="true when the user asks to run it now.")),
    }
    return _strict(create_model("MenuReadingWire", __config__=_FORBID, **fields))


# --- verbatim quotes ------------------------------------------------------------------------------------------------

_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                       "−": "-", " ": " "})
_ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…)\s*")
_EDGE = " \t\n\"'.,;:!?()[]"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "").translate(_FOLD)).casefold().strip()


def quote_in(quote: str, task: str) -> bool:
    """Whether the quote is the request's own words: case, typographic quotes and spacing aside, with "..." joining
    fragments that must appear in order. Edge punctuation is ignored; an empty quote is never verified."""
    text, at = _norm(task), 0
    fragments = [part.strip(_EDGE) for part in _ELLIPSIS.split(_norm(quote))]
    if not any(fragments):
        return False
    for fragment in fragments:
        if not fragment:
            continue
        found = text.find(fragment, at)
        if found < 0:
            return False
        at = found + len(fragment)
    return True


# --- wire -> MenuReading --------------------------------------------------------------------------------------------

@dataclass
class ReadReport:
    """What code dropped or filled while building the reading; each entry is `field: why`."""

    dropped: list[str] = field(default_factory=list)
    filled: list[str] = field(default_factory=list)


def _as_dict(payload) -> dict:
    return payload.model_dump(mode="json") if isinstance(payload, BaseModel) else dict(payload)


def _verified(quote, task: str, where: str, report: ReadReport) -> str:
    if quote_in(quote or "", task):
        return quote
    if str(quote or "").strip():
        report.dropped.append(f"{where}: quote not in the request: {quote!r}")
    return ""


def _said_from(raw: dict | None, task: str, where: str, report: ReadReport, all_values=()) -> Said:
    """One wire field as a `Said`. Without words from the request, nothing is stated."""
    if not raw or raw.get("status", "not_stated") == "not_stated":
        return Said()
    status = raw["status"]
    quote = _verified(raw.get("quote"), task, where, report)
    if not quote:
        report.dropped.append(f"{where}: {status} without verified words")
        return Said()
    if status == "stated":
        if raw.get("value") is None:
            report.dropped.append(f"{where}: stated without a value")
            return Said()
        return Said(status="stated", value=raw["value"], basis=raw.get("basis") or "explicit", quotes=[quote])
    return _doubt(status, raw.get("values") or [], quote, where, report, all_values)


def _doubt(status: str, values, quote: str, where: str, report: ReadReport, all_values=()) -> Said:
    allowed = set(all_values)
    kept = [v for v in dict.fromkeys(values) if v is not None and (not allowed or v in allowed)]
    if len(kept) < 2 and all_values:
        kept = list(dict.fromkeys([*kept, *(v for v in all_values if v != "off_menu")]))
        report.filled.append(f"{where}: {status} with fewer than two values -> every value on the menu")
    return Said(status=status, values=kept, quotes=[quote])


def _result(raw: dict, task: str, where: str, report: ReadReport, table: JudgmentDefaults,
            item_quote: str = "") -> tuple[Said, str]:
    """What the item names, as the artifact `Said` and its outside name. A result on the menu or a kind of result
    read with no words of its own rests on the item's words, which it was read from (d3)."""
    names = (raw or {}).get("names") or "nothing"
    if names in ("nothing", "workflow_only"):
        return Said(), ""  # a named workflow is counted by code from the words
    quote = _verified(raw.get("quote"), task, f"{where}.result", report)
    if not quote and names in ("menu_result", "kind_of_result") and quote_in(item_quote, task):
        quote = item_quote
        report.filled.append(f"{where}.result: {names} rests on the item's words")
    if not quote:
        report.dropped.append(f"{where}.result: {names} without verified words")
        return Said(), ""
    if names == "menu_result" and raw.get("value"):
        return Said(status="stated", value=raw["value"], basis="explicit", quotes=[quote]), ""
    if names == "kind_of_result" and raw.get("kind"):
        return Said(status="stated", value=raw["kind"], basis="explicit", quotes=[quote]), ""
    if names == "unsure_between_results":
        values = list(dict.fromkeys(raw.get("values") or []))
        if len(values) >= 2:
            return Said(status="unsure", values=values, quotes=[quote]), ""
        report.dropped.append(f"{where}.result: unsure between fewer than two results")
        return Said(), ""
    if names == "off_menu_result":
        outside = next((n for n in (raw.get("outside_name"), quote) if n and quote_in(n, task)), "")
        if outside and not workflows_in(outside) and not _IDENTIFIER.search(outside):
            return Said(status="stated", value="off_menu", basis="explicit", quotes=[quote]), outside
        # A registered workflow's name is on the menu, and a file name or identifier names no result: never a result
        # off it (d1: "Run LIONESS-PANDA"; d5: "analyze edges_release.tsv", "coexpression_file").
        report.dropped.append(f"{where}.result: off_menu_result without words naming a result off the menu")
        return Said(), ""
    report.dropped.append(f"{where}.result: {names} without its value")
    return Said(), ""


def _registered(workflow, control, where: str, report: ReadReport) -> tuple[str, str] | None:
    """A workflow and control the model wrote as plain strings, as the registry spells them; None when the control
    is no registered control and not `unregistered` (a slip of the pen never becomes a refusal reason)."""
    workflows = {name.casefold(): name for name in registered_workflows()}
    controls = {name.casefold(): name for limits in _controls().values() for name in limits}
    workflow = workflows.get(str(workflow or "").strip().casefold(), "")
    name = str(control or "").strip().casefold()
    if name == UNREGISTERED:
        return workflow, UNREGISTERED
    if name in controls:
        return workflow, controls[name]
    report.dropped.append(f"{where}: {control!r} is no control")
    return None


def _numbers(raw: dict, layout: Layout, report: ReadReport, doubtful: set[int] = frozenset()
             ) -> tuple[Count, Count, int | None, list[SettingAsked]]:
    """Counts and settings from the typed numbers. Two numbers of one count in a sentence that states a doubt are
    alternatives (d2: "two independent samples or five" typed as two plain counts); a control given two values is
    unsure between them, since a control takes one (d2: "it could be 0.3 or 3.0", both typed OTTER.lam)."""
    samples: dict[bool, list[NumberSpan]] = {False: [], True: []}
    layers: dict[str, dict[bool, list[NumberSpan]]] = {}
    settings: dict[tuple[str, str], list[NumberSpan]] = {}
    typed_all = [((raw or {}).get(f"n{index}") or {}, number) for index, number in enumerate(layout.numbers, 1)]
    for typed, number in typed_all:
        what, alternative = typed.get("what", "other"), bool(typed.get("alternative"))
        if what in ("sample_count", "feature_count") and not alternative and layout.sentence_of(number) in doubtful:
            same = [n for t, n in typed_all if t.get("what") == what and t.get("layer") == typed.get("layer")
                    and layout.sentence_of(n) == layout.sentence_of(number)]
            if len({n.value for n in same}) >= 2:
                alternative = True
                report.filled.append(f"numbers: {number.text} is one of several {what} values in a doubt")
        if what == "sample_count":
            samples[alternative].append(number)
        elif what == "feature_count":
            layers.setdefault(typed.get("layer") or UNSPECIFIED, {False: [], True: []})[alternative].append(number)
        elif what == "setting":
            found = _registered(typed.get("workflow"), typed.get("control") or UNREGISTERED, f"number {number.text}",
                                report)
            if found is not None:
                settings.setdefault(found, []).append(number)
    asked = []
    for (workflow, control), numbers in settings.items():
        values = list(dict.fromkeys(n.text for n in numbers))
        if control != UNREGISTERED and len(values) >= 2:
            report.filled.append(f"numbers: {workflow or 'any'}.{control} given {values} -> unsure between them")
            asked.append(SettingAsked(quote=numbers[0].context, workflow=workflow, control=control, unsure=True,
                                      values=values))
        else:
            asked += [SettingAsked(quote=n.context, workflow=workflow, control=control, value=n.text) for n in numbers]

    def options(found: dict[bool, list[NumberSpan]]) -> list[int]:
        doubtful = sorted({int(n.value) for n in found[True]})
        if len(doubtful) >= 2:
            return doubtful
        if doubtful:
            report.dropped.append(f"numbers: one alternative alone ({doubtful[0]}) read as stated")
        stated = [int(n.value) for n in (*found[False], *found[True])]
        return [max(stated)] if stated else []  # the largest stated number is the total

    def count(values: list[int], quotes: list[str]) -> Count:
        if not values:
            return Count()
        return Count(status="stated", value=values[0], quotes=quotes) if len(values) == 1 else \
            Count(status="conflicting", values=values, quotes=quotes)

    sample = count(options(samples), [n.context for n in (*samples[False], *samples[True])])
    per_layer = [values for found in layers.values() if (values := options(found))]
    feature, single = Count(), None
    if per_layer:
        totals = sorted({sum(choice) for choice in itertools.product(*per_layer)})
        feature = count(totals, [n.context for found in layers.values() for n in (*found[False], *found[True])])
        if len(per_layer) == 1 and len(per_layer[0]) == 1:
            single = per_layer[0][0]
    return sample, feature, single, asked


def _field_of(values) -> str | None:
    """The one field whose menu values include every value named (d4: 10 doubts typed about none)."""
    table, values = judgment_defaults(), {str(v) for v in values}
    if len(values) < 2:
        return None
    menus = {"artifact": (*table.dimensions["artifact"].values, "off_menu"),
             **{name: _values(table, name) for name in WANTED_FIELDS},
             **{name: _condition_values(table, name) for name in CONDITION_FIELDS}}
    fits = [name for name, menu in menus.items() if values <= set(menu)]
    return fits[0] if len(fits) == 1 else None


def _apply_doubts(raw: dict, task: str, layout: Layout, reading: dict, report: ReadReport,
                  table: JudgmentDefaults) -> None:
    """Each sentence's doubt, with verified words, sets its field to unsure with the values it leaves open."""
    for index in range(1, len(layout.sentences) + 1):
        typed = (raw or {}).get(f"s{index}") or {}
        about = typed.get("about") or "none"
        if typed.get("doubt") and about in ("none", "other") and str(typed.get("control") or "none").strip().casefold() \
                not in ("", "none"):
            about = "setting"  # the typed control says what the doubt is about (d3: U13, about none)
        elif typed.get("doubt") and about in ("none", "other") and (named := _field_of(typed.get("values") or [])):
            about = named
            report.filled.append(f"sentences.s{index}: doubt about {about}, the one field with values "
                                 f"{typed.get('values')}")
        if not typed.get("doubt") or about == "none":
            continue
        where = f"sentences.s{index}"
        quote = _verified(typed.get("quote"), task, where, report)
        if not quote:
            report.dropped.append(f"{where}: doubt about {about} without verified words")
            continue
        values = [str(v) for v in typed.get("values") or []]
        if about == "artifact":
            menu = (*table.dimensions["artifact"].values, "off_menu")
            said = _doubt("unsure", values, quote, where, report, ())
            said = said.model_copy(update={"values": [v for v in said.values if v in menu]})
            if len(said.values) < 2:
                report.dropped.append(f"{where}: doubt about the result with fewer than two results on the menu")
                continue
            items = [w for w in reading["wanted"] if w.form == "deliverable"]
            if not items:
                reading["wanted"].append(Wanted(quote=quote, artifact=said))
            for item in items:
                reading["wanted"][reading["wanted"].index(item)] = item.model_copy(update={"artifact": said})
        elif about in WANTED_FIELDS:
            said = _doubt("unsure", values, quote, where, report,
                          () if about in ("signed", "compare") else table.dimensions[about].values)
            for i, item in enumerate(reading["wanted"]):
                if item.form == "deliverable":
                    reading["wanted"][i] = item.model_copy(update={about: said})
        elif about in CONDITION_FIELDS:
            reading["conditions"][about] = _doubt("unsure", values, quote, where, report,
                                                  _condition_values(table, about))
        elif about in ("sample_count", "feature_count"):
            numbers = sorted({int(n.value) for value in values for n in request_layout(value).numbers})
            if len(numbers) >= 2 and reading[about].status != "conflicting":
                reading[about] = Count(status="conflicting", values=numbers, quotes=[quote])
            elif len(numbers) < 2:
                report.dropped.append(f"{where}: count doubt without two numbers")
        elif about == "setting":
            found = _registered(typed.get("workflow"), typed.get("control"), where, report)
            if found is not None and found[1] != UNREGISTERED and len(values) >= 2:
                workflow, control = found
                reading["settings"] = [s for s in reading["settings"] if s.control != control] + [SettingAsked(
                    quote=quote, workflow=workflow, control=control, unsure=True, values=values)]
            else:
                report.dropped.append(f"{where}: setting doubt without a control and two values")
        elif about == "file_content":
            reading["unsure_files"].append(quote)
        else:
            report.dropped.append(f"{where}: doubt about {about} -- no field takes it")


def to_menu_reading(payload, task: str, layout: Layout | None = None) -> tuple[MenuReading, ReadReport]:
    """The `MenuReading` the wire payload says, with every quote checked against the request."""
    raw, report, table = _as_dict(payload), ReadReport(), judgment_defaults()
    layout = layout or request_layout(task)
    wanted = []
    for index, item in enumerate(raw.get("wanted") or []):
        where = f"wanted[{index}]"
        fields = {name: _said_from(item.get(name), task, f"{where}.{name}", report,
                                   () if name in ("signed", "compare") else table.dimensions[name].values)
                  for name in WANTED_FIELDS}
        artifact, outside = _result(item.get("result") or {}, task, where, report, table, item.get("quote") or "")
        quote = item.get("quote") or ""
        if not quote_in(quote, task):
            report.dropped.append(f"{where}.quote: not in the request: {quote!r}")
            stated = [s for s in (artifact, *fields.values()) if s.status != "not_stated"]
            if not stated:
                report.dropped.append(f"{where}: item dropped, nothing in it is the request's words")
                continue
            quote = stated[0].quotes[0]
        requirements = []
        for number, entry in enumerate(item.get("requirements") or []):
            if entry.get("about") in _REQUIREMENT_KINDS and _verified(entry.get("quote"), task,
                                                                       f"{where}.requirements[{number}]", report):
                requirements.append(Requirement(quote=entry["quote"]))
        form = item.get("form") or "asks"
        if form == "asks":
            # An item that names no result, no workflow and states nothing is a question to us (which method, what
            # can we do); one that names any of them asks for that result (d2: "Can BONOBO output a cohort-level
            # aggregate network?").
            named = (item.get("result") or {}).get("names") not in (None, "nothing")
            stated = artifact.status != "not_stated" or any(s.status != "not_stated" for s in fields.values())
            form = "deliverable" if named or stated or requirements else "question_to_us"
        wanted.append(Wanted(quote=quote, form=form, artifact=artifact, outside_name=outside,
                             requirements=requirements, **fields))

    have, lack = [], []
    for name, entry in (raw.get("data") or {}).items():
        status = (entry or {}).get("status", "not_mentioned")
        if status != "not_mentioned" and _verified(entry.get("quote"), task, f"data.{name}", report):
            (have if status == "has" else lack).append(name)
    conditions = {}
    for name in CONDITION_FIELDS:
        said = _said_from((raw.get("conditions") or {}).get(name), task, f"conditions.{name}", report,
                          _condition_values(table, name))
        if said.status != "not_stated":
            conditions[name] = said
    doubtful = {index for index in range(1, len(layout.sentences) + 1)
                 if ((raw.get("sentences") or {}).get(f"s{index}") or {}).get("doubt")}
    sample, feature, single, settings = _numbers(raw.get("numbers") or {}, layout, report, doubtful)
    for index, entry in enumerate(raw.get("settings") or []):
        if not _verified(entry.get("quote"), task, f"settings[{index}]", report):
            continue
        workflow = "" if entry.get("workflow") == UNSPECIFIED else entry.get("workflow") or ""
        control = entry.get("control") or UNREGISTERED
        if control == UNREGISTERED and entry.get("asks_to_set") is False:
            report.dropped.append(f"settings[{index}]: describes the data, not a setting to use")
            continue  # d3: "The expression table has a header" refused BONOBO as a setting it lacks
        if any(s.control == control and s.workflow in (workflow, "") and control != UNREGISTERED for s in settings):
            continue  # already given by a typed number
        value = str(entry.get("value") or "")
        settings.append(SettingAsked(quote=entry["quote"], workflow=workflow, control=control,
                                     value="" if value == UNSPECIFIED else value))
    named = set(workflows_in(task))
    background = [name for name in raw.get("background_methods") or [] if name in named]
    registered = {_norm(name) for name in (*registered_workflows(), LIONESS_FAMILY)}
    unregistered = [name for index, name in enumerate(raw.get("unregistered_methods") or [])
                    if _verified(name, task, f"unregistered_methods[{index}]", report)
                    and _norm(name).strip(_EDGE) not in registered]
    for match in _LIONESS_VERSION.finditer(task):
        if match.group() not in registered_workflows() and match.group() not in unregistered:
            unregistered.append(match.group())  # method_names: a LIONESS version not registered names none
    run = raw.get("run_requested") or {}
    parts = {"wanted": wanted, "conditions": conditions, "settings": settings, "sample_count": sample,
             "feature_count": feature, "unsure_files": []}
    _apply_doubts(raw.get("sentences") or {}, task, layout, parts, report, table)
    reading = MenuReading(
        wanted=parts["wanted"], context_mentions=list(dict.fromkeys(background)),
        unregistered_methods=unregistered,
        claims=_said_from(raw.get("claims"), task, "claims", report),
        delivery=_said_from(raw.get("delivery"), task, "delivery", report),
        conditions=parts["conditions"], data=have, data_absent=lack,
        groups=[g for i, g in enumerate(raw.get("groups") or []) if _verified(g, task, f"groups[{i}]", report)],
        sample_count=parts["sample_count"], feature_count=parts["feature_count"], single_feature_count=single,
        settings=parts["settings"], unsure_files=list(dict.fromkeys(parts["unsure_files"])),
        run_requested=bool(run.get("value")) and bool(_verified(run.get("quote"), task, "run_requested", report)))
    return reading, report
