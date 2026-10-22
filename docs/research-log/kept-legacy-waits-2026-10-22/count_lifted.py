"""Offline: how often does a checked fact agent lift legacy waits, and how often does R1 drop an ask, vs gold."""
import json, sys
from collections import Counter
from pathlib import Path

base = json.load(open(sys.argv[1]))
stats = Counter()
lifted, r1 = [], []
for key, row in base.items():
    gold, rec = row.get("gold"), row.get("recorded")
    if not gold or not rec:
        continue
    ev = Path(row["where"]) / "events.jsonl"
    if not ev.exists():
        stats["no_events"] += 1
        continue
    facts = [json.loads(l)["payload"] for l in open(ev) if '"core.fact_check"' in l]
    stats["readings"] += 1
    if not facts:
        stats["no_fact_check"] += 1
        continue
    f = facts[0]
    stats[f"status_{f.get('status')}"] += 1
    if f.get("status") != "checked":
        continue
    legacy = f.get("legacy") or []
    asked = [a for a in f.get("accepted") or [] if not a.get("settled_by_input_check")]
    if legacy:
        stats["legacy_nonempty"] += 1
        if not asked:
            stats["legacy_lifted_no_ask"] += 1
            lifted.append((row["session"], gold, rec, [l.get("question", l)[:90] if isinstance(l, dict) else str(l)[:90] for l in legacy][:2]))
    rej = [r for r in f.get("rejected") or [] if r["rule"].startswith("R1 the check")]
    if rej and not asked and gold == "ASK" and rec != "ASK":
        r1.append((row["session"], gold, rec, rej[0]["proposal"].get("user_quote", "")[:80]))

print(dict(stats))
c = Counter((g, r) for _, g, r, _ in lifted)
print("legacy lifted, no ask: gold->recorded", dict(c))
for s in lifted:
    if s[1] != s[2]:
        print("  WRONG", s)
print("missed ASK with an R1-rejected proposal:", len(r1))
for s in r1:
    print("  ", s)
