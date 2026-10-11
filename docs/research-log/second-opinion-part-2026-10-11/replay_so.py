"""Log 407: replay recorded second opinions through a checkout's check step and renderer; no model is called.

Usage: python docs/research-log/second-opinion-part-2026-10-11/replay_so.py <code_root> <out.json>

For every recorded heldout11-14 session (`.worktrees/*/.netzoo/sessions/ve-*.json`) whose run has a
`routing.capability_second_opinion` event, the check's original proposal (`routing.capability_checked`),
any re-read (`routing.capability_reread`) and the recorded answers are fed back to
`router_invocation._with_capability_check` of the checkout at <code_root>, with the stored routing
decision; then `checked_match` (Log 405) and the reply and card are rendered as in the live turn. A
session whose recomputed pairs differ from the recorded ones is reported, not replayed. Each gold
requirement is scored from the resulting check, and the reply text and card are kept for comparison.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

CODE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(CODE / "scripts"))
ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / "docs" / "research-log"
sys.path.insert(0, str(LOG / "requirement-verdicts-2026-10-10"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model, reread_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402

POLICY = ProjectPolicyLoader(CODE).load()
GOLD = {}
for path, tag in [("requirement-verdicts-2026-10-10/heldout11.json", "n11"),
                  ("checked-no-result-2026-10-11/heldout12.json", "b12"),
                  ("checked-match-2026-10-11/heldout13.json", "m13"),
                  ("reread-2026-10-11/heldout14.json", "r14")]:
    for item in json.loads((LOG / path).read_text())["items"]:
        GOLD[(tag, item["id"])] = item
POS = {"supported", "with_step", "needs_input"}


def span(task, words):
    words = words.strip().rstrip(".?")
    start = task.casefold().find(words.casefold())
    return None if start < 0 else (start, start + len(words))


def score(task, item, check):
    rows = []
    for req in item["requirements"]:
        g = span(task, req["words"])
        if check.full_gap:
            verdict = "not_available (full gap)"
        else:
            hit = [r for r in check.results() if (q := span(task, r.quote)) and g and min(q[1], g[1]) > max(q[0], g[0])]
            verdict = hit[0].status if hit else "not read"
        right = verdict in ("available", "with_step", "partial") if req["expect"] in POS else verdict.startswith("not_available")
        rows.append({"words": req["words"], "expect": req["expect"], "verdict": verdict, "right": right})
    return rows


def main(out_path):
    import replay_sessions as R
    out = []
    for path in sorted((ROOT.parent / ".worktrees").glob("*/.netzoo/sessions/ve-*.json")):
        sid = path.stem
        tag, item = sid.split("-")[1], sid.split("-")[3]
        if (tag, item) not in GOLD:
            continue
        data = json.loads(path.read_text())
        trace = path.parents[1] / "traces" / str(data.get("run_id")) / "events.jsonl"
        if not trace.exists():
            continue
        events = [json.loads(line) for line in trace.read_text().splitlines() if line.strip()]
        opinions = [e for e in events if e["event_type"] == "routing.capability_second_opinion"]
        checked = [e for e in events if e["event_type"] == "routing.capability_checked"]
        if not opinions or not checked or opinions[-1]["payload"].get("answers") is None:
            continue
        try:
            raw = checked[-1]["payload"]["proposal"]
            proposal = proposal_model(len(raw)).model_validate(raw)
        except Exception:  # noqa: BLE001 -- an older check contract
            continue
        rereads = [e for e in events if e["event_type"] == "routing.capability_reread"]
        recorded_reread = rereads[-1]["payload"].get("reread") if rereads else None
        answers = opinions[-1]["payload"]["answers"]
        recorded_pairs = [tuple(p[:2]) for p in opinions[-1]["payload"]["pairs"]]
        seen = {}

        def second_opinion(context, state, pairs, usage, warnings, situation=()):
            seen["pairs"] = pairs
            return answers if len(pairs) == len(answers) else None, usage, warnings

        def reread(context, state, task, passages, usage, warnings, **kwargs):
            if recorded_reread is None:
                return None, usage, warnings
            return reread_model(len(recorded_reread)).model_validate(recorded_reread), usage, warnings

        router_invocation.record_event = lambda *args, **kwargs: None
        router_invocation.request_second_opinion = second_opinion
        router_invocation.request_capability_reread = reread
        stored = TaskDecision.model_validate(data["plan"]["decision"])
        task = [m["content"] for m in data["messages"] if m["role"] == "user"][-1]
        before = stored.model_copy(update={"capability_check": None})
        invocation = router_invocation._RouterInvocation(decision=before, routing_state={}, usage=LLMUsage(),
                                                         budget_warnings=[], reason_code=None)
        context = SimpleNamespace(project_policy=POLICY)
        try:
            result = router_invocation._with_capability_check(context, {}, task, invocation, proposal)
            if hasattr(router_invocation, "_with_checked_match"):
                result = router_invocation._with_checked_match(context, {}, result)
        except Exception as error:  # noqa: BLE001
            out.append({"session": sid, "error": f"{type(error).__name__}: {error}"[:300]})
            continue
        if "pairs" in seen and len(seen["pairs"]) != len(answers):
            out.append({"session": sid, "skipped": "pairs differ from the recorded ones"})
            continue
        decision = result.decision
        rendered = R.render(task, decision.model_dump(), {**(data.get("plan") or {}), "decision": decision.model_dump()},
                            R.study_purpose(path.parents[2].name, data.get("run_id")))
        out.append({"session": sid, "item": item, "tag": tag, "recorded_pairs": recorded_pairs, "answers": answers,
                    "scores": score(task, GOLD[(tag, item)], decision.capability_check),
                    "status": decision.capability_match_status, "reply": rendered["reply"],
                    "card": rendered["card"], "reply_kind": rendered["reply_kind"]})
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(out)} sessions -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[2])
