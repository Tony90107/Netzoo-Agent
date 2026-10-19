"""The contract veto layer (hybrid spec docs/superpowers/specs/2026-10-19-hybrid-contract-veto-design.md, section 3).

The live system reads the intent, picks the workflows and asks; when it is about to run (core DO), this layer checks
only the workflows it picked against their contracts. Pure code here; the reads are `graph.contract_veto_call`.

What is read (`limit_needs`): the slim core read for the C facts, D4 requirements and D7 covariates, and the focused
read of the limit fields only -- B4 conditions, B5 settings, B6 counts and the required declarations of those
workflows. Never B1-B3, never the slim reading's A1 to re-pick a workflow.

A veto needs a violation with the user's words (verified in the request when read) and the contract's words:
- code-verified: a setting's own contract line (`- setting <control> ...`), an `input_checks` text naming the count
  limit, the capability sheet's near-miss or registry-wide entry, or the registry itself (no such control, no such
  method);
- model-copied: for a fact no code line covers (a data form, a stated-absent input, an off-menu result, a requirement),
  the contract check copies the clause and says met / contradicted / not_addressed; only a contradicted clause that is
  verbatim in that workflow's contract counts (`menu_requirements.workflow_contract`).
A violation without contract words is reported (`unverified`), never a veto. Narrowing ("no registered result fits")
and unsure readings never veto; an unsure value that flips the same workflow from feasible to infeasible adds one
question (`questions`).
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field

from ..capability_sheet import sheet_entries
from ..contracts.menu_reading import Count, MenuReading, Said
from ..contracts.slim_reading import SlimReading
from ..judgment_defaults import JudgmentDefaults, judgment_defaults
from ..method_names import registered_workflows
from ..workflow_conditions import all_conditions, data_issue
from .interpretation_choices import confirm_items, disclosures_for
from .menu_decision import _OFF, _ruled_out, _with_setting, workflow_gate
from .menu_focus import focus_limits
from .menu_reader import _norm
from .menu_requirements import RequirementPair, workflow_contract
from .slim_reader import Needs, to_menu

__all__ = ["CheckPair", "VetoQuestion", "VetoVerdict", "Violation", "check_pairs", "check_text", "contract_veto",
           "limit_needs", "veto_notes", "vetoed_core", "violation_line", "with_veto_notes"]


@dataclass(frozen=True, slots=True)
class Violation:
    workflow: str
    kind: str
    """C2-C7, B4-B6 or D4: the spec's field of the user's fact."""
    reason: str
    user_quote: str
    contract_quote: str
    source: str = "contract"
    """contract (a clause of the workflow's contract), sheet (a capability-sheet entry) or registry."""


@dataclass(frozen=True, slots=True)
class CheckPair:
    """A user fact to check against one workflow's contract (the model copies the clause; code verifies it)."""

    kind: str
    quote: str
    workflow: str
    reason: str

    @property
    def requirement(self) -> RequirementPair:  # the shape `menu_requirements` numbers and renders
        return RequirementPair(item=0, index=0, quote=self.quote, workflow=self.workflow)


@dataclass(frozen=True, slots=True)
class VetoQuestion:
    workflow: str
    dimension: str
    values: tuple[str, ...]
    quote: str
    infeasible: tuple[str, ...]
    """The values that make the workflow infeasible."""
    contract_quote: str = ""


@dataclass
class VetoVerdict:
    workflows: list[str]
    violations: dict[str, list[Violation]] = field(default_factory=dict)
    questions: list[VetoQuestion] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    """Violations code found without contract words: reported, never a veto."""
    unconfirmed: list[str] = field(default_factory=list)
    """Requirements no kept workflow's contract addresses: listed for confirmation, never a veto."""
    disclosures: list[str] = field(default_factory=list)
    to_confirm: list[str] = field(default_factory=list)
    nearest: list[str] = field(default_factory=list)

    @property
    def vetoed(self) -> list[str]:
        return [w for w in self.workflows if self.violations.get(w)]

    @property
    def kept(self) -> list[str]:
        return [w for w in self.workflows if not self.violations.get(w)]


# --- what is read -----------------------------------------------------------------------------------------------------

def limit_needs(slim: SlimReading, workflows) -> Needs:
    """Step 3 for the live system's workflows: every B4 condition and required declaration they turn on that step 1
    did not read, their controls (B5) and the counts they limit (B6) -- never B1-B3."""
    table, known = judgment_defaults(), registered_workflows()
    workflows = tuple(w for w in workflows if w in known)
    if not workflows:
        return Needs()
    stated = {f.name for f in slim.stated}
    menu = to_menu(slim)
    data = tuple(dict.fromkeys(need for workflow in workflows for need in _unmentioned(menu, workflow, table)))
    conditions = []
    for workflow in workflows:
        for name in table.b4_conditions.get(workflow, ()):
            key = f"setting:{workflow}.{name.split(':', 1)[1]}" if name.startswith("setting:") else name
            if name not in stated and key not in conditions:
                conditions.append(key)
    return Needs(conditions=tuple(conditions), candidates=workflows,
                 counts=tuple(focus_limits(workflows)["counts"]), data=data)


def _unmentioned(menu: MenuReading, workflow: str, table: JudgmentDefaults) -> list[str]:
    """The workflow's core data (`workflow_data` core) the words neither have nor lack; none after "only these"."""
    if menu.only_data:
        return []
    found = []
    for need in table.workflow_data[workflow][0]:
        if need == "two_layers":
            mentioned = "two_layers" in menu.data or len(set(menu.data) & table.omics_layers) >= 2
        else:
            mentioned = any(o in menu.data or o in menu.data_absent for o in need.split("|"))
        if not mentioned:
            found.append(need)
    return found


# --- the contract check pairs -------------------------------------------------------------------------------------------

def _sheet_quote(table: JudgmentDefaults, workflow: str | None, dimension: str, value: str) -> str:
    """The capability-sheet entry a stated value rules out for this workflow (or registry-wide), in its words."""
    for key, (name, ruled) in table.ruled_by.items():
        entry = sheet_entries().get(key)
        if entry is None or (name, ruled) != (dimension, value):
            continue
        if entry.workflow in (workflow, None):
            return entry.text + (f" {entry.why_not}" if entry.why_not else "")
    return ""


def _quote_of(slim: SlimReading, name: str) -> str:
    return next((f.quote for f in slim.stated if f.name == name and f.quote), "")


def check_pairs(slim: SlimReading, workflows) -> list[CheckPair]:
    """The user facts no code line covers, each with each workflow it bears on: a data form or B4 value off the menu
    with no sheet entry for that workflow, a stated-absent input it needs, an off-menu result, a requirement."""
    table, menu, pairs = judgment_defaults(), to_menu(slim), []
    sheet = sheet_entries()
    for workflow in workflows:
        entries = [e for e in sheet.values() if e.kind == "produces" and e.workflow == workflow]
        for name, said in menu.conditions.items():
            if said.known() == _OFF.get(name) and any(_ruled_out(table, name, e) for e in entries) \
                    and not _sheet_quote(table, workflow, name, said.value):
                pairs.append(CheckPair("C4", (said.quotes or [""])[0], workflow, f"{name}={said.value}"))
        for need in table.workflow_data.get(workflow, ((), ()))[1]:
            options = need.split("|")
            lacked = [f for f in slim.data if f.value == "lacks" and f.name in options]
            if lacked and all(o in menu.data_absent for o in options):
                pairs.append(CheckPair("C6", lacked[0].quote, workflow, f"needs {need}"))
        for item in slim.results:
            if item.said == "off_menu_result":
                pairs.append(CheckPair("C1", item.outside_name or item.quote, workflow, "off-menu result"))
        for fact in slim.stated:
            if fact.field == "D4":
                pairs.append(CheckPair("D4", fact.quote, workflow, "requirement"))
    return list(dict.fromkeys(pairs))[:18]


def check_text(task: str, pairs: list[CheckPair]) -> str:
    workflows = list(dict.fromkeys(pair.workflow for pair in pairs))
    contracts = "\n\n".join(workflow_contract(workflow) for workflow in workflows)
    numbered = "\n".join(f'p{n}. the user says "{pair.quote}" -- workflow {pair.workflow}'
                         for n, pair in enumerate(pairs, 1))
    return f"REQUEST:\n{task}\n\nCONTRACTS:\n{contracts}\n\nPAIRS:\n{numbered}"


def _clauses(pairs: list[CheckPair], payload) -> dict[CheckPair, str]:
    """The pairs whose verdict is contradicted with a clause verbatim in that workflow's contract."""
    from ..contract_text import normalized
    raw = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload or {})
    found = {}
    for n, pair in enumerate(pairs, 1):
        answer = raw.get(f"p{n}") or {}
        clause = str(answer.get("clause") or "")
        if answer.get("verdict") == "contradicted" and normalized(clause) \
                and normalized(clause) in normalized(workflow_contract(pair.workflow)):
            found[pair] = clause
    return found


