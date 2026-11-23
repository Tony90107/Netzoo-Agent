"""Lean decider (2026-11-20): one model call with a nine-field form, then rules taken from the contracts (R0-R7).

Why: on the sealed six-tool bank (local evaluation data), the full routing stack (about ten model calls, ~91 typed
values per request, Jev checks) scored 68/120 against 73/120 for one plain model call (B1), and lost mainly by holding
back on doable requests (28 items: conceptual questions answered with "which result do you want", needless "did you
mean" / overlap questions). Here the model decides once; code only applies rules the workflow contracts state:

R0  Preparation steps (the registry marks them "a preparation step") run first; the rest keep their order.
R1  (other way, 2026-11-22) A DO or EXPLAIN whose request states the user's own doubt about this run (`doubt_before_run`)
    becomes a code-written question quoting it.
R1  A question needs the user's own doubt: ASK stands only when `unsure_quote` is found in the request, or code finds
    words of doubt in it (`stated_doubt`, 2026-11-21: F036's form left unsure_quote empty). (Tried and
    withdrawn 2026-11-20: keeping the question when the steps are not one contract chain. Replayed on the saved forms
    it lost F063 x3 and D007 -- "either matrix is fine" -- and fixed nothing; PANDA -> CONDOR is itself a handoff.)
    In a follow-up ("Previous NetZoo goal: ...\nUser follow-up: ..."), the doubt must be in the follow-up: the earlier
    doubt is what the question already asked about.
R2  Sample minimums (workflow_conditions.min_samples), when the request states the count in words found in it.
R3  SPONGE's own limits (prior_request.sponge_blockers, the non-human check of execution_sponge). An unstated organism
    is asked about, also when SPONGE is the only step (2026-11-23, user: the organism decides whether the priors are
    usable, so it must come from the user; this withdraws the 2026-11-22 exemption that let priors-only requests
    default to human, which the large blind bank had labelled do and the R15b blind bank labels ask).
R4  PORCUPINE reads sample-specific networks: an aggregate-only producer before it becomes its per-sample version
    (the workflow whose guidance_predecessors name it and whose handoff_targets include run_porcupine).

R5  A setting the request gives (words found in it) that the workflow's contract does not allow (setting_issue) stops
    the run; words naming no allowed choice are asked about, unless the request names that value word for word
    (2026-11-22, D002 "Kendall's tau"): then it is refused with the contract's list of allowed values.
R6  (2026-11-20, user: the model must not see the correspondence, or it forces a request onto a workflow) A second
    call reads the request blind -- it never sees the workflows -- and lists its parts; for each result asked for it
    picks the same result from the capability sheet's closed list of result texts (`_menu`: produces, near misses,
    registry-wide, preparation steps; who gives them is not shown). Code then looks the pick up: a result whose
    words are found in the request and that no workflow in scope gives directly (with_step counts as not given) stops
    the run. "None of these" stops nothing (settings and loose phrases land there: formal F114 "edge weights on the
    0-1 scale", F005 "needs a regulatory network"), nor do words naming one of the six ("run PANDA" read as OTTER's
    look-alike result: F006, X027). Replayed on every saved reading: 19 stops on gold dont, 0 on do/ask (the first
    version: 22 and 6). The refusal names the user's words, never a reason: the pick is the model's reading.
R7  Six-package scope: a DO with NORMALIZE-EXPRESSION whose request names a method other than SNAIL is refused.
R8  (2026-11-21; advisor 2026-11-11) SNAIL takes raw counts: a DO with NORMALIZE-EXPRESSION whose request calls the
    expression TPM, FPKM, CPM, log values or microarray intensities, and states raw counts nowhere, is refused
    when the request asks for a normalization (`normalization_asked`); when it does not, the model added SNAIL on
    its own and the step is dropped (F085). `non_count_scale`: clauses with a negation count neither way.
R11 (2026-11-22, scorpion.yaml) A network for each individual cell is refused with a code reason: SCORPION builds
    one network per group of cells, and nothing in scope builds one per cell (L163).
R9  (2026-11-21, scorpion.yaml) A SCORPION comparison needs two built networks on each side: a DO with SCORPION whose
    request asks for a comparison from one stated patient or donor, naming no replicate or other grouping, is
    refused (`single_source_comparison`). R8, R9 and R10 give code-written reasons.
R10 (2026-11-21, output_capability.incompatible_input_artifacts) The first step's contract refuses an input the
    request says the user already has (F080: computed co-expression networks for PORCUPINE).
R15 (2026-11-23, flag NETZOO_LEAN_CONDITION_CHECK, off) A DO whose request leaves a condition of the plan's contracts
    unstated (priors, GMT, sample count, raw counts...) becomes a question: code lists the conditions, Jev only says
    whether the request states each one (`required_conditions`).

Scope (2026-11-20, user: let it see only the six): the decider sees only PANDA, LIONESS-PANDA, SCORPION, PORCUPINE, SPONGE and
SNAIL (NORMALIZE-EXPRESSION, method snail), and their settings. NETZOO_LEAN_SCOPE=all shows every registered workflow;
NETZOO_LEAN_RESULT_CHECK=off skips R6's call.

EXPLAIN (2026-11-20, user: the model answers from the algorithms of the packages it has read): a question about how a method works, what it
needs or gives, how methods differ or how to proceed gets an answer written by a second call that sees only the
contracts and integration docs of the workflows it is about (`explain_context`). A DO lists the settings the request
gave and every default used, and what the files will be checked for before a run (`plan_notes`).

The tool descriptions are the system's own registry text (graph.jev_guard_call.registry_text) plus each workflow's
input checks from workflows/*.yaml. Nothing here runs anything: the result is a decision for the planner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

__all__ = ["SIX", "LeanDecision", "apply_rules", "decide", "explain_context", "instructions", "latest_words",
           "plan_notes", "prep_steps", "response_format", "result_check", "scope", "tool_names", "tools_text",
           "wanted_format", "wanted_instructions"]

ROOT = Path(__file__).resolve().parents[3]
SYSTEM_NAME = {"SPONGE": "SPONGE-PRIORS"}
SIX = ("PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE", "SPONGE", "NORMALIZE-EXPRESSION")
"""The thesis scope (advisor, 2026-11-14), by registry name; SNAIL is NORMALIZE-EXPRESSION with method snail."""


def scope() -> str:
    """Which workflows the decider sees: "six" (default, 2026-11-20 user: let it see only the six) or "all" registered
    workflows, from NETZOO_LEAN_SCOPE."""
    import os

    return "all" if os.environ.get("NETZOO_LEAN_SCOPE", "").strip().lower() == "all" else "six"


def result_check() -> bool:
    """R6's blind reading call runs unless NETZOO_LEAN_RESULT_CHECK=off."""
    import os

    return os.environ.get("NETZOO_LEAN_RESULT_CHECK", "").strip().lower() not in ("off", "0", "false")


