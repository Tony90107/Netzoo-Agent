"""Log 342 live gates: E1, E2, H1-H3 and the reported-only measures, from the two arms' sessions.

Usage (candidate repository root): python3 docs/research-log/purpose-contract-2026-10-04/analyze_live.py <tag> <repeats>
Reads each arm's .netzoo/sessions/hp-<tag>-<arm>-<id>-<rep>.json and its trace
(for provider errors), re-renders each decision offline with and without
stage 1, and writes live/<tag>-analysis.txt and live/<tag>-replies.md. Nothing
calls a model.
"""
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from langchain_core.messages import HumanMessage  # noqa: E402
from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.interpretation import practical_notes  # noqa: E402
from netzoo_agent_core.interpretation.study_purpose_notes import claim_cells, question_claim  # noqa: E402
from netzoo_agent_core.routing.study_purpose import StudyPurpose, study_purpose  # noqa: E402
from workflow_registry import UNSUPPORTED_CLAIMS  # noqa: E402

ARMS = {"base": Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-purpose-baseline"), "cand": ROOT}
# Log 359: HELDOUT names another held-out set (default the first, as in Log 343).
ITEMS = json.loads((HERE / os.environ.get("HELDOUT", "heldout/heldout.json")).read_text())["items"]
POLICY = ProjectPolicyLoader(ROOT).load()
STAGE1 = (response.with_study_purpose_reply, practical_notes.study_purpose)
GAP_TEXTS = [entry[0] for entry in UNSUPPORTED_CLAIMS.values()]
MODEL_ERRORS = {"ValueError", "ValidationError", "JSONDecodeError", "OutputParserException", "KeyError", "TypeError"}


def render(task, decision, stage1, purpose=None):
    response.with_study_purpose_reply, practical_notes.study_purpose = (
        STAGE1 if stage1 else (lambda result, state, reply: result, lambda task: StudyPurpose()))
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    if purpose is not None:
        state["study_purpose"] = purpose
    try:
        out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    except Exception:
        return None, "response_model"
    return str(out["messages"][-1].content), out.get("reply_kind")


def trace_purposes(arm):
    """session id -> the study purpose its trace recorded (routing.study_purpose_detected), if any."""
    found = {}
    for manifest in glob.glob(str(ARMS[arm] / ".netzoo" / "traces" / "*" / "manifest.json")):
        try:
            session = json.loads(Path(manifest).read_text()).get("session_id", "")
        except ValueError:
            continue
        if not session.startswith("hp-"):
            continue
        for line in open(Path(manifest).parent / "events.jsonl"):
            event = json.loads(line)
            if event.get("event_type") == "routing.study_purpose_detected":
                payload = event["payload"]
                found[session] = {key: payload.get(key) for key in ("source", "design", "design_quote", "claims")}
    return found


def trace_errors(arm):
    """session id -> error types recorded in its trace."""
    found = {}
    for manifest in glob.glob(str(ARMS[arm] / ".netzoo" / "traces" / "*" / "manifest.json")):
        try:
            session = json.loads(Path(manifest).read_text()).get("session_id", "")
        except ValueError:
            continue
        if not session.startswith("hp-"):
            continue
        errors = found.setdefault(session, [])
        for line in open(Path(manifest).parent / "events.jsonl"):
            payload = json.loads(line).get("payload") or {}
            if payload.get("error_type"):
                errors.append(payload["error_type"])
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
    return {"decision": decision, "reply": reply, "roles": {c["role"] for c in calls},
            "calls": len(calls), "cost": sum(c.get("cost_micro_usd") or 0 for c in calls) / 1e6}


def has_gap(text):
    return any(gap in text for gap in GAP_TEXTS)


def has_purpose(text):
    return 'For your question ("' in text


def only_adds(base, cand):
    """Every baseline paragraph is in the candidate, in order; a reworded tie lead keeps its question."""
    paragraphs = cand.split("\n\n")
    position = 0
    for part in base.split("\n\n"):
        tail = part.split("tell me:", 1)[1] if part.startswith(("These all fit;", "Both fit;")) else None
        while position < len(paragraphs) and not (
                paragraphs[position] == part or (tail is not None and paragraphs[position].endswith(tail)
                                                 and "tell me:" in paragraphs[position])):
            position += 1
        if position == len(paragraphs):
            return False
        position += 1
    return True


def main(tag, repeats):
    lines, replies = [f"# Log 342 live `{tag}`", ""], [f"# Log 342 live `{tag}`: replies", ""]
    errors = {arm: trace_errors(arm) for arm in ARMS}
    purposes = {arm: trace_purposes(arm) for arm in ARMS}
    roles = {arm: set() for arm in ARMS}
    calls = {arm: [] for arm in ARMS}
    cost = Counter()
    validity = Counter()
    e1 = Counter()
    e2 = {}
    h1 = []
    h1_by_arm = {arm: [] for arm in ARMS}
    h2 = Counter()
    h2_failures = []
    controls = []
    shapes = {}
    recall = Counter()
    for item in ITEMS:
        key, task = item["id"], item["prompt"]
        purpose = study_purpose(task)
        claims = [claim for claim, _ in purpose.claims]
        recall["design_" + ("hit" if (purpose.design or "none") == item["comparison_design"] else "miss")] += 1
        primary = purpose.claim or "none"
        recall["claim_" + ("hit" if primary == item["claim_kind"] else "miss")] += 1
        replies += [f"## {key} [{item['comparison_design']}/{item['claim_kind']}] witness: "
                    f"{purpose.design}/{claims}", "", f"> {task}", ""]
        for arm in ARMS:
            arm_shapes = Counter()
            for rep in range(1, repeats + 1):
                run = load(tag, arm, key, rep)
                session = f"hp-{tag}-{arm}-{key}-{rep}"
                if run is None:
                    validity[f"{arm}_missing"] += 1
                    continue
                provider = [error for error in errors[arm].get(session, []) if error not in MODEL_ERRORS]
                validity[f"{arm}_provider_error_sessions"] += bool(provider)
                roles[arm] |= run["roles"]
                calls[arm].append(run["calls"])
                cost[arm] += run["cost"]
                decision = TaskDecision.model_validate(run["decision"])
                arm_shapes[(decision.capability_match_status,
                            tuple(sorted(decision.hypothesis_actions or decision.matched_actions)))] += 1
                text = run["reply"]
                traced = purposes[arm].get(session)
                replies += [f"### {arm} r{rep}" + (f" (study purpose: {traced})" if traced else ""), "",
                            "```", text, "```", ""]
                # Log 359: false gaps are counted in both arms (H1 is relative to the baseline arm).
                if item["claim_kind"] not in UNSUPPORTED_CLAIMS and has_gap(text):
                    h1_by_arm[arm].append(f"{key}-{rep}")
                if arm != "cand":
                    continue
                trial_purpose = (StudyPurpose(traced.get("design"), traced.get("design_quote") or "",
                                              tuple(tuple(c) for c in traced.get("claims") or ()))
                                 if traced else purpose)
                if item["is_control"] and (has_gap(text) or has_purpose(text)):
                    controls.append(f"{key}-{rep}")
                if item["claim_kind"] not in UNSUPPORTED_CLAIMS and has_gap(text):
                    h1.append(f"{key}-{rep}")
                if item["claim_kind"] in UNSUPPORTED_CLAIMS:
                    e2.setdefault(key, []).append(has_gap(text))
                eligible = (question_claim(trial_purpose) is not None and len(decision.outcome_hypotheses) <= 1
                            and bool(claim_cells(decision, trial_purpose)))
                if eligible:
                    e1["eligible"] += 1
                    e1["present"] += has_purpose(text)
                    if not has_purpose(text):
                        e1[f"missing:{key}-{rep}"] += 1
                base_render, _ = render(task, decision, False)
                cand_render, kind = render(task, decision, True, traced)
                if kind == "response_model":
                    h2["response_model"] += 1
                    if has_gap(text) or has_purpose(text):
                        h2_failures.append(f"{key}-{rep}: stage-1 text in a response-model reply")
                elif cand_render != text:
                    h2["live_differs_from_offline_render"] += 1
                    h2_failures.append(f"{key}-{rep}: live reply differs from its offline render ({kind})")
                elif kind == "unresolved" and has_gap(text):
                    h2["r4_replacement"] += 1
                elif only_adds(base_render, cand_render):
                    h2["only_adds"] += 1
                else:
                    h2_failures.append(f"{key}-{rep}: stage 1 changed baseline text ({kind})")
            shapes[(key, arm)] = arm_shapes.most_common(1)[0] if arm_shapes else None
    e2_ok = {key: f"{sum(hits)}/{len(hits)}" for key, hits in e2.items()}
    e1_rate = e1["present"] / e1["eligible"] if e1["eligible"] else None
    lines += [
        f"validity: {dict(validity)}",
        f"E1: present {e1['present']} / eligible {e1['eligible']} = {e1_rate}  (gate >= 0.90) "
        f"missing: {[k for k in e1 if k.startswith('missing:')]}",
        f"E2 (gate: every prompt >= 2/3): {e2_ok}",
        f"H1 false gaps (cand): {h1}; by arm: { {arm: len(found) for arm, found in h1_by_arm.items()} }",
        f"H2 (gate: no failures; controls 0): {dict(h2)} failures={h2_failures} controls={controls}",
        f"H3 roles only in cand (gate none): {sorted(roles['cand'] - roles['base'])}",
        f"calls per trial: base {sum(calls['base']) / max(1, len(calls['base'])):.2f}, "
        f"cand {sum(calls['cand']) / max(1, len(calls['cand'])):.2f}; cost {dict(cost)}",
        f"witness vs labels (report only): {dict(recall)}",
        "",
        "## Modal shapes (status, candidates) per prompt",
        "",
    ]
    for item in ITEMS:
        lines.append(f"- {item['id']}: base {shapes[(item['id'], 'base')]} | cand {shapes[(item['id'], 'cand')]}")
    (HERE / "live" / f"{tag}-analysis.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (HERE / "live" / f"{tag}-replies.md").write_text("\n".join(replies), encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
