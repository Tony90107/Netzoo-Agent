"""Harness repair P5 round 1 scoring (ROUND-P5.md section 5; declared before the run, no model calls).

Usage: python3 score_p5.py facts [TAG]     -> fact-sheet / fact-key (blind: every ASK turn 1 on an ask item or a
                                              multi-turn item, systems and order hidden)
       python3 score_p5.py replies [TAG]   -> replies-TAG.json (every final DECLINE / PARTIAL reply, split into
                                              statements, for ROUND-19's frozen judge.py)
       python3 score_p5.py score [TAG]     -> score-TAG.json and printed tables (uses the facts-checked labels)
       python3 score_p5.py compare OLD:SYSTEM NEW:SYSTEM   -> per-item changes between two rounds' scored rows
TAG defaults to p5r1 (round 1); round 2 is p5r2, system E2. Round 1's label files keep their names; others get -TAG.

Calls: DO, PARTIAL (a DO whose core marks part not available), DECLINE, ASK, CLARIFY, UNCHECKED; NONE when a turn ran
no graph call. Error families: FA = false_accept, partly_accept; FR = false_refusal, partial_refusal, over_refusal;
MA = committed_without_asking, refused_without_asking. A needless question is a cost, not an error.
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "p5r1"
SYSTEMS = ("A", "D", "E", "E2")
ITEMS = HERE.parent / "h7" / "items.json"
HARD = ["S02", "S05", "S13", "S28", "S29", "S30", "S31", "S32"]
WAITING = ("ASK", "CLARIFY")
FAMILY = {"false_accept": "FA", "partly_accept": "FA", "false_refusal": "FR", "partial_refusal": "FR",
          "over_refusal": "FR", "committed_without_asking": "MA", "refused_without_asking": "MA",
          "needless_question": "cost"}
EXHAUSTED = "I have asked about this request twice already"
RESTATED = "I couldn't match your reply to an answer"
GENERIC = "Please enter a concrete follow-up question"
BOILERPLATE = ("No files were inspected", "No registered workflow can give this as you asked it",
               "I couldn't match this to a result any registered NetZoo workflow produces, so none is offered")
CANNED = "not matched to any registered workflow"
SEED = 1023


def items() -> dict:
    data = json.loads(ITEMS.read_text())
    return {item["id"]: item for item in data["single"] + data["multi"]}


def norm(names) -> set:
    return {str(n).strip().upper().replace("LIONESS ", "LIONESS-") for n in names or []}


def turn_core(turn: Path) -> dict | None:
    core = None
    for trace in sorted(turn.glob("trace-*.jsonl")):
        for line in trace.read_text().splitlines():
            if '"core.decision"' in line:
                row = json.loads(line)
                if row.get("event_type") == "core.decision":
                    core = row["payload"]
    return core


def actual(core: dict | None) -> str:
    if core is None:
        return "NONE"
    return "PARTIAL" if core.get("kind") == "DO" and core.get("partial") else core.get("kind", "NONE")


def reply_of(turn: Path, core: dict | None) -> str:
    """What the user saw: the graph turn's last reply, or the prompt a turn without a graph call printed."""
    if core is not None and (turn / "session.json").exists():
        said = [m["content"] for m in json.loads((turn / "session.json").read_text()).get("messages", [])
                if m["role"] == "assistant"]
        return said[-1] if said else ""
    text = (turn / "stdout.txt").read_text(errors="replace")
    return text.rsplit("Next step", 1)[-1] if "Next step" in text else text[-1500:]


def turns(folder: Path) -> list[dict]:
    job = json.loads((folder / "job.json").read_text())
    found = []
    for index, turn in enumerate(sorted(folder.glob("t*"), key=lambda p: int(p.name[1:]))):
        manifest = json.loads((turn / "manifest.json").read_text())
        core = turn_core(turn)
        reply = reply_of(turn, core)
        session = json.loads((turn / "session.json").read_text()) if (turn / "session.json").exists() else {}
        found.append({"turn": turn.name, "sent": job["sent"][index] if index < len(job["sent"]) else None,
                      "exit": manifest["exit"], "seconds": manifest["finished"] - manifest["started"],
                      "call": actual(core), "core": core, "reply": reply,
                      "reply_type": ("exhausted" if EXHAUSTED in reply else "restated" if RESTATED in reply
                                     else "generic" if GENERIC in reply else "graph" if core else "other"),
                      "task_state": session.get("task_state")})
    return found


