"""What each registered workflow can be run with: its method, its settings and its data limits (M1, 2026-10-14).

Final acceptance a24b (`docs/research-log/final-acceptance-2026-10-14/RESULTS.md`): 7 of 11 false yeses asked for a
result the right workflow produces, but with a method, a setting or an amount of data it cannot take -- OTTER with an
L1 penalty, GIRAFFE with a lambda, the TIGER model, LIONESS-OTTER, two samples for per-sample networks, a
LIONESS-DRAGON table above its cap. The capability sheet compares results only. This module is the one record of
those limits that the capability check reads. It holds no value of its own: each is read, when asked, from the
registry or from the constant the preflight or the executor enforces (`tests/test_workflow_conditions.py` changes
each source and sees it followed).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS, resolve_conditional_output

from .data import bonobo, cobra, dragon, giraffe, inspection, lioness_dragon, otter, sambar
from .method_names import LIONESS_FAMILY, UNREGISTERED, method_names, named_workflows, setting_names
from .runtime_constraints import runtime_control_constraints

__all__ = [
    "LIONESS_FAMILY", "UNREGISTERED", "SettingLimit", "StatedSetting", "WorkflowConditions", "all_conditions",
    "boolean_value", "combination_issues", "contract_forbids", "control_boolean_value", "conditions_for", "data_issue",
    "enum_value", "method_names",
    "named_workflows", "setting_issue", "setting_unresolved",
    "setting_names", "stated_numbers", "unpassed_setting",
]

# The executor's or preflight's own constants, read when asked so a change to one is followed here.
_MIN_SAMPLES: Mapping[str, Callable[[], int]] = MappingProxyType({
    "run_lioness_panda": lambda: inspection.LIONESS_MIN_SAMPLES,
    "run_lioness_puma": lambda: inspection.LIONESS_MIN_SAMPLES,
    "run_lioness_coexpression": lambda: inspection.LIONESS_MIN_SAMPLES,
    "run_lioness_dragon": lambda: max(lioness_dragon.LIONESS_DRAGON_MIN_SAMPLES, dragon.DRAGON_MIN_SAMPLES),
    "run_dragon": lambda: dragon.DRAGON_MIN_SAMPLES,
    "run_bonobo": lambda: bonobo.BONOBO_MIN_SAMPLES,
    "run_cobra": lambda: cobra.COBRA_MIN_SAMPLES,
    "run_giraffe": lambda: giraffe.GIRAFFE_MIN_SAMPLES,
    "run_otter": lambda: otter.OTTER_MIN_EXPRESSION_SAMPLES,
})
# Core decision phase 4a: a relation between two stated counts, read from the function the input check itself calls.
_RELATIONS: Mapping[str, Callable[[], tuple[str, Callable[[int, int], str | None]]]] = MappingProxyType({
    "run_cobra": lambda: ("features>samples", cobra.gene_sample_error),
})
_MAX_VALUES: Mapping[str, Callable[[], tuple[int, Callable[[int, int], int], str]]] = MappingProxyType({
    "run_lioness_dragon": lambda: (lioness_dragon.LIONESS_DRAGON_MAX_VALUES, lioness_dragon.lioness_dragon_size,
                                   "features x (features - 1) / 2 x samples"),
})


@dataclass(frozen=True, slots=True)
class SettingLimit:
    """One registry control as a request may set it."""

    name: str
    control_type: str
    allowed_values: tuple = ()
    default: object = None
    minimum: float | None = None
    maximum: float | None = None
    wired: bool = True
    """Passed to the executor (`ActionDefinition.executor_fields`)."""
    unavailable_values: frozenset[str] = frozenset()
    """Values the current runtime cannot honour (`runtime_constraints`)."""
    unavailable_message: str = ""
    value_names: tuple = ()
    """Other names for allowed values, from the contract ("HDF5" -> ".h5")."""


@dataclass(frozen=True, slots=True)
class WorkflowConditions:
    action: str
    workflow: str
    settings: Mapping[str, SettingLimit]
    min_samples: int | None = None
    max_values: int | None = None
    size: Callable[[int, int], int] | None = None
    """(samples, features) -> values the output holds; only where `max_values` caps it."""
    size_formula: str = ""
    omics_layers: int = 0
    """Paired omics tables the workflow joins; they must hold exactly the same sample IDs."""
    relation_name: str = ""
    relation: Callable[[int, int], str | None] | None = None
    """Phase 4a: (features, samples) -> why one data type of this size cannot run (COBRA: more genes than samples)."""


def _settings(action: str) -> Mapping[str, SettingLimit]:
    definition = ACTION_DEFINITIONS[action]
    runtime = runtime_control_constraints(action)
    limits = {}
    for control in definition.controls:
        blocked = runtime.get(control.name)
        limits[control.name] = SettingLimit(
            name=control.name, control_type=control.control_type, allowed_values=tuple(control.allowed_values),
            default=control.default,
            minimum=control.minimum, maximum=control.maximum,
            wired=control.executor_argument in definition.executor_fields,
            unavailable_values=blocked.unavailable_values if blocked else frozenset(),
            unavailable_message=blocked.message if blocked else "",
            value_names=tuple(control.value_names))
    return MappingProxyType(limits)


def all_conditions() -> dict[str, WorkflowConditions]:
    """Every registered run workflow's conditions, by workflow name."""
    found = {}
    for action in sorted(RUN_ACTIONS):
        definition = ACTION_DEFINITIONS[action]
        cap = _MAX_VALUES[action]() if action in _MAX_VALUES else None
        relation = _RELATIONS[action]() if action in _RELATIONS else None
        found[definition.workflow] = WorkflowConditions(
            action=action, workflow=definition.workflow, settings=_settings(action),
            min_samples=_MIN_SAMPLES[action]() if action in _MIN_SAMPLES else None,
            max_values=cap[0] if cap else None, size=cap[1] if cap else None, size_formula=cap[2] if cap else "",
            omics_layers=sum(1 for name in definition.required_inputs if name.startswith("omics_layer_")),
            relation_name=relation[0] if relation else "", relation=relation[1] if relation else None)
    return found


