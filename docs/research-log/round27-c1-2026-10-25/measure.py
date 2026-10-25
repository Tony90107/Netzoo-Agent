"""ROUND-27 C1 measurement (ROUND.md section 3).

Usage (from the worktree root, /opt/anaconda3/bin/python):
  measure.py baseline    replay every recorded reading (ROUND-13 harness, B2) at this checkout; keep each turn's core
  measure.py reads       the data-item read (gpt-4o-mini) on the 300 field-gold prompts and the replayed DO requests
  measure.py score       C-G1 .. C-G5 from base.json, reads.json and the adjudicated content gold
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths to this checkout's scripts)

replay_full = harness.replay_full
GOLD = LOGS / "field-gold-2026-10-22"
PHASE0 = LOGS / "round27-phase0-2026-10-25"
H7 = LOGS / "harness-repair-2026-10-23" / "h7" / "items.json"
BASE, READS, SCORE = HERE / "base.json", HERE / "reads.json", HERE / "score.json"
H7_SESSION = re.compile(r"^hb-p5r\d+-(?P<item>S\d\d)-")
# CENSUS.md: the C-G2 targets (offline). Replay targets by item, h7 targets by item.
TARGETS = {("core", "C18"), ("core", "C27"), ("core", "C20"), ("h4main", "M46"), ("h7", "S07"), ("h7", "S08")}
PRICE = (0.15e-6, 0.60e-6)  # gpt-4o-mini, USD per input / output token
CAP_USD = 0.5


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _h7_gold() -> dict:
    return {i["id"]: ("DO" if i["expected_call"] == "PARTIAL" else i["expected_call"])
            for i in json.loads(H7.read_text())["single"]}


def _item_of(session: str):
    if found := H7_SESSION.match(session):
        return ("h7", found.group("item"))
    if found := harness.SESSION.match(session):
        return ("core", found.group("item")) if found.group("item") else (found.group("set"), found.group("hitem"))
    return None


def _relabel(rows: dict) -> dict:
    """The P2 gold relabels (harness-repair score.py), as every replay since the freeze is scored."""
    relabels = json.loads((LOGS / "harness-repair-2026-10-23" / "gold-p2.json").read_text())["relabels"]
    for row in rows.values():
        if (found := relabels.get(row["session"])) and row["turn"] == "t1":
            assert row["gold"] == found["from"], (row["session"], row["gold"])
            row["gold"] = found["to"]
    return rows


def baseline():
    from netzoo_agent_core.interpretation import core_decision
    real = core_decision.decide_core
    captured = {}

    def capture(*args, **kwargs):
        captured["core"] = real(*args, **kwargs)
        return captured["core"]

    core_decision.decide_core = capture
    by_session, core_gold = harness._gold()
    h7 = _h7_gold()
    rows, counts = {}, Counter()
    for key, folder, sid, task, payload, reread, found, _checks in harness.readings():
        item = _item_of(sid)
        gold = harness._label(sid, by_session, core_gold)
        if gold is None and item and item[0] == "h7" and folder.name == "t1":
            gold = h7.get(item[1])
        captured.clear()
        try:
            call = replay_full.replay(folder, task, payload, reread, found)
        except Exception as error:  # noqa: BLE001 -- counted, never hidden
            counts["errors"] += 1
            rows[key] = {"session": sid, "turn": folder.name, "task": task, "gold": gold, "kind": "error",
                         "error": f"{type(error).__name__}: {error}"[:200]}
            continue
        core = captured.get("core")
        rows[key] = {"session": sid, "turn": folder.name, "item": list(item) if item else None, "task": task,
                     "gold": gold, "kind": call["kind"], "basis": call.get("basis"), "partial": call.get("partial"),
                     "workflows": list(core.workflows) if core is not None else []}
        counts["readings"] += 1
    rows = _relabel(rows)
    BASE.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows.values() if r["gold"] and r["kind"] != "error"]
    harness_gold = [r for r in labelled if not (r.get("item") and r["item"][0] == "h7")]
    print(dict(counts), f"labelled (harness gold) {len(harness_gold)}, right "
          f"{sum(r['kind'] == r['gold'] for r in harness_gold)}; h7 labelled {len(labelled) - len(harness_gold)}")


def _tasks() -> dict[str, str]:
    tasks = {}
    for name in ("core", "h1", "h2", "h3", "h4", "h5"):
        for item in json.loads((GOLD / f"batch-{name}.json").read_text())["items"]:
            tasks[_sha(item["prompt"])] = item["prompt"]
    for row in json.loads(BASE.read_text()).values():
        if row["kind"] == "DO" and row["gold"]:
            tasks[_sha(row["task"])] = row["task"]
    return tasks


def reads():
    replay_full_env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.data_items_call import DATA_ITEMS_MAX_TOKENS, invoke_data_items
    from netzoo_agent_core.llm import _estimated_tokens
    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, DATA_ITEMS_MAX_TOKENS)
    done = json.loads(READS.read_text())["reads"] if READS.exists() else {}
    todo = {k: t for k, t in _tasks().items() if k not in done or done[k]["read"] is None}
    spent = json.loads(READS.read_text()).get("usd", 0.0) if READS.exists() else 0.0
    print(f"{len(todo)} to read, {len(done)} cached, US${spent:.4f} spent")

    def one(pair):
        key, task = pair
        read, raw, input_text, output_text, error = invoke_data_items(llm, task)
        usage = getattr(raw, "usage_metadata", None) or {}
        tokens = [usage.get("input_tokens") or _estimated_tokens(input_text),
                  usage.get("output_tokens") or _estimated_tokens(output_text)]
        return key, {"task": task, "read": read.model_dump() if read is not None else None,
                     "error": None if error is None else f"{type(error).__name__}: {error}"[:200], "tokens": tokens}

    batch = list(todo.items())
    for start in range(0, len(batch), 40):
        if spent >= CAP_USD:
            print("hard cap reached; stopping")
            break
        with ThreadPoolExecutor(max_workers=6) as pool:
            for key, row in pool.map(one, batch[start:start + 40]):
                done[key] = row
                spent += row["tokens"][0] * PRICE[0] + row["tokens"][1] * PRICE[1]
        READS.write_text(json.dumps({"model": model, "usd": round(spent, 4), "reads": done}, indent=1,
                                    ensure_ascii=False))
        print(f"{min(start + 40, len(batch))}/{len(batch)} US${spent:.4f}")
    print(f"failed reads: {sum(r['read'] is None for r in done.values())}")


def replay_full_env():
    for line in (replay_full.units.MAIN / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _overlap(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    if a in b or b in a:
        return True
    wa, wb = set(re.findall(r"[\w.]+", a)), set(re.findall(r"[\w.]+", b))
    return bool(wa and wb) and len(wa & wb) / min(len(wa), len(wb)) >= 0.5


def _g1(all_reads: dict) -> dict:
    """C-G1: content of the read's verified items against the adjudicated has units (quote overlap)."""
    from netzoo_agent_core.interpretation.data_items import DataItemsRead, verified_items
    batch = {i["id"]: i for i in json.loads((PHASE0 / "content-batch.json").read_text())["items"]}
    gold = {}
    for unit in json.loads((PHASE0 / "content-labels-adjudicated.json").read_text())["units"]:
        gold.setdefault(unit["id"], []).append({**unit, "quote": batch[unit["id"]]["has"][unit["n"]]["quote"]})
    found = Counter()
    wrong, derived_wrong = [], []
    for item_id, units in gold.items():
        task = batch[item_id]["prompt"]
        row = all_reads.get(_sha(task))
        if row is None or row["read"] is None:
            found["unread requests"] += 1
            continue
        items = verified_items(task, DataItemsRead.model_validate(row["read"]))
        for item in items:
            match = next((u for u in units if _overlap(item.quote, u["quote"])), None)
            if match is None:
                found["read items with no gold unit"] += 1
                continue
            found["matched"] += 1
            derived = match["content"] in ("coexpression_matrix", "regulator_gene_network", "gene_gene_network") or \
                match["made_by"] not in ("outside", "not_stated")
            found["matched derived"] += derived
            found["certainty agrees"] += item.certainty == match["certainty_c1"]
            if item.content == "not_stated":
                continue
            found["concrete"] += 1
            found["concrete derived"] += derived
            if item.content != match["content"]:
                found["fabricated"] += 1
                record = {"id": item_id, "read": item.quote, "read_content": item.content,
                          "gold_content": match["content"], "gold_quote": match["quote"]}
                wrong.append(record)
                if derived:
                    found["fabricated derived"] += 1
                    derived_wrong.append(record)
        for unit in units:
            found["gold units"] += 1
            found["gold units read"] += any(_overlap(i.quote, unit["quote"]) for i in items)
    rate = found["fabricated"] / found["concrete"] if found["concrete"] else 0.0
    return {"counts": dict(found), "rate": round(rate, 4), "pass": rate <= 0.05, "wrong": wrong,
            "derived_wrong": derived_wrong}