def outcome(expected: str, also: list, gold_workflows: list, core: dict | None, right_fact=None) -> str:
    call, ok = actual(core), {expected, *(also or [])}
    if call in ok:
        if call in ("DO", "PARTIAL"):
            offered, gold = norm((core or {}).get("workflows")), norm(gold_workflows)
            if offered and gold and not offered <= gold:
                return "extra_options" if offered & gold else "wrong_workflow"
        if call == "ASK" and expected == "ASK" and right_fact is False:
            return "wrong_fact"
        return "correct"
    if call == "UNCHECKED":
        return "unchecked"
    if call == "NONE":
        return "no_call"
    if expected == "DO":
        return {"PARTIAL": "partial_refusal", "DECLINE": "false_refusal"}.get(call, "needless_question")
    if expected == "PARTIAL":
        return {"DO": "false_accept", "DECLINE": "over_refusal"}.get(call, "needless_question")
    if expected == "DECLINE":
        return {"DO": "false_accept", "PARTIAL": "partly_accept"}.get(call, "undecided")
    if call in WAITING:
        return "wrong_question_kind"
    return "committed_without_asking" if call == "DO" else "refused_without_asking"


def sessions() -> dict:
    found = {}
    for job in sorted((HERE / "live" / TAG).glob("*/job.json")):
        meta = json.loads(job.read_text())
        found[(meta["item"], meta["system"])] = {"job": meta, "turns": turns(job.parent)}
    return found


def multi_result(item: dict, run: dict, right_fact=None) -> dict:
    found, job = run["turns"], run["job"]
    first = found[0]
    t1 = outcome(item["t1_call"], [], item["workflows"], first["core"], right_fact)
    result = {"t1": t1, "t1_call": first["call"], "turns": [t["call"] if t["core"] else t["reply_type"] for t in found],
              "sent": job["sent"]}
    if first["call"] not in WAITING:
        return {**result, "success": False, "final": t1, "why": "turn 1 did not wait"}
    kind = item["type"]
    if kind == "unknown":
        later = found[1:]
        guessed = any(t["call"] in ("DO", "PARTIAL", "DECLINE") for t in later)
        stopped = bool(later) and (later[-1]["reply_type"] == "exhausted" or later[-1]["reply"].startswith(EXHAUSTED))
        return {**result, "guessed": guessed, "stopped_asking": stopped, "success": not guessed and stopped,
                "final": "guessed" if guessed else "stopped" if stopped else "asked_again"}
    if kind == "switch":
        last = found[1] if len(found) > 1 else None
        final = outcome(item["new_request_call"], [], item["new_request_workflows"], last and last["core"])
        state = (last or {}).get("task_state") or {}
        carried = bool(state.get("facts"))
        return {**result, "final": final, "carried_facts": carried, "success": final == "correct" and not carried}
    asked = len(job["sent"]) > 1 and job["sent"][1] == "answer"
    last = next((t for t in reversed(found[1:]) if t["core"] is not None), None)
    final = outcome(item["final_call"], [], item["final_workflows"], last and last["core"]) if last else "no_call"
    if len(found) > 1 and found[-1]["core"] is None:
        final = "no_call"  # the last reply never reached a graph turn
    return {**result, "fact_asked_by_keywords": asked, "final": final,
            "success": asked and final == "correct" and (kind != "correct" or len(found) == 3)}


def facts():
    known, pool = items(), []
    for (item_id, system), run in sessions().items():
        item, first = known[item_id], run["turns"][0]
        is_ask = item.get("class") == "ask" or "type" in item
        if is_ask and first["call"] == "ASK":
            what = item["deciding_fact"]["what"] if isinstance(item["deciding_fact"], dict) else item["deciding_fact"]
            pool.append((item_id, system, item["prompt"], what,
                         [f.get("question", "") for f in first["core"].get("facts") or []]))
    random.Random(SEED).shuffle(pool)
    sheet, key = [], {}
    for index, (item_id, system, prompt, what, questions) in enumerate(pool, 1):
        sid = f"F{index:03d}"
        key[sid] = f"{item_id}|{system}"
        sheet.append({"id": sid, "request": prompt, "deciding_fact": what, "questions_asked": questions})
    (HERE / _named("fact-sheet")).write_text(json.dumps(sheet, indent=1, ensure_ascii=False))
    (HERE / _named("fact-key")).write_text(json.dumps(key, indent=1))
    print(f"{len(sheet)} ASK turns on the blind fact sheet")


def statements(reply: str) -> list[dict]:
    """The reply's statements: each numbered item ("1. \"quote\" -- text") and each other paragraph, boilerplate out.
    The canned not-matched line is R0 (no reason); every other statement is R1 (judged)."""
    found = []
    for block in [b.strip() for b in reply.split("\n\n") if b.strip()]:
        for line in [l.strip() for l in block.splitlines() if l.strip()]:
            if line.endswith(":") or any(line.startswith(b) for b in BOILERPLATE):
                continue
            match = re.match(r'^\d+\.\s+"(.+?)"\s+--\s+(.*)$', line)
            quote, text = (match.group(1), match.group(2)) if match else ("", re.sub(r"^[-*\d.\s]+", "", line))
            if text:
                found.append({"quote": quote, "status": "not_available", "type": "R0" if CANNED in text else "R1",
                              "text": text})
    return found


