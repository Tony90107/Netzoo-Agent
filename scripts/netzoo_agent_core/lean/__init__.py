"""Lean decider (2026-11-20): one model call with a nine-field form, then rules taken from the contracts (R0-R5).

Why: on the sealed six-tool bank (local evaluation data), the full routing stack (about ten model calls, ~91 typed
values per request, Jev checks) scored 68/120 against 73/120 for one plain model call (B1), and lost mainly by holding
back on doable requests (28 items: conceptual questions answered with "which result do you want", needless "did you
mean" / overlap questions). Here the model decides once; code only applies rules the workflow contracts state:

R0  Preparation steps (the registry marks them "a preparation step") run first; the rest keep their order.
R1  A question needs the user's own doubt: ASK stands only when `unsure_quote` is found in the request. (Tried and
    withdrawn 2026-11-20: keeping the question when the steps are not one contract chain. Replayed on the saved forms
    it lost F063 x3 and D007 -- "either matrix is fine" -- and fixed nothing; PANDA -> CONDOR is itself a handoff.)
    In a follow-up ("Previous NetZoo goal: ...\nUser follow-up: ..."), the doubt must be in the follow-up: the earlier
    doubt is what the question already asked about.
R2  Sample minimums (workflow_conditions.min_samples), when the request states the count in words found in it.
R3  SPONGE's own limits (prior_request.sponge_blockers, the non-human check of execution_sponge).
R4  PORCUPINE reads sample-specific networks: an aggregate-only producer before it becomes its per-sample version
    (the workflow whose guidance_predecessors name it and whose handoff_targets include run_porcupine).

R5  A setting the request gives (words found in it) that the workflow's contract does not allow (setting_issue) stops
    the run; words naming no allowed choice are asked about.

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

__all__ = ["LeanDecision", "apply_rules", "decide", "explain_context", "instructions", "latest_words", "plan_notes",
           "prep_steps", "response_format",
           "tool_names", "tools_text"]

ROOT = Path(__file__).resolve().parents[3]
SYSTEM_NAME = {"SPONGE": "SPONGE-PRIORS"}


@lru_cache(maxsize=1)
def _specs() -> dict[str, dict]:
    return {spec["workflow"]: spec for spec in (yaml.safe_load(path.read_text()) for path in
                                                sorted((ROOT / "workflows").glob("*.yaml")))}


@lru_cache(maxsize=1)
def tools_text() -> str:
    """The registry line of every workflow and preparation step, each followed by its contract's input checks."""
    from ..graph.jev_guard_call import registry_text

    lines = []
    for line in registry_text().split("\n"):
        name = line[2:].split(":")[0].split(" ")[0]
        checks = [item["text"] for item in (_specs().get(name, {}).get("input_checks") or [])]
        lines.append(line + (f" Checks: {' '.join(checks)}" if checks else ""))
    return "\n".join(lines)


@lru_cache(maxsize=1)
def tool_names() -> tuple[str, ...]:
    return tuple(line[2:].split(":")[0].split(" ")[0] for line in tools_text().split("\n"))


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


@lru_cache(maxsize=1)
def prep_steps() -> frozenset[str]:
    """The preparation steps, by the names apply_rules uses (the registry line says "a preparation step")."""
    names = {line[2:].split(":")[0].split(" ")[0] for line in tools_text().split("\n") if "a preparation step" in line}
    return frozenset(SYSTEM_NAME.get(name, name) for name in names)


def _setting_names() -> list[str]:
    from ..method_names import UNREGISTERED, setting_names

    return [*setting_names(True), UNREGISTERED]


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

    def as_dict(self) -> dict:
        return {"kind": self.kind, "workflows": self.steps, "question": self.question, "reply": self.reply,
                "rules": self.rules, "notes": self.notes}


_CJK = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"


def _units(text: str) -> list[str]:
    """Words and single CJK characters, case-folded, with punctuation, symbols and spacing dropped."""
    import re

    return re.findall(rf"[{_CJK}]|[^\W{_CJK}_]+", (text or "").casefold().replace("_", " "))


def _found(task: str, quote: str) -> bool:
    """Whether the request says what the quote says, loosely (2026-11-20, user: the match need not be that exact).

    Found when the quote's words, ignoring case, punctuation, spacing and underscores ("min_cells 50" in "min_cells =
    50"), sit in the request in order; or when at least 60% of them, and two, appear in order within a passage at most
    twice the quote's length ("15 AD samples" in "15 Alzheimer's disease samples"). Chinese is compared character by
    character. A quote that is not found never stops anything here: its evidence is just not used.
    """
    from difflib import SequenceMatcher

    wanted, words = _units(quote), _units(task)
    if not wanted or not words:
        return False
    joined, target = " ".join(words), " ".join(wanted)
    if f" {target} " in f" {joined} ":
        return True
    if len(wanted) < 2:
        return False
    blocks = [b for b in SequenceMatcher(None, words, wanted, autojunk=False).get_matching_blocks() if b.size]
    for first in range(len(blocks)):
        matched = 0
        for last in range(first, len(blocks)):
            if blocks[last].a + blocks[last].size - blocks[first].a > 2 * len(wanted):
                break
            matched += blocks[last].size
            if matched >= 2 and matched >= 0.6 * len(wanted):
                return True
    return False


def _stated_value(task: str, value: str) -> bool:
    """A setting's value as the request writes it: its number, or its words."""
    from ..workflow_conditions import stated_numbers

    numbers = stated_numbers(value)
    return bool(numbers) and all(any(n == m for m in stated_numbers(task)) for n in numbers)