@lru_cache(maxsize=1)
def _specs() -> dict[str, dict]:
    return {spec["workflow"]: spec for spec in (yaml.safe_load(path.read_text()) for path in
                                                sorted((ROOT / "workflows").glob("*.yaml")))}


def _line_name(line: str) -> str:
    return line[2:].split(":")[0].split(" ")[0]


def _six_readers(actions) -> str:
    from workflow_registry import ACTION_DEFINITIONS

    return ", ".join(sorted(name for name in (ACTION_DEFINITIONS[action].workflow for action in actions) if name in SIX))


def _six_preparation_line(name: str, line: str) -> str:
    """A preparation step's registry line inside the six-package scope: only the six read its output, and
    normalization is SNAIL only (the other methods are outside the scope)."""
    from workflow_registry import ACTION_DEFINITIONS

    from ..graph.jev_guard_call import _defaults, _workflow_names
    from ..normalization_request import CHAINABLE_ACTIONS, METHOD_OPTION_LINES
    from ..prior_request import PRIOR_CONSUMERS

    if name == "SPONGE":
        return line.replace(f"inputs that {_workflow_names(PRIOR_CONSUMERS)} read",
                            f"inputs that {_six_readers(PRIOR_CONSUMERS)} read")
    normalize = ACTION_DEFINITIONS["normalize_expression"]
    return ("- NORMALIZE-EXPRESSION (SNAIL; a preparation step, not a network workflow): normalizes an expression matrix "
            f"between samples -- {METHOD_OPTION_LINES['snail']}. It writes a normalized expression matrix that "
            f"{_six_readers(CHAINABLE_ACTIONS)} can then read. Required inputs: {', '.join(normalize.required_inputs)}. "
            "Controls: normalization_method snail; "
            f"{_defaults('normalize_expression', skip=('normalization_method', 'gene_lengths_file'))}.")


def tools_text() -> str:
    """The registry line of every workflow and preparation step in `scope()`, each followed by its contract's input
    checks."""
    return _tools_text(scope())


@lru_cache(maxsize=2)
def _tools_text(which: str) -> str:
    from ..graph.jev_guard_call import registry_text

    lines = []
    for line in registry_text().split("\n"):
        name = _line_name(line)
        if which == "six":
            if name not in SIX:
                continue
            if name in ("SPONGE", "NORMALIZE-EXPRESSION"):
                line = _six_preparation_line(name, line)
            elif optional := [item for item in _specs().get(name, {}).get("optional_inputs") or []
                              if item.endswith("_file")]:  # PANDA's coexpression_file, SCORPION's cell metadata
                line = line.replace(" Controls:", f" Optional inputs: {', '.join(optional)}. Controls:", 1)
        checks = [item["text"] for item in (_specs().get(name, {}).get("input_checks") or [])]
        lines.append(line + (f" Checks: {' '.join(checks)}" if checks else ""))
    return "\n".join(lines)


def tool_names() -> tuple[str, ...]:
    return tuple(_line_name(line) for line in tools_text().split("\n"))


def instructions() -> str:
    return (
        "Return the handling of the researcher's request as the JSON object described below, using only the "
        "registered workflows and preparation steps listed after it.\n"
        "- steps: the workflows and steps that give what the request asks for, in run order (preparation steps "
        "first). For a question about how to do something or what a method does, the ones the answer is about. "
        "Empty only when none of them gives it.\n"
        "- decision: DO when the request asks for the steps' results to be produced; EXPLAIN when it asks how "
        "something works, what a method needs or gives, how methods differ or how to proceed, without asking for "
        "anything to be run now; ASK when something the user says they do not know or have not decided changes which "
        "steps fit or whether they can run; DECLINE when none of the steps gives what is asked, or a fact the user "
        "states breaks a stated requirement of the steps.\n"
        "- settings: each setting of a listed workflow that the request gives, as WORKFLOW.setting with the words "
        "giving its value and the exact words naming it; empty when it gives none.\n"
        "- unsure_quote: the user's exact words saying they do not know or have not decided something; empty when "
        "there are none.\n"
        "- question: for ASK, the one question to ask; otherwise empty.\n"
        "- decline_quote: for DECLINE, the exact words of the request that cannot be met; otherwise empty.\n"
        "- sample_count: the number of samples, patients or profiles the request states; null when it states none. "
        "sample_count_quote: the exact words stating it; empty when null.\n"
        "- reply: what you tell the user: what will be run, the question, or why it cannot be done.\n\n"
        "Registered workflows and steps:\n" + tools_text())