def replies():
    known, rows = items(), []
    for (item_id, system), run in sorted(sessions().items()):
        item = known[item_id]
        last = next((t for t in reversed(run["turns"]) if t["core"] is not None), None)
        if last is None or last["call"] not in ("DECLINE", "PARTIAL"):
            continue
        sent = run["job"]["sent"]
        if "type" not in item:
            gold, task = item["expected_call"], item["prompt"]
        elif last is run["turns"][0]:
            gold, task = item["t1_call"], item["prompt"]
        elif item["type"] == "switch":
            gold, task = item["new_request_call"], item["new_request"]
        else:
            said = {"answer": (item.get("deciding_fact") or {}).get("answer", ""),
                    "correction": item.get("correction", ""), "not_sure": "I'm not sure about that."}
            gold = item["final_call"]
            task = item["prompt"] + " | follow-up: " + " | ".join(said.get(branch, "") for branch in sent[1:])
        rows.append({"session": run["job"]["session"], "item": item_id, "system": system, "task": task,
                     "gold": gold, "gold_reason": item.get("final_reason") or item.get("reason", ""),
                     "gold_evidence": item.get("evidence", ""), "kind": "DECLINE" if last["call"] == "DECLINE" else "DO",
                     "partial": last["call"] == "PARTIAL", "lines": statements(last["reply"]) or
                     [{"quote": "", "status": "not_available", "type": "R0", "text": ""}]})
    (HERE / f"replies-{TAG}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} final DECLINE/PARTIAL replies; by system {dict(Counter(r['system'] for r in rows))}; "
          f"statements {sum(len(r['lines']) for r in rows)}")


