"""Log 406 pre-measure 2: the integrated check step on recorded turns, with live re-read and second opinion.

Usage (repository root, provider key in .env): set -a; . ./.env; set +a
  python docs/research-log/reread-2026-10-11/premeasure2.py <out.json>

For every recorded heldout11-13 session whose stored check leaves passages unread (`reread_passages`), the
check's original proposal is taken from the run's `routing.capability_checked` trace event and
`router_invocation._with_capability_check` runs again on it with the stored routing decision -- the
same step the product runs, now with the re-read -- calling the check's own model for the re-read and any
second opinion. One run per distinct request and passages. Each gold requirement is scored from the
resulting check: a full gap refuses everything; otherwise the result overlapping the gold words decides.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _own_llm  # noqa: E402
from netzoo_agent_core.interpretation.reread import reread_passages  # noqa: E402

LOG = ROOT / "docs" / "research-log"
GOLD = {}
for path, tag in [("requirement-verdicts-2026-10-10/heldout11.json", "n11"),
                  ("checked-no-result-2026-10-11/heldout12.json", "b12"),
                  ("checked-match-2026-10-11/heldout13.json", "m13")]:
    for item in json.loads((LOG / path).read_text())["items"]:
        GOLD[(tag, item["id"])] = item
POS = {"supported", "with_step", "needs_input"}


def span(task, words):
    words = words.strip().rstrip(".?")
    start = task.casefold().find(words.casefold())
    return None if start < 0 else (start, start + len(words))


def context():
    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    mini = _own_llm(os.environ.get("OPENROUTER_ROUTER_MODEL", "openai/gpt-4o-mini"), 1200)
    return SimpleNamespace(study_purpose_llm=mini, semantic_model_name="openai/gpt-4o-mini", router_max_tokens=1200,
                           task_token_budget=30000, price_catalog=None, project_policy=None,
                           recorder=SimpleNamespace(append=lambda *args, **kwargs: None), _model=model)


def proposal_of(worktree: Path, run_id: str):
    path = worktree / ".netzoo" / "traces" / str(run_id) / "events.jsonl"
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("event_type") == "routing.capability_checked":
            raw = event["payload"]["proposal"]
            try:
                return proposal_model(len(raw)).model_validate(raw)
            except Exception:  # noqa: BLE001 -- recorded under an older check contract (n11 base arm)
                return None
    return None


def score(task, item, check):
    rows = []
    for req in item["requirements"]:
        g = span(task, req["words"])
        if check.full_gap:
            verdict = "not_available (full gap)"
        else:
            hit = [r for r in check.results() if (q := span(task, r.quote)) and g and min(q[1], g[1]) > max(q[0], g[0])]
            verdict = hit[0].status if hit else "not read"
        ok = (verdict in ("available", "with_step", "partial")) if req["expect"] in POS else verdict.startswith("not_available")
        rows.append({"words": req["words"], "expect": req["expect"], "verdict": verdict, "right": ok})
    return rows


def main(out_path):
    jobs = {}
    for path in sorted((ROOT.parent / ".worktrees").glob("*/.netzoo/sessions/ve-*.json")):
        sid = path.stem
        tag, item = sid.split("-")[1], sid.split("-")[3]
        if (tag, item) not in GOLD:
            continue
        data = json.loads(path.read_text())
        decision = TaskDecision.model_validate(data["plan"]["decision"])
        task = [m["content"] for m in data["messages"] if m["role"] == "user"][-1]
        passages = reread_passages(task, decision)
        if passages and proposal_of(path.parents[2], data["run_id"]) is not None:
            jobs.setdefault((tag, item, task, tuple(passages)), []).append((path.parents[2], data["run_id"], decision))
    ctx = context()

    def run(key):
        tag, item, task, _passages = key
        worktree, run_id, stored = jobs[key][0]
        proposal = proposal_of(worktree, run_id)
        if proposal is None:
            return {"tag": tag, "item": item, "error": "no proposal in trace"}
        before = stored.model_copy(update={"capability_check": None})
        invocation = router_invocation._RouterInvocation(decision=before, routing_state={}, usage=LLMUsage(),
                                                         budget_warnings=[], reason_code=None)
        try:
            after = router_invocation._with_capability_check(ctx, {}, task, invocation, proposal).decision
        except Exception as error:  # noqa: BLE001
            return {"tag": tag, "item": item, "error": f"{type(error).__name__}: {error}"[:300]}
        return {"tag": tag, "item": item, "family": GOLD[(tag, item)]["family"], "sessions": len(jobs[key]),
                "before": score(task, GOLD[(tag, item)], stored.capability_check),
                "after": score(task, GOLD[(tag, item)], after.capability_check),
                "status": after.capability_match_status, "full_gap": after.capability_check.full_gap}

    with ThreadPoolExecutor(5) as pool:
        results = list(pool.map(run, list(jobs)))
    Path(out_path).write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"{len(jobs)} distinct runs -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
