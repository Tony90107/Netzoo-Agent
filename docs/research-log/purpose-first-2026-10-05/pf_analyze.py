"""Log 379 live gates, from both arms' sessions and traces. Nothing calls a model.

Usage (any directory): python3 docs/research-log/purpose-first-2026-10-05/pf_analyze.py <tag> <repeats>
Imports the candidate worktree's code (the shipped renderer) and writes live/<tag>-analysis.txt.

A session's recommendation is what the user is told to use: the decision's advisory
recommendation, else the single exact match, else "none".
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
WORKTREES = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
ARMS = {"base": WORKTREES / "netzoo-item3-base", "cand": WORKTREES / "netzoo-item3-cand"}
sys.path.insert(0, str(ARMS["cand"] / "scripts"))
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

ITEMS = {item["id"]: item for item in json.loads((HERE / os.environ.get("HELDOUT", "heldout19/heldout.json")).read_text())["items"]}
POLICY = ProjectPolicyLoader(ARMS["cand"]).load()
NAME = {definition.workflow.upper(): action for action, definition in ACTION_DEFINITIONS.items()}
MODEL_ERRORS = {"ValueError", "ValidationError", "JSONDecodeError", "OutputParserException", "KeyError", "TypeError",
                "AssertionError"}
NO_PICK_CLAIMS = {"none", "causal", "prediction"}


def actions(names):
    return {NAME.get(name.upper(), name) for name in names}


def traces(arm):
    """session id -> {event_type: last payload, 'errors': [...]} for hp- sessions."""
    found = {}
    for manifest in glob.glob(str(ARMS[arm] / ".netzoo" / "traces" / "*" / "manifest.json")):
        try:
            session = json.loads(Path(manifest).read_text()).get("session_id", "")
        except ValueError:
            continue
        if not session.startswith("hp-"):
            continue
        entry = found.setdefault(session, {"errors": []})
        for line in open(Path(manifest).parent / "events.jsonl"):
            event = json.loads(line)
            payload = event.get("payload") or {}
            entry[event.get("event_type")] = payload
            if payload.get("error_type"):
                entry["errors"].append(payload["error_type"])
    return found


def load(tag, arm, key, rep):
    path = ARMS[arm] / ".netzoo" / "sessions" / f"hp-{tag}-{arm}-{key}-{rep}.json"
    if not path.exists():
        return None
    session = json.loads(path.read_text())
    decision = (session.get("plan") or {}).get("decision") or {}
    reply = next((str(m.get("content")) for m in reversed(session.get("messages", []))
                  if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
    calls = (session.get("token_usage") or {}).get("calls", [])
    return {"decision": decision, "reply": reply, "roles": [c["role"] for c in calls],
            "cost": sum(c.get("cost_micro_usd") or 0 for c in calls) / 1e6, "plan": session.get("plan") or {}}


def recommendation(decision):
    advice = decision.get("advisory_recommendation") or {}
    if advice.get("action"):
        return advice["action"]
    matched = decision.get("matched_actions") or []
    if decision.get("capability_match_status") == "exact" and len(matched) == 1:
        return matched[0]
    return "none"


def render(task, decision, purpose, facts):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose, "data_facts": facts}
    try:
        out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    except Exception as error:  # noqa: BLE001 -- reported, never hidden
        return f"<render failed: {type(error).__name__}>"
    return str(out["messages"][-1].content)


def main(tag, repeats):
    lines = []
    out = lambda text="": lines.append(text)  # noqa: E731
    sessions = {arm: {} for arm in ARMS}
    traced = {arm: traces(arm) for arm in ARMS}
    for arm in ARMS:
        for key in ITEMS:
            for rep in range(1, repeats + 1):
                sessions[arm][(key, rep)] = load(tag, arm, key, rep)

    out(f"# Log 379 live analysis `{tag}` ({repeats} repeats, {len(ITEMS)} items)")
    out()
    # V1 validity
    for arm in ARMS:
        missing = [f"{k}-{r}" for (k, r), s in sessions[arm].items() if s is None]
        errors = Counter(e for name, entry in traced[arm].items() if name.startswith(f"hp-{tag}-{arm}-")
                         for e in entry["errors"])
        provider = {e: n for e, n in errors.items() if e not in MODEL_ERRORS}
        cost = sum(s["cost"] for s in sessions[arm].values() if s)
        out(f"V1 {arm}: sessions {sum(1 for s in sessions[arm].values() if s)}/{len(sessions[arm])}, "
            f"missing {missing}, provider errors {provider}, model-output errors {dict(errors)}, cost ${cost:.4f}")
    out()

    picks, applies, reasons = [], 0, Counter()
    s3, s4, h2 = [], [], []
    facts_reading = Counter()
    for (key, rep), session in sessions["cand"].items():
        if session is None:
            continue
        item = ITEMS[key]
        name = f"hp-{tag}-cand-{key}-{rep}"
        entry = traced["cand"].get(name, {})
        selection = entry.get("routing.purpose_selection")
        decision = TaskDecision.model_validate(session["decision"])
        if (facts := entry.get("routing.data_facts_detected")) is not None:
            facts_reading[(item["priors_stated"], facts.get("priors"))] += 1
        if selection is not None:
            applies += 1
            if selection.get("recommended"):
                picks.append((key, rep, selection["recommended"]))
                if item["claim_kind"] in NO_PICK_CLAIMS or item.get("is_control"):
                    s3.append(f"{key}-{rep}: {selection['recommended']}")
            else:
                reasons[selection.get("reason")] += 1
            listed = set(decision.hypothesis_actions)
            removed = [fit["action"] for fit in selection.get("fits", []) if fit.get("candidate") and fit["action"] not in listed]
            if removed:
                s4.append(f"{key}-{rep}: {removed}")
        purpose = entry.get("routing.study_purpose_detected")
        purpose = {k: purpose.get(k) for k in ("source", "design", "design_quote", "claims")} if purpose else None
        facts_state = ({k: facts.get(k) for k in ("source", "priors", "priors_quote")} if facts else None)
        if session["plan"].get("status") == "respond_only" and render(item["prompt"], decision, purpose, facts_state) != session["reply"]:
            h2.append(f"{key}-{rep}")

    acceptable = [p for p in picks if p[2] in actions(ITEMS[p[0]]["acceptable_candidates"])]
    in_subset = [p for p in picks if p[2] in actions(ITEMS[p[0]]["recommended_subset"])]
    out(f"S1 cand picks acceptable: {len(acceptable)}/{len(picks)}"
        + (f" ({100 * len(acceptable) / len(picks):.0f}%)" if picks else "")
        + f"; not acceptable {[p for p in picks if p not in acceptable]}")
    out(f"S2 (report) picks in recommended_subset: {len(in_subset)}/{len(picks)}")
    out(f"S3 picks on control/causal/prediction/none: {len(s3)} {s3}")
    out(f"S4 candidates removed: {len(s4)} {s4}")
    out(f"H2 cand respond-only replies differing from the offline render: {len(h2)} {h2}")
    roles = {arm: set(r for s in sessions[arm].values() if s for r in s["roles"]) for arm in ARMS}
    out(f"H3 roles cand - base: {sorted(roles['cand'] - roles['base'])}; base - cand: {sorted(roles['base'] - roles['cand'])}")
    out(f"(report) PF applied in {applies} cand sessions, picked {len(picks)}; no-pick reasons {dict(reasons)}")
    out(f"(report) data-facts reading (annotated priors -> read): {dict(facts_reading)}")
    out()

    # P1 purpose sensitivity per family, both arms
    out("P1 per family: modal recommendation per item (arm), acceptable?")
    separated = {}
    for arm in ARMS:
        separated[arm] = []
        by_family = defaultdict(dict)
        for key, item in ITEMS.items():
            if item["family"] == "T":
                continue
            recs = Counter(recommendation(s["decision"]) for (k, _), s in sessions[arm].items() if k == key and s)
            modal = recs.most_common(1)[0][0] if recs else "missing"
            by_family[item["family"]][key] = modal
        for family, modal in sorted(by_family.items()):
            ok = all(value == "none" or value in actions(ITEMS[key]["acceptable_candidates"])
                     for key, value in modal.items())
            distinct = len(set(modal.values()))
            if distinct >= 2 and ok:
                separated[arm].append(family)
            shown = ", ".join(f"{k}={v.removeprefix('run_')}" for k, v in sorted(modal.items()))
            out(f"  {arm} {family}: {shown} | distinct {distinct} | all acceptable {ok}")
    out(f"P1 families separated: base {len(separated['base'])} {separated['base']}; "
        f"cand {len(separated['cand'])} {separated['cand']}")
    out()
    # Reported: every recommendation's precision per arm
    for arm in ARMS:
        recs = [(k, recommendation(s["decision"])) for (k, _), s in sessions[arm].items() if s]
        made = [(k, a) for k, a in recs if a != "none"]
        good = [(k, a) for k, a in made if a in actions(ITEMS[k]["acceptable_candidates"])]
        on_none = [(k, a) for k, a in made if ITEMS[k]["claim_kind"] in NO_PICK_CLAIMS]
        out(f"(report) {arm}: recommendations {len(made)}/{len(recs)}, acceptable {len(good)}, "
            f"on none/causal/prediction items {len(on_none)}")
    text = "\n".join(lines)
    (HERE / "live" / f"{tag}-analysis.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
