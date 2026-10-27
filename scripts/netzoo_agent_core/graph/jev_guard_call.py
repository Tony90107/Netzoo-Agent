"""The Jev guard (docs/research-log/jev-shadow-2026-10-27/PLAN-FRESH.md). Off by default: NETZOO_JEV_GUARD=shadow
records what it would do, =on applies it.

TypeSafe's Jev decision model reads the request and the registry only -- never the reading or the call -- and picks
one of the four kinds. After the contract veto, a confident Jev CLARIFY or ASK may turn a DO or DECLINE into that
question; nothing else changes. An ASK needs the sentence where the user says they are unsure, picked by Jev from the
request's own sentences (code-cut, so the quote is verbatim); without one the call is left as it came. Jev never makes
a DO or a DECLINE, never picks a workflow and writes no reason. A call that fails leaves the core unchanged.
"""

from __future__ import annotations

import os
import re
from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import yaml

from ..contracts.core_decision import CoreDecision, DeclinedPart, FactQuestion
from ..jev_client import decide
from .context import record_event

__all__ = ["ABOUT_LINES", "KIND_CRITERIA", "apply_jev_guard", "guarded_core", "jev_mode", "request_sentences",
           "start_jev"]

THRESHOLD = 0.7
TIMEOUT = 20
WORKFLOWS = Path(__file__).resolve().parents[3] / "workflows"

KIND_INSTRUCTIONS = (
    "Decide what this network-analysis assistant should do with the user's request on its first turn. "
    "It can only run the registered workflows listed in the state. Pick the kind of reply."
)
# The shadow round's wording (jev-shadow-2026-10-27/jev_call.py), unchanged: spec 2026-10-15 section 3.
KIND_CRITERIA = {
    "DO": "The user names the result they want, a registered workflow can produce it as asked, and nothing the "
          "user is unsure about would change that verdict. Unstated settings or files are fine: later input "
          "checks handle them.",
    "ASK": "The wanted result is clear, but one specific unknown would change the verdict (for example which of "
           "two named results they want, whether a file is the right kind, or a count or setting the user says "
           "they are unsure of). Ask only about an unknown the user shows uncertainty about or that decides "
           "whether a workflow can do it.",
    "CLARIFY": "The user does not say what result they want: only a topic or purpose (understand regulation, do "
               "some network analysis, see what we find), or they name workflows without saying the goal. The "
               "goal must be clarified before choosing a workflow.",
    "DECLINE": "The wanted result is clear but cannot be done as asked: no registered workflow produces it, or "
               "the request needs something a workflow's declared inputs, controls or ranges rule out.",
}
SENTENCE_INSTRUCTIONS = (
    "Pick the sentence of the user's request where the user says they are unsure of a fact about their data or "
    "setup that decides whether the request can be done, or which workflow does it. Pick none when no sentence "
    "does."
)
ABOUT_INSTRUCTIONS = "What kind of fact is the user unsure of in that sentence?"
ABOUT_CRITERIA = {
    "which_file": "which of two files, exports or tables they have",
    "data_property": "a property of their data (how values were transformed, value type, sample origin, call origin)",
    "count": "a count such as samples, features or layers",
    "input_exists": "whether an input the result needs exists or was made",
    "which_result": "which of two named results they want",
}
ABOUT_LINES = {
    "which_file": "Which of the files do you have?",
    "data_property": "What is the case for your data on this point?",
    "count": "What is the number?",
    "input_exists": "Do you have this input?",
    "which_result": "Which result do you want?",
}
_KINDS = ("DO", "DECLINE")
_QUESTIONS = ("ASK", "CLARIFY")
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jev")


def jev_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_GUARD", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


@lru_cache(maxsize=1)
def registry_text() -> str:
    lines = []
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        cap = spec.get("output_capability") or {}
        controls = []
        for control in spec.get("controls") or []:
            bits = [control["name"], control.get("type", "")]
            if control.get("allowed_values"):
                bits.append("one of " + "/".join(map(str, control["allowed_values"])))
            if control.get("minimum") is not None or control.get("maximum") is not None:
                bits.append(f"range {control.get('minimum')}..{control.get('maximum')}")
            controls.append(" ".join(bit for bit in bits if bit))
        regulators = ("; regulators " + ", ".join(cap["regulator_types"])) if cap.get("regulator_types") else ""
        lines.append(
            f"- {spec['workflow']}: {spec['description'].strip()} Produces {cap.get('artifact_type')} "
            f"({', '.join(cap.get('granularities') or [])}{regulators}). "
            f"Required inputs: {', '.join(spec.get('required_inputs') or [])}. "
            f"Controls: {'; '.join(controls) or 'none'}.")
    return "\n".join(lines)


