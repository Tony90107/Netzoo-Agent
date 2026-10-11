"""Log 406 pre-measure: re-read the passages recorded checks left unread, and compare with gold.

Usage (repository root, provider key in .env): set -a; . ./.env; set +a
  python docs/research-log/reread-2026-10-11/premeasure.py <out.json>

For every recorded heldout11-13 session (all arms under .worktrees) whose stored decision gives
`reread_passages`, the passages are read once by the check's own model with `reread_model` (one call
per distinct request and passages), verified with `build_capability_check` on the whole request, and
each new result is matched to the gold requirement it overlaps. No reply is rendered; no session runs.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _own_llm, capability_check_system  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.reread import reread_passages  # noqa: E402

LOG = ROOT / "docs" / "research-log"
GOLD = {}
for path, tag in [("requirement-verdicts-2026-10-10/heldout11.json", "n11"),
                  ("checked-no-result-2026-10-11/heldout12.json", "b12"),
                  ("checked-match-2026-10-11/heldout13.json", "m13")]:
    for item in json.loads((LOG / path).read_text())["items"]:
        GOLD[(tag, item["id"])] = item


def span(task, words):
    words = words.strip().rstrip(".?")
    start = task.casefold().find(words.casefold())
    return None if start < 0 else (start, start + len(words))


def gold_for(task, quote, item):
    q = span(task, quote)
    for req in item["requirements"]:
        g = span(task, req["words"])
        if q and g and min(q[1], g[1]) - max(q[0], g[0]) > 0:
            return req
    return None


def read(task, passages):
    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "6000")))
    numbered = "\n".join(f"{i}. {p}" for i, p in enumerate(passages, 1))
    messages = [SystemMessage(content=capability_check_system()),
                HumanMessage(content=f"Request:\n{task}\n\nPassages to read:\n{numbered}")]
    schema = reread_model(len(passages))
    for _ in range(2):
        try:
            out = llm.with_structured_output(schema, method="function_calling", strict=True).invoke(messages)
            return schema.model_validate(out if isinstance(out, dict) else out.model_dump())
        except Exception as error:  # noqa: BLE001
            last = error
    raise last


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
        if passages:
            jobs.setdefault((tag, item, task, tuple(passages)), []).append(sid)

    def run(key):
        tag, item, task, passages = key
        try:
            check, _ = build_capability_check(task, reread_as_proposal(read(task, list(passages))))
        except Exception as error:  # noqa: BLE001
            return {"tag": tag, "item": item, "passages": passages, "error": f"{type(error).__name__}: {error}"[:300]}
        rows = []
        for req in check.results():
            g = gold_for(task, req.quote, GOLD[(tag, item)])
            rows.append({"quote": req.quote, "status": req.status, "delivered_by": req.delivered_by,
                         "gold_words": g and g["words"], "expect": g and g["expect"]})
        return {"tag": tag, "item": item, "family": GOLD[(tag, item)]["family"], "passages": passages,
                "sessions": jobs[key], "results": rows, "full_gap": check.full_gap}

    with ThreadPoolExecutor(5) as pool:
        results = list(pool.map(run, list(jobs)))
    Path(out_path).write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"{len(jobs)} distinct re-reads -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