def _addressed(pairs: list[CheckPair], payload) -> set[CheckPair]:
    raw = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload or {})
    return {pair for n, pair in enumerate(pairs, 1) if (raw.get(f"p{n}") or {}).get("verdict") == "met"}


# --- code-verified contract words ---------------------------------------------------------------------------------------

def _setting_line(workflow: str, control: str) -> str:
    return next((line[2:] for line in workflow_contract(workflow).splitlines()
                 if line.startswith(f"- setting {control} (")), "")


def _input_check(workflow: str, limit: str) -> str:
    """The contract's own words for a request-level count limit (`input_checks` scope request; the policy loader
    proves they are in the contract)."""
    from ..contract_text import check_limit, check_text as words
    from .menu_requirements import _policy
    spec = _policy().workflows[registered_workflows()[workflow]]
    return next((words(check) for check in spec.input_checks if check_limit(check).split(":")[0] == limit), "")


def _count_violations(workflow: str, menu: MenuReading) -> list[tuple[str, str, str]]:
    """(reason, contract words, user words) for each count limit the stated counts break."""
    limits = all_conditions().get(workflow)
    if limits is None:
        return []
    samples = menu.sample_count.value if menu.sample_count.status == "stated" else None
    features = menu.feature_count.value if menu.feature_count.status == "stated" else None
    found = []
    for limit, args, quotes in (
            ("min_samples", (dataclasses.replace(limits, relation=None, max_values=None), samples, None, None),
             menu.sample_count.quotes),
            ("relation", (dataclasses.replace(limits, min_samples=None, max_values=None), samples, None,
                          menu.single_feature_count), menu.feature_count.quotes or menu.sample_count.quotes),
            ("max_values", (dataclasses.replace(limits, min_samples=None, relation=None), samples, features, None),
             menu.feature_count.quotes)):
        if (problem := data_issue(*args)) and (words := _input_check(workflow, limit)):
            found.append((problem, words, (quotes or [""])[0]))
    return found


