"""The closed-menu decision table and ask loop (spec docs/superpowers/specs/2026-10-18-closed-menu-judgment-design.md,
sections 3.2-3.4, 3.8-3.10).

`decide_menu` reads a `MenuReading` -- what the user said, never whether it can be done -- with the defaults table
(`judgment_defaults`) and the capability sheet, and makes one `MenuDecision`. It makes no model call. For each thing
the user wants delivered:

1. the candidates are the sheet results whose artifact the words allow (all of them when the result is open);
2. stated values narrow them (granularity, regulators, signs, joint layers, a comparison), and named workflows
   restrict them; nothing not stated narrows anything, except a dimension's plain value (`extra`);
3. contract conditions rule candidates out with a reason -- a condition value off the menu, data the user says they
   lack, a count or setting the workflow cannot take, a requirement its contract contradicts, an unregistered method;
4. what is still open and decides something is asked: an intent that splits the remaining candidates (coarse question
   groups first), or a value the user is unsure of between alternatives that lead to different outcomes -- asked with
   the user's own alternatives; requirements the contract does not address are asked while fewer than
   `soft_requirements_met` of the user's requirements are met;
5. otherwise the workflows left are the answer; several of the same kind are a tie offered with `tie_options`.

Then: a question about a result the user never named -> CLARIFY; any other question -> ASK; nothing left anywhere ->
DECLINE; some parts left -> DO, partial when others were ruled out. A ruled-out part always has a positive reason:
an empty match is never a refusal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from ..capability_sheet import sheet_entries
from ..contracts.capability_check import CONDITIONS
from ..contracts.menu_reading import (
    Count, Declined, Infeasible, MenuDecision, MenuReading, Option, Question, Said, SettingAsked, TieChoice, Wanted,
)
from ..judgment_defaults import JudgmentDefaults, judgment_defaults
from ..method_names import LIONESS_FAMILY, registered_workflows, workflows_in
from ..workflow_conditions import (
    UNREGISTERED, StatedSetting, all_conditions, combination_issues, data_issue, setting_issue,
)

__all__ = ["B_INTENTS", "PROBED_INTENTS", "GateVerdict", "apply_answers", "b_fields", "candidate_workflows", "decide_menu",
           "confirm_items", "deciding_intents", "disclosures_for", "intent_values", "workflow_conditions",
           "workflow_gate"]

PROBED_INTENTS = ("artifact", "integration", "granularity", "regulators", "layers")
"""The intents the phase-1b intent probe may ask about (the user's decision, 2026-10-18); never any other field."""
B_INTENTS = ("granularity", "regulators", "integration", "layers")
"""B1-B3 of the slim reading (spec 2026-10-19): the intents of a thing asked that only the focused read (step 3) reads."""

_REGULATION = frozenset({"regulatory_network", "targeting_scores", "tf_activity"})
_JOINT = frozenset({"multi_omic_network", "edge_significance"})
_SCALES = ("whole_cohort", "per_group", "per_sample")
_RESULT = ("artifact", "artifact_group")
# A stated condition value off the menu, and the entries it rules out.
_OFF = {name: rules_out for name, (_values, rules_out, _description) in CONDITIONS.items()}
_OFF["input_network"] = "gene_gene"


def _ruled_out(table: JudgmentDefaults, name: str, item) -> bool:
    if name in ("data_unit", "time_model", "spatial"):
        return True
    if name == "mutation_origin":
        return item.workflow == "SAMBAR"
    if name == "value_type":  # every workflow but SAMBAR and CONDOR models continuous measurements
        return not {"mutation_calls", "regulator_gene_network"} & set(table.workflow_data[item.workflow][0])
    if name == "samples_matched":
        return item.layers is not None
    if name == "mirna_driver":
        return bool(item.regulators and "mirna" in item.regulators)
    if name == "group_membership":
        return item.groups == "one_group"
    if name == "input_network":
        return item.input_network == "regulator_gene"
    return False


@dataclass
class _Item:
    index: int
    wanted: Wanted
    result_open: bool = False
    questions: list[Question] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    ties: list[TieChoice] = field(default_factory=list)
    declined: Declined | None = None
    assumptions: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    unconfirmed: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    settled: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
    """Workflows still in play once the stated values narrowed them, before contract conditions are checked."""
    evidence: list[str] = field(default_factory=list)
    """The user's words showing the goal is unclear; a result question is CLARIFY only with them (2026-10-18)."""
    options: list[Option] = field(default_factory=list)
    infeasible: list[Infeasible] = field(default_factory=list)
    nearest: list[Option] = field(default_factory=list)


def _said(value: str, quote: str = "") -> Said:
    return Said(status="stated", value=value, basis="answered", quotes=[quote or value])


def _with_setting(reading: MenuReading, key: str, value: str) -> MenuReading:
    workflow, control = key.split(".", 1)
    settings = [s.model_copy(update={"value": value, "unsure": False, "values": []})
                if s.control == control and s.workflow in (workflow, "") and s.unsure else s for s in reading.settings]
    if settings == reading.settings:
        settings.append(SettingAsked(quote=value, workflow=workflow, control=control, value=value))
    return reading.model_copy(update={"settings": settings})


def apply_answers(reading: MenuReading, answers) -> MenuReading:
    """The reading with each answer filled in as stated (`basis` answered); answered fields are never re-read.

    An answer to the coarse result question (`artifact_group`) leaves the result open among that group's results.
    Item index `len(reading.wanted)` is the result asked for when the request named none; -1 is the request level.
    """
    if not answers:
        return reading
    table = judgment_defaults()
    for answer in answers:
        if answer.item < 0:
            if answer.dimension in ("sample_count", "feature_count"):
                reading = reading.model_copy(update={answer.dimension: Count(
                    status="stated", value=int(float(answer.value)), quotes=[answer.value])})
            elif answer.dimension.startswith("setting:"):
                reading = _with_setting(reading, answer.dimension.split(":", 1)[1], answer.value)
            elif answer.dimension == "file":
                reading = reading.model_copy(update={"unsure_files": []} if answer.value == "as_needed" else {
                    "unsure_files": [], "data_absent": [*reading.data_absent, *reading.data]})
            else:
                reading = reading.model_copy(update={"conditions": {**reading.conditions,
                                                                    answer.dimension: _said(answer.value)}})
            continue
        wanted = [item.model_copy(deep=True) for item in reading.wanted]
        while answer.item >= len(wanted):
            wanted.append(Wanted(quote=""))
        item = wanted[answer.item]
        if answer.dimension == "artifact_group":
            names = list(table.question_groups[answer.value].artifacts)
            item = item.model_copy(update={"artifact": Said(status="unsure", values=names, basis="answered",
                                                            quotes=[answer.value])})
        elif answer.dimension.startswith("requirement:"):
            index = int(answer.dimension.split(":", 1)[1])
            requirements = list(item.requirements)
            requirements[index] = requirements[index].model_copy(update={"must": answer.value == "yes"})
            item = item.model_copy(update={"requirements": requirements})
        else:
            item = item.model_copy(update={answer.dimension: _said(answer.value)})
        wanted[answer.item] = item
        reading = reading.model_copy(update={"wanted": wanted})
    return reading


class _Context:
    def __init__(self, reading: MenuReading, table: JudgmentDefaults, task: str, names=None, limits=None,
                 probing: bool = False):
        self.reading, self.table, self.task = reading, table, task
        self.probing = probing
        """A what-if evaluation (`_probe`, `_nearest`): it compares outcomes only -- no nearest options and no unstated
        B4 questions, which would re-probe without end (a probe's off-menu value relaxed away by `_nearest`)."""
        # The words of what the request says that is no result: a question to us, a purpose, a context.
        self.loose = [w.quote for w in reading.wanted
                      if w.form in ("question_to_us", "purpose", "context") and w.quote]
        self.names = names if names is not None else (
            reading.named_workflows if reading.named_workflows is not None
            else [name for name in workflows_in(task) if name not in reading.context_mentions])
        known = registered_workflows()
        named = {name for name in self.names if name in known}
        if LIONESS_FAMILY in self.names:  # LIONESS stands for every registered LIONESS-X
            named |= {name for name in known if name.startswith(f"{LIONESS_FAMILY}-")}
        self.named = named
        self.layers = len(set(reading.data) & table.omics_layers)
        self.limits = limits if limits is not None else all_conditions()  # read once: each limit is read live

    def has(self, need: str, data) -> bool:
        return any((len(set(data) & self.table.omics_layers) >= 2) if option == "two_layers" else option in data
                   for option in need.split("|"))

    def but(self, reading: MenuReading, probing: bool | None = None) -> "_Context":
        return _Context(reading, self.table, self.task, self.names, self.limits,
                        self.probing if probing is None else probing)


def _artifact_of(table: JudgmentDefaults, key: str) -> str:
    artifact = table.by_entry[key]
    return table.artifacts["comparison"].of.get(key, artifact) if artifact == "comparison" else artifact


def _scales(item) -> set[str]:
    found = set()
    if "aggregate" in item.granularity:
        found |= {"whole_cohort", "per_group"}
    if "sample_specific" in item.granularity:
        found.add("per_sample")
    return found


def _label(table: JudgmentDefaults, dimension: str, value: str) -> str:
    if dimension == "artifact":
        return table.artifacts[value].means if value in table.artifacts else "Something NetZoo does not give"
    if dimension == "artifact_group":
        return table.question_groups[value].label
    if value in ("off_menu", "three_or_more_jointly"):
        return "Something NetZoo does not give"
    return table.dimensions[dimension].options.get(value, value) if dimension in table.dimensions else value


def _outcome(item: _Item) -> tuple:
    """What a probe comes to: refused, the workflows given, the questions -- and the workflows still possible, so a
    value that takes a workflow away decides even while the same question is pending either way (slim reading D4:
    C50's log transform decides BONOBO, beside the requirement asked in both branches)."""
    return (item.declined is not None, tuple(item.workflows), tuple(q.dimension for q in item.questions),
            tuple(o.workflow for o in item.options))


def _probe(ctx: _Context, item: _Item, dimension: str, value: str) -> tuple:
    """What the item comes to with one more value stated -- whether an alternative decides anything."""
    reading, wanted = ctx.reading, item.wanted
    if dimension in ("sample_count", "feature_count"):
        reading = reading.model_copy(update={dimension: Count(status="stated", value=int(value))})
    elif dimension.startswith("setting:"):
        reading = _with_setting(reading, dimension.split(":", 1)[1], value)
    elif dimension in ctx.reading.conditions or dimension in _OFF:  # any request-level condition
        reading = reading.model_copy(update={"conditions": {**reading.conditions, dimension: _said(value)}})
    else:
        wanted = wanted.model_copy(update={dimension: _said(value)})
    probe = _Item(item.index, wanted)
    _evaluate(ctx.but(reading, probing=True), probe)
    return _outcome(probe)


def _decides(ctx: _Context, item: _Item, dimension: str, values) -> bool:
    return len({_probe(ctx, item, dimension, value) for value in values}) > 1


def _evaluate(ctx: _Context, item: _Item) -> None:
    table, sheet, reading, w = ctx.table, sheet_entries(), ctx.reading, item.wanted
    artifact, off_menu = w.artifact, table.dimensions["artifact"].off_menu
    if artifact.status == "stated" and artifact.value in off_menu:
        item.declined = Declined(quote=w.outside_name or w.quote,
                                 reasons=[f"not a registered result: {w.outside_name or w.quote}"])
        return
    in_play = [value for value in artifact.values if value] if artifact.status in ("unsure", "conflicting") else []
    choosing = bool(w.method_choice)
    if artifact.status == "stated":
        artifacts, item.result_open = set(table.expand(artifact.value)), artifact.value in table.generic
        if item.result_open:  # only a generic word ("a network analysis"): the goal is unclear
            item.evidence += artifact.quotes[:1] or [w.quote]
    elif in_play:
        artifacts = {name for value in in_play if value not in off_menu for name in table.expand(value)}
        item.result_open = artifact.basis == "answered" or any(value in table.generic for value in in_play)
        if any(value in table.generic for value in in_play):
            item.evidence += artifact.quotes[:1]
    else:
        # Not stated, or read as unsure with no alternatives: that alone is no ambiguity (options-first decision,
        # 2026-10-18). The result is inferred from the named workflows, the data and the other fields; it is asked
        # as the goal (CLARIFY) only with words showing the goal is unclear.
        artifacts, item.result_open = set(table.artifacts) - {"comparison"}, True
        if choosing:
            item.evidence += w.method_choice
        elif not w.quote:
            # Nothing in the request asks for a result: its questions to us and purposes are the evidence, workflow
            # names or not ("Should I use COBRA or CONDOR?" names methods, no result).
            item.evidence += ctx.loose
        elif not ctx.named and not _states_any(w):
            item.evidence += [*ctx.loose, w.quote]  # an item naming nothing, and no workflow named
    compare = w.compare.known() or "none"
    if compare in ("describe", "test"):
        entries = [key for key, of in table.artifacts["comparison"].of.items() if of in artifacts
                   and (compare == "describe" or "sample_specific" in sheet[key].granularity)]
    else:
        entries = [key for key, name in table.by_entry.items() if name in artifacts]
    failed: dict[str, list[str]] = {key: [] for key in entries}
    narrowed: list[str] = []

    def keep(predicate, why: str) -> None:
        for key in [key for key in failed if not predicate(sheet[key], key)]:
            del failed[key]
        if not failed:
            narrowed.append(why)

    # Named workflows restrict the candidates; one named and no result named: its direct results are the result,
    # several named and no result named: their direct results are the choice.
    if ctx.named:
        if artifact.status == "not_stated" or (artifact.status in ("unsure", "conflicting") and not in_play):
            failed = {key: [] for key, entry in sheet.items() if entry.kind == "produces"
                      and entry.workflow in ctx.named and entry.level == "direct"}
            item.result_open = True
        elif restricted := {key for key in failed if sheet[key].workflow in ctx.named}:
            keep(lambda entry, key: key in restricted, "named")
    considered = {sheet[key].workflow for key in failed}
    # An open result is narrowed to the workflows whose core data the user says they have.
    if item.result_open and reading.data:
        fitting = {key for key in failed
                   if all(ctx.has(need, reading.data) for need in table.workflow_data[sheet[key].workflow][0])}
        if fitting:
            keep(lambda entry, key: key in fitting, "data")
    # Stated values narrow; a dimension's plain value narrows too (`extra`).
    scale = w.granularity.known()
    if scale in ("whole_cohort", "per_group"):
        keep(lambda entry, key: "aggregate" in entry.granularity, f"granularity={scale}")
        plain = {_artifact_of(table, key) for key in failed if sheet[key].granularity == frozenset({"aggregate"})}
        for key in [key for key in failed if "sample_specific" in sheet[key].granularity
                    and _artifact_of(table, key) in plain]:
            del failed[key]  # a per-sample workflow beside a cohort one computes networks nobody asked for
    elif scale == "per_sample":
        keep(lambda entry, key: "sample_specific" in entry.granularity, "granularity=per_sample")
    regulators = w.regulators.known() or ("tf" if _plain_regulators(ctx, w) else None)
    if regulators == "off_menu":
        for key in failed:
            if _artifact_of(table, key) in _REGULATION:
                failed[key].append("near_miss:puma.no_lncrna_cerna")
    elif regulators:
        def regulator_fit(entry, key):
            if _artifact_of(table, key) not in _REGULATION or entry.regulators is None:
                return True
            kinds = set(entry.regulators)
            return kinds == {"tf"} if regulators == "tf" else "mirna" in kinds
        keep(regulator_fit, f"regulators={regulators}")
    signed = w.signed.known()
    if signed:
        keep(lambda entry, key: _artifact_of(table, key) not in _REGULATION or entry.signed is None
             or entry.signed == (signed == "signed"), f"signed={signed}")
    joint = w.integration.known()
    if joint == "joint":
        keep(lambda entry, key: _artifact_of(table, key) in _JOINT, "integration=joint")
    elif joint == "per_layer":
        keep(lambda entry, key: _artifact_of(table, key) not in _JOINT, "integration=per_layer")
    if w.layers.known() == "three_or_more_jointly":
        for key in failed:
            if _artifact_of(table, key) in _JOINT:
                failed[key].append("near_miss:dragon.no_more_layers")
    if not failed:
        item.candidates = sorted(considered)
        stated = {(name, getattr(w, name).known()) for name in ("granularity", "signed", "integration", "regulators")}
        misses = [f"near_miss:{key}" for key, (name, value) in table.ruled_by.items()
                  if (name, value) in stated and sheet[key].workflow in considered]
        item.declined = Declined(quote=w.quote, reasons=misses or [f"no registered result fits: {narrowed[0]}"])
        item.infeasible = [Infeasible(workflow=workflow, reasons=[m for m in misses if sheet[m.split(":", 1)[1]].workflow
                                                                   in (workflow, None)] or item.declined.reasons,
                                      contract=_contract_words(table, workflow, misses))
                           for workflow in sorted(considered)]
        item.nearest = [] if ctx.probing else _nearest(ctx, item, misses)
        return
    alive_before = sorted({sheet[key].workflow for key in failed})
    item.candidates = alive_before
    _rule_out(ctx, item, failed)
    alive = [key for key, reasons in failed.items() if not reasons]
    item.infeasible = _infeasible(table, failed)
    if not alive:
        reasons = list(dict.fromkeys(reason for reasons in failed.values() for reason in reasons))
        item.declined = Declined(quote=w.quote, reasons=reasons,
                                 instead=alive_before if reading.unregistered_methods else [])
        item.nearest = [] if ctx.probing else _nearest(ctx, item, reasons)
        return
    workflows = sorted({sheet[key].workflow for key in alive})
    _ask(ctx, item, alive)
    if not item.questions:
        _doubts(ctx, item, workflows)
    if not item.questions:
        workflows = _requirements(ctx, item, workflows)
    item.options = _options(ctx, item, [key for key in alive if sheet[key].workflow in workflows])
    if item.questions:
        return
    item.workflows = workflows
    if len(workflows) > 1:
        item.ties.append(_tie(ctx, workflows))
    for name, dimension in table.dimensions.items():
        if dimension.kind == "condition" and dimension.policy == "default" and name not in reading.conditions:
            if dimension.condition is None or any(_ruled_out(table, dimension.condition, sheet[key]) for key in alive):
                item.assumptions.append(f"{name}={dimension.value}")
    item.needs = sorted({need for workflow in workflows for need in table.workflow_data[workflow][1]
                         if not ctx.has(need, reading.data)}
                        | {f"declare {control}={value}" for workflow in workflows
                           for control, value in table.required_settings.get(workflow, {}).items()
                           if not any(s.workflow in (workflow, "") and s.control == control for s in reading.settings)})


def _rule_out(ctx: _Context, item: _Item, failed: dict[str, list[str]]) -> None:
    """Contract conditions: each candidate the request's stated facts rule out gets its reason."""
    table, sheet, reading, w = ctx.table, sheet_entries(), ctx.reading, item.wanted
    for name, said in reading.conditions.items():
        if name == "data_stage":
            if said.known() == "raw_files":
                item.steps.append("process the raw files into tables outside NetZoo first")
            continue
        if said.known() == _OFF.get(name):
            for key in failed:
                if _ruled_out(table, name, sheet[key]):
                    failed[key].append(f"{name}={said.value}")
    for key in failed:
        for need in table.workflow_data[sheet[key].workflow][1]:
            if all(option in reading.data_absent for option in need.split("|")) or (
                    reading.only_data and not ctx.has(need, reading.data)):
                failed[key].append(f"needs {need}, which the request says is not available")
    samples = reading.sample_count.value if reading.sample_count.status == "stated" else None
    features = reading.feature_count.value if reading.feature_count.status == "stated" else None
    for key in failed:
        workflow = sheet[key].workflow
        limits = ctx.limits.get(workflow)
        if limits is None:
            continue
        if problem := data_issue(limits, samples, features, reading.single_feature_count):
            failed[key].append(problem)
        # Settings only from this candidate's controls (options-first decision, 2026-10-18): words read as another
        # workflow's control describe the data or the output ("header present", "put everything in X/"), never a
        # setting this one lacks. Only an `unregistered` setting -- one no control takes -- rules it out.
        stated = [StatedSetting(name=f"{workflow}.{asked.control}" if asked.control in limits.settings else UNREGISTERED,
                                quote=asked.quote, value=asked.value)
                  for asked in reading.settings if asked.workflow in (workflow, "") and not asked.unsure
                  and (asked.control in limits.settings or asked.control == UNREGISTERED)]
        for setting in stated:
            if problem := setting_issue(limits, setting):
                failed[key].append(problem)
        doubted = any(asked.unsure and asked.workflow in (workflow, "") and asked.control in limits.settings
                      for asked in reading.settings)
        if not doubted:  # a control the user is unsure of is asked first; its default is never assumed (phase 1, d5)
            failed[key].extend(combination_issues(limits, stated, samples))
        for control, value in table.required_settings.get(workflow, {}).items():
            said = next((s for s in reading.settings if s.workflow in (workflow, "") and s.control == control
                         and not s.unsure), None)
            if said is not None and said.value.casefold() != value:
                failed[key].append(f"{workflow} runs only with {control}={value}")
    for requirement in w.requirements:
        if requirement.must is False:
            continue
        for key in failed:
            if requirement.verdicts.get(sheet[key].workflow) == "contradicted":
                failed[key].append(f'the contract contradicts "{requirement.quote}"')
    if reading.unregistered_methods:
        for key in failed:
            failed[key].append(f"not a registered method: {', '.join(reading.unregistered_methods)}")


def _question(item: _Item, dimension: str, values, table: JudgmentDefaults, quote: str, kind="intent") -> Question:
    return Question(item=item.index, dimension=dimension, kind=kind, quote=quote,
                    options=[(value, _label(table, dimension, value)) for value in values])


def _plain_regulators(ctx: _Context, w: Wanted) -> bool:
    """The `extra` rule for regulators: never mentioned -> TF only. miRNA data or a miRNA prior the user says they have
    is a mention, so an unstated regulator kind is then asked (phase 0 missed-field check: C25, C59); so is naming a
    workflow that models miRNAs -- the plain value never refuses the workflow the user named (slim reading spec 4.2;
    S2: "Can LIONESS-PUMA handle ...?" declined on regulators=tf)."""
    mirna_named = any(entry.kind == "produces" and entry.workflow in ctx.named and entry.regulators
                      and "mirna" in entry.regulators for entry in sheet_entries().values())
    return w.regulators.status == "not_stated" and not mirna_named \
        and not {"mirna_prior", "mirna_expression"} & set(ctx.reading.data)


_INTENTS = ("integration", "granularity", "regulators", "layers")


def _states_any(w: Wanted) -> bool:
    """The item states an intent beyond the result, or a requirement (then it names what it wants)."""
    return any(getattr(w, name).status != "not_stated" for name in (*_INTENTS, "signed", "compare")) \
        or bool(w.requirements)


def _ask(ctx: _Context, item: _Item, alive: list[str]) -> None:
    """The intent questions that decide something, coarse to fine; an unsure value is asked with its alternatives.

    Options-first decision (2026-10-18): a result question never hides a doubt read correctly -- the doubts that
    decide something for one of the results still open are asked beside it (two questions a turn at most). One
    result left by the named workflows or the stated fields is no question; one left by the data alone is confirmed.
    """
    table, sheet, w = ctx.table, sheet_entries(), item.wanted
    artifact = w.artifact
    results = sorted({_artifact_of(table, key) for key in alive})
    specific = [v for v in artifact.values if v not in table.generic] if artifact.status in ("unsure", "conflicting") else []
    if specific and not item.result_open:
        if _decides(ctx, item, "artifact", specific):
            item.questions.append(_question(item, "artifact", specific, table, (artifact.quotes or [w.quote])[0]))
            item.questions += _result_doubts(ctx, item, alive, [v for v in specific if v in results] or results)
            return
    elif item.result_open:
        determined = (ctx.named and not w.method_choice) or _states_any(w)
        if len(results) > 1 or not determined or item.evidence:
            quote = (item.evidence or artifact.quotes or [w.quote])[0]
            if len(results) <= table.ask_max_options:
                item.questions.append(_question(item, "artifact", results, table, quote))
            else:
                groups = [name for name, group in table.question_groups.items() if set(group.artifacts) & set(results)]
                item.questions.append(_question(item, "artifact_group", groups, table, quote))
            item.questions += _result_doubts(ctx, item, alive, results)
            return  # the unstated finer dimensions wait for the result; read doubts were asked beside it
    for dimension in _INTENTS:
        said: Said = getattr(w, dimension)
        quote = (said.quotes or [w.quote])[0]
        if said.status in ("unsure", "conflicting") or dimension == "regulators" and not said.known() \
                and not _plain_regulators(ctx, w):
            values = said.values or {"regulators": ["tf", "tf_mirna"]}.get(dimension, [])
            if len(values) > 1 and _decides(ctx, item, dimension, values):
                item.questions.append(_question(item, dimension, values, table, quote))
            continue
        if said.status == "stated":
            continue
        values = _open_values(ctx, item, dimension, alive)
        if len(values) > 1:
            item.questions.append(_question(item, dimension, values, table, quote))


def _result_doubts(ctx: _Context, item: _Item, alive: list[str], results: list[str]) -> list[Question]:
    """The doubts read correctly that decide something for one of the results still open (each probed with that
    result stated): an unsure intent, condition, count, setting or file."""
    found: dict[str, Question] = {}
    w = item.wanted
    probes = [_Item(item.index, w.model_copy(update={"artifact": _said(result)})) for result in results]
    for dimension in _INTENTS:
        said = getattr(w, dimension)
        if said.status in ("unsure", "conflicting") and len(said.values) > 1 and dimension not in found:
            if any(_decides(ctx, probe, dimension, said.values) for probe in probes):
                found[dimension] = _question(item, dimension, said.values, ctx.table, (said.quotes or [w.quote])[0])
    workflows = sorted({sheet_entries()[key].workflow for key in alive})
    for probe in probes:
        _doubts(ctx, probe, workflows, unstated=False)
        for question in probe.questions:
            found.setdefault(question.dimension, question)
    return list(found.values())


def _open_values(ctx: _Context, item: _Item, dimension: str, alive: list[str]) -> list[str]:
    """The values of an unstated intent that lead to different candidates -- empty when it decides nothing."""
    table, sheet, w = ctx.table, sheet_entries(), item.wanted
    joint = [key for key in alive if _artifact_of(table, key) in _JOINT]
    if dimension == "integration":
        return ["joint", "per_layer"] if ctx.layers >= 2 and joint and len(joint) < len(alive) else []
    if dimension == "granularity":
        by_scale = {}
        for scale in _SCALES:
            if scale == "per_group" and not ctx.reading.groups:
                continue
            serving = frozenset(sheet[key].workflow for key in alive if scale in _scales(sheet[key]))
            if serving:
                by_scale[scale] = serving
        distinct = len(set(by_scale.values())) > 1 or ("per_group" in by_scale and "whole_cohort" in by_scale)
        return list(by_scale) if distinct else []
    if dimension == "layers":
        if ctx.layers >= 3 and joint and (w.integration.known() == "joint" or len(joint) == len(alive)):
            stated = [name for name in table.omics_layers if name in ctx.reading.data]
            return [f"{a}+{b}" for a, b in combinations(stated, 2)]
    return []


def _doubts(ctx: _Context, item: _Item, workflows: list[str], unstated: bool = True) -> None:
    """A condition, count or setting the user is unsure of, asked when its alternatives lead to different outcomes;
    a doubt about a named file is settled by the input check before a run."""
    reading, table = ctx.reading, ctx.table
    asked: list[Question] = []
    for name, said in reading.conditions.items():
        if said.status in ("unsure", "conflicting"):
            values = said.values or [v for v in CONDITIONS.get(name, ((),))[0] if v != "not_stated"]
            if len(values) > 1 and _decides(ctx, item, name, values):
                asked.append(_question(item, name, values, table, (said.quotes or [""])[0], "condition"))
    for dimension in ("sample_count", "feature_count"):
        count = getattr(reading, dimension)
        if count.status in ("unsure", "conflicting") and len(count.values) > 1:
            values = [str(v) for v in count.values]
            if _decides(ctx, item, dimension, values):
                asked.append(_question(item, dimension, values, table, (count.quotes or [""])[0], "condition"))
    for setting in reading.settings:
        if setting.unsure and len(setting.values) > 1:
            for workflow in [setting.workflow] if setting.workflow else workflows:
                key = f"setting:{workflow}.{setting.control}"
                if _decides(ctx, item, key, setting.values):
                    asked.append(_question(item, key, setting.values, table, setting.quote, "condition"))
                    break
    if unstated:  # B4 not stated waits for the result: beside a result question only the user's own doubts are asked
        asked += _unstated_b4(ctx, item, workflows, {q.dimension for q in asked})
    if reading.unsure_files:
        if reading.run_requested:
            item.settled = list(reading.unsure_files)
        else:
            asked.append(Question(item=item.index, dimension="file", kind="condition", quote=reading.unsure_files[0],
                                  options=[("as_needed", "It is the file the workflow needs"),
                                           ("other", "It is the other one")]))
    for question in asked:  # request-level doubts are answered at item -1
        question.item = -1
    item.questions.extend(asked)


def _b4_open(ctx: _Context, workflows, asked) -> list[tuple[str, list[str]]]:
    """The B4 conditions of these workflows not stated, as (key, values): a condition name, or `setting:W.control`
    for a required setting (BONOBO's declared log transform and centering)."""
    found, reading, table = [], ctx.reading, ctx.table
    for workflow in workflows:
        for name in table.b4_conditions.get(workflow, ()):
            if name.startswith("setting:"):
                control = name.split(":", 1)[1]
                key = f"setting:{workflow}.{control}"
                if key in asked or any(s.control == control and s.workflow in (workflow, "") for s in reading.settings):
                    continue
                values = ["true", "false"]
            else:
                key = name
                if key in asked or name in reading.conditions:
                    continue
                values = [v for v in CONDITIONS.get(name, (table.dimensions[name].values,))[0] if v != "not_stated"]
            asked = {*asked, key}
            found.append((key, values))
    return found


def _unstated_b4(ctx: _Context, item: _Item, workflows: list[str], asked: set[str]) -> list[Question]:
    """B4 (slim reading spec 2026-10-19): the condition a candidate workflow's contract turns on, not stated -> asked
    when its values lead to different calls. A condition the user was unsure of is already asked above."""
    if ctx.probing:
        return []
    # User decision 2026-10-19 (a): conditions take their draft-5 default or the input check (disclosed) and are asked
    # only on a doubt (above); a required declaration (BONOBO's log transform, centering) is asked when not stated.
    return [_question(item, key, values, ctx.table, "", "condition") for key, values in _b4_open(ctx, workflows, asked)
            if key.startswith("setting:") and _decides(ctx, item, key, values)]


def _requirements(ctx: _Context, item: _Item, workflows: list[str]) -> list[str]:
    """D4 (slim reading spec 2026-10-19, 4.3): each requirement against each candidate's contract. Contradicted ones
    already ruled their workflow out; one a candidate's contract does not address is asked once, whether it is a
    must. A must is kept with a warning ("the contract does not say; it cannot be guaranteed"); one dropped is gone.
    The share met is only the match rate the options card shows -- it decides nothing."""
    counted = [r for r in item.wanted.requirements if r.must is not False]
    if not counted:
        return workflows
    open_ones = [(index, r) for index, r in enumerate(item.wanted.requirements)
                 if r.must is None and any(r.verdicts.get(w) != "met" for w in workflows)]
    for index, requirement in open_ones[:ctx.table.max_questions_per_turn]:
        item.questions.append(Question(item=item.index, dimension=f"requirement:{index}", kind="requirement",
                                       options=[("yes", "Yes, it is a must"), ("no", "No, it can be dropped")],
                                       quote=requirement.quote))
    if not open_ones:
        item.unconfirmed = [r.quote for r in counted if any(r.verdicts.get(w) != "met" for w in workflows)]
    return workflows


def _choice_applies(ctx: _Context, choice) -> bool:
    reading = ctx.reading
    if choice.trigger == "groups_mentioned":
        return bool(reading.groups)
    if choice.trigger == "batch_with_comparison":
        compared = bool(reading.groups) or any(w.compare.known() in ("describe", "test") for w in reading.wanted)
        return bool({"batch", "site"} & set(reading.covariates)) and compared
    if choice.trigger == "several_covariates":
        return len(reading.covariates) >= 2 or ("COBRA" in ctx.named and len(ctx.named) >= 2)
    if choice.trigger == "three_or_more_layers":
        return ctx.layers >= 3
    return False


_CHECKED = {"samples_matched": "Whether both layers come from the same samples is checked from your files (sample IDs) "
                               "before the run.",
            "input_network": "Whether your network file holds regulator-to-gene edges is checked before the run."}


def disclosures_for(reading: MenuReading, workflows, table: JudgmentDefaults | None = None) -> list[str]:
    """Code-written lines for a run (hybrid spec 4): the default interpretation choices of these workflows (unless
    the user set that control), the draft-5 defaults an unstated B4 condition takes, and the input checks that settle
    the others -- never a model's words (user decisions 2026-10-19)."""
    table = table or judgment_defaults()
    lines, workflows = [], list(workflows)
    stated = {s.control for s in reading.settings if not s.unsure}
    for choice in table.choices.values():
        if choice.policy == "default_disclose" and set(choice.workflows) & set(workflows) \
                and not stated & set(choice.unless_settings):
            lines.append(choice.disclose)
    for workflow in workflows:
        for name in table.b4_conditions.get(workflow, ()):
            if name in reading.conditions or name.startswith("setting:"):
                continue
            dimension = table.dimensions[name]
            if dimension.policy == "default":
                label = dimension.options.get(dimension.value, str(dimension.value))
                lines.append(f"Assumed for {workflow}: {label[0].lower()}{label[1:]} (the default; say so if not).")
            elif name in _CHECKED:
                lines.append(_CHECKED[name])
    return list(dict.fromkeys(lines))


def confirm_items(reading: MenuReading, workflows, task: str = "", table: JudgmentDefaults | None = None) -> list[str]:
    """The must-confirm interpretation choices a run of these workflows triggers, listed at run confirmation (hybrid
    spec 4): each one keeps the workflow but changes what the result means."""
    table = table or judgment_defaults()
    ctx = _Context(reading, table, task)
    return [choice.question for choice in table.choices.values()
            if choice.policy == "must_confirm" and set(choice.workflows) & set(workflows)
            and _choice_applies(ctx, choice)]


def _tie(ctx: _Context, workflows: list[str]) -> TieChoice:
    group = next((name for name, (_asked, options) in ctx.table.tie_options.items()
                  if set(workflows) <= {option.workflow for option in options}), None)
    fits = []
    if group is not None:
        for option in ctx.table.tie_options[group][1]:
            if option.workflow in workflows and option.fits_when and all(
                    value in ctx.reading.data for name, value in option.fits_when if name == "data_available"):
                fits.append(option.workflow)
    return TieChoice(group=group, workflows=workflows, fits=fits)


def workflow_conditions(workflow: str, table: JudgmentDefaults | None = None) -> list[str]:
    """The data conditions whose off-menu value rules this workflow out (`_ruled_out`), in the table's order."""
    table, sheet = table or judgment_defaults(), sheet_entries()
    entries = [entry for entry in sheet.values() if entry.kind == "produces" and entry.workflow == workflow]
    return [name for name in (*CONDITIONS, "input_network") if name in _OFF
            and any(_ruled_out(table, name, entry) for entry in entries)]


def candidate_workflows(reading: MenuReading, task: str = "", table: JudgmentDefaults | None = None) -> list[str]:
    """The workflows in play for the things asked, once stated values narrowed them and before any contract condition
    is checked -- what the phase-1 focused re-read reads limits and doubts for. Empty for a failed reading."""
    table = table or judgment_defaults()
    if reading.status == "failed":
        return []
    ctx = _Context(reading, table, task)
    items = [_Item(index, wanted) for index, wanted in enumerate(reading.wanted) if wanted.form == "deliverable"]
    found: set[str] = set()
    for item in items or [_Item(len(reading.wanted), Wanted(quote=""))]:
        _evaluate(ctx, item)
        found |= set(item.candidates)
    return sorted(found)


def _contract_words(table: JudgmentDefaults, workflow: str, reasons) -> list[str]:
    """The capability sheet's words behind each reason: a near miss's why-not line, or the why-not lines of the
    entries the stated off-menu value rules out for this workflow."""
    sheet, found = sheet_entries(), []
    for reason in reasons:
        keys = []
        if reason.startswith("near_miss:"):
            keys = [reason.split(":", 1)[1]]
        elif "=" in reason and " " not in reason.split("=", 1)[0]:
            name, value = reason.split("=", 1)
            keys = [key for key, ruled in table.ruled_by.items() if ruled == (name, value)
                    and key in sheet and sheet[key].workflow in (workflow, None)]
        for key in keys:
            entry = sheet.get(key)
            if entry is not None:
                words = f"{entry.text} -- {entry.why_not}" if entry.why_not else entry.text
                if words not in found:
                    found.append(words)
    return found


def _infeasible(table: JudgmentDefaults, failed: dict[str, list[str]]) -> list[Infeasible]:
    sheet, by_workflow = sheet_entries(), {}
    for key, reasons in failed.items():
        if reasons:
            merged = by_workflow.setdefault(sheet[key].workflow, [])
            merged += [reason for reason in reasons if reason not in merged]
    return [Infeasible(workflow=workflow, reasons=reasons, contract=_contract_words(table, workflow, reasons))
            for workflow, reasons in sorted(by_workflow.items())]


def _tie_order(table: JudgmentDefaults, workflow: str) -> tuple[int, int]:
    for rank, (_group, (_asked, options)) in enumerate(table.tie_options.items()):
        names = [option.workflow for option in options]
        if workflow in names:
            return rank, names.index(workflow)
    return 99, 0


def _option_lines(table: JudgmentDefaults, workflow: str, keys: list[str]) -> tuple[str, str]:
    """difference / good_for: the tie options' lines where the workflow is in a tie group, else the sheet's words."""
    sheet = sheet_entries()
    for _group, (_asked, options) in table.tie_options.items():
        for option in options:
            if option.workflow == workflow:
                return option.difference, option.good_for
    entry = sheet[sorted(keys, key=lambda key: sheet[key].level != "direct")[0]]
    return entry.text, entry.reading or ""


def _points(ctx: _Context, w: Wanted, workflow: str, keys: list[str]) -> list[tuple[str, bool]]:
    """The user's stated points relevant to this option, each with whether it satisfies them."""
    table, sheet, reading = ctx.table, sheet_entries(), ctx.reading
    points = []
    if w.artifact.status == "stated" and w.artifact.value not in table.generic:
        points.append(((w.artifact.quotes or [w.artifact.value])[0], True))
    for name in (*_INTENTS, "signed", "compare"):
        said = getattr(w, name)
        if said.status == "stated":
            points.append(((said.quotes or [f"{name}={said.value}"])[0], True))
    core, needs = table.workflow_data.get(workflow, ((), ()))
    used = {option for need in (*core, *needs) for option in need.split("|")}
    for kind in reading.data:
        if kind in used or ("two_layers" in used and kind in table.omics_layers):
            points.append((f"you have {kind.replace('_', ' ')}", True))
    for name, said in reading.conditions.items():
        if said.status == "stated" and any(_ruled_out(table, name, sheet[key]) for key in keys if name in _OFF):
            points.append(((said.quotes or [f"{name}={said.value}"])[0], True))
    for asked in reading.settings:
        if asked.workflow in (workflow, "") and not asked.unsure and asked.control in (
                ctx.limits[workflow].settings if workflow in ctx.limits else {}):
            points.append((asked.quote or asked.control, True))
    for requirement in w.requirements:
        if requirement.must is not False:
            points.append((requirement.quote, requirement.verdicts.get(workflow) == "met"))
    return points


def _options(ctx: _Context, item: _Item, alive: list[str]) -> list[Option]:
    """The feasible options, ranked: the match rate, then the tie order; at most `ask_max_options`."""
    table, sheet, reading = ctx.table, sheet_entries(), ctx.reading
    by_workflow: dict[str, list[str]] = {}
    for key in alive:
        by_workflow.setdefault(sheet[key].workflow, []).append(key)
    built = []
    for workflow, keys in by_workflow.items():
        points = _points(ctx, item.wanted, workflow, keys)
        matched = sum(ok for _quote, ok in points)
        difference, good_for = _option_lines(table, workflow, keys)
        to_confirm = [q.dimension for q in item.questions]
        to_confirm += [f'requirement not addressed by the contract: "{r.quote}"' for r in item.wanted.requirements
                       if r.must is not False and r.verdicts.get(workflow) != "met"]
        to_confirm += [f"input needed: {need.replace('|', ' or ')}" for need in table.workflow_data[workflow][1]
                       if not ctx.has(need, reading.data)]
        artifacts = sorted({_artifact_of(table, key) for key in keys})
        built.append(Option(workflow=workflow, artifact=", ".join(artifacts), difference=difference,
                            good_for=good_for, fits=list(dict.fromkeys(q for q, ok in points if ok))[:4],
                            to_confirm=to_confirm, matched=matched, relevant=len(points)))
    built.sort(key=lambda o: (-(o.matched / o.relevant if o.relevant else 1.0), _tie_order(table, o.workflow),
                              o.workflow))
    return built[:table.ask_max_options]


def _nearest(ctx: _Context, item: _Item, reasons) -> list[Option]:
    """DECLINE: the nearest registered options that can be done. A near miss's registered alternative first; then the
    same request without the constraints the contracts rule out (off-menu conditions, settings, requirements,
    methods), each option saying what it leaves out."""
    table, sheet, reading, w = ctx.table, sheet_entries(), ctx.reading, item.wanted
    found: list[Option] = []
    known = {action: name for name, action in registered_workflows().items()}
    for reason in reasons:
        key = reason.split(":", 1)[1] if reason.startswith("near_miss:") else None
        alternative = known.get(sheet[key].instead_registered) if key in sheet and sheet[key].instead_registered else None
        if alternative and alternative not in {o.workflow for o in found}:
            keys = [k for k, e in sheet.items() if e.kind == "produces" and e.workflow == alternative]
            difference, good_for = _option_lines(table, alternative, keys)
            found.append(Option(workflow=alternative, artifact=_artifact_of(table, keys[0]), difference=difference,
                                good_for=good_for, to_confirm=[f"instead of: {sheet[key].text}"]))
    dropped, conditions = [], {}
    for name, said in reading.conditions.items():
        if said.known() == _OFF.get(name):
            dropped.append(f"{name.replace('_', ' ')}: {said.value.replace('_', ' ')}")
        else:
            conditions[name] = said
    settings = [s for s in reading.settings if s.control != UNREGISTERED]
    dropped += [f"setting: {s.quote}" for s in reading.settings if s.control == UNREGISTERED]
    wanted = w.model_copy(update={
        "requirements": [r for r in w.requirements if "contradicted" not in r.verdicts.values()],
        **({"regulators": Said()} if w.regulators.known() == "off_menu" else {}),
        **({"layers": Said()} if w.layers.known() == "three_or_more_jointly" else {})})
    dropped += [f'requirement: "{r.quote}"' for r in w.requirements if "contradicted" in r.verdicts.values()]
    dropped += [f"method: {name}" for name in reading.unregistered_methods]
    if w.regulators.known() == "off_menu":
        dropped.append("regulators NetZoo does not model")
    if w.layers.known() == "three_or_more_jointly":
        dropped.append("three or more layers in one model")
    if not dropped or (w.artifact.status == "stated" and w.artifact.value in table.dimensions["artifact"].off_menu):
        return found[:table.ask_max_options]
    relaxed = reading.model_copy(update={"conditions": conditions, "settings": settings, "unregistered_methods": []})
    probe = _Item(item.index, wanted)
    _evaluate(ctx.but(relaxed, probing=True), probe)
    for option in probe.options or [o for o in []]:
        if option.workflow not in {o.workflow for o in found}:
            found.append(option.model_copy(update={"to_confirm": [*(f"leaves out {d}" for d in dropped),
                                                                  *option.to_confirm]}))
    return found[:table.ask_max_options]


def intent_values(dimension: str, table: JudgmentDefaults | None = None) -> tuple[str, ...]:
    """A probed intent's menu values: the results, kinds of result and off-menu for the artifact; else its values and
    off-menu values."""
    table = table or judgment_defaults()
    dimension_ = table.dimensions[dimension]
    if dimension == "artifact":
        return (*dimension_.values, *table.generic, *dimension_.off_menu)
    return (*dimension_.values, *dimension_.off_menu)


def deciding_intents(reading: MenuReading, task: str = "",
                     table: JudgmentDefaults | None = None) -> list[tuple[int, str]]:
    """(item, intent) for each probed intent whose menu values lead a thing asked to different calls (`_probe`), counting
    only the values that leave it a candidate. An
    intent the user is already unsure of is asked anyway and never probed. With nothing asked, item
    `len(reading.wanted)` is the result the request leaves unnamed (as in `decide_menu`)."""
    table = table or judgment_defaults()
    if reading.status == "failed":
        return []
    ctx = _Context(reading, table, task)
    items = [_Item(index, wanted) for index, wanted in enumerate(reading.wanted) if wanted.form == "deliverable"]
    found = []
    for item in items or [_Item(len(reading.wanted), Wanted(quote=""))]:
        for dimension in PROBED_INTENTS:
            if getattr(item.wanted, dimension).status in ("unsure", "conflicting"):
                continue
            # As `_open_values`: only values that leave the thing asked a candidate count; a value that rules every
            # candidate out ("joint" for a TF network) is no reading of the words, so it decides nothing here.
            alive = {outcome for outcome in (_probe(ctx, item, dimension, value)
                                             for value in intent_values(dimension, table)) if not outcome[0]}
            if len(alive) > 1:
                found.append((item.index, dimension))
    return found


def b_fields(reading: MenuReading, task: str = "", table: JudgmentDefaults | None = None
             ) -> tuple[list[tuple[int, str]], list[str], list[str]]:
    """Slim reading step 2 (spec 2026-10-19, sections 2 and 3, B): what the focused read (step 3) reads, chosen from
    the candidates' contracts -- for each thing asked, each B1-B3 intent not stated whose values lead to different
    calls (off-menu values count: stating one refuses, so it must be read), and the B4 conditions of its candidate
    workflows not stated whose values do the same. "One per group" is a value only when the user names groups; B3
    only while a candidate gives a joint multi-omic result.

    Returns the (item, intent) pairs, the B4 keys and the candidate workflows."""
    table = table or judgment_defaults()
    if reading.status == "failed":
        return [], [], []
    ctx = _Context(reading, table, task)
    items = [_Item(index, wanted) for index, wanted in enumerate(reading.wanted) if wanted.form == "deliverable"]
    intents, conditions, candidates = [], [], set()
    for item in items or [_Item(len(reading.wanted), Wanted(quote=""))]:
        _evaluate(ctx.but(reading, probing=True), item)
        candidates |= set(item.candidates)
        # B3 only while a candidate gives a joint multi-omic result (spec 3, B3): "joint" stated on any other request
        # refuses it, which is no reason to read the field.
        joint = any(entry.kind == "produces" and entry.workflow in item.candidates and _artifact_of(table, key) in _JOINT
                    for key, entry in sheet_entries().items())
        for dimension in B_INTENTS:
            if getattr(item.wanted, dimension).status != "not_stated" or (
                    dimension in ("integration", "layers") and not joint):
                continue
            values = [v for v in intent_values(dimension, table) if v != "per_group" or reading.groups]
            if _decides(ctx, _Item(item.index, item.wanted), dimension, values):
                intents.append((item.index, dimension))
        for key, values in _b4_open(ctx, item.candidates, set(conditions)):
            if _decides(ctx, _Item(item.index, item.wanted), key, values):
                conditions.append(key)
    return intents, conditions, sorted(candidates)


@dataclass
class GateVerdict:
    """One workflow's hard conditions on a request (the live system's hybrid gates, 2026-10-18)."""

    workflow: str
    reasons: list[str] = field(default_factory=list)
    """Why it cannot run what was asked; empty when it can."""
    contract: list[str] = field(default_factory=list)
    must_ask: list[str] = field(default_factory=list)
    """Requirements its contract does not address, asked while fewer than `soft_requirements_met` are met."""
    unconfirmed: list[str] = field(default_factory=list)
    """Requirements not addressed, listed for confirmation when enough of the others are met."""


def workflow_gate(reading: MenuReading, workflow: str, task: str = "",
                  table: JudgmentDefaults | None = None) -> GateVerdict:
    """The contract's hard conditions for one workflow another call already chose (the live path's DO): the stated
    settings it lacks or cannot take, data the user says is absent, counts it cannot take, off-menu conditions,
    unregistered methods and contradicted requirements -- each a reason it cannot run -- then the 9/10 rule for
    requirements its contract does not address. Intents are not judged here: the caller chose the result."""
    table = table or judgment_defaults()
    ctx = _Context(reading, table, task, names=[workflow])
    item = _Item(0, reading.wanted[0] if reading.wanted else Wanted(quote=""))
    failed = {key: [] for key, entry in sheet_entries().items() if entry.kind == "produces" and entry.workflow == workflow}
    _rule_out(ctx, item, failed)
    verdict = GateVerdict(workflow=workflow)
    if failed and all(failed.values()):
        verdict.reasons = list(dict.fromkeys(r for reasons in failed.values() for r in reasons))
        verdict.contract = _contract_words(table, workflow, verdict.reasons)
        return verdict
    counted = [r for r in item.wanted.requirements if r.must is not False]
    if counted:
        met = sum(r.verdicts.get(workflow) == "met" for r in counted) / len(counted)
        open_ones = [r.quote for r in counted if r.verdicts.get(workflow) != "met"]
        if met >= table.soft_requirements_met:
            verdict.unconfirmed = open_ones
        else:
            verdict.must_ask = open_ones[:table.max_questions_per_turn]
    return verdict


def decide_menu(reading: MenuReading, task: str = "", answers=(), rounds_asked: int = 0,
                table: JudgmentDefaults | None = None) -> MenuDecision:
    """The turn's call from what the user said (and answered), by the closed menu's rules alone."""
    table = table or judgment_defaults()
    if reading.status == "failed":
        return MenuDecision(kind="UNCHECKED", basis="reading_failed")
    reading = apply_answers(reading, list(answers))
    ctx = _Context(reading, table, task)
    declined = []
    for name in ("claims", "delivery"):
        said = getattr(reading, name)
        if said.known() in table.dimensions[name].off_menu:
            declined.append(Declined(quote=(said.quotes or [""])[0], reasons=[f"{name}={said.value}"]))
    deliverables = [_Item(index, wanted) for index, wanted in enumerate(reading.wanted) if wanted.form == "deliverable"]
    if not deliverables and not (declined and not ctx.named) and not (reading.unregistered_methods and not ctx.named):
        deliverables = [_Item(len(reading.wanted), Wanted(quote=""))]
    if not deliverables and reading.unregistered_methods:
        declined.append(Declined(quote=", ".join(reading.unregistered_methods), reasons=["not a registered method"]))
    for item in deliverables:
        _evaluate(ctx, item)
    asked = [q for item in deliverables for q in item.questions]
    questions = sorted(asked, key=lambda q: (q.kind != "intent", q.item))[:table.max_questions_per_turn]
    declined += [item.declined for item in deliverables if item.declined is not None]
    given = [item for item in deliverables if item.workflows]
    options = [option for item in deliverables for option in item.options]
    seen_options: set[str] = set()
    options = [o for o in options if not (o.workflow in seen_options or seen_options.add(o.workflow))]
    common = dict(declined=declined, assumptions=sorted({a for i in given for a in i.assumptions}),
                  needs=sorted({n for i in given for n in i.needs}),
                  unconfirmed=[u for i in given for u in i.unconfirmed],
                  steps=list(dict.fromkeys(s for i in deliverables for s in i.steps)),
                  settled=list(dict.fromkeys(s for i in deliverables for s in i.settled)),
                  options=options[:table.ask_max_options * max(1, len(deliverables))],
                  # a workflow that can run one of the results asked is an option, never also "not possible"
                  infeasible=[x for item in deliverables for x in item.infeasible if x.workflow not in seen_options],
                  nearest=[o for item in deliverables for o in item.nearest])
    if questions:
        # CLARIFY needs the user's words showing the goal is unclear (options-first decision, 2026-10-18); a result
        # question without them is an ASK with options.
        evidence = [quote for item in deliverables if any(q.dimension in _RESULT and q.item == item.index
                                                           for q in questions) for quote in item.evidence]
        result_open = bool(evidence)
        common["evidence"] = list(dict.fromkeys(evidence))
        return MenuDecision(kind="CLARIFY" if result_open else "ASK",
                            basis="result_open" if result_open else questions[0].kind,
                            questions=questions, final_round=rounds_asked >= table.max_ask_rounds,
                            workflows=sorted({w for i in given for w in i.workflows}), **common)
    if not given:
        return MenuDecision(kind="DECLINE", basis="nothing_fits", **common)
    workflows = sorted({w for item in given for w in item.workflows})
    ties = [tie for item in given for tie in item.ties]
    partial = bool(declined)
    return MenuDecision(kind="DO", basis="tie" if ties else "fits", workflows=workflows, ties=ties, partial=partial,
                        run_ready=(reading.run_requested and not partial and len(workflows) == 1), **common)