def prep_steps() -> frozenset[str]:
    """The preparation steps, by the names apply_rules uses (the registry line says "a preparation step")."""
    names = {_line_name(line) for line in tools_text().split("\n") if "a preparation step" in line}
    return frozenset(SYSTEM_NAME.get(name, name) for name in names)


def _setting_names() -> list[str]:
    from ..method_names import UNREGISTERED, setting_names

    names = setting_names(True)
    if scope() == "six":
        names = tuple(name for name in names if name.split(".", 1)[0] in SIX)
    return [*names, UNREGISTERED]


WANTED_ROLES = ("result", "purpose", "data", "other")


@lru_cache(maxsize=2)
def _menu(which: str) -> tuple[tuple[str, str, frozenset[str]], ...]:
    """R6's closed list of result kinds: every capability-sheet result text (produces, near misses, registry-wide,
    the preparation steps), each once, in alphabetical order under a neutral key, with the workflows in `which` scope
    that give it directly (system names). A with_step result is given by none (2026-11-20, user: a result NetZoo
    leaves to a step outside it counts as not produced). The reader sees the texts only, never who gives them."""
    from workflow_registry import ACTION_DEFINITIONS

    from ..capability_sheet import lean_entries, sheet_entries

    givers: dict[str, set[str]] = {}
    for item in [*sheet_entries().values(), *lean_entries().values()]:
        given = givers.setdefault(item.text, set())
        # A near miss of one workflow that the sheet says another gives instead ("One network per sample." from OTTER
        # is LIONESS-PANDA's) is given by that one.
        workflow = item.workflow if item.kind == "produces" and item.level == "direct" else (
            ACTION_DEFINITIONS[item.instead_registered].workflow if item.instead_registered else None)
        if workflow and (which == "all" or workflow in SIX):
            given.add(SYSTEM_NAME.get(workflow, workflow))
    import hashlib

    texts = sorted(givers, key=lambda text: (text.casefold(), text))
    # The key is the text's own hash, so a saved reading still means the same result after the sheet changes.
    return tuple((f"K{hashlib.sha1(text.encode()).hexdigest()[:6]}", text, frozenset(givers[text])) for text in texts)


def _signature(entry) -> tuple:
    return (entry.granularity, entry.regulators, entry.signed, entry.layers, entry.groups, entry.input_network,
            entry.family, entry.data_units)


def _covered(quote: str, phrase: str) -> bool:
    """At least 80% of the phrase's words, in order, inside the quote (2026-11-23: the loose 60% match let SCORPION's
    "single-cell regulatory network" cover "that cell's own TF-to-gene regulatory network", A057)."""
    from difflib import SequenceMatcher

    wanted, words = _units(phrase), _units(quote)
    matched = sum(b.size for b in SequenceMatcher(None, words, wanted, autojunk=False).get_matching_blocks())
    return matched >= 0.8 * len(wanted)


def _group_difference_without_groups(key: str, quote: str, steps: list[str]) -> bool:
    """R6 (2026-11-23): the reader picked a planned step's own near miss about predefined groups (PORCUPINE: "Pathways
    differentially expressed or enriched between predefined groups") for words that name no two groups -- "pathways
    whose regulation varies across patients" is PORCUPINE's heterogeneity across individuals, not a group difference
    (L024, A053, A079, A127, A130, A143). A quote that names two sides ("between responders and non-responders") still
    stops."""
    from ..capability_sheet import sheet_entries

    texts = {k: text for k, text, _ in _menu(scope())}
    near = [e for e in sheet_entries().values() if e.text == texts.get(key) and e.kind == "near_miss"
            and SYSTEM_NAME.get(e.workflow, e.workflow) in steps and "groups" in e.text.casefold()]
    return bool(near) and not _COMPARE.search(quote)


def _own_phrase(quote: str, steps: list[str]) -> str:
    """A planned step's own selection phrase (workflows/*.yaml output_capability.selection_phrases) that the quote says
    (2026-11-22, L024: "the pathways whose regulation varies across patients" is PORCUPINE's "pathways that vary across
    patients"). The reader picked another result for words the contract itself uses for this step."""
    for step in steps:
        for phrase in ((_specs().get(step) or {}).get("output_capability") or {}).get("selection_phrases") or []:
            if len(_units(phrase)) >= 3 and _covered(quote, phrase):
                return phrase
    return ""


def _names_outside_method(task: str) -> list[str]:
    """Registered methods outside the six that the request names (registry spelling, `method_names.workflows_in`).
    When the user names OTTER, a PANDA network of the same type is not what they asked for (Gemini review, round 5):
    R6's same-type exemption does not apply."""
    from ..method_names import workflows_in

    return [name for name in workflows_in(task) if name not in SIX and name != "LIONESS"]