def sign_test(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(wins, losses) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def wilson(k: int, n: int) -> str:
    if n == 0:
        return "-"
    z, p = 1.96, k / n
    centre, half = (p + z * z / (2 * n)) / (1 + z * z / n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return f"{max(0, centre - half):.0%}-{min(1, centre + half):.0%}"


def score():
    known, runs = items(), sessions()
    labelled = json.loads((HERE / _named("facts-checked")).read_text()) if (HERE / _named("facts-checked")).exists() else {}
    key = json.loads((HERE / _named("fact-key")).read_text()) if (HERE / _named("fact-key")).exists() else {}
    fact_ok = {key[sid]: value for sid, value in labelled.items() if sid in key}
    rows = []
    for (item_id, system), run in sorted(runs.items()):
        item = known[item_id]
        right_fact = fact_ok.get(f"{item_id}|{system}")
        if "type" in item:
            rows.append({"item": item_id, "system": system, "part": "multi", "type": item["type"],
                         **multi_result(item, run, right_fact)})
        else:
            first = run["turns"][0]
            result = outcome(item["expected_call"], item.get("also_acceptable"), item["workflows"], first["core"],
                             right_fact)
            rows.append({"item": item_id, "system": system, "part": "single", "class": item["class"],
                         "expected": item["expected_call"], "call": first["call"], "outcome": result,
                         "success": result == "correct", "hard": item_id in HARD})
    report = {"single": {}, "multi": {}, "paired": {}, "costs": {}}
    for system in SYSTEMS:
        mine = [r for r in rows if r["system"] == system and r["part"] == "single"]
        if mine:
            fam = Counter(FAMILY.get(r["outcome"], "other" if r["outcome"] != "correct" else "correct") for r in mine)
            report["single"][system] = {
                "correct": f"{fam['correct']}/{len(mine)}", "ci": wilson(fam["correct"], len(mine)),
                "FA": f"{fam['FA']}/{sum(r['expected'] in ('DECLINE', 'PARTIAL') for r in mine)}",
                "FR": f"{fam['FR']}/{sum(r['expected'] in ('DO', 'PARTIAL') for r in mine)}",
                "MA": f"{fam['MA']}/{sum(r['expected'] in WAITING for r in mine)}",
                "needless": fam["cost"], "other": dict(Counter(r["outcome"] for r in mine
                                                               if FAMILY.get(r["outcome"]) is None
                                                               and r["outcome"] != "correct")),
                "by_class": {c: f"{sum(r['success'] for r in mine if r['class'] == c)}/"
                                f"{sum(r['class'] == c for r in mine)}" for c in ("do", "dont", "ask", "vague")},
                "hard": f"{sum(r['success'] for r in mine if r['hard'])}/{sum(r['hard'] for r in mine)}"}
        multi = [r for r in rows if r["system"] == system and r["part"] == "multi"]
        if multi:
            report["multi"][system] = {
                "success": f"{sum(r['success'] for r in multi)}/{len(multi)}",
                "t1_waited": f"{sum(r['t1_call'] in WAITING for r in multi)}/{len(multi)}",
                "t1_FA": sum(FAMILY.get(r["t1"]) == "FA" for r in multi),
                "by_type": {t: f"{sum(r['success'] for r in multi if r['type'] == t)}/"
                               f"{sum(r['type'] == t for r in multi)}"
                            for t in ("answer", "volunteer", "correct", "switch", "unknown")},
                "unknown_guessed": sum(r.get("guessed", False) for r in multi),
                "unknown_stopped": sum(r.get("stopped_asking", False) for r in multi),
                "switch_carried_facts": sum(r.get("carried_facts", False) for r in multi)}
    for left, right, part in (("A", "E", "single"), ("A", "E", "multi"), ("D", "E", "multi")):
        by = defaultdict(dict)
        for r in rows:
            if r["part"] == part and r["system"] in (left, right):
                by[r["item"]][r["system"]] = r["success"]
        fixes = sorted(i for i, s in by.items() if s.get(right) and not s.get(left) and len(s) == 2)
        breaks = sorted(i for i, s in by.items() if s.get(left) and not s.get(right) and len(s) == 2)
        report["paired"][f"{left}->{right} {part}"] = {"fixes": fixes, "breaks": breaks,
                                                       "sign_p": round(sign_test(len(fixes), len(breaks)), 3)}
    for system in SYSTEMS:
        calls, seconds, count = {}, [], 0
        for (item_id, sys_name), run in runs.items():
            if sys_name != system:
                continue
            for t in run["turns"]:
                count += 1
                seconds.append(t["seconds"])
            folder = HERE / "live" / TAG / run["job"]["session"]
            for path in list(folder.glob("t*/session.json")) + list(folder.glob("t*/trace-*.jsonl")):
                usages = ([json.loads(path.read_text()).get("token_usage") or {}] if path.suffix == ".json" else
                          [(json.loads(l).get("payload") or {}).get("token_usage") or {}
                           for l in path.read_text().splitlines() if '"run.finished"' in l])
                for usage in usages:
                    for call in usage.get("calls", []):
                        calls[call["call_id"]] = (call.get("cost_micro_usd") or 0, call.get("total_tokens") or 0)
        if count:
            report["costs"][system] = {"turns": count, "usd": round(sum(c for c, _ in calls.values()) / 1e6, 4),
                                       "tokens": sum(t for _, t in calls.values()),
                                       "sec_per_turn": round(sum(seconds) / count, 1)}
    report["fact_labels"] = {"labelled": len(fact_ok), "deciding_fact_asked": sum(fact_ok.values())}
    (HERE / f"score-{TAG}.json").write_text(json.dumps({"report": report, "rows": rows}, indent=1, default=str))
    print(json.dumps(report, indent=1))


def _named(stem: str) -> str:
    return f"{stem}.json" if TAG == "p5r1" else f"{stem}-{TAG}.json"


def compare(old: str, new: str):
    """Per item, round to round: which became right, which became wrong (scored rows of score-TAG.json)."""
    (old_tag, old_system), (new_tag, new_system) = old.split(":"), new.split(":")
    rows = {tag: {r["item"]: r for r in json.loads((HERE / f"score-{tag}.json").read_text())["rows"] if r["system"] == s}
            for tag, s in ((old_tag, old_system), (new_tag, new_system))}
    before, after = rows[old_tag], rows[new_tag]
    shared = sorted(set(before) & set(after))
    fixes = [i for i in shared if after[i]["success"] and not before[i]["success"]]
    breaks = [i for i in shared if before[i]["success"] and not after[i]["success"]]
    for part in ("single", "multi"):
        mine = [i for i in shared if before[i]["part"] == part]
        print(f"{part}: {old} {sum(before[i]['success'] for i in mine)}/{len(mine)} -> {new} "
              f"{sum(after[i]['success'] for i in mine)}/{len(mine)}")
    print(f"became right {fixes}; became wrong {breaks}; sign p = {sign_test(len(fixes), len(breaks)):.3f}")
    for i in fixes + breaks:
        b, a = before[i], after[i]
        print(f"  {i}: {b.get('outcome', b.get('final'))} -> {a.get('outcome', a.get('final'))}")


if __name__ == "__main__":
    if sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        TAG = sys.argv[2] if len(sys.argv) > 2 else TAG
        {"facts": facts, "replies": replies, "score": score}[sys.argv[1]]()
