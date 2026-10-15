"""Collect round m3f (the lean live check): capture validation and a per-session summary, no model calls.

Usage: python docs/research-log/m3-method-fitting-2026-10-15/collect_m3f.py m3f --dotenv <main>/.env

Each recorded job in `live/<tag>` goes through round m3's `collect.collect_session` (exit codes, file hashes, session
identity, retained context) and is summarised: the final decision, the check's result rows (or the run verdict's),
what the request-level reading typed for the new count fields and the method, the gold requirement each row answers
(round m3's quote rule), and the final turn's visible reply. Writes `structure.json`, `summary.json` and one
packet (`packet-01.md`: no gold, but not blind -- session names show the item) beside the jobs; existing outputs are
never overwritten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M3 = HERE.parent / "m3-clarification-2026-10-15"
sys.path.insert(0, str(M3))

from collect import collect_session, environment, quote_match  # noqa: E402
from plan import load_items, write_json  # noqa: E402


def _request_reading(events: list[dict]) -> dict:
    for event in events:
        if event["event_type"] == "routing.capability_checked":
            conditions = (event["payload"].get("proposal") or {}).get("conditions") or {}
            return {key: conditions.get(key) for key in ("named_method", "named_method_quote", "settings",
                                                           "sample_count", "sample_count_quote", "feature_counts")}
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("--dotenv", type=Path)
    args = parser.parse_args()
    live = HERE / "live" / args.tag
    items = load_items(M3 / "heldout.json")
    meta = json.loads((live / "round.json").read_text())
    env = environment(args.dotenv)
    secrets = [v for k, v in env.items() if any(x in k.upper() for x in ("KEY", "TOKEN", "SECRET", "PASSWORD"))]
    rows, summary, blocks = {}, {}, []
    for folder in sorted(path for path in live.iterdir() if path.is_dir()):
        job = json.loads((folder / "job.json").read_text())
        item = items[job["item"]]
        row, body = collect_session(folder, item, job["rep"], meta, secrets)
        rows[folder.name] = row
        blocks.append((folder.name, body))
        final = folder / f"t{len(job['codes'])}"
        session = json.loads((final / "session.json").read_text())
        events = [json.loads(line) for line in (final / "events.jsonl").read_text().splitlines() if line.strip()]
        decision = (session.get("plan") or {}).get("decision") or {}
        check = decision.get("capability_check") or {}
        results = [r for r in check.get("requirements", []) if r.get("kind") == "result"] or [
            {"kind": "result", **r} for r in (decision.get("run_verdict") or {}).get("results", [])]
        task = "\n".join(item.get("turns") or [item["prompt"]])
        summary[folder.name] = {
            "item": item["id"], "codes": job["codes"], "action": decision.get("action"),
            "run_verdict": (decision.get("run_verdict") or {}).get("verdict"),
            "full_gap": check.get("full_gap"), "unchecked": check.get("unchecked"),
            "request_reading": _request_reading(events),
            "rows": [[r["quote"], r.get("status"), r.get("limits", [])[:1]] for r in results],
            "gold": [{"words": g["words"], "expect": g["expect"],
                      "rows": [[r["quote"], r.get("status")] for r in results
                               if quote_match(task, g["words"], r["quote"])]} for g in item["requirements"]],
            "check_calls": row["check_calls"], "errors": row["errors"],
            "reply": (final / "stdout.txt").read_text(errors="replace")}
    outputs = [live / "structure.json", live / "summary.json", live / "packet-01.md"]
    if any(path.exists() for path in outputs):
        raise ValueError("Collection outputs already exist; archive them explicitly before rebuilding")
    write_json(outputs[0], rows)
    write_json(outputs[1], summary)
    outputs[2].write_text("\n".join(f"## {sid}\n\n{body}\n" for sid, body in blocks))
    print(f"{len(rows)} captured sessions verified. Capture validation is not full replay.")


if __name__ == "__main__":
    main()