# --- the verdict --------------------------------------------------------------------------------------------------------

def _violations(slim: SlimReading, menu: MenuReading, workflow: str, task: str, clauses: dict[CheckPair, str],
                table: JudgmentDefaults) -> tuple[list[Violation], list[str]]:
    found, unverified = [], []
    for name, value in (("claims", menu.claims.known()), ("delivery", menu.delivery.known())):
        if value in table.dimensions[name].off_menu:
            words = _sheet_quote(table, None, name, value)
            quote = _quote_of(slim, name)
            if words and quote:
                found.append(Violation(workflow, "C2" if name == "claims" else "C3", f"{name}={value}", quote, words,
                                       "sheet"))
    if methods := _methods(menu, [workflow]):
        found.append(Violation(workflow, "C5", f"not a registered method: {', '.join(methods)}", methods[0],
                               "NetZoo registers: " + ", ".join(sorted(registered_workflows())) + ".", "registry"))
    for reason, words, quote in _count_violations(workflow, menu):
        found.append(Violation(workflow, "B6", reason, quote, words))
    limits = all_conditions().get(workflow)
    count_reason = data_issue(limits, menu.sample_count.value if menu.sample_count.status == "stated" else None,
                              menu.feature_count.value if menu.feature_count.status == "stated" else None,
                              menu.single_feature_count) if limits is not None else None
    gated = menu.model_copy(update={"unregistered_methods": _methods(menu, [workflow])})
    for reason in workflow_gate(gated, workflow, task, table).reasons:
        if reason.startswith("not a registered method") or reason == count_reason:
            continue  # said above, each with its own contract words
        violation = _gate_violation(slim, menu, workflow, reason, clauses, table)
        if violation is not None:
            found.append(violation)
        else:
            unverified.append(f"{workflow}: {reason}")
    for pair, clause in clauses.items():
        if pair.workflow == workflow and pair.kind in ("C1", "D4") and not any(v.user_quote == pair.quote
                                                                                for v in found):
            found.append(Violation(workflow, pair.kind, f'the contract contradicts "{pair.quote}"', pair.quote, clause))
    return found, unverified


