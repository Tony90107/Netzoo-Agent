"""ROUND-27 phase 0: draw the 10% content-label spot check (random.Random(27)) and print each unit in context."""
import json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
batch = {i["id"]: i for i in json.loads((HERE / "content-batch.json").read_text())["items"]}
units = json.loads((HERE / "content-labels.json").read_text())["units"]
units.sort(key=lambda u: (u["id"], u["n"]))
pick = sorted(random.Random(27).sample(range(len(units)), round(len(units) * 0.1)))
for k in pick:
    u = units[k]; item = batch[u["id"]]; h = item["has"][u["n"]]
    print(f"[{k}] {u['id']}#{u['n']} quote={h['quote']!r} slot={h['slot']}\n  -> {u['content']} / {u['made_by']} / {u['certainty']} | {u['why']}\n  PROMPT: {item['prompt']}\n")
print(len(pick), "units")
