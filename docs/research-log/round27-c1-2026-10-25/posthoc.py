"""ROUND-27 C1 POST HOC (not adopted, not a second version): the declared run's reads re-judged with every made_by
treated as not_stated, to size what the producer misread cost. Run after score.py; no model calls."""
import hashlib, json, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.interpretation.data_items import DataItemsRead, data_item_findings  # noqa: E402

rows = json.loads((HERE / "base.json").read_text())
reads = json.loads((HERE / "reads.json").read_text())["reads"]
found = Counter()
breaks, fixes = [], []
for key, row in rows.items():
    if not row["gold"] or row["kind"] == "error":
        continue
    new = row["kind"]
    if row["kind"] == "DO":
        read = DataItemsRead.model_validate(reads[hashlib.sha256(row["task"].encode()).hexdigest()[:16]]["read"])
        for item in read.items:
            item.made_by, item.made_by_alternatives = "not_stated", []
        if data_item_findings(row["task"], read, row["workflows"]):
            new = "ASK"
    if row["kind"] == row["gold"] and new != row["gold"]:
        breaks.append(row["session"])
    if row["kind"] != row["gold"] and (new == row["gold"] or (row["gold"] == "DECLINE" and new == "ASK")):
        fixes.append(row["session"])
print("breaks", len(breaks), sorted(breaks))
print("fixes (DECLINE->ASK counted)", len(fixes), sorted(fixes))
