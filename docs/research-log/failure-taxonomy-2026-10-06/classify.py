"""Failure taxonomy (2026-10-06): classify every recorded session's user-visible failures and where they arose.

Usage: python3 classify.py <decisions.json> <heldout.json> <arm> <code-root> <out.jsonl>
Runs under <code-root>'s own code (the arm's code), so each step of the reply's input paragraph is
re-run exactly as that arm ran it. Offline; no model is called. Seen data only.

Outcome failures (what the user sees):
  O1 missed data question   - the item needs a question about data the user left unstated; none asked
  O2 needless data question - a data question about data stated, ruled out, or not needed by the question
  O3 unusable tool offered  - offered as the answer (Selected path / Fallback / advisory) though it needs
                              data the user ruled out (hard) or left unstated (soft)
  O4 wrong tool offered     - offered tool fits neither the question nor the labels' candidate lists
  O5 degraded reply         - model-written / budget fallback, or offline re-render differs
Each failure gets the layer where it arose (see CAUSES in aggregate.py).
"""
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

decisions_path, heldout_path, ARM, ROOT, OUT = sys.argv[1:6]
sys.path.insert(0, str(Path(ROOT) / "scripts"))
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.interpretation import input_alternatives as IA  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.capability_compatibility import input_availability  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, REQUIRED_INPUTS, RUN_ACTIONS  # noqa: E402

POLICY = ProjectPolicyLoader(Path(ROOT)).load()
NAME = {definition.workflow.upper(): action for action, definition in ACTION_DEFINITIONS.items()}
PRIORS_WORDS = re.compile(r"motif|binding|\bPPI\b|protein[- ]protein|protein interaction", re.I)
MIRNA_WORDS = re.compile(r"mi(?:cro)?[- ]?RNA|\bmiR\b|small[- ]RNA", re.I)
POSSESSION = re.compile(r"\bdo you (?:also |already )?have\b|\bhave you (?:got|built|obtained|assembled)\b", re.I)
OFFERED = re.compile(r"(?:Selected path|Fallback recommendation): \*\*(.+?)\*\*")
BUDGET = "No additional response-model call was made"
EXPRESSION_ONLY = {"run_bonobo", "run_lioness_coexpression", "run_cobra"}


def acts(names):
    return {NAME.get(n.strip().upper(), n.strip()) for n in names}


def needs(action, kind):
    fields = {"priors": {"motif_file", "ppi_file"}, "mirna": {"mirna_file"}}[kind]
    return bool(fields & set(REQUIRED_INPUTS.get(action, ())))


def labels(item):
    """Normalized labels across heldout19 (older schema) and heldout20-21."""
    priors = item.get("priors_label") or item.get("priors_stated")
    mirna = item.get("mirna_label") or ("stated" if item.get("mirna_stated") is True else None)
    acceptable = acts(item.get("acceptable_candidates", []))
    fits = acceptable | acts(item.get("conditional_candidates", [])) | acts(item.get("inapplicable", []))
    kind = item.get("purpose_kind") or item.get("claim_kind") or ""
    no_answer = any(word in kind for word in ("causal", "prediction")) and "+" not in kind
    if "data_question" in item and "priors_label" in item:
        question = item["data_question"]
    else:  # heldout19: derived -- priors unstated and the question needs a TF workflow
        needs_tf = (any(needs(a, "priors") for a in acceptable)
                    or (not acceptable and kind == "regulator_change"))
        question = "priors" if priors == "unstated" and needs_tf and not no_answer else "none"
    return {"priors": priors, "mirna": mirna, "acceptable": acceptable, "fits": fits, "kind": kind,
            "no_answer": no_answer, "question": question}


def questions(text):
    sentences = re.split(r"(?<=[.?!])\s+|\n+", text.replace("**", ""))
    return [s.strip() for s in sentences if s.strip().rstrip('")\'').endswith("?") and POSSESSION.search(s)]


def render(task, decision, purpose):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose}
    try:
        out = response.respond(SimpleNamespace(project_policy=POLICY), state)
        return str(out["messages"][-1].content), out.get("reply_kind")
    except Exception as error:  # noqa: BLE001
        return f"<render failed: {type(error).__name__}>", None


def why_no_paragraph(decision, task, kind):
    """The first condition that kept the input paragraph (and its question) out, under this arm's code."""
    candidates = [a for a in dict.fromkeys([*decision.matched_actions, *decision.hypothesis_actions,
                                            *decision.recommended_actions])
                  if a in OUTPUT_CAPABILITIES and a in RUN_ACTIONS]
    outcome = IA._primary(decision)
    present = IA._present(task, decision)
    judged = getattr(present, "judged", frozenset())
    if not candidates:
        return "R0" if outcome is None else "R1"
    if outcome is None:
        return "R0"
    stated = set(input_availability(task).present)
    if not stated and not judged:
        return "D-words-no-data"
    if outcome.artifact_type not in IA._NETWORKS and not judged:
        return "P-not-network"
    running = [a for a in candidates if IA._runs_on(a, present, task)]
    if running:
        if any(needs(a, "priors") for a in running):
            return "D-model-priors-present" if judged else "D-words-priors-present"
        return "N-mixed-list"
    found = IA.input_alternative(decision, task)
    if found is None:
        if not judged:
            return "P-no-alternative" if True else "X"
        facts = getattr(decision, "data_facts", None) or {}
        if facts.get("priors") in {"stated", "ruled_out"}:
            return "D-model-priors-" + facts["priors"]
        return "X-found-none"
    if not found.asked:
        return "D-model-priors-" + str((getattr(decision, "data_facts", None) or {}).get("priors")) if judged else "D-words-nothing-missing"
    kinds = getattr(IA, "_REPLY_KINDS", frozenset())
    if kind not in kinds and not (judged and kind == "hypothesis_routes" and hasattr(IA, "asks_for_data")):
        return f"P-kind:{kind}"
    if hasattr(IA, "asks_for_data"):
        return "Q-purpose-no-ask"
    return "X-paragraph-dropped"