def _same_kind_given(key: str, steps: list[str]) -> bool:
    """R6 (2026-11-21, blind bank B013): the picked result has the same typed fields on the capability sheet
    (granularity, regulators, signed, layers, groups, input network, family, data unit) as a result a planned step
    gives directly; it differs only in the method's own wording ("fitted so that it agrees with the PPI network" is
    OTTER's aggregate TF-gene network, PANDA's has the same fields). Entries without a family are never matched.
    Replayed on every saved reading: removes B013's false stop, keeps all 24 stops on gold dont."""
    from ..capability_sheet import lean_entries, sheet_entries

    texts = {k: text for k, text, _ in _menu(scope())}
    entries = [*sheet_entries().values(), *lean_entries().values()]
    picked = [e for e in entries if e.text == texts.get(key) and e.family]
    planned = [e for e in entries if e.kind == "produces" and e.level == "direct"
               and SYSTEM_NAME.get(e.workflow, e.workflow) in steps]
    # The data unit follows the user's data, not the result (L086: SCORPION's one network for all nuclei).
    return any(_signature(p)[:-1] == _signature(m)[:-1] for p in picked for m in planned)


_NAMED_IN_SCOPE = __import__("re").compile(
    r"(?<![\w-])(?:LIONESS-PANDA|PANDA|LIONESS|SCORPION|PORCUPINE|SPONGE|(?:py)?SNAIL)(?![\w-])"
    r"|smooth[- _]?quantile|qsmooth", __import__("re").I)  # SNAIL's method by name (L149: read as batch removal)


def wanted_instructions() -> str:
    """The blind reading (R6): the request's parts and, for each result asked for, its kind from the closed list."""
    return (
        "List the parts of the researcher's request as the JSON object described below, from the request's own words "
        "only.\n"
        "- items: one entry per part of the request.\n"
        "  - quote: the request's exact words for that part.\n"
        "  - role: result when the part asks for something to be produced or delivered; purpose when it says why the "
        "researcher wants it or what they will do with it afterwards; data when it describes what they have; other "
        "otherwise.\n"
        "  - kind: for a result, the key of the result kind below that is that same result; none when no kind below "
        "is that result. For any other role, none.\n\n"
        "Result kinds:\n" + "\n".join(f"{key}: {text}" for key, text, _ in _menu(scope())))


def wanted_format() -> dict:
    keys = [key for key, _, _ in _menu(scope())] + ["none"]
    return {"type": "json_schema", "json_schema": {"name": "LeanWanted", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["items"],
        "properties": {"items": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["quote", "role", "kind"],
            "properties": {"quote": {"type": "string"}, "role": {"type": "string", "enum": list(WANTED_ROLES)},
                           "kind": {"type": "string", "enum": keys}}}}}}}}


def response_format() -> dict:
    return {"type": "json_schema", "json_schema": {"name": "LeanHandling", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["steps", "decision", "unsure_quote", "question", "decline_quote", "settings", "sample_count",
                     "sample_count_quote", "reply"],
        "properties": {
            "steps": {"type": "array", "items": {"type": "string", "enum": list(tool_names())}},
            "decision": {"type": "string", "enum": ["DO", "EXPLAIN", "ASK", "DECLINE"]},
            "settings": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["setting", "value", "quote"],
                "properties": {"setting": {"type": "string", "enum": _setting_names()},
                               "value": {"type": "string"}, "quote": {"type": "string"}}}},
            "unsure_quote": {"type": "string"}, "question": {"type": "string"},
            "decline_quote": {"type": "string"},
            "sample_count": {"type": ["integer", "null"]}, "sample_count_quote": {"type": "string"},
            "reply": {"type": "string"}}}}}


@dataclass
class LeanDecision:
    kind: str
    steps: list[str]
    question: str = ""
    reply: str = ""
    rules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    """For a DO: the settings the request gave, every default used, and what the files are checked for."""
    calls: list[dict] = field(default_factory=list)
    """Each model call: model, input_tokens, output_tokens, cost_usd, duration_ms (for the app's usage record)."""
    decline_quote: str = ""
    """R6: the request's words for the result no workflow in scope gives (the refusal names them, never a reason)."""

    def as_dict(self) -> dict:
        return {"kind": self.kind, "workflows": self.steps, "question": self.question, "reply": self.reply,
                "rules": self.rules, "notes": self.notes}


from .request_facts import (  # noqa: E402,F401 - re-exported: the rules below and callers use these names
    _CJK,
    _units,
    _found,
    _stated_value,
    _stated,
    _per_sample_version,
    _RE,
    _CLAUSE,
    _NEGATION,
    _NON_COUNT,
    _RAW_COUNTS,
    _OTHER_DATA,
    _clauses,
    non_count_scale,
    _ASK_NORMALIZE,
    _DONE,
    normalization_asked,
    _ARTIFACT_WORDS,
    _ACCEPTED_WORDS,
    _HAS,
    _WANTS,
    held_incompatible_input,
    _COMPARE,
    _PER_CELL,
    _INDIVIDUAL,
    _SINGLE,
    _REPLICATED,
    _NO_REPLICATE,
    _MANY_INDIVIDUALS,
    _THREE_PLUS_UNITS,
    _ONE_PER_SIDE,
    single_source_comparison,
    _DOUBT,
    stated_doubt,
    _PRIORS_HELD,
    _BUILD_WORDS,
    _HOLD,
    priors_on_hand,
    _LATER,
    doubt_before_run,
    _PER_CELL_NETWORK,
    per_cell_networks,
    _PER_SAMPLE,
    _NAMED_SCORPION,
    _NAMED_BULK_TOOL,
    data_unit_label,
    _data_unit_swap,
    _EXPRESSION_HELD,
    _NETWORKS_HELD,
    expression_without_networks,
    _GONE,
    _EXPRESSION_WORDS,
    expression_gone,
    _FEW_CELLS,
    _NEGATIVE_VALUES,
    scorpion_input_broken,
    FOLLOW_UP,
    latest_words,
)

