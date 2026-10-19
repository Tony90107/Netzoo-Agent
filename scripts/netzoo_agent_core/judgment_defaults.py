"""The closed-menu judgment's defaults table (spec 2026-10-18, sections 3.3 and 3.8): `scripts/judgment_defaults.yaml`.

It holds the closed vocabulary of results a request can ask for (each capability-sheet `produces` entry in exactly
one artifact), the coarse question groups asked first, and, for every dimension a request may leave unsaid, what code
does. The reader never fills a default; it reports what the user said, and the decision table applies this file.

Draft 2 (the user's decision, 2026-10-18): an intent dimension is never assumed. Not stated, it is asked when it
splits the candidates (policy `ask`); only data conditions keep defaults. Draft 3: the maps that let tests check the
dimensions are complete and none is idle (spec section 3.9) -- `method_ties`, `entry_attributes`, `ruled_by` and
`limit_fields`; every reference in them must name a dimension and one of its values. Draft 4: policy `extra` (an
extra the user asks for, plain when the topic is never mentioned), `tie_options` (what each tied method gives, with
its source) and `soft_requirements_met`.

Loading fails closed: an entry in no artifact or in two, an unknown sheet id, a generic word or comparison object
naming no artifact, an artifact in no question group or in two, an unknown class or policy, an intent dimension
with a default other than `compare`, or a condition default that is not one of that condition's values raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import yaml

from .capability_sheet import sheet_entries
from .contracts.capability_check import CONDITIONS

__all__ = ["CLASSES", "DEFAULTS_PATH", "POLICIES", "SLIM_CLASSES", "Artifact", "Dimension", "JudgmentDefaults",
           "InterpretationChoice", "QuestionGroup", "SlimField", "TieOption", "judgment_defaults", "load_defaults"]

DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "judgment_defaults.yaml"
POLICIES = frozenset({"ask", "extra", "default", "no_filter", "input_check", "needs_input"})
CLASSES = frozenset({"intent", "condition", "input_check", "setting"})
_INTENT_POLICIES = frozenset({"ask", "extra", "no_filter"})
_OPTION_PARTS = ("difference", "good_for", "logic", "source")
SLIM_CLASSES = frozenset({"A", "B", "C", "D"})
_READING_SLOTS = frozenset({"run", "groups", "unsure_files", "covariates"})
"""What a slim field may fill beside a dimension: reading slots the decision reads directly."""


@dataclass(frozen=True, slots=True)
class SlimField:
    """One field of the slim reading (spec 2026-10-19, section 3)."""

    name: str
    kind: str
    """A, B, C or D."""
    fills: tuple[str, ...]
    values: tuple[str, ...] = ()
    means: str = ""


CHOICE_TRIGGERS = frozenset({"groups_mentioned", "batch_with_comparison", "several_covariates", "three_or_more_layers"})
"""What code checks to make a must-confirm interpretation choice apply (spec change log 2026-10-19)."""


@dataclass(frozen=True, slots=True)
class InterpretationChoice:
    """A choice that keeps the workflow but changes what the result means (user decision 2026-10-19)."""

    name: str
    n: int
    policy: str
    """must_confirm or default_disclose."""
    workflows: tuple[str, ...]
    source: str
    field: str = ""
    """must_confirm: B1 or B3 (the live path's scale or layer question) or `confirm` (listed at run confirmation)."""
    trigger: str = ""
    question: str = ""
    options: Mapping[str, str] = MappingProxyType({})
    reason: str = ""
    disclose: str = ""
    unless_settings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Artifact:
    name: str
    means: str
    entries: tuple[str, ...]
    of: Mapping[str, str]
    """For `comparison`: each entry's compared result (an artifact name); empty otherwise."""


@dataclass(frozen=True, slots=True)
class QuestionGroup:
    name: str
    label: str
    artifacts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TieOption:
    """One method offered beside others that give the same kind of result (draft 5).

    `difference` and `good_for` are shown; `logic` and `source` are the contract reasoning behind them, never shown.
    """

    workflow: str
    difference: str
    good_for: str
    logic: str
    source: str
    fits_when: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Dimension:
    name: str
    kind: str
    """Its class: intent, condition, input_check or setting."""
    policy: str
    value: object = None
    """The assumed value (`default`), or the plain value (`extra`)."""
    implied_by_data: str = ""
    """For `ask`: the rule code applies to the stated data before asking."""
    condition: str | None = None
    values: tuple[str, ...] = ()
    off_menu: tuple[str, ...] = ()
    """Values the user may state that no registered workflow takes: a positive reason to rule candidates out."""
    options: Mapping[str, str] = MappingProxyType({})
    """For `ask`: the user-facing text of each answer."""
    serves: str = ""
    """What the dimension decides, for one no other map shows."""


@dataclass(frozen=True, slots=True)
class JudgmentDefaults:
    ask_max_options: int
    max_questions_per_turn: int
    max_ask_rounds: int
    artifacts: Mapping[str, Artifact]
    question_groups: Mapping[str, QuestionGroup]
    generic: Mapping[str, tuple[str, ...]]
    dimensions: Mapping[str, Dimension]
    by_entry: Mapping[str, str]
    """Sheet produces id -> its artifact."""
    method_ties: tuple[frozenset[str], ...] = ()
    entry_attributes: Mapping[str, str] = MappingProxyType({})
    ruled_by: Mapping[str, tuple[str, str]] = MappingProxyType({})
    """Near-miss or registry-wide id -> (dimension, value) that rules it out."""
    limit_fields: Mapping[str, str] = MappingProxyType({})
    tie_options: Mapping[str, tuple[str, tuple[TieOption, ...]]] = MappingProxyType({})
    """Tie group -> (the result asked, its options)."""
    soft_requirements_met: float = 1.0
    workflow_data: Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]] = MappingProxyType({})
    """Workflow -> (core data, needs); each item is a data_available value, "a|b", or two_layers."""
    omics_layers: frozenset[str] = frozenset()
    required_settings: Mapping[str, Mapping[str, str]] = MappingProxyType({})
    slim_fields: Mapping[str, SlimField] = MappingProxyType({})
    b4_conditions: Mapping[str, tuple[str, ...]] = MappingProxyType({})
    """Workflow -> the conditions (or `setting:control`) its contract turns on, read in step 3 (B4); only `setting:`
    ones (required declarations) are asked when not stated (user decision 2026-10-19 (a))."""
    workflow_logic: Mapping[str, tuple[str, str]] = MappingProxyType({})
    """Workflow -> (logic, source): the algorithm core, for code and reviewers only -- never shown, never read."""
    choices: Mapping[str, InterpretationChoice] = MappingProxyType({})

    def expand(self, artifact: str) -> tuple[str, ...]:
        """The artifacts a word stands for: a generic word's list, or the artifact itself."""
        return self.generic.get(artifact, (artifact,))