def _stated(task: str, number: int) -> bool:
    """The number itself is in the request (digits, or a number word the contract reader knows)."""
    from ..workflow_conditions import stated_numbers

    return any(float(number) == value for value in stated_numbers(task))


def _per_sample_version(workflow: str) -> str | None:
    """R4: the workflow that derives `workflow`'s per-sample networks and hands them to PORCUPINE."""
    action = f"run_{workflow.lower()}"
    for name, spec in _specs().items():
        capability = spec.get("output_capability") or {}
        if action in (capability.get("guidance_predecessors") or []) and "run_porcupine" in (
                capability.get("handoff_targets") or []):
            return name
    return None


FOLLOW_UP = "\nUser follow-up: "


def latest_words(task: str) -> str:
    """The user's newest words: the follow-up of a combined turn, else the whole request."""
    return task.rsplit(FOLLOW_UP, 1)[1] if FOLLOW_UP in task else task


def apply_rules(task: str, raw: dict) -> LeanDecision:
    """The model's handling with the contracts' rules applied (R0-R5 in the module docstring)."""
    from ..prior_request import _NON_HUMAN, sponge_blockers
    from ..workflow_conditions import conditions_for

    steps = list(dict.fromkeys(SYSTEM_NAME.get(name, name) for name in raw.get("steps") or []))
    kind, question, reply, rules = raw.get("decision", "ASK"), raw.get("question", ""), raw.get("reply", ""), []

    ordered = sorted(steps, key=lambda name: name not in prep_steps())  # R0 (sorted is stable)
    if ordered != steps:
        steps = ordered
        rules.append("R0: preparation steps run first")

    for index, name in enumerate(steps):  # R4
        if name == "PORCUPINE" and index > 0:
            before = steps[index - 1]
            spec = (_specs().get(before) or {}).get("output_capability") or {}
            if "run_porcupine" not in (spec.get("handoff_targets") or []) and (swap := _per_sample_version(before)):
                steps[index - 1] = swap
                rules.append(f"R4: PORCUPINE reads per-sample networks, so {before} became {swap}")

    if kind == "ASK" and not _found(latest_words(task), raw.get("unsure_quote", "")) and steps:  # R1
        kind, question = "DO", ""
        rules.append("R1: no doubt stated by the user, so no question")

    count = raw.get("sample_count")
    if (kind == "DO" and isinstance(count, int) and _found(task, raw.get("sample_count_quote", ""))
            and _stated(task, count)):  # R2: the words and the number itself are in the request
        for name in steps:
            limits = conditions_for(name)
            if limits and limits.min_samples and count < limits.min_samples:
                kind, question = "DECLINE", ""
                reply = f"{name} needs at least {limits.min_samples} samples; the request has {count}."
                rules.append(f"R2: {name} minimum {limits.min_samples} samples, request states {count}")
                break

    if kind == "DO" and "SPONGE-PRIORS" in steps:  # R3
        blockers = sponge_blockers(task)
        if (non_human := _NON_HUMAN.search(task)):
            blockers.append(f"SPONGE builds human priors only (hg38, hg19 or T2T-CHM13); the request names "
                            f"{non_human.group(0)}")
        stops = [b for b in blockers if "say which one" not in b and "say whether they are human" not in b]
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
            if issue and issue.endswith(UNCLEAR_CHOICE):
                kind, question, reply = "ASK", issue + ".", issue + "."
                rules.append(f"R5: {item['setting']} value unclear")
                break
            if issue and (_found(task, item.get("value", "")) or _stated_value(task, item.get("value", ""))):
                kind, question, reply = "DECLINE", "", issue + "."
                rules.append(f"R5: {item['setting']} not allowed by the contract")
                break

    if kind == "DO" and not steps:
        kind = "ASK"  # nothing to run: ask what is wanted
    notes = plan_notes(task, steps, stated, raw) if kind == "DO" else []
    return LeanDecision(kind=kind, steps=steps if kind != "DECLINE" else [], question=question, reply=reply,
                        rules=rules, notes=notes)


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
            notes.append("SPONGE: TFs " + (", ".join(tfs) + " (from your request)" if tfs else
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


@lru_cache(maxsize=64)
def explain_context(steps: tuple[str, ...]) -> str:
    """What the answer may rest on: each workflow's contract text, its capability-sheet entries and its integration
    doc. With no steps, the six main workflows."""
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
        if name in _DOCS and (ROOT / "docs" / _DOCS[name]).exists():
            block.append((ROOT / "docs" / _DOCS[name]).read_text())
        parts.append("\n".join(block))
    return "\n\n---\n\n".join(parts)


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
    calls: list[dict] = []
    response = _call(client, calls, usage_extra, model=model, temperature=0, max_tokens=max_tokens,
                     response_format=response_format(),
                     messages=[{"role": "system", "content": instructions()}, {"role": "user", "content": task}])
    raw = json.loads(response.choices[0].message.content)
    decided = apply_rules(task, raw)
    if decided.kind == "EXPLAIN":
        decided.reply, _ = _explain(task, decided.steps, client, model, max_tokens, calls, usage_extra)
    elif decided.notes and plan_details:
        decided.reply += "\n\nPlan details:\n" + "\n".join(f"- {note}" for note in decided.notes)
    decided.calls = calls
    return decided, raw, sum(call["cost_usd"] for call in calls)