def main():
    rows = json.loads(Path(decisions_path).read_text())
    items = {i["id"]: i for i in json.loads(Path(heldout_path).read_text())["items"]}
    out = []
    for key, row in rows.items():
        arm, item_id, rep = key.split("-")
        if arm != ARM or item_id not in items:
            continue
        lab = labels(items[item_id])
        task, reply = row["prompt"], row["reply"]
        decision = TaskDecision.model_validate(row["decision"])
        purpose = row.get("study_purpose")
        if isinstance(purpose, str):
            import ast
            purpose = ast.literal_eval(purpose) if purpose not in ("", "None") else None
        purpose = {k: purpose.get(k) for k in ("source", "design", "design_quote", "claims")} if purpose else None
        rendered, kind = render(task, decision, purpose)
        model_written = "response" in (row.get("roles") or []) or reply.startswith(BUDGET)
        asked = questions(reply)
        asks_priors = any(PRIORS_WORDS.search(q) for q in asked)
        asks_mirna = any(MIRNA_WORDS.search(q) for q in asked)
        offered = {NAME.get(n.strip().upper(), n.strip()) for m in OFFERED.findall(reply) for n in m.split("→")}
        if decision.advisory_recommendation is not None:
            offered.add(decision.advisory_recommendation.action)
        listed = {*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions}
        facts = getattr(decision, "data_facts", None) or (row.get("data_facts_event") or {}) or {}
        words = set(input_availability(task).present)
        fails = []
        # O1 missed data question
        if lab["question"] == "priors" and not asks_priors:
            fails.append(("O1", why_no_paragraph(decision, task, kind)))
        # O2 needless data question
        if asks_priors and lab["question"] != "priors":
            if lab["priors"] == "stated":
                cause = "D-model-missed-stated" if facts.get("priors") else (
                    "D-words-missed-stated" if not {"motif_prior", "ppi_prior"} <= words else "X")
            elif lab["priors"] == "ruled_out":
                cause = "D-model-missed-ruled-out" if facts.get("priors") else "D-words-missed-ruled-out"
            elif lab["no_answer"]:
                cause = "Q-question-needs-no-data"
            elif not (listed & lab["fits"]) or not any(needs(a, "priors") for a in lab["fits"]):
                cause = "R2-tf-tools-for-non-tf-question"
            else:
                cause = "X"
            fails.append(("O2", cause))
        # O3 unusable tool offered
        for kind_, label in (("priors", lab["priors"]), ("mirna", lab["mirna"])):
            bad = [a for a in offered if needs(a, kind_)]
            if bad and label in {"ruled_out", "unstated"}:
                path = ("fallback" if "Fallback recommendation" in reply else
                        "advisory" if decision.advisory_recommendation is not None and decision.advisory_recommendation.action in bad
                        else "selected")
                applic = {item.action: item.status for item in getattr(decision, "applicability", [])}
                judged = any(a in applic for a in bad)
                cause = (f"A-no-applicability:{path}" if not judged else
                         f"A-judged-but-shown:{path}" if any(applic.get(a) != "applicable" for a in bad) else
                         "D-model-read-as-stated")
                fails.append((f"O3-{'hard' if label == 'ruled_out' else 'soft'}-{kind_}", cause))
        # O4 wrong tool offered (fits nothing in the labels)
        wrong = [a for a in offered if a not in lab["fits"] and not (
            (needs(a, "priors") and lab["priors"] in {"ruled_out", "unstated"}) or
            (needs(a, "mirna") and lab["mirna"] in {"ruled_out", "unstated"}))]
        if wrong:
            fails.append(("O4", "R-no-answer-question-got-a-tool" if lab["no_answer"] else "R-tool-does-not-fit"))
        # O5 degraded
        if model_written:
            fails.append(("O5", "budget-fallback" if reply.startswith(BUDGET) else "model-written"))
        elif rendered != reply:
            fails.append(("O5", "render-differs"))
        out.append({"key": key, "item": item_id, "kind": kind, "labels": {k: v for k, v in lab.items()
                    if k in ("priors", "mirna", "question", "kind", "no_answer")},
                    "listed": sorted(listed), "offered": sorted(offered), "asks_priors": asks_priors,
                    "asks_mirna": asks_mirna, "facts": {k: facts.get(k) for k in ("priors", "mirna")} if facts else None,
                    "status": decision.capability_match_status, "fails": fails})
    Path(OUT).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
    print(OUT, len(out), sum(1 for r in out if r["fails"]))


main()