def request_sentences(task: str) -> list[str]:
    """The request's sentences, verbatim (a quote is always the user's own words)."""
    return [part.strip() for part in re.split(r"(?<=[.?!])\s+", task.strip()) if len(part.strip()) >= 8]


def _decide(state: str, questions: dict) -> dict:
    return decide(state, questions, timeout=TIMEOUT)


def _read(task: str) -> dict:
    """Jev's kind, and -- when it says ASK -- the sentence and the kind of fact. Raises on any failure."""
    state = f"Registered workflows:\n{registry_text()}\n\nUser request (first turn):\n{task}"
    out = _decide(state, {"kind": {"type": "choice", "instructions": KIND_INSTRUCTIONS, "criteria": KIND_CRITERIA}})
    kind = out["answers"]["kind"]
    read = {"model": out.get("model"), "kind": kind["choice"], "confidence": kind["confidence"],
            "probabilities": kind.get("probabilities"), "cost": (out.get("usage") or {}).get("cost", 0)}
    sentences = request_sentences(task)
    if kind["choice"] == "ASK" and sentences:
        options = {f"s{i}": text for i, text in enumerate(sentences, 1)} | {"none": "no sentence says this"}
        fact = _decide(state, {
            "sentence": {"type": "choice", "instructions": SENTENCE_INSTRUCTIONS, "criteria": options},
            "about": {"type": "choice", "instructions": ABOUT_INSTRUCTIONS, "criteria": ABOUT_CRITERIA}})
        sentence, about = fact["answers"]["sentence"], fact["answers"]["about"]
        read |= {"sentence": options.get(sentence["choice"]) if sentence["choice"] != "none" else None,
                 "sentence_confidence": sentence["confidence"], "about": about["choice"],
                 "cost": read["cost"] + (fact.get("usage") or {}).get("cost", 0)}
    return read


def start_jev(task: str) -> Future | None:
    """Jev's read of the request, started in the background (it needs only the text); None when the guard is off."""
    return None if jev_mode() == "off" else _POOL.submit(_read, task)


CONTRACT_INSTRUCTIONS = (
    "The user is unsure of the fact in the quoted sentence. Pick the line of the workflow contracts that states what "
    "that fact must be for the workflow to do the request. Pick none when no line does."
)
ANSWER_INSTRUCTIONS = (
    "The assistant asked the user to settle the uncertain point in their sentence. Given the contract line and the "
    "user's answer, decide whether the answer means their data meets what the contract line requires."
)
ANSWER_CRITERIA = {
    "meets": "The answer says the fact is as the contract line needs: the workflow can take it.",
    "fails": "The answer says the fact is not as the contract line needs: the input is missing, is of another kind, "
             "or is ruled out by the line.",
    "unclear": "The answer does not settle the point: it restates the request, hedges, or answers something else.",
}


