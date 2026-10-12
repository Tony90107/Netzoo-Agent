"""Log 412 pre-measure: the candidate check call (conditions) on seen requests, against the recorded live verdicts.

Usage (repository root, provider key in the environment, OPENROUTER_CAPABILITY_MODEL set as live):
  python docs/research-log/request-conditions-2026-10-12/premeasure.py <out.json> [tag:item ...]

For every r17 session (heldout17, rep 1) and every f16 cand session (heldout16, rep 1), takes the task the
check read (the composed "Previous NetZoo goal" task for follow-ups), asks this checkout's check model once
with this checkout's schema, builds the check, and records per gold requirement the candidate status and
the verified conditions next to the recorded live status. Check call only: no re-read, no second opinion,
so it shows what the conditions do to the first reading, not the final reply. Both sets are seen.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOG = HERE.parent
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(LOG / "reread-2026-10-11"))

from collect14 import layers  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _own_llm, build_capability_check_messages  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

ROUNDS = [("r17", "netzoo-score2-live", "rescore-2026-10-12/heldout17.json", "live"),
          ("f16", "netzoo-mt-cand", "follow-up-conditions-2026-10-12/heldout16.json", "cand")]


def jobs():
    for tag, tree, items_path, arm in ROUNDS:
        items = {item["id"]: item for item in json.loads((LOG / items_path).read_text())["items"]}
        for key, item in items.items():
            if not item["requirements"]:
                continue
            path = WORKTREES / tree / ".netzoo" / "sessions" / f"ve-{tag}-{arm}-{key}-1.json"
            data = json.loads(path.read_text())
            users = [m["content"] for m in data["messages"] if m["role"] == "user"]
            turns = item.get("turns") or [item["prompt"]]
            ran = len(users) >= len(turns)
            check = ((data.get("plan") or {}).get("decision") or {}).get("capability_check") or {} if ran else {}
            task = users[-1] if ran else turns[-1]
            yield {"tag": tag, "item": key, "family": item["family"], "task": task, "gold": item["requirements"],
                   "live": [layer["checked"] for layer in layers(task, item["requirements"], check)]}


def run(job):
    llm = _own_llm(os.environ["OPENROUTER_CAPABILITY_MODEL"], 6000)
    messages, count = build_capability_check_messages(job["task"])
    schema = proposal_model(count)
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, _raw = semantic_payload(adapter.invoke(messages))
        proposal = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
    except Exception as error:  # noqa: BLE001 - recorded
        return {**job, "error": f"{type(error).__name__}: {str(error)[:200]}"}
    check, _ = build_capability_check(job["task"], proposal)
    return {**job, "cand": [layer["checked"] for layer in layers(job["task"], job["gold"], check.model_dump())],
            "conditions": check.conditions, "raw_conditions": proposal.conditions.model_dump(),
            "results": [(item.quote, item.status, item.delivered_by, item.attrs) for item in check.results()],
            "full_gap": check.full_gap}


def main():
    out = Path(sys.argv[1])
    only = set(sys.argv[2:])  # optional "tag:item" filters
    selected = [job for job in jobs() if not only or f"{job['tag']}:{job['item']}" in only]
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(run, selected))
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} rows, errors {sum('error' in row for row in rows)} -> {out}")


if __name__ == "__main__":
    main()