def _dimension(name: str, raw: dict) -> Dimension:
    rule = raw.get("not_stated") or {}
    policy, kind = rule.get("policy"), raw.get("class")
    if kind not in CLASSES:
        raise ValueError(f"judgment defaults: {name} has unknown class {kind!r}")
    if policy not in POLICIES:
        raise ValueError(f"judgment defaults: {name} has unknown policy {policy!r}")
    if kind == "intent" and policy not in _INTENT_POLICIES:
        raise ValueError(f"judgment defaults: intent {name} must not be assumed (user decision 2026-10-18)")
    value = rule.get("plain") if policy == "extra" else rule.get("value")
    if policy in ("default", "extra") and value is None:
        raise ValueError(f"judgment defaults: {name} ({policy}) needs a value")
    if policy == "extra" and value not in (raw.get("values") or ()):
        raise ValueError(f"judgment defaults: {name} plain value {value!r} is not one of its values")
    condition = raw.get("condition")
    if condition is not None:
        if condition not in CONDITIONS:
            raise ValueError(f"judgment defaults: {name} names unknown condition {condition!r}")
        allowed = CONDITIONS[condition][0]
        if policy == "default" and value not in allowed:
            raise ValueError(f"judgment defaults: {name} default {value!r} is not one of {allowed}")
    values = tuple(raw.get("values") or (CONDITIONS[condition][0] if condition else ()))
    return Dimension(name=name, kind=kind, policy=policy, value=value, implied_by_data=rule.get("implied_by_data", ""),
                     condition=condition, values=values, off_menu=tuple(raw.get("off_menu") or ()),
                     options=MappingProxyType(dict(raw.get("options") or {})), serves=raw.get("serves", ""))


def _reference(where: str, text: str, dimensions: Mapping[str, Dimension]) -> tuple[str, str]:
    name, _, value = str(text).partition("=")
    dimension = dimensions.get(name)
    if dimension is None or value not in (*dimension.values, *dimension.off_menu):
        raise ValueError(f"judgment defaults: {where} names {text!r}, not a dimension and one of its values")
    return name, value