def _methods(menu: MenuReading, workflows=()) -> list[str]:
    """Unregistered methods (C5) that are not settings: words naming one of these workflows' controls (a whole word),
    or read as a setting, are the setting's (read once; H1 debug: BONOBO's sparsify and save_pvals read as an
    unregistered method)."""
    controls = {name.casefold() for w in workflows if w in all_conditions() for name in all_conditions()[w].settings}
    settings = [_norm(s.quote) for s in menu.settings if s.quote]
    found = []
    for method in menu.unregistered_methods:
        words = _norm(method)
        if any(re.search(rf"(?<![\w]){re.escape(control)}(?![\w])", words) for control in controls) or any(
                words in quote or quote in words for quote in settings):
            continue
        found.append(method)
    return found


def _gate_violation(slim, menu, workflow, reason, clauses, table) -> Violation | None:
    """A `workflow_gate` reason with the user's and the contract's words, or None when the contract's words are
    missing (then it is reported as unverified, never a veto)."""
    if "=" in reason and reason.split("=")[0] in menu.conditions and " " not in reason.split("=")[0]:
        name, value = reason.split("=", 1)
        quote = (menu.conditions[name].quotes or [""])[0]
        words = _sheet_quote(table, workflow, name, value)
        if words:
            return Violation(workflow, "C4" if name in ("data_unit", "time_model", "spatial", "group_membership")
                             or name == "value_type" else "B4", reason, quote, words, "sheet")
        clause = next((c for p, c in clauses.items() if p.workflow == workflow and p.reason == reason), "")
        return Violation(workflow, "C4" if name != "mutation_origin" else "B4", reason, quote, clause) \
            if clause else None
    if reason.startswith("needs ") and "not available" in reason:
        need = reason.split()[1].rstrip(",")
        clause = next((c for p, c in clauses.items() if p.workflow == workflow and p.reason == f"needs {need}"), "")
        lacked = next((f.quote for f in slim.data if f.value == "lacks" and f.name in need.split("|")), "")
        quote = lacked or slim.only_quote
        return Violation(workflow, "C6", reason, quote, clause) if clause and quote else None
    if reason.startswith('the contract contradicts "'):
        quote = reason.split('"')[1]
        clause = next((c for p, c in clauses.items() if p.workflow == workflow and p.quote == quote), "")
        return Violation(workflow, "D4", reason, quote, clause) if clause else None
    controls = sorted(all_conditions()[workflow].settings) if workflow in all_conditions() else []
    named = [c for c in controls if c in reason]
    settings = [s for s in menu.settings if s.workflow in (workflow, "") and not s.unsure]
    if "has no setting for" in reason or "passes no settings" in reason:
        # The registry's controls are the contract: none takes it (the reason's own words, the user's cut off).
        quote = reason.split('"')[1] if '"' in reason else ""
        words = reason.split("; ", 1)[1] if "; " in reason else reason.split(", so ", 1)[0]
        return Violation(workflow, "C7", reason, quote, words, "registry") if quote else None
    if named:
        words = next((line for line in (_setting_line(workflow, c) for c in named) if line), "")  # one verbatim line
        quote = next((s.quote for s in settings if s.control in named), "")
        if words and quote:
            return Violation(workflow, "B5", reason, quote, words)
    return None