def conditions_for(name: str) -> WorkflowConditions | None:
    """One workflow's conditions, by workflow name (DRAGON) or action (run_dragon)."""
    found = all_conditions()
    return found.get(name) or next((item for item in found.values() if item.action == name), None)


@dataclass(frozen=True, slots=True)
class StatedSetting:
    """A setting the request gives: WORKFLOW.control or `unregistered`, the words naming it, and its value's words."""

    name: str
    quote: str
    value: str = ""


_NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s?[kK]\b)?")
_WORDS = {word: index for index, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
_WORDS.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
               "hundred": 100, "single": 1})


def stated_numbers(text: str) -> list[float]:
    """The numbers the words state, in order: digits ("20,000", "0.1", "20k") and number words up to twenty."""
    found = []
    for match in _NUMBER.finditer(text or ""):
        raw = match.group().replace(",", "").replace(" ", "")
        if not any(ch.isdigit() for ch in raw):
            continue
        scale = 1000 if raw[-1:] in "kK" else 1
        try:
            found.append(float(raw.rstrip("kK")) * scale)
        except ValueError:
            continue
    words = re.findall(r"[a-z]+", (text or "").casefold())
    found += [float(_WORDS[word]) for word in words if word in _WORDS]
    return found


def _fold(text: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", (text or "").casefold()).strip("_")


def _names(values) -> str:
    values = list(values)
    return values[0] if len(values) == 1 else ", ".join(values[:-1]) + " and " + values[-1]


def enum_value(limit: SettingLimit, words: str):
    """The single allowed choice named by the value, shared by validation and run binding.

    A value is named by its own spelling or by the contract's other name for it (p3-p4c C52: "saved as HDF5" named
    neither ".h5" nor ".hdf", so BONOBO was declined for its own default format); words naming two stay unresolved.
    """
    folded = _fold(words)
    names = [*((item, item) for item in limit.allowed_values), *limit.value_names]
    chosen = list(dict.fromkeys(value for name, value in names
                                if (key := _fold(str(name))) and f"_{key}_" in f"_{folded}_"))
    return chosen[0] if len(chosen) == 1 else None


_NEGATIONS = frozenset({"no", "not", "without", "dont", "never", "off", "false", "disable", "disabled", "skip", "0"})
_AFFIRMATIONS = frozenset({"yes", "true", "on", "enable", "enabled", "1"})


def _tokens(words: str) -> set[str]:
    # Keep decimal/scientific numbers whole: confidence 0.05 is neither the boolean 0 nor 1.
    words = re.sub(r"don['\u2019]t", "dont", (words or "").casefold())
    return set(re.findall(r"(?<![a-z0-9.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:e[-+]?\d+)?(?![a-z0-9.])"
                          r"|[a-z][a-z0-9]*", words))


def boolean_value(words: str, quote: str = "") -> bool | None:
    """A boolean setting's value: its value words, or, given none, the words naming it (a bare "sparsify" enables it,
    "without sparsification" does not). Words both negating and affirming it, or neither, stay unresolved.

    Review of the M3 fix: value words are the user's own ("without", "don't", "turned off"); reading only
    true/false/off/"do not X" left each of them unresolved, which refuses the workflow for a plain no.
    """
    if not words.strip():
        return not (_tokens(quote) & _NEGATIONS) if quote.strip() else None
    if _fold(words) in ("y", "n"):
        return _fold(words) == "y"
    tokens = _tokens(words)
    negated, affirmed = bool(tokens & _NEGATIONS), bool(tokens & _AFFIRMATIONS)
    if negated and affirmed:
        return None  # "yes, turn it off"
    if negated:
        return False  # "with no sparsification" is a no
    return True if affirmed or "with" in tokens else None


def control_boolean_value(limit: SettingLimit, words: str, quote: str = "") -> bool | None:
    """A boolean control's value, also when the words state the control itself as done.

    `boolean_value` reads yes/no words; when they settle nothing, value words that name the control -- a word of its
    own name ("log2-transformed" for log_transformed, "centered per gene" for centered, "each patient's mutation
    burden" for norm_patient) -- with no negation say it holds. Derived from the control's name, never a phrase list.
    """
    value = boolean_value(words, quote)
    if value is not None or not (words or "").strip():
        return value
    own = {token for token in _tokens(limit.name.replace("_", " ")) if len(token) > 3 and not token.isdigit()}
    tokens = _tokens(words)
    return True if own & tokens and not tokens & _NEGATIONS else None


def setting_issue(conditions: WorkflowConditions, setting: StatedSetting) -> str | None:
    """Why the workflow cannot run with this setting, or None when it can or the words do not say.

    A setting it has no control for, or does not pass to its executor, cannot be applied; a number outside the
    control's range, or a value the runtime cannot honour, cannot be used. A value the words do not state is never
    judged.
    """
    control = setting.name.split(".", 1)[-1] if setting.name != UNREGISTERED else None
    limit = conditions.settings.get(control) if control else None
    if limit is None or not limit.wired:
        wired = [name for name, item in conditions.settings.items() if item.wired]
        if not wired:
            return (f'NetZoo runs {conditions.workflow} with its package defaults and passes no settings to it, so '
                    f'"{setting.quote}" cannot be applied')
        return (f'NetZoo\'s {conditions.workflow} has no setting for "{setting.quote}"; the settings it passes are '
                f"{_names(wired)}")
    value = setting.value or ""
    if limit.control_type in ("number", "integer"):
        numbers = list(dict.fromkeys(stated_numbers(value)))
        if len(numbers) != 1:
            return None
        number = numbers[0]
        low = limit.minimum if limit.minimum is not None else float("-inf")
        high = limit.maximum if limit.maximum is not None else float("inf")
        if not low <= number <= high or (limit.control_type == "integer" and number != int(number)):
            bounds = (f"between {limit.minimum:g} and {limit.maximum:g}" if limit.minimum is not None
                      and limit.maximum is not None else f"at least {limit.minimum:g}" if limit.minimum is not None
                      else f"at most {limit.maximum:g}")
            if limit.control_type == "integer":
                bounds = "a whole number " + (f"of {bounds}" if bounds.startswith("at") else bounds)
            return f'{conditions.workflow}\'s {limit.name} must be {bounds}; "{value}" is not'
        return None
    if limit.control_type == "enum":
        chosen = enum_value(limit, value)
        if value.strip() and chosen is None and setting_unresolved(conditions, setting) is None:
            return (f'{conditions.workflow}\'s {limit.name} requires one of {_names(map(str, limit.allowed_values))}; '
                    f'"{value}" {UNCLEAR_CHOICE}')
        if chosen is not None and str(chosen).casefold() in limit.unavailable_values:
            return limit.unavailable_message.rstrip(".")
    return None


UNCLEAR_CHOICE = "does not identify one allowed choice"
"""How `setting_issue` ends when the words name no allowed choice: unsettled words, never a run the method cannot do
(ROUND-17: they hold no other row of the run)."""

_UNPASSED = (
    re.compile(r'^NetZoo runs (?P<workflow>\S+) with its package defaults and passes no settings to it, so '
               r'"(?P<words>.*)" cannot be applied$', re.S),
    re.compile(r'^NetZoo\'s (?P<workflow>\S+) has no setting for "(?P<words>.*)"; the settings it passes are ', re.S),
)


def unpassed_setting(reason: str) -> tuple[str, str] | None:
    """(workflow, the user's words) when the reason is `setting_issue`'s "no setting for" or "passes no settings"."""
    found = next((match for pattern in _UNPASSED if (match := pattern.match(reason))), None)
    return (found["workflow"], found["words"]) if found else None


def contract_forbids(conditions: WorkflowConditions, setting: StatedSetting) -> bool:
    """Whether the workflow's own numeric control is given a number its contract's range forbids -- the method cannot
    run so (OTTER's lam is in [0, 1]; "lam set to 1.5"). A value the contract allows but this runtime cannot honour
    (OTTER's computing=gpu), words naming no allowed choice (C40's genes_axis, asked or read again, never forbidden),
    and a setting it has no control for are not forbidden by its contract."""
    if setting.name == UNREGISTERED:
        return False
    limit = conditions.settings.get(setting.name.split(".", 1)[-1])
    return (limit is not None and limit.wired and limit.control_type in ("number", "integer")
            and setting_issue(conditions, setting) is not None)


def setting_unresolved(conditions: WorkflowConditions, setting: StatedSetting) -> str | None:
    """Words naming a supported control whose value they do not settle -- asked, never a violation or the default.

    A boolean whose words read as neither true nor false (h2 J17 "keep the normalization"); a number given as more than
    one value ("0.2 or 0.5"); an enum value naming more than one allowed choice. One concrete disallowed enum value is
    still a violation (`setting_issue`), and a number stated without digits is no value (`stated_no_value`).
    """
    control = setting.name.split(".", 1)[-1] if setting.name != UNREGISTERED else None
    limit = conditions.settings.get(control) if control else None
    value = (setting.value or "").strip()
    if limit is None or not limit.wired or not value:
        return None
    if limit.control_type == "boolean" and control_boolean_value(limit, value, setting.quote) is None:
        return f'{conditions.workflow}\'s {limit.name} value "{value}" is unresolved; clarify whether to enable it'
    if limit.control_type in ("number", "integer") and len(set(stated_numbers(value))) > 1:
        return f'{conditions.workflow}\'s {limit.name} value "{value}" does not settle one number'
    if limit.control_type == "enum":
        folded = f"_{_fold(value)}_"
        candidates = {choice for name, choice in [*((v, v) for v in limit.allowed_values), *limit.value_names]
                      if (key := _fold(str(name))) and f"_{key}_" in folded}
        if len(candidates) > 1:
            return f'{conditions.workflow}\'s {limit.name} value "{value}" does not settle one allowed choice'
    return None


def data_issue(conditions: WorkflowConditions, samples: int | None, features: int | None,
               single_features: int | None = None) -> str | None:
    """Why the workflow cannot take data of this size, or None when it can or the request does not say.

    A count the request does not state is never assumed. A partial feature count is a lower bound, and the size
    only grows with it, so a cap it already exceeds is exceeded. A relation between counts (phase 4a) is judged only
    on `single_features` -- the request states exactly one feature count -- so it is never a sum over data types.
    """
    if samples is not None and conditions.min_samples is not None and samples < conditions.min_samples:
        return f"{conditions.workflow} needs at least {conditions.min_samples} samples; the request has {samples}"
    if (samples is not None and single_features is not None and conditions.relation is not None
            and (problem := conditions.relation(single_features, samples)) is not None):
        return f"{problem}; the request has {single_features:,} genes and {samples:,} samples"
    if samples and features and conditions.max_values is not None and conditions.size is not None:
        size = conditions.size(samples, features)
        if size > conditions.max_values:
            return (f"{conditions.workflow} writes at most {conditions.max_values:,} values "
                    f"({conditions.size_formula}); {features:,} features and {samples:,} samples give {size:,}")
    return None


def combination_issues(conditions: WorkflowConditions, settings: list[StatedSetting],
                       samples: int | None = None) -> list[str]:
    """Why the settings cannot be used together, from the rules the executors apply (M2; was M1's open item).

    DRAGON and LIONESS-DRAGON take both lambdas or neither; SAMBAR needs kmin <= kmax and, clustering, at least
    kmax samples; BONOBO with sparsify needs delta above 0 and below 1/3; and no combination the registry marks
    invalid among its conditional outputs (BONOBO's save_pvals without sparsify). A value the words do not state is
    never judged; a setting the words name without a value is taken as stated (sparsify). A lambda named without a
    number is DRAGON's estimate, its contract's empty value, not a manual one (ROUND-12 C17: "the transcript layer's
    shrinkage is fixed at 0.3, while the metabolite layer's shrinkage is estimated from the data" sets one alone).
    """
    stated = {item.name.split(".", 1)[1]: item for item in settings
              if item.name != UNREGISTERED and item.name.split(".", 1)[1] in conditions.settings}

    def number(name: str) -> float | None:
        values = list(dict.fromkeys(stated_numbers(stated[name].value))) if name in stated else []
        return values[0] if len(values) == 1 else None

    def enabled(name: str) -> bool | None:
        if name not in stated:
            return conditions.settings[name].default
        # A bare request to sparsify/cluster enables it; an explicit false must not.
        return control_boolean_value(conditions.settings[name], stated[name].value, stated[name].quote)

    found = []
    if {"lambda1", "lambda2"} <= set(conditions.settings) and stated.keys() & {"lambda1", "lambda2"}:
        manual = {name: stated[name] for name in ("lambda1", "lambda2")
                  if name in stated and stated_numbers(stated[name].value)}
        if error := dragon.lambda_pair_error(manual.get("lambda1"), manual.get("lambda2")):
            found.append(f"{conditions.workflow}: {error.rstrip('.')}")
    if conditions.action == "run_sambar":
        kmin, kmax = number("kmin"), number("kmax")
        if kmin is not None or kmax is not None:
            chosen = {"kmin": int(kmin) if kmin is not None else conditions.settings["kmin"].default,
                      "kmax": int(kmax) if kmax is not None else conditions.settings["kmax"].default}
            found += [f"SAMBAR: {error}" for error in sambar._parameter_errors(chosen) if "greater than or equal" in error]
        if (enabled("cluster") is True and kmax is not None and samples is not None
                and (error := sambar.kmax_sample_error(int(kmax), samples))):
            found.append(f"SAMBAR: {error}")
    if conditions.action == "run_bonobo" and enabled("sparsify") is True and (delta := number("delta")) is not None:
        if error := bonobo.bonobo_delta(delta, True)[1]:
            found.append(f"BONOBO: {error.split(':')[0]}")
    if error := _invalid_output(conditions, stated):
        found.append(f"{conditions.workflow}: {error}")
    return found


def _invalid_output(conditions: WorkflowConditions, stated: dict[str, StatedSetting]) -> str | None:
    """The registry's reason when the stated values pick a conditional output it marks invalid -- the rule the
    executor applies before it runs (`execution_bonobo`: `resolve_conditional_output`, BONOBO_PVALUES_REQUIRE_SPARSIFY).

    Round m3 K05 ("keep save_pvals=true but set sparsify=false"): the request-level settings were read and each was
    legal alone, so the methods question was answered as if BONOBO could run so. Judged only when the request states one
    of the controls the rules govern and the words settle each one it states; the others keep their defaults.
    """
    definition = ACTION_DEFINITIONS.get(conditions.action)
    capability = getattr(definition, "output_capability", None)
    rules = tuple(getattr(capability, "conditional_outputs", ()) or ())
    governed = [name for name in dict.fromkeys(name for rule in rules for name in rule.when)
                if name in conditions.settings]
    if not governed or not stated.keys() & set(governed):
        return None
    values = {}
    for name in governed:
        limit, said = conditions.settings[name], stated.get(name)
        if said is None:
            values[name] = limit.default
            continue
        if limit.control_type == "boolean":
            value = control_boolean_value(limit, said.value, said.quote)
        elif limit.control_type == "enum":
            value = enum_value(limit, said.value)
        elif limit.control_type in ("number", "integer"):
            numbers = list(dict.fromkeys(stated_numbers(said.value)))
            value = numbers[0] if len(numbers) == 1 else None
        else:
            value = None
        if value is None:
            return None  # words that do not settle a value are never judged
        values[name] = value
    rule = resolve_conditional_output(conditions.action, values, registry=ACTION_DEFINITIONS)
    if rule is None or getattr(rule, "valid", True):
        return None
    return re.sub(r"^invalid:\s*", "", rule.semantics).rstrip(".")

