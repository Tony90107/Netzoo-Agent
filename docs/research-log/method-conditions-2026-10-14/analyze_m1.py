"""M1 step 4.3: what each live_m1 session read and decided, from the session record, its traces and the CLI output.

Usage: python3 docs/research-log/method-conditions-2026-10-14/analyze_m1.py <tag> [out.json]

Per item: the CLI's "Workflow" line, the decision (action, run verdict, held), each checked result (status, credited
workflows, the verified method fields, limits, alternatives) and, from the last turn's trace, the model's raw method
fields for every ask (before code kept or dropped them). No model is called.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[2]
ITEMS = {item["id"]: item for item in json.loads((HERE / "live_m1.json").read_text())["items"]}
RAW = ("named_method", "named_method_quote", "settings", "sample_count", "sample_count_quote", "feature_counts")


def traces(session_id):
    found = []
    for path in (TREE / ".netzoo" / "traces").glob("*/events.jsonl"):
        first = path.open().readline()
        if f'"session_id":"{session_id}"' in first.replace(" ", ""):
            found.append((json.loads(first)["occurred_at"], path))
    return [path for _, path in sorted(found)]


def raw_asks(path):
    asks = []
    for line in path.read_text().splitlines():
        if '"routing.capability_checked"' in line or '"routing.capability_reread"' in line:
            event = json.loads(line)
            proposal = event["payload"].get("proposal") or event["payload"].get("reread") or {}
            for name, sentence in proposal.items():
                if re.fullmatch(r"s\d+", name):
                    asks += [{key: ask.get(key) for key in ("quote", *RAW)} | {"from": event["event_type"][8:]}
                             for ask in sentence.get("asks", [])]
    return asks


def events(path, *names):
    return [json.loads(line) for line in path.read_text().splitlines()
            if any(f'"{name}"' in line for name in names)]


def main(tag, out=None):
    rows = {}
    for key, item in ITEMS.items():
        session_id = f"mc-{tag}-{key}"
        record = TREE / ".netzoo" / "sessions" / f"{session_id}.json"
        if not record.exists():
            rows[key] = {"missing": True}
            continue
        data = json.loads(record.read_text())
        decision = (data.get("plan") or {}).get("decision") or {}
        check = decision.get("capability_check") or {}
        turns = len(item.get("turns") or [1])
        cli = (HERE / "live" / f"{tag}-{key}-t{turns}.out")
        text = cli.read_text() if cli.exists() else ""
        paths = traces(session_id)
        last = paths[-1] if paths else None
        rows[key] = {
            "workflow_line": next((line.strip() for line in text.splitlines() if "Workflow" in line and "✓" in line), ""),
            "action": decision.get("action"),
            "run_verdict": {k: (decision.get("run_verdict") or {}).get(k) for k in ("action", "verdict", "held")},
            "full_gap": check.get("full_gap"), "provisional": check.get("provisional"),
            "unavailable": check.get("unavailable"),
            "results": [{k: req.get(k) for k in ("quote", "status", "delivered_by", "method", "limits", "instead",
                                                 "defaults")}
                        for req in check.get("requirements", []) if req.get("kind") == "result"],
            "raw_asks": raw_asks(last) if last else [],
            "second_opinion": [e["payload"] for e in events(last, "routing.capability_second_opinion")] if last else [],
            "reply_head": "\n".join(text.splitlines()[:14]),
            "target": item["m1_target"],
        }
    if out:
        Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for key, row in rows.items():
        if row.get("missing"):
            print(f"== {key}: no session record")
            continue
        print(f"== {key} | {row['workflow_line']} | action={row['action']} run={row['run_verdict']} "
              f"full_gap={row['full_gap']} provisional={row['provisional']}")
        for result in row["results"]:
            print(f"   [{result['status']}] {result['quote'][:90]!r} by={result['delivered_by']} "
                  f"method={result['method']} limits={result['limits']} instead={result['instead']} "
                  f"defaults={result['defaults']}")
        for ask in row["raw_asks"]:
            print(f"   raw({ask['from']}): {ask['quote'][:60]!r} named={ask['named_method']}:{ask['named_method_quote']!r} "
                  f"settings={ask['settings']} samples={ask['sample_count']}:{ask['sample_count_quote']!r} "
                  f"features={ask['feature_counts']}")


if __name__ == "__main__":
    main(*sys.argv[1:])