def _flip_questions(menu: MenuReading, workflow: str, task: str, table: JudgmentDefaults) -> list[VetoQuestion]:
    """An unsure value that makes the same workflow feasible or infeasible: one question (never a veto)."""
    found = []

    def infeasible(reading: MenuReading) -> bool:
        return bool(workflow_gate(reading, workflow, task, table).reasons or _count_violations(workflow, reading))

    for name, said in menu.conditions.items():
        if said.status in ("unsure", "conflicting") and len(said.values) > 1:
            bad = [v for v in said.values if infeasible(menu.model_copy(update={"conditions": {
                **menu.conditions, name: Said(status="stated", value=v, basis="answered", quotes=said.quotes)}}))]
            if bad and len(bad) < len(said.values):
                found.append(VetoQuestion(workflow, name, tuple(said.values), (said.quotes or [""])[0], tuple(bad)))
    for name in ("sample_count", "feature_count"):
        count: Count = getattr(menu, name)
        if count.status in ("unsure", "conflicting") and len(count.values) > 1:
            def probe(value):
                update = {name: Count(status="stated", value=value, quotes=count.quotes)}
                if name == "feature_count" and menu.features_one_type:
                    update["single_feature_count"] = value
                return menu.model_copy(update=update)
            bad = [str(v) for v in count.values if infeasible(probe(v))]
            if bad and len(bad) < len(count.values):
                found.append(VetoQuestion(workflow, name, tuple(map(str, count.values)), (count.quotes or [""])[0],
                                          tuple(bad)))
    for control, value in table.required_settings.get(workflow, {}).items():
        # A required declaration (BONOBO's log transform, centering) not given: asked, never assumed (user decision
        # 2026-10-19 (a)); declared otherwise, the gate refuses it with the setting's own line.
        if not any(s.control == control and s.workflow in (workflow, "") for s in menu.settings):
            other = "false" if value == "true" else "true"
            found.append(VetoQuestion(workflow, f"setting:{workflow}.{control}", (value, other), "", (other,),
                                      _setting_line(workflow, control)))
    for setting in menu.settings:
        if setting.unsure and len(setting.values) > 1 and setting.workflow in (workflow, ""):
            bad = [v for v in setting.values
                   if infeasible(_with_setting(menu, f"{workflow}.{setting.control}", v))]
            if bad and len(bad) < len(setting.values):
                found.append(VetoQuestion(workflow, f"setting:{workflow}.{setting.control}", tuple(setting.values),
                                          setting.quote, tuple(bad), _setting_line(workflow, setting.control)))
    return found


_CORE_LABEL = {"expression": "a gene expression table", "coexpression_matrix": "a gene co-expression matrix",
               "mutation_calls": "somatic mutation calls", "two_layers": "two omics layers measured on the same samples",
               "regulator_gene_network": "an existing regulator-to-gene network"}


def _core_data_question(menu: MenuReading, workflows: list[str], table: JudgmentDefaults) -> VetoQuestion | None:
    """The core data a chosen workflow cannot run without (`workflow_data` core), never mentioned -- neither had nor
    lacked, in words or file names (A3): asked once, in the same reply, never a veto (user decision 2026-10-19). Data
    the user says they lack is C6 (above); "only these" leaves nothing unmentioned."""
    needs: dict[str, list[str]] = {}
    for workflow in workflows:
        for need in _unmentioned(menu, workflow, table):
            needs.setdefault(need, []).append(workflow)
    if not needs:
        return None
    return VetoQuestion(workflow=", ".join(dict.fromkeys(w for ws in needs.values() for w in ws)),
                        dimension="data:" + "+".join(needs), values=("yes", "no"), quote="", infeasible=("no",),
                        contract_quote="; ".join(f"{', '.join(ws)} needs " + " or ".join(
                            _CORE_LABEL.get(o, o.replace("_", " ")) for o in need.split("|"))
                                                 for need, ws in needs.items()))


