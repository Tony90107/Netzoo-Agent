"""One bounded repeat of the twelve reported English failures through the real CLI.

Uses the existing recorder, configured models, unique planning sessions and no
execution confirmation. Re-running a started round is forbidden.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HARNESS = ROOT / "docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py"
MODELS = {"openai/gpt-4o-mini", "openai/gpt-4o-mini-2024-07-18"}
IDS = ["H18", "L13", "M25", "H34", "J29", "H21", "J17", "H37", "H46", "J06", "H11", "M01"]
TAG = "judgmentrepairs20261021"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fingerprint():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--",
                                     "scripts", "workflows", "prompts", "AGENTS.md"], cwd=ROOT).decode().split("\0")
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in sorted(set(names)) if name and (ROOT / name).is_file()}


def main():
    if (HERE / "live-round.json").exists():
        raise RuntimeError("Round already started; use an explicitly named new round after reviewing it")
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location("existing_judgment_live", HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(ROOT.parents[1] / "netzoo_agent/.env")
    config = {key: env.get(key, "") for key in ("OPENROUTER_MODEL", "OPENROUTER_ROUTER_MODEL",
              "OPENROUTER_SEMANTIC_MODEL", "OPENROUTER_CAPABILITY_MODEL")}
    if not env.get("OPENROUTER_API_KEY") or set(config.values()) - MODELS:
        raise RuntimeError("Missing credential or unexpected model configuration")
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=20) as response:
        metadata = json.load(response)
    prices = {row["id"]: row["pricing"] for row in metadata["data"] if row["id"] in MODELS}
    if set(prices) != MODELS:
        raise RuntimeError("Could not verify the configured model prices")
    max_rate = max(float(price[key]) for price in prices.values() for key in ("prompt", "completion"))
    envelope = len(IDS) * 60_000 * max_rate
    prior_cost = 0
    if HERE.name.startswith("verification-"):
        seen = {}
        for path in HERE.parent.rglob("events.jsonl"):
            for line in path.read_text().splitlines():
                event = json.loads(line)
                if event["event_type"] == "llm.completed":
                    seen[event["payload"]["call_id"]] = event["payload"]
        prior_cost = sum(item.get("cost_micro_usd") or 0 for item in seen.values()) / 1_000_000
    if prior_cost + envelope > 0.50:
        raise RuntimeError("Estimated token envelope exceeds the $0.50 smoke limit")
    stamp = datetime.now(timezone.utc).isoformat()
    pricing = {name: {"input_micro_usd_per_million": round(float(price["prompt"]) * 1e12),
                     "output_micro_usd_per_million": round(float(price["completion"]) * 1e12),
                     "effective_at": stamp} for name, price in prices.items()}
    env.update({"NETZOO_MAX_TASK_TOKENS": "30000", "OPENROUTER_CAPABILITY_EXTRA_TOKENS": "30000",
                "NETZOO_MODEL_PRICING_JSON": json.dumps(pricing), "PYTHONUNBUFFERED": "1"})
    audit = json.loads((ROOT / "docs/research-log/strictness-audit-2026-10-20/audit.json").read_text())["items"]
    items = [{"id": key, "prompt": audit[key]["prompt"],
              "expected": {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}[audit[key]["class"]]}
             for key in IDS]
    write("live-items.json", items)
    frozen = fingerprint()
    write("live-round.json", {"started_utc": stamp, "code": frozen, "config": config,
                              "price_source": "https://openrouter.ai/api/v1/models", "prices": prices,
                              "token_envelope_usd": envelope, "budget_usd": 0.50,
                              "prior_round_cost_usd": prior_cost,
                              "fresh_blind_items": False, "actual_execution_authorized": False})
    folder = HERE / "live"
    folder.mkdir(exist_ok=False)
    results = []

    def job(item):
        if fingerprint() != frozen:
            raise RuntimeError("Runtime changed after the round was frozen")
        tag = TAG
        sid = live.session_id(tag, item["id"], 1)
        sid, codes = live.run_job(tag, item["id"], 1, item, ROOT, folder,
                                  {**env, "NETZOO_PROFILE": sid}, 600)
        if fingerprint() != frozen:
            raise RuntimeError("Runtime changed during the round")
        events_path = folder / sid / "t1/events.jsonl"
        events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.exists() else []
        cores = [event["payload"] for event in events if event["event_type"] == "core.decision"]
        return {"id": item["id"], "session": sid, "codes": codes, "expected": item["expected"],
                "core": cores[-1] if cores else None}

    pilot = job(items[0])
    results.append(pilot)
    write("live-jobs.json", results)
    print(json.dumps({k: pilot[k] for k in ("id", "codes", "expected", "core")}), flush=True)
    if any(code != 0 for code in pilot["codes"]):
        raise RuntimeError("Pilot failed; remaining calls were not started")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(job, item): item["id"] for item in items[1:]}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as error:
                result = {"id": futures[future], "error_type": type(error).__name__}
            results.append(result)
            write("live-jobs.json", results)
            print(json.dumps(result), flush=True)
    write("live-finished.json", {"finished_utc": datetime.now(timezone.utc).isoformat(),
                                 "runtime_unchanged": fingerprint() == frozen, "sessions": len(results)})


if __name__ == "__main__":
    if "--verification-02" in sys.argv[1:]:
        HERE = HERE / "verification-02"
        HERE.mkdir(exist_ok=True)
        TAG += "r2"
    elif "--verification-03" in sys.argv[1:]:
        HERE = HERE / "verification-03"
        HERE.mkdir(exist_ok=True)
        TAG += "r3"
        IDS = ["J29", "J17"]
    elif "--verification-04" in sys.argv[1:]:
        HERE = HERE / "verification-04"
        HERE.mkdir(exist_ok=True)
        TAG += "r4"
        IDS = ["J17"]
    elif "--verification-05" in sys.argv[1:]:
        HERE = HERE / "verification-05"
        HERE.mkdir(exist_ok=True)
        TAG += "r5"
        IDS = ["H34"]
    main()
