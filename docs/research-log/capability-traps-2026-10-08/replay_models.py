"""Log 389 model comparison: only the capability-check call, replayed on the seen trap sets.

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/capability-traps-2026-10-08/replay_models.py <model> <tag> <repeats>

For every prompt of traps.json, heldout1.json and heldout2.json it builds the check messages with the
working tree's code, calls <model> through OpenRouter (temperature 0, strict function calling), and
verifies the proposal with `build_capability_check`, passing the exact routing match recorded for that
prompt in the Log 387/388 candidate runs. Scores are computed from the item labels alone:
- U/N: full gap (honest) or not; over-credit = any result still credited to a workflow;
- C: false gap = full gap or no available result; hit = an `accept` workflow credited;
  over-credit = a credited workflow outside `accept`;
- P: both = an accept workflow credited and some result not available.
Writes replay/<tag>.json (per call: proposal, check, scores) and prints a summary. Nothing else runs.
"""
import glob
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.llm import build_llm  # noqa: E402

CAND = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-cc-cand/.netzoo/traces")
SETS = {"traps.json": "ct-d4-{id}-1", "heldout1.json": "ce-h1-cand-{id}-1", "heldout2.json": "ce-h2-cand-{id}-1"}


def routing_exact():
    """session id -> exact matched actions recorded in the candidate runs."""
    found = {}
    for manifest in glob.glob(str(CAND / "*" / "manifest.json")):
        sid = json.loads(Path(manifest).read_text()).get("session_id", "")
        for line in open(Path(manifest).parent / "events.jsonl"):
            event = json.loads(line)
            if event["event_type"] == "routing.registry_match_completed":
                payload = event["payload"]
                found[sid] = payload["matched_actions"] if payload["status"] == "exact" else []
    return found


def credited(check):
    actions = set()
    for item in check.results():
        actions |= {entry(k).action for k in item.delivered_by} | set(item.instead)
    return actions


def score(item, check):
    family, results = item["family"], check.results()
    got = credited(check)
    if family in "UN":
        return {"honest": check.full_gap, "over_credit": bool(got)}
    accept = set(item.get("accept", []))
    available = [r for r in results if r.status in ("available", "with_step", "partial")]
    if family == "C":
        return {"false_gap": check.full_gap or not available, "hit": bool(got & accept),
                "over_credit": bool(got - accept)}
    return {"both": bool(got & accept) and any(r.status == "not_available" for r in results)}


def main(model, tag, repeats):
    exact = routing_exact()
    jobs = []
    for name, pattern in SETS.items():
        for item in json.loads((HERE / name).read_text())["items"]:
            for rep in range(1, repeats + 1):
                jobs.append((name, item, frozenset(exact.get(pattern.format(id=item["id"]), [])), rep))
    only = {tuple(job.split(":")) for job in os.environ.get("ONLY", "").split(",") if job}
    if only:  # retry listed id:rep jobs and merge them into an existing replay file
        jobs = [job for job in jobs if (job[1]["id"], str(job[3])) in only]
    llm = build_llm(model, 0.0, max_output_tokens=int(os.environ.get("MAX_OUT", "4000")), timeout_seconds=180)

    def run(job):
        name, item, exact_actions, rep = job
        messages, count = build_capability_check_messages(item["prompt"])
        schema = proposal_model(count)
        started = time.time()
        try:
            adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
            raw = adapter.invoke(messages)
            proposal = raw["parsed"] if isinstance(raw, dict) else raw
            if proposal is None:
                raise ValueError(str(raw.get("parsing_error"))[:300])
            check, rejected = build_capability_check(item["prompt"], proposal, frozenset(),
                                                     *([exact_actions] if os.environ.get("WITH_EXACT") else []))
            usage = (raw.get("raw").usage_metadata or {}) if isinstance(raw, dict) and raw.get("raw") else {}
            return {"set": name, "id": item["id"], "family": item["family"], "rep": rep,
                    "proposal": proposal.model_dump(), "check": check.model_dump(), "rejected": rejected,
                    "score": score(item, check), "usage": usage, "seconds": round(time.time() - started, 1)}
        except Exception as error:  # noqa: BLE001 - a failed call is a recorded result
            return {"set": name, "id": item["id"], "family": item["family"], "rep": rep,
                    "error": f"{type(error).__name__}: {error}"[:500]}

    with ThreadPoolExecutor(int(os.environ.get("PAR", "6"))) as pool:
        rows = list(pool.map(run, jobs))
    (HERE / "replay").mkdir(exist_ok=True)
    if only and (HERE / "replay" / f"{tag}.json").exists():
        done = {(row["id"], row["rep"]): row for row in json.loads((HERE / "replay" / f"{tag}.json").read_text())}
        done.update({(row["id"], row["rep"]): row for row in rows})
        rows = list(done.values())
    (HERE / "replay" / f"{tag}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    summary = {}
    for row in rows:
        key = "UN" if row["family"] in "UN" else row["family"]
        bucket = summary.setdefault(key, {"n": 0, "errors": 0})
        bucket["n"] += 1
        if "error" in row:
            bucket["errors"] += 1
            continue
        for name, value in row["score"].items():
            bucket[name] = bucket.get(name, 0) + int(value)
    tokens = sum((row.get("usage") or {}).get("input_tokens", 0) for row in rows), \
        sum((row.get("usage") or {}).get("output_tokens", 0) for row in rows)
    print(model, json.dumps(summary), "tokens in/out", tokens)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