@lru_cache(maxsize=32)
def contract_lines(workflows: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """(workflow, line) for each sentence of the workflows' handoff contracts and each input check, verbatim."""
    found = []
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if spec["workflow"] not in workflows:
            continue
        handoff = " ".join(((spec.get("output_capability") or {}).get("handoff_contract") or "").split())
        found += [(spec["workflow"], line) for line in re.split(r"(?<=\.)\s+", handoff) if len(line) >= 20]
        found += [(spec["workflow"], check["text"].strip()) for check in spec.get("input_checks") or []
                  if check.get("text")]
    return tuple(dict.fromkeys(found))


def pick_contract(task: str, sentence: str, workflows) -> dict:
    """The contract line the unsure sentence depends on (None when Jev picks none or is unsure)."""
    lines = contract_lines(tuple(workflows))
    if not lines:
        return {"contract": None}
    options = {f"c{i}": f"{name}: {line}" for i, (name, line) in enumerate(lines, 1)} | {"none": "no line states it"}
    state = f"User request:\n{task}\n\nThe sentence the user is unsure about:\n{sentence}"
    out = _decide(state, {"contract": {"type": "choice", "instructions": CONTRACT_INSTRUCTIONS, "criteria": options}})
    answer = out["answers"]["contract"]
    index = None if answer["choice"] == "none" else int(answer["choice"][1:]) - 1
    picked = lines[index] if index is not None and answer["confidence"] >= THRESHOLD else None
    return {"contract": picked[1] if picked else None, "contract_workflow": picked[0] if picked else None,
            "contract_confidence": answer["confidence"], "cost": (out.get("usage") or {}).get("cost", 0)}


def judge_answer(contract: str, sentence: str, question: str, answer: str) -> dict:
    """Jev's reading of the user's answer against the contract line: meets, fails or unclear, with its confidence."""
    state = (f"Contract line:\n{contract}\n\nThe user's uncertain sentence:\n{sentence}\n\n"
             f"The assistant's question:\n{question}\n\nThe user's answer:\n{answer}")
    out = _decide(state, {"answer": {"type": "choice", "instructions": ANSWER_INSTRUCTIONS,
                                     "criteria": ANSWER_CRITERIA}})
    judged = out["answers"]["answer"]
    return {"answer": judged["choice"], "confidence": judged["confidence"],
            "cost": (out.get("usage") or {}).get("cost", 0)}


CONDITION_INSTRUCTIONS = (
    "Does the user's request state a fact about their data, inputs, sizes or settings that this contract line of a "
    "workflow rules out?"
)
CONDITION_CRITERIA = {
    "violates": "The request states a fact (about the data, inputs, sizes or settings) that this line rules out.",
    "meets": "The request states facts that satisfy this line.",
    "not_stated": "The request says nothing this line decides, or only asks a question about it.",
}
BREAKING_INSTRUCTIONS = "Pick the sentence of the user's request that states the fact this contract line rules out."


@lru_cache(maxsize=32)
def condition_lines(workflows: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """CONDITIONS.md: (workflow, line) the request may break -- the contract lines and each incompatible input."""
    found = list(contract_lines(workflows))
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if spec["workflow"] in workflows:
            found += [(spec["workflow"], f"{spec['workflow']} incompatible_input_artifacts: {artifact}")
                      for artifact in (spec.get("output_capability") or {}).get("incompatible_input_artifacts") or []]
    return tuple(dict.fromkeys(found))


def check_conditions(task: str, workflows) -> dict:
    """Jev's read of each condition line against the request, and -- for the first confidently violated one -- the
    sentence that states the breaking fact. `violated` is None when nothing is."""
    lines = condition_lines(tuple(workflows))
    if not lines:
        return {"violated": None, "lines": 0}
    questions = {f"c{i}": {"type": "choice", "instructions": f"{CONDITION_INSTRUCTIONS}\nLine: {name}: {line}",
                           "criteria": CONDITION_CRITERIA} for i, (name, line) in enumerate(lines, 1)}
    out = _decide(f"User request:\n{task}", questions)
    cost = (out.get("usage") or {}).get("cost", 0)
    read = {key: (answer["choice"], answer["confidence"]) for key, answer in out["answers"].items()}
    broken = sorted((key for key, (choice, conf) in read.items() if choice == "violates" and conf >= THRESHOLD),
                    key=lambda key: -read[key][1])
    result = {"violated": None, "lines": len(lines), "read": read, "cost": cost}
    sentences = request_sentences(task)
    if broken and sentences:
        name, line = lines[int(broken[0][1:]) - 1]
        options = {f"s{i}": text for i, text in enumerate(sentences, 1)} | {"none": "no sentence states it"}
        picked = _decide(f"User request:\n{task}\n\nContract line:\n{name}: {line}", {"sentence": {
            "type": "choice", "instructions": BREAKING_INSTRUCTIONS, "criteria": options}})
        answer = picked["answers"]["sentence"]
        result["cost"] = cost + (picked.get("usage") or {}).get("cost", 0)
        if answer["choice"] != "none" and answer["confidence"] >= THRESHOLD:
            result |= {"violated": line, "workflow": name, "sentence": options[answer["choice"]],
                       "confidence": read[broken[0]][1], "sentence_confidence": answer["confidence"]}
        else:
            result |= {"unplaced": line, "sentence_confidence": answer["confidence"]}
    return result


DATA_INSTRUCTIONS = "Which kind of data does the user say the analysis should be built from?"
DATA_CRITERIA = {
    "expression_matrix": "a gene-by-sample expression table (counts, TPM, microarray intensities)",
    "coexpression_network": "a gene-by-gene co-expression or correlation matrix, including a COBRA adjusted one",
    "mutation_matrix": "somatic mutation calls per sample (binary or counts per gene)",
    "regulatory_network": "an inferred TF-to-gene network or its edge list",
    "measurement_dataset": "another omics measurement table: proteomics, metabolomics, methylation and the like",
    "several": "more than one of these kinds as the main data",
    "not_stated": "the request does not say what data the analysis is built from",
}
SAME_INSTRUCTIONS = "Does the user say the two data layers were measured on the same samples (the same individuals)?"
SAME_CRITERIA = {"yes": "the user says or makes clear they are the same samples",
                 "no": "the user says or makes clear they come from different samples or individuals",
                 "not_stated": "the request does not say"}
SAME_SAMPLE_LINE = "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven."
_PAIRED = ("DRAGON", "LIONESS-DRAGON")


@lru_cache(maxsize=1)
def _typed_contracts() -> dict:
    out = {}
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        cap = spec.get("output_capability") or {}
        refuses = {check["limit"].split(":", 1)[1]: check["text"].strip() for check in spec.get("input_checks") or []
                   if str(check.get("limit", "")).startswith("refuses_input:")}  # the check's own words (RESULTS-J2.md)
        out[spec["workflow"]] = {"incompatible": set(cap.get("incompatible_input_artifacts") or []), "refuses": refuses,
                                 "accepted": list(cap.get("input_artifacts") or [])}
    return out


def ruled_out(workflow: str, data: tuple[str, float], same: tuple[str, float] | None) -> str | None:
    """CONDITIONS-TYPED.md: the typed contract field that rules the workflow out for the read data, else None."""
    typed = _typed_contracts().get(workflow) or {}
    kind, conf = data
    if conf >= THRESHOLD and kind in typed.get("incompatible", ()):
        return f"{workflow} incompatible_input_artifacts: {kind}"
    if conf >= THRESHOLD and kind == "coexpression_network" and "coexpression_matrix" in typed.get("refuses", {}):
        return typed["refuses"]["coexpression_matrix"]  # j2 Q48: the field key was misread; the check's text is not
    if workflow in _PAIRED and same is not None and same[0] == "no" and same[1] >= THRESHOLD:
        return SAME_SAMPLE_LINE
    # PLAN-J2.md step 1'': a single kind of data none of the workflow's declared input artifacts is
    accepted = typed.get("accepted") or []
    if conf >= THRESHOLD and kind in DATA_CRITERIA and kind not in ("several", "not_stated") and accepted \
            and kind not in accepted:
        return f"{workflow} input_artifacts: {', '.join(accepted)}"
    return None


def check_typed_data(task: str, workflows) -> dict:
    """Jev's typed read of the user's data, and the call's workflows it rules out; `violated` when it rules out all of
    them and a sentence states it."""
    questions = {"data": {"type": "choice", "instructions": DATA_INSTRUCTIONS, "criteria": DATA_CRITERIA}}
    if any(name in _PAIRED for name in workflows):
        questions["same_samples"] = {"type": "choice", "instructions": SAME_INSTRUCTIONS, "criteria": SAME_CRITERIA}
    out = _decide(f"User request:\n{task}", questions)
    answers = out["answers"]
    data = (answers["data"]["choice"], answers["data"]["confidence"])
    same = (answers["same_samples"]["choice"], answers["same_samples"]["confidence"]) if "same_samples" in answers \
        else None
    reasons = {name: ruled_out(name, data, same) for name in workflows}
    result = {"violated": None, "data": data, "same_samples": same, "ruled_out": reasons,
              "cost": (out.get("usage") or {}).get("cost", 0)}
    sentences = request_sentences(task)
    if workflows and all(reasons.values()) and sentences:
        name, line = workflows[0], reasons[workflows[0]]
        options = {f"s{i}": text for i, text in enumerate(sentences, 1)} | {"none": "no sentence states it"}
        picked = _decide(f"User request:\n{task}\n\nContract:\n{line}", {"sentence": {
            "type": "choice", "instructions": BREAKING_INSTRUCTIONS, "criteria": options}})
        answer = picked["answers"]["sentence"]
        result["cost"] += (picked.get("usage") or {}).get("cost", 0)
        if answer["choice"] != "none" and answer["confidence"] >= THRESHOLD:
            result |= {"violated": line, "workflow": name, "sentence": options[answer["choice"]]}
        else:
            result |= {"unplaced": line}
    return result


RESULT_INSTRUCTIONS = (
    "Which result does the user ask for? Each option is one registered workflow's result; pick the one whose result is "
    "what the user wants to get, even if they do not name the workflow."
)
RESULT_NONE = {"none_registered": "the user asks for a concrete result that none of these workflows produce",
               "not_named": "the user names no concrete result (only a topic, a purpose, or what they could do)"}


@lru_cache(maxsize=1)
def result_menu() -> dict[str, str]:
    """RESULTS.md (steps 2/4): one option per workflow, generated from its contract's output capability."""
    menu = {}
    for path in sorted(WORKFLOWS.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        cap = spec.get("output_capability") or {}
        regulators = f"; regulators {', '.join(cap['regulator_types'])}" if cap.get("regulator_types") else ""
        menu[spec["workflow"]] = (f"{spec['description'].strip()} Result: {cap.get('artifact_type')} "
                                  f"({', '.join(cap.get('granularities') or [])}{regulators}).")
    return menu | RESULT_NONE


def check_result(task: str) -> dict:
    """Jev's pick of the registered result the request asks for (a workflow name, or one of RESULT_NONE)."""
    out = _decide(f"User request:\n{task}", {"result": {"type": "choice", "instructions": RESULT_INSTRUCTIONS,
                                                         "criteria": result_menu()}})
    answer = out["answers"]["result"]
    return {"result": answer["choice"], "confidence": answer["confidence"],
            "cost": (out.get("usage") or {}).get("cost", 0)}


def conditioned_core(core: CoreDecision, typed: dict, asked: set[str] = frozenset()) -> tuple[CoreDecision, str]:
    """PLAN-J2.md step 1'': a DO whose every workflow a typed contract field rules out for the user's stated data ->
    ASK `jev_condition`, a confirm quoting the user's sentence and the field. The pending question keeps the field as
    its contract line, so the reply is read by step 3 (a confident `fails` declines). Never a decline here."""
    if core.kind != "DO":
        return core, "not_do"
    if not typed.get("violated") or not typed.get("sentence"):
        return core, "no_violation"
    if typed["sentence"] in asked:
        return core, "already_asked"
    workflow = typed["workflow"]
    fact = FactQuestion(question="Before I go ahead, could you confirm this about your data?",
                        user_quote=typed["sentence"], workflows=[workflow, *(w for w in core.workflows if w != workflow)],
                        contract_quote=typed["violated"], uncertainty="said_unknown", depends_on="jev:condition")
    evidence = {**core.evidence, "jev_condition": {"kind_before": core.kind, "basis_before": core.basis,
                                                   "data": typed.get("data"), "same_samples": typed.get("same_samples")}}
    return CoreDecision(kind="ASK", basis="jev_condition", facts=[fact], workflows=list(fact.workflows),
                        evidence=evidence), "ask"


def linked_already(task_state) -> bool:
    """LINKS.md: a task asks its result confirm at most once."""
    state = task_state or {}
    return any(str(item.get("what", "")).startswith("jev_link:")
               for key in ("pending", "facts") for item in state.get(key) or [])


def linked_core(core: CoreDecision, pick: dict) -> tuple[CoreDecision, str]:
    """LINKS.md step 4: a CLARIFY whose request Jev reads as one workflow's result -> ASK `jev_link`, a confirm of that
    result in its contract's words. Anything else leaves the call."""
    if core.kind != "CLARIFY":
        return core, "not_clarify"
    name = pick.get("result")
    if name not in result_menu() or name in RESULT_NONE or pick.get("confidence", 0) < THRESHOLD:
        return core, "no_pick"
    description = next(yaml.safe_load(path.read_text())["description"].strip()
                       for path in sorted(WORKFLOWS.glob("*.yaml")) if yaml.safe_load(path.read_text())["workflow"] == name)
    fact = FactQuestion(question=f"Did you mean {name}'s result?", workflows=[name], contract_quote=description,
                        depends_on=f"jev_link:{name}")
    evidence = {**core.evidence, "jev_link": {"kind_before": core.kind, "basis_before": core.basis, **pick}}
    return CoreDecision(kind="ASK", basis="jev_link", facts=[fact], workflows=[name], evidence=evidence), "link"


def asked_sentences(task_state) -> set[str]:
    """The sentences a Jev question already asked in this task (pending or answered): arm A J20/J48 asked one again
    after the user answered it, since an option-free answer is never bound."""
    state = task_state or {}
    return {item.get("user_quote", "") for key in ("pending", "facts") for item in state.get(key) or []
            if str(item.get("what", "")).startswith("jev:")}


def guarded_core(core: CoreDecision, read: dict, clarify, asked: set[str] = frozenset()) -> tuple[CoreDecision, str]:
    """(the call after the guard, what it did). `clarify` builds the CLARIFY view when needed; `asked` holds the
    sentences already asked in this task, never asked again."""
    if core.kind not in _KINDS:
        return core, "not_acting"
    if read["kind"] not in _QUESTIONS or read["confidence"] < THRESHOLD:
        return core, "agrees_or_unsure"
    evidence = {**core.evidence, "jev_guard": {"kind_before": core.kind, "basis_before": core.basis,
                                               "jev": read["kind"], "confidence": read["confidence"]}}
    if read["kind"] == "CLARIFY":
        try:
            need = clarify()
        except Exception:  # noqa: BLE001 -- no view to show: the call stays as it came
            return core, "clarify_failed"
        return CoreDecision(kind="CLARIFY", basis="jev_goal", clarify=need, evidence=evidence), "clarify"
    sentence = read.get("sentence")
    if not sentence or read.get("sentence_confidence", 0) < THRESHOLD:
        return core, "no_sentence"
    if sentence in asked:
        return core, "already_asked"
    question = (f"Before I go ahead, could you settle this point you mentioned? "
                f"{ABOUT_LINES.get(read.get('about'), '')}").strip()
    fact = FactQuestion(question=question, user_quote=sentence, workflows=list(core.workflows),
                        uncertainty="said_unknown", depends_on=f"jev:{read.get('about') or ''}")
    return CoreDecision(kind="ASK", basis="jev_fact", facts=[fact], workflows=list(core.workflows),
                        evidence=evidence), "ask"


def asked_contract_question(task_state) -> dict | None:
    """The Jev question this task asked with a contract line, still waiting for its answer (ANSWERS.md)."""
    for item in (task_state or {}).get("pending") or []:
        if (str(item.get("what", "")).startswith("jev:") and item.get("status", "asked") == "asked"
                and (item.get("labels") or {}).get("contract")):
            return item
    return None


def answered_core(core: CoreDecision, question: dict, answer: str, judged: dict) -> tuple[CoreDecision, str]:
    """ANSWERS.md: the user's answer fails the contract line the question quoted -> DECLINE of the asked workflow,
    its reason the two verbatim quotes. Only on a DO; anything else, or `meets` / `unclear`, leaves the call."""
    if core.kind != "DO":
        return core, "answer_not_on_do"
    if judged["answer"] != "fails" or judged["confidence"] < THRESHOLD:
        return core, f"answer_{judged['answer']}"
    workflow = (question.get("workflows") or ["the workflow"])[0]
    line = (f'You answered "{answer.strip()}" about "{question.get("user_quote", "").rstrip(". ")}". '
            f'{workflow}\'s contract: "{question["labels"]["contract"].rstrip(". ")}". '
            f"So {workflow} cannot do this as you asked.")
    evidence = {**core.evidence, "jev_answer": {"kind_before": core.kind, "basis_before": core.basis, **judged}}
    return CoreDecision(kind="DECLINE", basis="jev_answer", evidence=evidence,
                        declined=[DeclinedPart(quote=answer.strip(), reasons=[line], line=line)]), "declined"


def apply_jev_guard(context, state, decision, core: CoreDecision, user_task: str, pending: Future | None):
    """The call after the guard (shadow: the call as it came, with what the guard would have done recorded)."""
    mode = jev_mode()
    if mode == "off" or pending is None:
        return core
    question = asked_contract_question(state.get("task_state"))
    if question is not None:  # the answer turn: Jev reads the answer against the line the question quoted
        from ..llm import latest_user_message

        answer = latest_user_message(state.get("messages") or [])
        try:
            judged = judge_answer(question["labels"]["contract"], question.get("user_quote", ""),
                                  question.get("question", ""), answer)
        except Exception as exc:  # noqa: BLE001 -- the call as it came, and says so
            judged = {"answer": f"not_run:{type(exc).__name__}", "confidence": 0.0}
        after, action = answered_core(core, question, answer, judged)
        record_event(context, state, "core.jev_answer", "classify", {
            "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
            "would_have": {"kind": after.kind, "basis": after.basis}, "judged": judged,
            "contract": question["labels"]["contract"]})
        if after is not core:
            return after if mode == "on" else core
    if core.kind == "DO" and core.workflows:  # PLAN-J2.md step 1'': typed data checks against the DO's workflows
        try:
            typed = check_typed_data(user_task, core.workflows)
        except Exception as exc:  # noqa: BLE001 -- the call as it came, and says so
            typed = {"violated": None, "error": type(exc).__name__}
        after, action = conditioned_core(core, typed, asked_sentences(state.get("task_state")))
        record_event(context, state, "core.jev_condition", "classify", {
            "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
            "would_have": {"kind": after.kind, "basis": after.basis}, "typed": typed})
        if after is not core:
            return after if mode == "on" else core
    if core.kind == "CLARIFY" and not linked_already(state.get("task_state")):  # LINKS.md step 4
        try:
            pick = check_result(user_task)
        except Exception as exc:  # noqa: BLE001 -- the call as it came, and says so
            pick = {"result": f"not_run:{type(exc).__name__}", "confidence": 0.0}
        after, action = linked_core(core, pick)
        record_event(context, state, "core.jev_link", "classify", {
            "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
            "would_have": {"kind": after.kind, "basis": after.basis, "workflows": after.workflows}, "pick": pick})
        return after if mode == "on" else core
    try:
        read = pending.result(timeout=TIMEOUT * 3)
    except Exception as exc:  # noqa: BLE001 -- any failure leaves the call as it came, and says so
        record_event(context, state, "core.jev_guard", "classify",
                     {"status": f"not_run:{type(exc).__name__}", "mode": mode, "kind_before": core.kind})
        return core

    def clarify():
        from ..interpretation.core_decision import _clarify_need

        return _clarify_need(decision, decision.capability_check, task=user_task)

    after, action = guarded_core(core, read, clarify, asked_sentences(state.get("task_state")))
    if action == "ask" and after.workflows:  # ANSWERS.md: the contract line the unsure sentence depends on
        try:
            pick = pick_contract(user_task, after.facts[0].user_quote, after.workflows)
        except Exception as exc:  # noqa: BLE001 -- asked without a line, as before
            pick = {"contract": None, "error": type(exc).__name__}
        read = {**read, **{f"pick_{key}": value for key, value in pick.items()}}
        if pick.get("contract"):
            named = [pick["contract_workflow"], *(w for w in after.workflows if w != pick["contract_workflow"])]
            fact = after.facts[0].model_copy(update={"contract_quote": pick["contract"], "workflows": named})
            after = after.model_copy(update={"facts": [fact], "workflows": named})
    record_event(context, state, "core.jev_guard", "classify", {
        "status": "checked", "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
        "would_have": {"kind": after.kind, "basis": after.basis, "workflows": after.workflows},
        "jev": read})
    return after if mode == "on" else core
