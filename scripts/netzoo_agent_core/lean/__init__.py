"""Lean decider (2026-11-20): one model call with a nine-field form, then rules taken from the contracts (R0-R7).

Why: on the sealed six-tool bank (local evaluation data), the full routing stack (about ten model calls, ~91 typed
values per request, Jev checks) scored 68/120 against 73/120 for one plain model call (B1), and lost mainly by holding
back on doable requests (28 items: conceptual questions answered with "which result do you want", needless "did you
mean" / overlap questions). Here the model decides once; code only applies rules the workflow contracts state:

R0  Preparation steps (the registry marks them "a preparation step") run first; the rest keep their order.
R1  A question needs the user's own doubt: ASK stands only when `unsure_quote` is found in the request, or code finds
    words of doubt in it (`stated_doubt`, 2026-11-21: F036's form left unsure_quote empty). (Tried and
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
R9  (2026-11-21, scorpion.yaml) A SCORPION comparison needs two built networks on each side: a DO with SCORPION whose
    request asks for a comparison from one stated patient or donor, naming no replicate or other grouping, is
    refused (`single_source_comparison`). R8, R9 and R10 give code-written reasons.
R10 (2026-11-21, output_capability.incompatible_input_artifacts) The first step's contract refuses an input the
    request says the user already has (F080: computed co-expression networks for PORCUPINE).

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
    return any(_signature(p) == _signature(m) for p in picked for m in planned)


_NAMED_IN_SCOPE = __import__("re").compile(
    r"(?<![\w-])(?:LIONESS-PANDA|PANDA|LIONESS|SCORPION|PORCUPINE|SPONGE|(?:py)?SNAIL)(?![\w-])", __import__("re").I)


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


_RE = __import__("re")
_CLAUSE = _RE.compile(r"[.;:!?\n，。；：！？]|,\s|、")
_NEGATION = _RE.compile(r"\b(?:no|not|never|without|deleted|discarded|lost|unavailable)\b|n't\b|沒有|沒|無|未|不|刪", _RE.I)
_NON_COUNT = _RE.compile(
    r"(?<![A-Za-z0-9])(?:log2?\s*\(?\s*)?(?:TPM|[FR]PKM)(?:\s*\+\s*1\s*\))?(?![A-Za-z0-9])"
    # CPM is also a gene (carboxypeptidase M): only as a unit ("log2 CPM", "CPM-normalized", "in CPM")
    r"|(?<![A-Za-z0-9])log2?\s*\(?\s*CPM(?![A-Za-z0-9])|(?<![A-Za-z0-9])CPM(?=[- ](?:normali|values?\b|matri|table|"
    r"units?\b|scale|transform))|\b(?:in|as|to)\s+CPM(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9])log(?:2|10)?[- ]?(?:transformed|scale[d]?|values?|intensit(?:y|ies)|expression)"
    r"|(?<![A-Za-z0-9])RMA(?![A-Za-z0-9])|microarrays?|Affymetrix|BeadChip|(?:array|probe)[- ]intensit(?:y|ies)"
    r"|晶片|強度值|log2?\s*強度", _RE.I)
_RAW_COUNTS = _RE.compile(
    r"raw\s+(?:\w+\s+){0,2}counts?|read[- ]counts?|integer\s+counts?|unnormali[sz]ed\s+counts?"
    r"|count\s+(?:matrix|table)|featureCounts|HTSeq|原始.{0,6}(?:counts?|計數)|read\s*count"
    r"|\bcounts?\b", _RE.I)  # bare "the counts are in data.tsv" (Gemini review): count data stated, no refusal
_OTHER_DATA = _RE.compile(r"\bpreviously\b|\bpublished\b|\bearlier\b|以前|之前|發表", _RE.I)


def _clauses(task: str) -> list[str]:
    return [part for part in _CLAUSE.split(task) if part.strip()]


def non_count_scale(task: str) -> str:
    """R8 (2026-11-21; advisor 2026-11-11: SNAIL takes raw counts): the words calling the expression TPM, FPKM, CPM,
    log values or microarray intensities, when no clause of the request states raw counts. Clauses with a negation
    are skipped both ways ("the read counts were not saved" is no raw-count statement; "not sure whether raw counts
    or TPM" states neither), and a scale in a clause about other data ("previously we published TPM") is no
    statement either. Any counts named (even "the counts are in data.tsv") means no refusal: a wrong refusal costs
    more than a run that SNAIL's own input check can still stop. Empty when the request states counts or no other
    scale."""
    plain = [part for part in _clauses(task) if not _NEGATION.search(part)]
    if any(_RAW_COUNTS.search(part) for part in plain):
        return ""
    return next((found.group(0).strip() for part in plain
                 if not _OTHER_DATA.search(part) and (found := _NON_COUNT.search(part))), "")


_ASK_NORMALIZE = _RE.compile(r"(?<![A-Za-z0-9])(?:py)?snail(?![A-Za-z0-9])|qsmooth|smooth[- _]?quantile"
                            r"|\bnormali[sz](?:e|es|ing|ation)\b|標準化|正規化", _RE.I)
_DONE = _RE.compile(r"\balready\b|\bpreviously\b|已|過", _RE.I)


def normalization_asked(task: str) -> bool:
    """The request asks for a normalization: SNAIL or smooth quantile named, or "normalize" (or its Chinese word) in a clause that
    does not say it was already done ("already normalized to log2 TPM", or the same in Chinese)."""
    return any(_ASK_NORMALIZE.search(part) and not _DONE.search(part) for part in _clauses(task))


_ARTIFACT_WORDS = {  # what a request calls an input artifact the contracts name in incompatible_input_artifacts
    "coexpression_network": (r"co-?expression\s+(?:networks?|matri(?:x|ces)|tables?|edges?)|共表現(?:網路|矩陣)",
                             "a co-expression network"),
    "mutation_matrix": (r"(?:somatic\s+)?mutation\s+(?:matri(?:x|ces)|tables?|calls)|突變矩陣", "a mutation matrix"),
}
_ACCEPTED_WORDS = {  # what a request calls an input the contract's input_artifacts accept
    "expression_matrix": r"expression|RNA-?seq|counts?\b|microarray|transcriptom|表現|表達|定序",
    "regulatory_network": r"TF[- ]?(?:to[- ])?(?:gene|target)|regulatory\s+networks?|LIONESS|PANDA|調控網路",
    "coexpression_network": _ARTIFACT_WORDS["coexpression_network"][0],
}
_HAS = _RE.compile(r"\b(?:computed|calculated|stored|saved|built|made|generated|exported|estimated|have|has|had|got)\b"
                   r"|手上|已經|已有|算好|建好|存成", _RE.I)
_WANTS = _RE.compile(r"\b(?:need|needs|want|wants|please|would\s+like|give\s+me|build|make|construct|get)\b"
                     r"|想要|需要|請|幫我", _RE.I)


def held_incompatible_input(task: str, workflow: str) -> tuple[str, str]:
    """R10 (2026-11-21, workflows/*.yaml output_capability.incompatible_input_artifacts): the artifact the request says
    the user already has (a clause with "computed", "stored", "we have"...; none with "need", "build", "please"...) that
    `workflow`'s contract lists as incompatible, when no clause names an input it accepts (input_artifacts) apart from
    it. ("label", "quote") or ("", ""). A co-expression network the user asks
    for (X003, X019) is a wanted result, not an input: its clause has a want word, so it is never read here."""
    spec = (_specs().get(workflow) or {}).get("output_capability") or {}
    plain = [part for part in _clauses(task) if not _NEGATION.search(part)]
    for accepted in spec.get("input_artifacts") or []:  # a usable input is stated too: the other data is background
        words = _ACCEPTED_WORDS.get(accepted)  # ("mutation calls and RNA-seq ... run PANDA on the RNA-seq", review)
        if words and any(_RE.search(words, part, _RE.I) and not _RE.search(
                "|".join(w for w, _ in _ARTIFACT_WORDS.values()), part, _RE.I) for part in plain):
            return "", ""
    for artifact in spec.get("incompatible_input_artifacts") or []:
        if artifact not in _ARTIFACT_WORDS:
            continue
        words, label = _ARTIFACT_WORDS[artifact]
        for part in _clauses(task):
            if (found := _RE.search(words, part, _RE.I)) and _HAS.search(part) and not _WANTS.search(part) \
                    and not _NEGATION.search(part):
                return label, found.group(0)
    return "", ""


_COMPARE = _RE.compile(  # two sides named: "between core and margin", "failing vs healthy", "腫瘤和正常之間"
    r"\bbetween\b.{1,80}?\band\b|\bversus\b|\bvs\.?(?!\w)|\bcompar\w*\b.{1,80}?\b(?:and|with|to|against)\b"
    r"|兩組|兩邊|(?:和|與|跟|及|對).{1,30}?之間|(?:比較|對照)", _RE.I | _RE.S)
_PER_CELL = _RE.compile(  # one network per cell is R6's (no workflow gives it), never a one-per-side comparison
    r"\b(?:each|every|per|individual|single)\s+(?:individual\s+)?cells?\b|\bcell[- ]to[- ]cell\b|between\s+cells"
    r"|每(?:一)?個?細胞|細胞(?:與|和|跟|到)細胞", _RE.I)
_INDIVIDUAL = r"(?:patients?|donors?|individuals?|subjects?|persons?|mice|mouse|animals?|病人|患者|捐贈者|個體|受試者|小鼠|老鼠)"
_SINGLE = _RE.compile(
    rf"\b(?:our|the|a|this)\s+only\s+(?:\w+\s+)?{_INDIVIDUAL}\b"
    rf"|\b(?:only|just)\s+one\s+(?:\w+\s+)?{_INDIVIDUAL}\b"
    rf"|\b(?:a\s+single|one|single)\s+(?!per\b|each\b|for\b|of\b)(?:[\w-]+\s+)?{_INDIVIDUAL}(?![\w-])"
    r"(?!\s+to\s+(?:the\s+)?(?:next|another|other))"
    rf"|(?<!每)(?:同一|只有一|僅一|單一|唯一|一)[位名個隻](?:[^\s，。；、]{{0,8}}?){_INDIVIDUAL}", _RE.I)
_REPLICATED = _RE.compile(
    r"\b(?:\d+|two|three|four|five|six|several|multiple)\s+(?:\w+\s+)?(?:replicates?|libraries|biopsies|captures|"
    r"runs|batches|sections|samples|donors|patients|time\s?points|stages|lanes|pools|slices|wells|organoids|lines|"
    r"visits)\b|\breplicates?\b|cell[- ]?types?|clusters?|重複|細胞類型|時間點", _RE.I)
_NO_REPLICATE = _RE.compile(r"\bno\s+(?:other\s+)?(?:donors?|patients?|individuals?|(?:biological\s+)?replicates?)"
                           r"(?:\s+(?:and|or)\s+no\s+(?:other\s+)?(?:donors?|patients?|replicates?))?"
                           r"|沒有(?:其他)?(?:捐贈者|病人|重複)", _RE.I)
_MANY_INDIVIDUALS = _RE.compile(r"\b(?:[2-9]|\d{2,}|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s+"
                               r"(?:\w+\s+)?(?:donors|patients|individuals|subjects|mice|animals)\b", _RE.I)
_THREE_PLUS_UNITS = _RE.compile(  # "exactly two biopsies" across two sides is one per side (F010); three or more may not be
    r"\b(?:[3-9]|\d{2,}|three|four|five|six|seven|eight|nine|ten|several|multiple)\s+(?:\w+\s+)?(?:replicates?|"
    r"libraries|biopsies|captures|runs|batches|sections|samples|time\s?points|stages|lanes|pools|slices|wells|"
    r"organoids|lines|visits|treated|controls?)\b", _RE.I)
_ONE_PER_SIDE = _RE.compile(  # "one donor per condition" (Gemini review); the unit is named: "one network per condition"
    r"\b(?:one|a\s+single)\s+(?:donor|patient|individual|subject|mouse|animal|sample|library|biopsy)\s+"
    r"(?:per|for\s+each|in\s+each)\s+(?:condition|group|side|arm|region|state|genotype|treatment)\b", _RE.I)


def single_source_comparison(task: str) -> str:
    """R9 (2026-11-21, scorpion.yaml: "A comparison needs compare_by in group_by and at least two built networks on each
    side"): the words stating a single patient or donor, in a request that compares two named sides and names no
    replicate, other grouping column or second individual. A request about each cell (X032: per-cell networks) is
    left to R6, whose refusal states no reason: R9's reason would be wrong there. Empty otherwise."""
    if not _COMPARE.search(task) or _PER_CELL.search(task):
        return ""
    plain = " . ".join(part for part in _clauses(task) if not _NEGATION.search(part))
    if (none := _NO_REPLICATE.search(task)) and not _MANY_INDIVIDUALS.search(plain) \
            and not _THREE_PLUS_UNITS.search(plain):  # "6 organoids (3 treated vs 3 control)" can (review)
        return none.group(0).strip()  # F010: "There are no other donors and no replicates."
    if _REPLICATED.search(plain):
        return ""
    found = _SINGLE.search(task) or _ONE_PER_SIDE.search(task)
    return found.group(0).strip() if found else ""


_DOUBT = _RE.compile(
    r"\bnot\s+sure\b|\bunsure\b|\bdon'?t\s+know\b|\bdo\s+not\s+know\b|\bhaven'?t\s+(?:decided|settled|found\s+out|"
    r"checked)|\bnot\s+(?:yet\s+)?(?:decided|settled|certain)\b|\bmay\s+or\s+may\s+not\b|\bno\s+idea\b|"
    r"\bwondering\s+whether\b|不確定|不知道|還沒決定|還沒確定|不清楚|還在問|沒把握", _RE.I)


def stated_doubt(task: str) -> str:
    """R1's second source (2026-11-21, F036): the user's own words of doubt in their newest words, found by code when
    the form's unsure_quote is empty. Replayed on every saved form: R1 turned 30 gold-do questions into runs and none
    of them has these words; 3 gold-ask ones do."""
    found = _DOUBT.search(latest_words(task))
    return found.group(0) if found else ""


FOLLOW_UP = "\nUser follow-up: "


def latest_words(task: str) -> str:
    """The user's newest words: the follow-up of a combined turn, else the whole request."""
    return task.rsplit(FOLLOW_UP, 1)[1] if FOLLOW_UP in task else task


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
    if decided.kind == "EXPLAIN":
        decided.reply, _ = _explain(task, decided.steps, client, model, max_tokens, calls, usage_extra)
    elif decided.notes and plan_details:
        decided.reply += "\n\nPlan details:\n" + "\n".join(f"- {note}" for note in decided.notes)
    decided.calls = calls
    return decided, raw, sum(call["cost_usd"] for call in calls)
