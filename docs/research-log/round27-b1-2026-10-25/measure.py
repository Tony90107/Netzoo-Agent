"""ROUND-27 B1 measurement (ROUND.md section 2): 2a's measurement with the B1 guard.

Both arms replay the same recorded readings with the same R22-B cache (ROUND-22's) and the P2 gold relabels. The new
arm adds the B1 links: verified, without emptier links, guarded against new limits (both checks built in code, as
live does), merged before replay builds its check; held links turn a DO into an ASK.

Usage (from the worktree root, /opt/anaconda3/bin/python):
  measure.py inputs     every reading's credited candidate workflows -> inputs.json
  measure.py ask        one B1 read per distinct (request, workflows) -> links-reads.json (gpt-4o-mini)
  measure.py score      field-level B-G1..G3 -> score.json, score-summary.json
  measure.py replay     both arms over every reading -> replay-old.json, replay-new.json; B-G4, B-G5
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths to this checkout's scripts)

sys.path.insert(0, str(LOGS / "field-gold-2026-10-22"))
import linking  # noqa: E402

replay_full = harness.replay_full
CAP_USD = 1.0
PRICE = (0.15e-6, 0.60e-6)
R22_CACHE = LOGS / "input-constraints-2026-10-21" / "settings-reads.json"
LINKS = HERE / "links-reads.json"
replay_full.SETTINGS_READS.update({f"{d['task']}\x00{d['workflow']}": d["read"]
                                   for d in json.loads(R22_CACHE.read_text())["reads"] if d["read"]})


def _env():
    for line in (replay_full.units.MAIN / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def _workflows(task: str, payload: dict) -> list[str]:
    from netzoo_agent_core.interpretation.settings_links import link_workflows
    return link_workflows(task, payload)


def inputs():
    pairs, readings = {}, 0
    for _key, _folder, _sid, task, payload, _reread, _found, _n in harness.readings():
        readings += 1
        if workflows := _workflows(task, payload):
            pairs[(task, tuple(workflows))] = None
    rows = [{"task": task, "workflows": list(workflows)} for task, workflows in pairs]
    (HERE / "inputs.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{readings} readings; {len(rows)} distinct (request, workflows) inputs;",
          dict(Counter(len(r["workflows"]) for r in rows)))


def ask():
    _env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.settings_links_call import invoke_settings_links
    from netzoo_agent_core.llm import _estimated_tokens
    rows = json.loads((HERE / "inputs.json").read_text())
    saved = json.loads(LINKS.read_text()) if LINKS.exists() else {"usd": 0.0, "reads": []}
    done, usd = saved["reads"], saved["usd"]
    have = {(d["task"], tuple(d["workflows"])) for d in done if d["read"] is not None}
    done = [d for d in done if (d["task"], tuple(d["workflows"])) in have]
    rows = [row for row in rows if (row["task"], tuple(row["workflows"])) not in have]
    print(f"{len(rows)} reads to ask; spent so far US${usd:.4f}")
    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, 2000)

    def one(row):
        read, raw, input_text, output_text, error = invoke_settings_links(llm, row["task"], row["workflows"])
        usage = getattr(raw, "usage_metadata", None) or {}
        tokens = [usage.get("input_tokens") or _estimated_tokens(input_text),
                  usage.get("output_tokens") or _estimated_tokens(output_text)]
        return {**row, "read": read.model_dump() if read is not None else None,
                "error": f"{type(error).__name__}: {error}"[:300] if error else None, "tokens": tokens}

    for start in range(0, len(rows), 40):
        if usd >= CAP_USD:
            print("hard cap reached; stopping")
            break
        with ThreadPoolExecutor(6) as pool:
            for row in pool.map(one, rows[start:start + 40]):
                done.append(row)
                usd += row["tokens"][0] * PRICE[0] + row["tokens"][1] * PRICE[1]
        LINKS.write_text(json.dumps({"model": model, "usd": round(usd, 4), "reads": done}, indent=1,
                                    ensure_ascii=False))
        print(f"{min(start + 40, len(rows))}/{len(rows)} US${usd:.4f}")
    print(f"failed reads: {sum(d['read'] is None for d in done)}")


def _reads() -> dict:
    return {(d["task"], tuple(d["workflows"])): d["read"] for d in json.loads(LINKS.read_text())["reads"]
            if d["read"] is not None}


def _builder(task: str, found: list[dict]):
    from replay import _proposal
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.input_bindings import bound_expression_samples
    study = replay_full._first(found, "routing.study_purpose_detected") or {}
    claims = {claim: quote for claim, quote in study.get("claims") or ()}
    counted = bound_expression_samples(task)

    def build(reading: dict):
        proposal = _proposal(reading)
        return build_capability_check(task, proposal, claims, counted)[0] if proposal is not None else None
    return build


def _guarded(task: str, payload: dict, reread: dict | None, found: list[dict], reads: dict):
    """(payload, reread, kept, held) with the B1 links merged as live merges them; unchanged with no read."""
    from netzoo_agent_core.interpretation.settings_links import (
        guarded_links, links_model, merged_reading, reading_doubts, verified_links, without_emptier)
    workflows = tuple(_workflows(task, payload))
    read = reads.get((task, workflows))
    if not workflows or read is None:
        return payload, reread, [], []
    links, empty = verified_links(task, list(workflows), links_model(workflows).model_validate(read),
                                  reading_doubts(task, payload))
    links = without_emptier(task, payload, links)
    if not links:
        return payload, reread, [], []
    kept, held = guarded_links(task, payload, links, empty, _builder(task, found))
    if not kept:
        return payload, reread, [], held
    merged = merged_reading(task, payload, kept, empty)
    if reread and isinstance(reread.get("reread"), dict):
        reread = {**reread, "reread": merged_reading(task, reread["reread"], kept, empty, add=False)}
    return merged, reread, kept, held


def _sign_p(fixed: int, broken: int) -> float:
    n = fixed + broken
    return sum(math.comb(n, k) for k in range(fixed, n + 1)) / 2 ** n if n else 1.0


def score():
    reads = _reads()
    labels = {path.stem.split("-", 1)[1]: {item["id"]: item for item in json.loads(path.read_text())["items"]}
              for path in (LOGS / "field-gold-2026-10-22").glob("labels-*.json")}
    per_unit = defaultdict(lambda: {"old": Counter(), "new": Counter()})
    extra = {"old": set(), "new": set()}
    rows = []
    for _key, _folder, sid, task, payload, reread, found, _n in harness.readings():
        match = harness.SESSION.match(sid)
        if not match:
            continue
        where, item = (("core", match.group("item")) if match.group("item")
                       else (linking.SETS.get(match.group("set")), match.group("hitem")))
        gold = labels.get(where, {}).get(item)
        if gold is None:
            continue
        merged, merged_reread, kept, held = _guarded(task, payload, reread, found, reads)
        arms = {}
        for arm, (reading, again, also) in (("old", (payload, reread, [])),
                                            ("new", (merged, merged_reread, [(l["name"], l["quote"]) for l in held]))):
            settings, results = linking.reader_links(reading, again, found)
            units = [u for u in linking.score(task, gold, settings + also, results) if u["field"] == "settings"]
            arms[arm] = units
            for unit in units:
                if unit["kind"] == "extra":
                    extra[arm].add((where, item, unit["read"][0]))
                else:
                    per_unit[(where, item, unit["quote"], unit["gold"], unit["kind"])][arm][unit["outcome"]] += 1
        rows.append({"session": sid, "set": where, "item": item,
                     "kept": [{k: v for k, v in l.items() if k != "span"} for l in kept],
                     "held": [{k: v for k, v in l.items() if k != "span"} for l in held], **arms})
    (HERE / "score.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))

    def majority(counts: Counter) -> str:
        top = counts.most_common()
        if not top:
            return "missed"
        best = [name for name, n in top if n == top[0][1]]
        return best[0] if len(best) == 1 else ("not_right" if "right" in best else best[0])

    report = {}
    for kind in ("option", "declared"):
        units = {k: v for k, v in per_unit.items() if k[4] == kind}
        fixed = [k for k, v in units.items() if majority(v["old"]) != "right" and majority(v["new"]) == "right"]
        broken = [k for k, v in units.items() if majority(v["old"]) == "right" and majority(v["new"]) != "right"]
        right = {arm: sum(majority(v[arm]) == "right" for v in units.values()) for arm in ("old", "new")}
        wrong = {arm: sum(majority(v[arm]) == "wrong" for v in units.values()) for arm in ("old", "new")}
        report[kind] = {"units": len(units), "right": right, "wrong": wrong, "fixed": len(fixed),
                        "broken": len(broken), "p": round(_sign_p(len(fixed), len(broken)), 6),
                        "fixed_units": [list(k[:4]) for k in fixed], "broken_units": [list(k[:4]) for k in broken]}
        if kind == "option":
            items = {(k[0], k[1]) for k in units}
            extras = {arm: len({e for e in extra[arm] if (e[0], e[1]) in items}) for arm in ("old", "new")}
            report[kind]["extra"] = extras
            report[kind]["precision"] = {arm: round(right[arm] / max(1, right[arm] + wrong[arm] + extras[arm]), 4)
                                         for arm in ("old", "new")}
            report[kind]["extra_new_only"] = sorted(map(list, (extra["new"] - extra["old"])))
    o, d = report["option"], report["declared"]
    report["gates"] = {
        "B-G1": o["fixed"] - o["broken"] >= 6 and o["p"] < 0.05,
        "B-G2": o["precision"]["old"] - o["precision"]["new"] <= 0.02,
        "B-G3": d["broken"] <= d["fixed"]}
    (HERE / "score-summary.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for kind in ("option", "declared"):
        r = report[kind]
        print(f"{kind}: {r['units']} units; right {r['right']['old']} -> {r['right']['new']}; wrong "
              f"{r['wrong']['old']} -> {r['wrong']['new']}; fixed {r['fixed']} broken {r['broken']} p={r['p']}"
              + (f"; extra {r['extra']}; precision {r['precision']}" if kind == "option" else ""))
    print("gates", report["gates"])


def _relabel(rows: dict) -> dict:
    relabels = json.loads((LOGS / "harness-repair-2026-10-23" / "gold-p2.json").read_text())["relabels"]
    for row in rows.values():
        if (found := relabels.get(row["session"])) and row["turn"] == "t1":
            assert row["gold"] == found["from"], (row["session"], row["gold"])
            row["gold"] = found["to"]
    return rows


def _arm(new: bool, reads: dict) -> dict:
    from netzoo_agent_core.interpretation import core_decision
    from netzoo_agent_core.interpretation.settings_links import held_core
    real = core_decision.decide_core
    captured = {}

    def capture(*args, **kwargs):
        captured["core"] = real(*args, **kwargs)
        return captured["core"]

    core_decision.decide_core = capture
    by_session, core_gold = harness._gold()
    rows = {}
    try:
        for key, folder, sid, task, payload, reread, found, _n in harness.readings():
            held = []
            if new:
                payload, reread, _kept, held = _guarded(task, payload, reread, found, reads)
            captured.clear()
            try:
                call = replay_full.replay(folder, task, payload, reread, found)
            except Exception as error:  # noqa: BLE001 -- counted, never hidden
                rows[key] = {"session": sid, "turn": folder.name, "gold": harness._label(sid, by_session, core_gold),
                             "kind": "error", "error": f"{type(error).__name__}: {error}"[:200]}
                continue
            core = captured.get("core")
            kind, basis = call["kind"], call.get("basis")
            if core is not None and held:
                asked = held_core(core, held)
                kind, basis = asked.kind, asked.basis
            problems = sorted({str(p) for row in call.get("rows") or [] for p in (row["limits"] or []) +
                               (row["violations"] or [])})
            rows[key] = {"session": sid, "turn": folder.name, "task": task,
                         "gold": harness._label(sid, by_session, core_gold), "kind": kind, "basis": basis,
                         "partial": call.get("partial"), "problems": problems,
                         "held": [{k: v for k, v in l.items() if k != "span"} for l in held]}
    finally:
        core_decision.decide_core = real
    return _relabel(rows)


def replay():
    reads = _reads()
    old, new = _arm(False, reads), _arm(True, reads)
    (HERE / "replay-old.json").write_text(json.dumps(old, indent=1, ensure_ascii=False))
    (HERE / "replay-new.json").write_text(json.dumps(new, indent=1, ensure_ascii=False))
    labelled = [k for k, r in old.items() if r["gold"] and r["kind"] != "error"]
    right = {arm: sum(rows[k]["kind"] == rows[k]["gold"] for k in labelled) for arm, rows in (("old", old),
                                                                                                ("new", new))}
    breaks = [k for k in labelled if old[k]["kind"] == old[k]["gold"] and new[k]["kind"] != new[k]["gold"]]
    fixes = [k for k in labelled if old[k]["kind"] != old[k]["gold"] and new[k]["kind"] == new[k]["gold"]]
    new_problems = {k: sorted(set(new[k]["problems"]) - set(old[k]["problems"])) for k in old
                    if new[k].get("problems") is not None and old[k].get("problems") is not None
                    and set(new[k]["problems"]) - set(old[k]["problems"])}
    cost = [k for k in labelled if old[k]["gold"] == "DO" and old[k]["kind"] == "DO" and new[k]["kind"] == "ASK"]
    fa_to_ask = [k for k in labelled if old[k]["gold"] == "DECLINE" and old[k]["kind"] == "DO"
                 and new[k]["kind"] == "ASK"]
    summary = {"labelled": len(labelled), "right": right, "breaks": [[k, old[k]["session"], old[k]["kind"],
                                                                       new[k]["kind"], old[k]["gold"]] for k in breaks],
               "fixes": [[k, old[k]["session"], old[k]["kind"], new[k]["kind"], old[k]["gold"]] for k in fixes],
               "new_problems": {old[k]["session"] + "/" + old[k]["turn"]: v for k, v in new_problems.items()},
               "gold_DO_to_ASK": [old[k]["session"] for k in cost],
               "gold_DECLINE_DO_to_ASK": [old[k]["session"] for k in fa_to_ask],
               "questions": [{"session": new[k]["session"], "held": new[k]["held"]} for k in new
                             if new[k].get("held") and new[k]["kind"] == "ASK" and new[k]["basis"] == "setting_link_fact"],
               "gates": {"B-G4": len(breaks) <= 2, "B-G5": not new_problems}}
    (HERE / "replay-summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(f"labelled {len(labelled)}; right {right}; breaks {len(breaks)}; fixes {len(fixes)}; "
          f"new problems in {len(new_problems)} readings; gold DO->ASK {len(cost)}; gold DECLINE DO->ASK "
          f"{len(fa_to_ask)}; gates {summary['gates']}")


if __name__ == "__main__":
    {"inputs": inputs, "ask": ask, "score": score, "replay": replay}[sys.argv[1]]()