def apply_rules(task: str, raw: dict) -> LeanDecision:
    """The model's handling with the contracts' rules applied (R0-R9 in the module docstring)."""
    from ..prior_request import _NON_HUMAN, sponge_blockers
    from ..workflow_conditions import conditions_for

    steps = list(dict.fromkeys(SYSTEM_NAME.get(name, name) for name in raw.get("steps") or []))
    kind, question, reply, rules = raw.get("decision", "ASK"), raw.get("question", ""), raw.get("reply", ""), []

    ordered = sorted(steps, key=lambda name: name not in prep_steps())  # R0 (sorted is stable)
    if ordered != steps:
        steps = ordered
        rules.append("R0: preparation steps run first")

    swapped = _data_unit_swap(task, steps)  # R12
    if swapped != steps:
        rules.append(f"R12: the request's data unit is {data_unit_label(task)}, so {steps} became {swapped}")
        steps = swapped

    if steps and steps[0] == "PORCUPINE" and expression_without_networks(task):  # R4, first step
        from ..routing.data_unit import data_unit_of

        builder = "SCORPION" if data_unit_of(task) == "single_cells" else "LIONESS-PANDA"
        steps = [builder, *steps]
        rules.append(f"R4: PORCUPINE reads sample-specific networks and the request has expression, so {builder} first")

    for index, name in enumerate(steps):  # R4
        if name == "PORCUPINE" and index > 0:
            before = steps[index - 1]
            spec = (_specs().get(before) or {}).get("output_capability") or {}
            if "run_porcupine" not in (spec.get("handoff_targets") or []) and (swap := _per_sample_version(before)):
                steps[index - 1] = swap
                rules.append(f"R4: PORCUPINE reads per-sample networks, so {before} became {swap}")

    if (kind == "ASK" and steps and not _found(latest_words(task), raw.get("unsure_quote", ""))
            and not stated_doubt(task)):  # R1
        kind, question = "DO", ""
        rules.append("R1: no doubt stated by the user, so no question")

    if kind == "DO" and (per_cell := per_cell_networks(task)):  # R11 (before R2/R3's questions: A173)
        kind, question = "DECLINE", ""
        reply = (f'"{per_cell}": SCORPION builds one network per group of cells (at least min_cells of them), never one '
                 "per cell, and no other workflow in scope builds networks for single cells.")
        rules.append(f"R11: one network per cell ({per_cell})")

    if kind == "DO" and (gone := expression_gone(task)) and any(
            name in steps for name in ("PANDA", "LIONESS-PANDA", "SCORPION", "NORMALIZE-EXPRESSION")):  # R13
        kind, question = "DECLINE", ""
        reply = (f'Every network workflow in scope reads a gene-by-sample (or gene-by-cell) expression matrix, none of them '
                 f'makes one, and the request says "{gone}".')
        rules.append(f"R13: the expression data are stated gone ({gone})")

    if kind == "DO" and "SCORPION" in steps and (broken := scorpion_input_broken(task)):  # R14
        kind, question = "DECLINE", ""
        reply = broken[1]
        rules.append(f"R14: SCORPION input condition ({broken[0]})")

    count = raw.get("sample_count")
    if (kind == "DO" and isinstance(count, int) and _found(task, raw.get("sample_count_quote", ""))
            and _stated(task, count)):  # R2: the words and the number itself are in the request
        for name in steps:
            limits = conditions_for(name)
            if limits and limits.min_samples and count < limits.min_samples:
                if stated_doubt(task):  # 2026-11-22: the user doubts the count, so it is asked, not refused
                    kind = "ASK"
                    question = reply = (f"{name} needs at least {limits.min_samples} samples. How many usable "
                                        "samples do you have?")
                    rules.append(f"R2: {name} minimum {limits.min_samples}, count {count} doubted by the user")
                    break
                kind, question = "DECLINE", ""
                reply = f"{name} needs at least {limits.min_samples} samples; the request has {count}."
                rules.append(f"R2: {name} minimum {limits.min_samples} samples, request states {count}")
                break

    if kind == "DO" and "SPONGE-PRIORS" in steps and len(steps) > 1 and priors_on_hand(task):
        from ..prior_request import prior_requested  # 2026-11-22 (L046): the user has priors and asked to build none

        if not prior_requested(task) and not _BUILD_WORDS.search(task):
            steps = [name for name in steps if name != "SPONGE-PRIORS"]
            rules.append("R3: SPONGE not asked for and the request has its own priors, so the step was dropped")
    if kind == "DO" and "SPONGE-PRIORS" in steps:  # R3
        blockers = sponge_blockers(task)  # an unstated organism is asked about, priors-only too (2026-11-23)
        if (non_human := _NON_HUMAN.search(task)):
            blockers.append(f"SPONGE builds human priors only (hg38, hg19 or T2T-CHM13); the request names "
                            f"{non_human.group(0)}")
        stops = [b for b in blockers if "say which one" not in b and "say whether they are human" not in b]
        from ..prior_request import prior_requested

        if stops and non_human and not prior_requested(task) and not _BUILD_WORDS.search(task) \
                and not priors_on_hand(task) and len(steps) > 1:  # 2026-11-23 (A064): can't build, may have them
            organism = non_human.group(0)
            kind = "ASK"
            question = reply = (f"SPONGE builds human priors only, so it cannot make {organism} priors. Do you have "
                                f"{organism} motif and PPI prior files?")
            rules.append("R3: non-human data and no priors stated, so asked for the user's own priors")
            stops = []
            blockers = []
        if stops:
            kind, question, reply = "DECLINE", "", stops[0]
            rules.append("R3: SPONGE limit stated in the request")
        elif blockers:
            kind, question, reply = "ASK", blockers[0], blockers[0]
            rules.append("R3: SPONGE needs an answer first")

    stated = [item for item in raw.get("settings") or [] if _found(task, item.get("quote", ""))]
    if kind == "DO":  # R5
        for item in stated:
            workflow = item["setting"].split(".", 1)[0]
            limits = conditions_for(workflow) if workflow in steps else None
            if limits is None:
                continue
            from ..workflow_conditions import UNCLEAR_CHOICE, StatedSetting, setting_issue

            issue = setting_issue(limits, StatedSetting(name=item["setting"], quote=item["quote"],
                                                        value=item.get("value", "")))
            value = (item.get("value") or "").strip()
            if issue and issue.endswith(UNCLEAR_CHOICE) and value and _RE.search(
                    rf"(?<![A-Za-z]){_RE.escape(value)}(?![A-Za-z])", task, _RE.I):
                # 2026-11-22 (D002): the request names the value itself ("Kendall's tau") and it is not an allowed
                # choice: a refusal with the contract's list, not a question about what was meant.
                kind, question = "DECLINE", ""
                reply = f'{issue.split(";")[0]}; the request asks for "{value}".'
                rules.append(f"R5: {item['setting']} value {value} named and not allowed by the contract")
                break
            if issue and issue.endswith(UNCLEAR_CHOICE):
                kind, question, reply = "ASK", issue + ".", issue + "."
                rules.append(f"R5: {item['setting']} value unclear")
                break
            if issue and (_found(task, item.get("value", "")) or _stated_value(task, item.get("value", ""))):
                kind, question, reply = "DECLINE", "", issue + "."
                rules.append(f"R5: {item['setting']} not allowed by the contract")
                break

    if kind == "DO" and scope() == "six" and "NORMALIZE-EXPRESSION" in steps:  # R7
        from ..normalization_request import METHOD_LABELS, method_named

        method = method_named(task)
        if method and method != "snail":
            kind, question = "DECLINE", ""
            reply = (f"In the six-package scope NetZoo normalizes with SNAIL only; the request names "
                     f"{METHOD_LABELS[method]}.")
            rules.append(f"R7: normalization {method} is outside the six-package scope")

    if kind == "DO" and "NORMALIZE-EXPRESSION" in steps and (scale := non_count_scale(task)):  # R8
        if normalization_asked(task):
            kind, question = "DECLINE", ""
            reply = (f"SNAIL normalizes raw read counts only; the request states \"{scale}\" and no raw counts. "
                     "With the raw count matrix, SNAIL can run.")
            rules.append(f"R8: SNAIL needs raw counts, request states {scale}")
        else:  # the model added SNAIL on its own to expression that is not counts (F085: TPM, log, batch-corrected)
            steps = [name for name in steps if name != "NORMALIZE-EXPRESSION"]
            rules.append(f"R8: SNAIL not asked for and needs raw counts ({scale}), so the step was dropped")

    if kind == "DO" and "SCORPION" in steps and (single := single_source_comparison(task)) and stated_doubt(task):
        kind = "ASK"  # R9 under the user's own doubt (L111 "might be a single donor, but I'm not sure"): asked
        question = reply = ("A SCORPION comparison needs at least two built networks on each side. How many donors "
                            "(or other replicates) does each side have?")
        rules.append(f"R9: one network per side ({single}) doubted by the user")
    if kind == "DO" and "SCORPION" in steps and (single := single_source_comparison(task)):  # R9
        kind, question = "DECLINE", ""
        reply = (f"A SCORPION comparison needs at least two built networks on each side; with \"{single}\" and no "
                 "replicate column, each side gives one network. A replicate column such as the donor, with two or "
                 "more per side, makes the comparison possible.")
        rules.append(f"R9: SCORPION comparison with one network per side ({single})")

    if kind == "DO" and steps and steps[0] not in prep_steps():  # R10: the first step reads the user's input
        label, quote = held_incompatible_input(task, steps[0])
        if label:
            kind, question = "DECLINE", ""
            reply = f'{steps[0]} does not take {label} as input, and the request has "{quote}".'
            rules.append(f"R10: {steps[0]} input {label} is incompatible ({quote})")

    if (kind in ("DO", "EXPLAIN") and steps or kind == "DECLINE" and not rules and raw.get("decision") == "DECLINE") \
            and (doubt := doubt_before_run(task)):  # R1 the other way (a model refusal too: A120), after the contract rules
        # (their own question, e.g. R9's donors per side, is more specific)
        kind, question = "ASK", f'You wrote that you are not sure: "{doubt}". Which is it? Nothing runs until then.'
        reply = question
        rules.append("R1: the user's own doubt about this run, so a question first")

    decline_quote = ""
    if kind == "DO" and raw.get("wanted") is not None:  # R6
        from ..interpretation.reason_layers import UNMATCHED_RESULT

        givers = {key: given for key, _, given in _menu(scope())}
        for item in raw["wanted"]:
            quote, key = item.get("quote", ""), item.get("kind")
            if item.get("role") != "result" or not _found(task, quote) or key not in givers or givers[key]:
                continue  # "none" (and a key from another version of the list) is no evidence either way
            if scope() == "six" and _NAMED_IN_SCOPE.search(quote):
                continue  # "run PANDA", "SPONGE run please": the reader cannot know what a name gives; the named step does
            if _own_phrase(quote, steps) or _group_difference_without_groups(key, quote, steps):
                continue  # PORCUPINE's "pathways that vary across patients" read as a group difference (L024)
            if _same_kind_given(key, steps) and not _names_outside_method(task):
                continue  # OTTER's "fitted so that it agrees with the PPI" read for PANDA's network (B013): same typed result
            kind, question, decline_quote = "DECLINE", "", quote
            reply = f'"{quote}" -- {UNMATCHED_RESULT}'
            rules.append(f"R6: {item.get('kind')} is given by no workflow in scope ({scope()})")
            break

    if kind == "DO" and not steps:
        kind = "ASK"  # nothing to run: ask what is wanted
    notes = plan_notes(task, steps, stated, raw) if kind == "DO" else []
    return LeanDecision(kind=kind, steps=steps if kind != "DECLINE" else [], question=question, reply=reply,
                        rules=rules, notes=notes, decline_quote=decline_quote)


