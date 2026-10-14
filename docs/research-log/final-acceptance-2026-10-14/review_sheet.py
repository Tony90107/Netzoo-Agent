"""Print the sessions I must review (live/<tag>-to-review.json): gold, the labeller's labels, and the reply."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plan24 import ITEMS  # noqa: E402

tag, start, count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
codes = json.loads((HERE / "live" / f"{tag}-to-review.json").read_text())[start:start + count]
key = json.loads((HERE / "live" / f"{tag}-blind-key.json").read_text())
labels = json.loads((HERE / "live" / f"{tag}-labels-A.json").read_text())
rows = json.loads((HERE / "live" / f"{tag}-structure.json").read_text())
packets = "".join((HERE / "live" / f"{tag}-packet-{i:02d}.md").read_text() for i in range(1, 7))
for code in codes:
    sid = key[code]
    row = rows[sid]
    item = ITEMS[row["item"]]
    block = re.search(rf"^## {code}\n(.*?)(?=^## S\d{{3}}\n|\Z)", packets, re.S | re.M).group(1)
    reply = block.split("Reply:", 1)[1]
    print(f"######## {code} {sid} action={row['action']} run_verdict={row.get('run_verdict')} held={bool((row.get('run') or {}).get('held'))}")
    print("REQUEST:", " || ".join(item.get("turns") or [item["prompt"]]))
    for (r, lab) in zip(item["requirements"], labels[code]["R"]):
        print(f"  [{r['expect']}] {r['words']!r} by={r.get('by')} -> labeller {lab}" + (f" | fact: {r.get('deciding_fact')}" if r.get('deciding_fact') else ""))
    print("  contradiction:", labels[code].get("contradiction"))
    print(reply.strip()[:2600])
    print()