def load_defaults(path: Path = DEFAULTS_PATH) -> JudgmentDefaults:
    """The table, validated against the capability sheet; raises ValueError on any inconsistency."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    produces = {key for key, item in sheet_entries().items() if item.kind == "produces"}
    artifacts, by_entry = {}, {}
    for name, raw in (data.get("artifacts") or {}).items():
        listed = raw.get("entries") or []
        of = dict(listed) if isinstance(listed, dict) else {}
        for key in listed:
            if key not in produces:
                raise ValueError(f"judgment defaults: artifact {name} lists unknown produces entry {key!r}")
            if key in by_entry:
                raise ValueError(f"judgment defaults: {key} is in both {by_entry[key]} and {name}")
            by_entry[key] = name
        artifacts[name] = Artifact(name=name, means=raw.get("means", ""), entries=tuple(listed),
                                   of=MappingProxyType(of))
    if missing := sorted(produces - set(by_entry)):
        raise ValueError(f"judgment defaults: produces entries in no artifact: {missing}")
    for artifact in artifacts.values():
        if bad := sorted(set(artifact.of.values()) - set(artifacts)):
            raise ValueError(f"judgment defaults: {artifact.name} compares unknown artifacts {bad}")
    generic = {}
    for word, names in (data.get("generic") or {}).items():
        if word in artifacts or (bad := sorted(set(names) - set(artifacts))):
            raise ValueError(f"judgment defaults: generic {word!r} is an artifact or names unknown ones")
        generic[word] = tuple(names)
    groups, grouped = {}, {}
    for name, raw in (data.get("question_groups") or {}).items():
        names = tuple(raw.get("artifacts") or ())
        for artifact in names:
            if artifact not in artifacts or artifact == "comparison" or artifact in grouped:
                raise ValueError(f"judgment defaults: question group {name} lists {artifact!r} (unknown, comparison "
                                 "or already grouped)")
            grouped[artifact] = name
        groups[name] = QuestionGroup(name=name, label=raw.get("label", ""), artifacts=names)
    if ungrouped := sorted(set(artifacts) - set(grouped) - {"comparison"}):
        raise ValueError(f"judgment defaults: artifacts in no question group: {ungrouped}")
    dimensions = {name: _dimension(name, raw) for name, raw in (data.get("dimensions") or {}).items()}
    if "artifact" not in dimensions or dimensions["artifact"].policy != "ask":
        raise ValueError("judgment defaults: the artifact dimension must exist and assume nothing")
    thresholds = data.get("thresholds") or {}
    for key, least in (("ask_max_options", 2), ("max_questions_per_turn", 1), ("max_ask_rounds", 1)):
        if not isinstance(thresholds.get(key), int) or thresholds[key] < least:
            raise ValueError(f"judgment defaults: thresholds.{key} must be an integer >= {least}")
    ruled_by = {key: _reference(f"ruled_by {key}", text, dimensions) for key, text in (data.get("ruled_by") or {}).items()}
    for kind, names in (("entry_attributes", (data.get("entry_attributes") or {}).values()),
                        ("limit_fields", (data.get("limit_fields") or {}).values())):
        if unknown := sorted(set(names) - set(dimensions)):
            raise ValueError(f"judgment defaults: {kind} names unknown dimensions {unknown}")
    ties = {}
    known_workflows = {item.workflow for item in sheet_entries().values() if item.workflow}
    for group, raw in (data.get("tie_options") or {}).items():
        options = []
        for workflow, parts in (raw.get("options") or {}).items():
            if workflow not in known_workflows or any(not str(parts.get(part, "")).strip() for part in _OPTION_PARTS):
                raise ValueError(f"judgment defaults: tie option {group}/{workflow} is unknown or misses a part")
            fits = tuple(_reference(f"tie option {group}/{workflow}", text, dimensions)
                         for text in parts.get("fits_when") or ())
            options.append(TieOption(workflow=workflow, fits_when=fits, **{part: parts[part] for part in _OPTION_PARTS}))
        if len(options) < 2:
            raise ValueError(f"judgment defaults: tie group {group} needs at least two options")
        ties[group] = (raw.get("asked", ""), tuple(options))
    data_values = {*dimensions["data_available"].values, "two_layers"} if "data_available" in dimensions else set()
    workflow_data = {}
    for workflow, raw in (data.get("workflow_data") or {}).items():
        core, needs = tuple(raw.get("core") or ()), tuple(raw.get("needs") or ())
        if workflow not in known_workflows or not core or any(
                set(item.split("|")) - data_values for item in (*core, *needs)):
            raise ValueError(f"judgment defaults: workflow_data {workflow} is unknown or names unknown data")
        workflow_data[workflow] = (core, needs)
    if missing := sorted(known_workflows - set(workflow_data)):
        raise ValueError(f"judgment defaults: workflows without workflow_data: {missing}")
    required = {workflow: MappingProxyType(dict(values))
                for workflow, values in (data.get("required_settings") or {}).items()}
    if unknown := sorted(set(required) - known_workflows):
        raise ValueError(f"judgment defaults: required_settings names unknown workflows {unknown}")
    layers = frozenset(data.get("omics_layers") or ())
    if layers - data_values:
        raise ValueError("judgment defaults: omics_layers names unknown data")
    slim = {}
    for name, raw in (data.get("slim_fields") or {}).items():
        kind, fills = raw.get("class"), tuple(raw.get("fills") or ())
        if kind not in SLIM_CLASSES or not fills or any(
                item not in dimensions and item not in _READING_SLOTS for item in fills):
            raise ValueError(f"judgment defaults: slim field {name} has an unknown class or fills unknown slots")
        slim[name] = SlimField(name=name, kind=kind, fills=fills, values=tuple(raw.get("values") or ()),
                               means=raw.get("means", ""))
    b4 = {}
    for workflow, names in (data.get("b4_conditions") or {}).items():
        if workflow not in known_workflows:
            raise ValueError(f"judgment defaults: b4_conditions names unknown workflow {workflow}")
        for name in names:
            control = name.split(":", 1)[1] if name.startswith("setting:") else None
            if control is None and (name not in dimensions or dimensions[name].kind not in ("condition",
                                                                                              "input_check")):
                raise ValueError(f"judgment defaults: b4 condition {name} of {workflow} is no condition")
        b4[workflow] = tuple(names)
    logic = {}
    for workflow, raw in (data.get("workflow_logic") or {}).items():
        if workflow not in known_workflows or not raw.get("logic") or not raw.get("source"):
            raise ValueError(f"judgment defaults: workflow_logic {workflow} is unknown or lacks logic or source")
        logic[workflow] = (raw["logic"], raw["source"])
    from .workflow_conditions import all_conditions
    controls = {workflow: set(limits.settings) for workflow, limits in all_conditions().items()}
    choices = {}
    for name, raw in (data.get("interpretation_choices") or {}).items():
        workflows = tuple(raw.get("workflows") or ())
        policy = raw.get("policy")
        if policy not in ("must_confirm", "default_disclose") or not workflows or set(workflows) - known_workflows:
            raise ValueError(f"judgment defaults: interpretation choice {name} has an unknown policy or workflow")
        if not raw.get("source"):
            raise ValueError(f"judgment defaults: interpretation choice {name} has no source")
        if policy == "must_confirm" and (raw.get("trigger") not in CHOICE_TRIGGERS
                                         or raw.get("field") not in ("B1", "B3", "confirm") or not raw.get("question")):
            raise ValueError(f"judgment defaults: must-confirm choice {name} needs a known trigger, field and question")
        if policy == "must_confirm" and raw.get("field") == "confirm" and len(raw.get("options") or {}) < 2:
            raise ValueError(f"judgment defaults: choice {name} needs two options")
        if policy == "default_disclose" and not raw.get("disclose"):
            raise ValueError(f"judgment defaults: default choice {name} needs a disclosure line")
        unless = tuple(raw.get("unless_settings") or ())
        if any(not any(control in controls.get(w, ()) for w in workflows) for control in unless):
            raise ValueError(f"judgment defaults: choice {name} names a control none of its workflows has")
        choices[name] = InterpretationChoice(
            name=name, n=int(raw.get("n", 0)), policy=policy, workflows=workflows, source=raw["source"],
            field=raw.get("field", ""), trigger=raw.get("trigger", ""), question=raw.get("question", ""),
            options=MappingProxyType(dict(raw.get("options") or {})), reason=raw.get("reason", ""),
            disclose=raw.get("disclose", ""), unless_settings=unless)
    share = thresholds.get("soft_requirements_met")
    if not isinstance(share, (int, float)) or not 0 < share <= 1:
        raise ValueError("judgment defaults: thresholds.soft_requirements_met must be in (0, 1]")
    return JudgmentDefaults(ask_max_options=thresholds["ask_max_options"],
                            max_questions_per_turn=thresholds["max_questions_per_turn"],
                            max_ask_rounds=thresholds["max_ask_rounds"], artifacts=MappingProxyType(artifacts),
                            question_groups=MappingProxyType(groups), generic=MappingProxyType(generic),
                            dimensions=MappingProxyType(dimensions), by_entry=MappingProxyType(by_entry),
                            method_ties=tuple(frozenset(pair) for pair in data.get("method_ties") or ()),
                            entry_attributes=MappingProxyType(dict(data.get("entry_attributes") or {})),
                            ruled_by=MappingProxyType(ruled_by),
                            limit_fields=MappingProxyType(dict(data.get("limit_fields") or {})),
                            tie_options=MappingProxyType(ties), soft_requirements_met=float(share),
                            workflow_data=MappingProxyType(workflow_data), omics_layers=layers,
                            required_settings=MappingProxyType(required), slim_fields=MappingProxyType(slim),
                            b4_conditions=MappingProxyType(b4), workflow_logic=MappingProxyType(logic),
                            choices=MappingProxyType(choices))


@lru_cache(maxsize=1)
def judgment_defaults() -> JudgmentDefaults:
    return load_defaults()