def plan_notes(task: str, steps: list[str], stated: list[dict], raw: dict) -> list[str]:
    """What the plan preview shows beside the steps: settings the request gave, defaults used, file checks."""
    from workflow_registry import ACTION_DEFINITIONS

    from ..normalization_request import method_named
    from ..prior_request import _assembly, _window, requested_tf_names
    from ..workflow_conditions import conditions_for

    from ..method_names import UNREGISTERED

    given = {item["setting"]: item for item in stated}
    notes = [f'"{item["quote"]}" was not matched to a registered setting of these workflows, so it is not applied.'
             for item in stated if item["setting"] == UNREGISTERED]
    for name in steps:
        if name == "SPONGE-PRIORS":
            defaults = ACTION_DEFINITIONS["build_priors"].executor_defaults
            tfs, assembly, (up, down) = requested_tf_names(task), _assembly(task), _window(task)
            notes.append("SPONGE: human priors; TFs " + (", ".join(tfs) + " (from your request)" if tfs else
                                            "every vertebrate JASPAR CORE motif (default; can take hours)")
                         + f"; genome assembly {assembly + ' (from your request)' if assembly else defaults['genome_assembly'] + ' (default)'}"
                         + f"; promoter window {up if up is not None else defaults['promoter_upstream']} bp upstream to "
                           f"{down if down is not None else defaults['promoter_downstream']} bp downstream"
                         + (" (from your request)" if up is not None or down is not None else " (default)"))
            continue
        if name == "NORMALIZE-EXPRESSION":
            method = method_named(task)
            notes.append(f"Normalization: {method + ' (from your request)' if method else 'SNAIL (default)'}; "
                         "groups file none and median aggregation unless you give them (defaults)")
            continue
        limits = conditions_for(name)
        if limits is None:
            continue
        used = [f"{key} = {item['value']} (from your request)" for key, item in given.items()
                if key.split(".", 1)[0] == name]
        defaults = [f"{control} = {limit.default} (default)" for control, limit in limits.settings.items()
                    if f"{name}.{control}" not in given and limit.default not in (None, "", [])]
        if used or defaults:
            notes.append(f"{name}: " + "; ".join(used + defaults))
        count = raw.get("sample_count")
        if limits.min_samples and not (isinstance(count, int) and _found(task, raw.get("sample_count_quote", ""))):
            notes.append(f"{name} needs at least {limits.min_samples} samples: checked against your files before "
                         "anything runs.")
    return notes