def _nearest(menu: MenuReading, vetoed: list[str], kept: list[str], task: str, table: JudgmentDefaults,
             global_veto: bool) -> list[str]:
    """Registered workflows giving a result a vetoed one gives that pass the same code checks (none after a veto that
    holds for every workflow: a claim, an outside action, an unregistered method)."""
    if global_veto or not vetoed:
        return []
    sheet = sheet_entries()
    results = {table.by_entry[k] for k, e in sheet.items() if e.kind == "produces" and e.workflow in vetoed}
    found = []
    for workflow in sorted(table.workflow_data):
        if workflow in vetoed or workflow in kept:
            continue
        gives = {table.by_entry[k] for k, e in sheet.items() if e.kind == "produces" and e.workflow == workflow}
        if gives & results - {"comparison"} and not workflow_gate(menu, workflow, task, table).reasons \
                and not _count_violations(workflow, menu):
            found.append(workflow)
    return found[:table.ask_max_options]


def contract_veto(slim: SlimReading, workflows, task: str = "", check_payload=None, pairs=(),
                  table: JudgmentDefaults | None = None) -> VetoVerdict:
    """The live system's chosen workflows judged against their contracts (hybrid spec 3)."""
    table = table or judgment_defaults()
    known = registered_workflows()
    workflows = [w for w in workflows if w in known]
    verdict = VetoVerdict(workflows=workflows)
    if slim.status == "failed" or not workflows:
        return verdict
    menu = to_menu(slim)
    pairs = list(pairs)
    clauses = _clauses(pairs, check_payload) if pairs else {}
    met = _addressed(pairs, check_payload) if pairs else set()
    for workflow in workflows:
        found, unverified = _violations(slim, menu, workflow, task, clauses, table)
        if found:
            verdict.violations[workflow] = found
        verdict.unverified += unverified
    for workflow in verdict.kept:
        verdict.questions += _flip_questions(menu, workflow, task, table)
    if verdict.kept and (core_data := _core_data_question(menu, verdict.kept, table)) is not None:
        verdict.questions.append(core_data)
    verdict.unconfirmed = list(dict.fromkeys(
        p.quote for p in pairs if p.kind == "D4" and p.workflow in verdict.kept and p not in met
        and p not in clauses))
    global_veto = any(v.kind in ("C2", "C3", "C5") for vs in verdict.violations.values() for v in vs)
    verdict.nearest = _nearest(menu, verdict.vetoed, verdict.kept, task, table, global_veto)
    verdict.disclosures = disclosures_for(menu, verdict.kept, table)
    verdict.to_confirm = confirm_items(menu, verdict.kept, task, table)
    return verdict


# --- the live call after the veto (hybrid spec 3, 4) ------------------------------------------------------------------

_SOURCE = {"contract": "contract", "sheet": "capability sheet", "registry": "registry"}


def violation_line(violation: Violation) -> str:
    """'NetZoo cannot run X for this: <reason>.' with the user's words and the contract's (spec 4, the English
    "cannot, because" template)."""
    from .menu_reply import _reason
    lines = [f"NetZoo cannot run {violation.workflow} for this: {_reason(violation.reason)}."]
    if violation.user_quote:
        lines.append(f'You wrote: "{violation.user_quote}".')
    lines.append(f'The {_SOURCE.get(violation.source, "contract")} says: "{violation.contract_quote}"')
    return " ".join(lines)


