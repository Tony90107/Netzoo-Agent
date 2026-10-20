"""How the current code calls every recorded turn whose blind gold is ASK, by the kind of the deciding fact, only on
recordings where the fact agent ran (phase 2 on). Usage: python3 gold_ask_calls.py CORES.json"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure import GOLD_FACT, WT, MAIN, _gold, _label  # noqa: E402

cores = json.loads(Path(sys.argv[1]).read_text())
by_session, core_items = _gold()
calls, items = Counter(), {}
for key, core in cores.items():
    item, gold = _label(core["session"], by_session, core_items)
    if gold != "ASK":
        continue
    folder = next((p for root in (WT, MAIN) if (p := root / core["where"]).joinpath("events.jsonl").exists()), None)
    if not any('"core.fact_check"' in line for line in open(folder / "events.jsonl")):
        continue
    calls[(GOLD_FACT.get(item), core["kind"])] += 1
    items.setdefault(GOLD_FACT.get(item), set()).add(item)
for fact in ("quantity", "data_property", "setting", "which_result"):
    row = {kind: calls[(fact, kind)] for kind in ("ASK", "DO", "DECLINE", "CLARIFY", "UNCHECKED") if calls[(fact, kind)]}
    print(f"{fact:14} items {len(items.get(fact, ())):2}  turns {sum(row.values()):3}  {row}")