_DOCS = {"SPONGE": "SPONGE_INTEGRATION.md", "SCORPION": "SCORPION_INTEGRATION.md",
         "PORCUPINE": "PORCUPINE_INTEGRATION.md", "NORMALIZE-EXPRESSION": "KNOWN_LIMITATIONS.md"}
_MAIN = ("PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE", "SPONGE", "NORMALIZE-EXPRESSION")


def explain_scope() -> bool:
    """The scope card in front of EXPLAIN's sources, unless NETZOO_LEAN_EXPLAIN_SCOPE=off."""
    import os

    return os.environ.get("NETZOO_LEAN_EXPLAIN_SCOPE", "").strip().lower() not in ("off", "0", "false")


def _scope_card() -> str:
    """Layer one of EXPLAIN's sources (2026-11-22, audit of 33 answers: the 2 misapplied answers had only the chosen
    workflow's text, so a single-cell user was not pointed to SCORPION): every workflow and step in scope, one registry
    line each (without its input checks), and the known limitations."""
    lines = [line.split(" Checks: ")[0] for line in _tools_text("six").split("\n")]
    limits = ROOT / "docs" / "KNOWN_LIMITATIONS.md"
    return ("Everything this system can run (one line each):\n" + "\n".join(lines)
            + (f"\n\n{limits.read_text()}" if limits.exists() else ""))