def score():
    from netzoo_agent_core.interpretation.data_items import DataItemsRead, data_item_findings
    rows = json.loads(BASE.read_text())
    all_reads = json.loads(READS.read_text())["reads"]
    out = {"g1": _g1(all_reads)}
    changed, missing = [], 0
    for key, row in rows.items():
        new = row["kind"]
        findings = []
        if row["kind"] == "DO" and row["gold"]:
            read = all_reads.get(_sha(row["task"]))
            if read is None or read["read"] is None:
                missing += 1
            else:
                findings = data_item_findings(row["task"], DataItemsRead.model_validate(read["read"]),
                                              row["workflows"])
                if findings:
                    new = "ASK"
        row["new"] = new
        row["findings"] = [f.__dict__ for f in findings]
        if new != row["kind"]:
            changed.append(key)
    labelled = {k: r for k, r in rows.items() if r["gold"] and r["kind"] != "error"}
    harness_rows = {k: r for k, r in labelled.items() if not (r.get("item") and r["item"][0] == "h7")}
    breaks = [k for k, r in harness_rows.items() if r["kind"] == r["gold"] and r["new"] != r["gold"]]
    fixes = [k for k, r in harness_rows.items() if r["kind"] != r["gold"] and r["new"] == r["gold"]]
    out["g3"] = {"labelled": len(harness_rows), "right before": sum(r["kind"] == r["gold"] for r in harness_rows.values()),
                 "right after": sum(r["new"] == r["gold"] for r in harness_rows.values()), "breaks": breaks,
                 "fixes": fixes, "pass": len(breaks) <= 2, "unread DO rows": missing}
    targets = []
    for key, row in labelled.items():
        if row.get("item") and tuple(row["item"]) in TARGETS:
            right_before = row["kind"] == row["gold"] or (row["gold"] == "DECLINE" and row["kind"] != "DO")
            fixed = (row["gold"] == "DECLINE" and row["new"] != "DO") or \
                (row["gold"] == "ASK" and row["new"] == "ASK" and bool(row["findings"]))
            targets.append({"key": key, "item": row["item"], "session": row["session"], "gold": row["gold"],
                            "before": row["kind"], "after": row["new"], "right_at_baseline": right_before,
                            "fixed": fixed and not right_before,
                            # scorer fix (2026-10-25, before any reading of the breaks): a row right at baseline is
                            # broken only when its call changes away from right (first version counted every
                            # unchanged right ASK as broken because it had no C1 finding)
                            "broken": right_before and row["new"] != row["kind"] and row["new"] != row["gold"]
                            and not (row["gold"] == "DECLINE" and row["new"] != "DO")})
    live = [t for t in targets if not t["right_at_baseline"]]
    out["g2"] = {"targets": targets, "fixed": sum(t["fixed"] for t in live), "broken": sum(t["broken"] for t in targets),
                 "dropped_right_at_baseline": [t["item"] for t in targets if t["right_at_baseline"]]}
    out["g2"]["pass"] = out["g2"]["fixed"] - out["g2"]["broken"] >= 3 and out["g2"]["broken"] == 0
    out["g5"] = [{"key": k, "session": r["session"], "findings": r["findings"]} for k, r in labelled.items()
                 if r["gold"] == "DO" and r["kind"] == "DO" and r["new"] == "ASK"]
    out["questions"] = [{"key": k, "session": rows[k]["session"], "gold": rows[k]["gold"], "task": rows[k]["task"],
                         "findings": rows[k]["findings"]} for k in changed]
    SCORE.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    g1 = out["g1"]
    print("C-G1", g1["counts"], "rate", g1["rate"], "pass", g1["pass"])
    print("C-G2 fixed", out["g2"]["fixed"], "broken", out["g2"]["broken"], "dropped",
          out["g2"]["dropped_right_at_baseline"], "pass", out["g2"]["pass"])
    print("C-G3", {k: v for k, v in out["g3"].items() if k not in ("breaks", "fixes")}, "breaks",
          len(out["g3"]["breaks"]), "fixes", len(out["g3"]["fixes"]))
    print("C-G5 gold-DO turned ASK:", len(out["g5"]), "| changed rows:", len(changed))


if __name__ == "__main__":
    {"baseline": baseline, "reads": reads, "score": score}[sys.argv[1]]()