def _question(q: VetoQuestion) -> str:
    table = judgment_defaults()
    if q.dimension.startswith("setting:"):
        workflow, control = q.dimension.split(":", 1)[1].split(".", 1)
        if set(q.values) == {"true", "false"}:
            return f"For {workflow}: are your data {control.replace('_', ' ')}? (yes / no)"
        return f"Which value of {workflow}'s {control} applies: {' or '.join(q.values)}?"
    if q.dimension.startswith("data:"):
        needs = q.dimension.split(":", 1)[1].split("+")
        labels = [" or ".join(_CORE_LABEL.get(o, o.replace("_", " ")) for o in need.split("|")) for need in needs]
        return (f"Do you have {labels[0]} ({q.workflow} cannot run without it)?" if len(labels) == 1 else
                f"Which of these do you have: {'; '.join(labels)}? ({q.workflow} cannot run without them.)")
    if q.dimension in ("sample_count", "feature_count"):
        return f"How many {'samples' if q.dimension == 'sample_count' else 'features'} are there: {' or '.join(q.values)}?"
    options = table.dimensions[q.dimension].options if q.dimension in table.dimensions else {}
    return "Which applies: " + " or ".join(options.get(v, v.replace("_", " ")) for v in q.values) + "?"


def vetoed_core(core, verdict: VetoVerdict):
    """The live DO after the veto; anything else is returned as it came (only a DO is ever changed)."""
    from ..contracts.core_decision import CoreDecision, DeclinedPart, FactQuestion
    if core.kind != "DO" or not verdict.workflows:
        return core
    evidence = {**core.evidence, "contract_veto": {
        "judged": verdict.workflows, "vetoed": {w: [dataclasses.asdict(v) for v in verdict.violations[w]]
                                                for w in verdict.vetoed},
        "questions": [dataclasses.asdict(q) for q in verdict.questions], "unverified": verdict.unverified,
        "unconfirmed": verdict.unconfirmed, "disclosures": verdict.disclosures, "to_confirm": verdict.to_confirm,
        "nearest": verdict.nearest}}
    parts = [DeclinedPart(quote=v.user_quote, reasons=[v.reason], alternatives=verdict.nearest, line=violation_line(v))
             for w in verdict.vetoed for v in verdict.violations[w]]
    if not verdict.kept:
        return CoreDecision(kind="DECLINE", basis="contract_veto", workflows=verdict.vetoed, declined=parts,
                            evidence=evidence)
    if verdict.questions:
        facts = [FactQuestion(question=_question(q), user_quote=q.quote, workflows=[q.workflow],
                              contract_quote=q.contract_quote) for q in verdict.questions]
        return CoreDecision(kind="ASK", basis="contract_veto_fact", workflows=verdict.kept, facts=facts,
                            declined=[*core.declined, *parts], evidence=evidence)
    return core.model_copy(update={"workflows": verdict.kept, "declined": [*core.declined, *parts],
                                   "run_allowed": core.run_allowed and not parts, "evidence": evidence})


def veto_notes(core) -> str:
    """For a DO the veto passed: the disclosure lines, the must-confirm choices to settle before running, and the
    requirements no contract addresses (spec 4) -- code's words only."""
    found = (core.evidence or {}).get("contract_veto") or {} if core is not None and core.kind == "DO" else {}
    lines = []
    if found.get("disclosures"):
        lines += ["Good to know before running:", *(f"- {line}" for line in found["disclosures"])]
    if found.get("to_confirm"):
        lines += ["Before anything runs, please confirm:", *(f"- {item}" for item in found["to_confirm"])]
    if found.get("unconfirmed"):
        lines += ["Not covered by the contract, so it cannot be guaranteed:",
                  *(f'- "{quote}"' for quote in found["unconfirmed"])]
    return "\n".join(lines)


def with_veto_notes(result: dict, state, reply) -> dict:
    """`respond()`'s last step: a DO the contract veto passed gains its disclosure and confirmation lines (code's
    words only); nothing changes when the veto did not run."""
    from ..contracts import TaskDecision

    notes = veto_notes(TaskDecision.model_validate(state["decision"]).core) if state.get("decision") else ""
    if not notes or not result.get("messages"):
        return result
    return reply(f"{result['messages'][-1].content}\n\n{notes}", result.get("reply_kind") or "")