def explain_context(steps: tuple[str, ...], scope_card: bool | None = None) -> str:
    """What the answer may rest on: the scope card (`_scope_card`, unless NETZOO_LEAN_EXPLAIN_SCOPE=off), then each
    workflow's contract text, its capability-sheet entries and its integration doc. With no steps, the six main
    workflows."""
    return _explain_context(tuple(steps), explain_scope() if scope_card is None else scope_card)


@lru_cache(maxsize=128)
def _explain_context(steps: tuple[str, ...], card: bool) -> str:
    from ..capability_sheet import sheet_entries
    from ..contract_text import contract_text
    from ..policy import ProjectPolicyLoader

    specs = {spec.workflow: spec for spec in ProjectPolicyLoader().load().workflows.values()}
    registry = {line[2:].split(":")[0].split(" ")[0]: line for line in tools_text().split("\n")}
    parts = []
    for step in steps or _MAIN:
        name = "SPONGE" if step == "SPONGE-PRIORS" else step
        block = [contract_text(specs[name]) if name in specs else registry.get(name, name)]
        entries = [f"- {'gives' if item.kind == 'produces' else 'does not give'}: {item.text}"
                   for item in sheet_entries().values() if item.workflow == name and item.kind != "registry_wide"]
        block += entries
        if name in _DOCS and (ROOT / "docs" / _DOCS[name]).exists() and not (card and _DOCS[name] == "KNOWN_LIMITATIONS.md"):
            block.append((ROOT / "docs" / _DOCS[name]).read_text())
        parts.append("\n".join(block))
    return "\n\n---\n\n".join(([_scope_card()] if card else []) + parts)


def _call(client, record: list, usage_extra: bool, **request):
    """One chat completion, its usage appended to `record`."""
    import time

    started = time.time()
    response = client.chat.completions.create(**request, **(
        {"extra_body": {"usage": {"include": True}}} if usage_extra else {}))
    usage = response.usage
    cost = getattr(usage, "cost", None) or (getattr(usage, "model_extra", None) or {}).get("cost") or 0
    record.append({"model": request["model"], "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                   "output_tokens": getattr(usage, "completion_tokens", 0) or 0, "cost_usd": float(cost),
                   "duration_ms": int((time.time() - started) * 1000)})
    return response


def _explain(task: str, steps: list[str], client, model: str, max_tokens: int = 1200,
             record: list | None = None, usage_extra: bool = True) -> tuple[str, float]:
    record = [] if record is None else record
    response = _call(client, record, usage_extra,
        model=model, temperature=0, max_tokens=max_tokens,
        messages=[{"role": "system", "content": (
            "Answer the researcher's question using only the workflow descriptions below. Name the workflows the "
            "answer is about. Where the descriptions do not settle a point, say so instead of filling it in. Answer "
            "in the language of the question.\n\n" + explain_context(tuple(steps)))},
            {"role": "user", "content": task}])
    return response.choices[0].message.content, record[-1]["cost_usd"]


def decide(task: str, client, model: str = "openai/gpt-4o-mini", max_tokens: int = 1200, *,
           usage_extra: bool = True, plan_details: bool = True) -> tuple[LeanDecision, dict, float]:
    """One model call (temperature 0) and the rules. Returns the decision, the raw form and the calls' cost.
    `max_tokens`: reasoning models spend output tokens before the answer (free models: 6000, as bootstrap gives).
    `usage_extra`: ask for the cost in the usage block (OpenRouter's `usage.include`; other providers may refuse it).
    `plan_details`: append the plan notes to a DO's reply (the app shows them under its own plan instead)."""
    from concurrent.futures import ThreadPoolExecutor

    calls: list[dict] = []
    read_calls: list[dict] = []
    with ThreadPoolExecutor(max_workers=2) as pool:  # R6's blind reading runs beside the form, never sees it
        form = pool.submit(_call, client, calls, usage_extra, model=model, temperature=0, max_tokens=max_tokens,
                           response_format=response_format(),
                           messages=[{"role": "system", "content": instructions()}, {"role": "user", "content": task}])
        reading = pool.submit(_call, client, read_calls, usage_extra, model=model, temperature=0,
                              max_tokens=max_tokens, response_format=wanted_format(),
                              messages=[{"role": "system", "content": wanted_instructions()},
                                        {"role": "user", "content": task}]) if result_check() else None
        response = form.result()
        read = reading.result() if reading else None
    raw = json.loads(response.choices[0].message.content)
    if read is not None:
        raw["wanted"] = json.loads(read.choices[0].message.content).get("items", [])
    calls += read_calls
    decided = apply_rules(task, raw)
    if decided.kind == "DO":  # R15 (flag off by default): conditions the contracts need, unstated in the request
        from .required_conditions import check, enabled

        if enabled():
            decided, record = check(task, raw, decided)
            if record:
                calls.append({"input_tokens": 0, "output_tokens": 0, "duration_ms": 0, **record})
    if decided.kind == "EXPLAIN":
        decided.reply, _ = _explain(task, decided.steps, client, model, max_tokens, calls, usage_extra)
    elif decided.notes and plan_details:
        decided.reply += "\n\nPlan details:\n" + "\n".join(f"- {note}" for note in decided.notes)
    decided.calls = calls
    return decided, raw, sum(call["cost_usd"] for call in calls)
