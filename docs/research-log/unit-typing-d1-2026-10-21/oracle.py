"""ROUND-11 (collab/ROUND-11-PLAN.md) Q2 and Q3: each recorded reading decided again by this checkout, as read (B)
and with its piece types set to the gold ones (O-a, O-b, O-c, O). No model calls.

Live shape (rounds p4b p4c p5r g4o1 g4o2): the recorded first read and re-read are edited, then rebuilt as
request-facts-round03 `replay.py checks` does (build_capability_check, merge_reread), the recorded second opinion is
applied as credited-counts `replay_so.py` does -- except that each recorded pair is moved to the rebuilt row with the
same quote (an edit shifts row indices) -- then without_legacy_waits when the fact check ran, and decide_core with the
recorded reason code. Condition checks and the ruled-out step are not replayed (as in every replay since ROUND-03),
so B is compared with the recorded calls and every variant is compared with B, never with the round's score.

Variants (asks, about_methods and goal only; every count, setting and attribute inside a kept ask stays as read):
  O-a  results paired with (or repeating) a gold Q or P piece are removed; a Q piece's quote moves to its sentence's
       about_methods
  O-b  extra results (E1, E3, and E2 repeats of a D piece or of an extra) are removed, except the re-read's copy of
       a gold D piece (the re-read reads that piece again; merge_reread folds it into the piece's row)
  O-c  goal set from the gold pieces: result_named with a D piece, else method_named with a Q piece, else purpose_only
  O-ab O-a and O-b (the piece types alone, goal as read; added after the first run, from the plan's parts)
  O    all three
A sentence whose asks or about_methods changed gets its role again: asks, methods_question or background by what it
holds, mixed when it holds more than one.

v7 (Q3): the phase-1 focused readings decided by decide_menu and scored by phase0_gate.score, as read and with every
wanted piece paired to a gold piece given the gold form and every unpaired result piece made context.

Usage: python3 oracle.py OUT.json
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import units  # noqa: E402  (sets the import path to this checkout's scripts)

LOGS = units.WT / "docs/research-log"
sys.path.insert(0, str(LOGS / "request-facts-round03-2026-10-20"))
sys.path.insert(0, str(LOGS / "closed-menu-phase0-2026-10-18"))
VARIANTS = ("B", "O-a", "O-b", "O-c", "O-ab", "O")
TYPE_FORM = {"D": "deliverable", "Q": "question_to_us", "P": "purpose"}


def _events(folder: Path) -> list[dict]:
    return [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]


def _role(sentence: dict) -> str:
    held = [name for name, key in (("asks", "asks"), ("methods_question", "about_methods"), ("background", "has"))
            if sentence.get(key)]
    return held[0] if len(held) == 1 else ("mixed" if held else "background")


def _first_part(quote: str) -> str:
    return quote.replace("…", "...").split("...")[0].strip()


def edit(task: str, truth: dict, payload: dict, reread: dict | None, variant: str):
    """The reading with the variant's gold piece types; returns (payload, reread, what changed)."""
    payload, reread = copy.deepcopy(payload), copy.deepcopy(reread)
    found = units.score(task, truth, units.live_units(payload, reread))
    drop, move, changed = set(), [], Counter()
    for piece in found["pieces"]:
        source, name, _key, index = piece["where"]
        kind = piece["paired"] or piece.get("repeats")
        if variant in ("O-a", "O-ab", "O") and kind in ("Q", "P"):
            drop.add((source, name, index))
            changed[f"removed {kind}"] += 1
            if kind == "Q" and source == "read":
                move.append((name, (payload if source == "read" else reread["reread"])[name]["asks"][index]["quote"]))
        elif (variant in ("O-b", "O-ab", "O") and piece["extra"] is not None and kind not in ("Q", "P")
              and not (source == "reread" and kind == "D")):  # a re-read of a gold piece is that piece, kept
            drop.add((source, name, index))
            changed[f"removed {piece['extra']}"] += 1
    touched = set()
    for source, body in (("read", payload), ("reread", (reread or {}).get("reread") or {})):
        for name, sentence in body.items():
            if not name[1:].isdigit():
                continue
            asks = sentence.get("asks") or []
            kept = [ask for index, ask in enumerate(asks) if (source, name, index) not in drop]
            if len(kept) != len(asks):
                sentence["asks"] = kept
                touched.add((source, name))
    for name, quote in move:
        payload[name].setdefault("about_methods", []).append(quote)
        touched.add(("read", name))
    for source, name in touched:
        if source == "read":
            payload[name]["role"] = _role(payload[name])
    if variant in ("O-c", "O"):
        types = [g["type"] for g in truth["units"]]
        goal = "result_named" if "D" in types else ("method_named" if "Q" in types else "purpose_only")
        conditions = payload.setdefault("conditions", {})
        if conditions.get("goal") != goal:
            piece = next(g for g in found["gold"] if g["type"] == goal_type(goal))
            conditions["goal"], conditions["goal_quote"] = goal, piece["read_as"] or _first_part(piece["quote"])
            changed[f"goal -> {goal}"] += 1
    return payload, reread, dict(changed)


def goal_type(goal: str) -> str:
    return {"result_named": "D", "method_named": "Q", "purpose_only": "P"}[goal]


def decide(folder: Path, task: str, payload: dict, reread: dict | None, events: list[dict]):
    """This checkout's call on the (edited) reading, through the recorded session's decision."""
    from replay import _proposal
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.interpretation.capability_check import (
        apply_second_opinion, build_capability_check, wait_on_asked)
    from netzoo_agent_core.interpretation.core_decision import decide_core
    from netzoo_agent_core.interpretation.reread import merge_reread

    proposal = _proposal(payload)
    if proposal is None:
        return {"kind": "unparsable"}
    check, _ = build_capability_check(task, proposal)
    if reread and reread.get("reread"):
        raw = reread["reread"]
        model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
        again, unplaced = build_capability_check(
            task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)))
        check = merge_reread(task, check, again, reread.get("passages") or [], unplaced)
    opinion = next((e["payload"] for e in events if e["event_type"] == "routing.capability_second_opinion"), None)
    moved = lost = 0
    if opinion and opinion.get("pairs") and opinion.get("answers"):
        before = None
        for event in events:
            if event["event_type"] in ("routing.capability_checked", "routing.capability_reread"):
                before = event["payload"].get("check") or before
            if event["event_type"] == "routing.capability_second_opinion":
                break
        quotes = [row.get("quote") for row in (before or {}).get("requirements", [])]
        rebuilt = [row.quote for row in check.requirements]
        pairs, answers = [], []
        for (index, action, keys), answer in zip(opinion["pairs"], opinion["answers"]):
            quote = quotes[index] if index < len(quotes) else None
            if quote in rebuilt:
                pairs.append((rebuilt.index(quote), action, keys))
                answers.append(answer)
                moved += rebuilt.index(quote) != index
            else:
                lost += 1
        if pairs:
            check = wait_on_asked(apply_second_opinion(check, pairs, answers, task), pairs)
    session = json.loads((folder / "session.json").read_text())
    decision = TaskDecision.model_validate(session["plan"]["decision"])
    if decision.fact_check is not None and decision.fact_check.status == "checked":
        check = without_legacy_waits(check)
    recorded = next((e["payload"] for e in reversed(events) if e["event_type"] == "core.decision"), {})
    reason = recorded.get("evidence", {}).get("reason_code", "") or ""
    core = decide_core(decision.model_copy(update={"capability_check": check}), task, reason_code=reason)
    return {"kind": core.kind, "basis": core.basis, "pairs_moved": moved, "pairs_lost": lost,
            "rows": [[row.kind, row.status, row.quote[:60]] for row in check.requirements]}


def live(truth: dict, tasks: dict) -> list[dict]:
    rows = []
    for name, model in units.ROUNDS.items():
        for item, folder, task, payload, reread, _failed in units.recorded(name):
            if item not in truth or payload is None:
                continue
            events = _events(folder)
            recorded = next((e["payload"] for e in reversed(events) if e["event_type"] == "core.decision"), {})
            row = {"round": name, "model": model, "item": item, "gold": tasks[item]["gold"],
                   "recorded": recorded.get("kind"), "calls": {}}
            for variant in VARIANTS:
                try:
                    edited, again, changed = ((payload, reread, {}) if variant == "B"
                                              else edit(task, truth[item], payload, reread, variant))
                    row["calls"][variant] = {**decide(folder, task, edited, again, events), "changed": changed}
                except Exception as error:  # noqa: BLE001 -- reported, never hidden
                    row["calls"][variant] = {"kind": "error", "error": f"{type(error).__name__}: {error}"[:300]}
            rows.append(row)
    return rows


def v7(truth: dict) -> list[dict]:
    from phase0_gate import score as gate_score
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu

    bench = json.loads(units.V7.read_text())
    items = {i["id"]: i for i in json.loads(units.ITEMS.read_text())["items"]}
    import yaml
    facts = {k: v.get("fact") for k, v in yaml.safe_load(units.GOLD.read_text()).items()}
    rows = []
    for found in bench["rows"]:
        item = items[found["id"]]
        source = found["focus"] if found.get("focus", {}).get("ran") else found
        reading = source["reading"]
        row = {"round": f"v7-{found['rep']}", "item": found["id"], "gold": units.KIND[item["class"]], "calls": {}}
        for variant in ("B", "forms", "extras", "O"):
            edited = copy.deepcopy(reading)
            changed = Counter()
            if variant != "B":
                task = item["prompt"]
                golds = [(units.span(task, g["quote"]), g["type"]) for g in truth[found["id"]]["units"]]
                pairs = sorted(((units.matches(units.span(task, w["quote"]), gs, "half"), wi, gi)
                                for wi, w in enumerate(edited.get("wanted", [])) for gi, (gs, _t) in enumerate(golds)),
                               reverse=True)
                paired, used = {}, set()
                for shared, wi, gi in pairs:
                    if shared and wi not in paired and gi not in used:
                        paired[wi] = gi
                        used.add(gi)
                for wi, w in enumerate(edited.get("wanted", [])):
                    form = w.get("form", "deliverable")
                    if wi in paired and variant in ("forms", "O"):
                        new = TYPE_FORM[golds[paired[wi]][1]]
                        if new != form:
                            w["form"] = new
                            changed[f"{form}->{new}"] += 1
                    elif wi not in paired and form == "deliverable" and variant in ("extras", "O"):
                        w["form"] = "context"
                        changed["extra->context"] += 1
            decision = decide_menu(MenuReading.model_validate(edited), item["prompt"])
            outcome = gate_score(item, decision, facts[found["id"]])
            row["calls"][variant] = {"kind": decision.kind, "outcome": outcome, "changed": dict(changed)}
        rows.append(row)
    return rows


def transitions(rows: list[dict], base: str, variant: str, right) -> Counter:
    found = Counter()
    for row in rows:
        a, b = right(row, base), right(row, variant)
        found["wrong->right" if (not a and b) else "right->wrong" if (a and not b)
              else "right" if a else "wrong->same" if row["calls"][base]["kind"] == row["calls"][variant]["kind"]
              else "wrong->other wrong"] += 1
    return found


def main(out: str):
    truth, tasks = units.gold(), units.items()
    live_rows, v7_rows = live(truth, tasks), v7(truth)
    Path(out).write_text(json.dumps({"live": live_rows, "v7": v7_rows}, indent=1, ensure_ascii=False))

    def live_right(row, variant):
        return row["calls"][variant]["kind"] == row["gold"]

    errors = Counter(v for row in live_rows for v, call in row["calls"].items() if call["kind"] in ("error", "unparsable"))
    print(f"live readings {len(live_rows)}; errors {dict(errors)}")
    for group, names in (("mini", ("p4b", "p4c", "p5r")), ("gpt-4o", ("g4o1", "g4o2"))):
        mine = [row for row in live_rows if row["round"] in names]
        same = sum(row["calls"]["B"]["kind"] == row["recorded"] for row in mine)
        print(f"\n== {group}: {len(mine)} readings; B equals the recorded call {same}; "
              f"recorded right {sum(row['recorded'] == row['gold'] for row in mine)}; "
              f"B right {sum(live_right(row, 'B') for row in mine)}")
        for variant in VARIANTS[1:]:
            print(f"  {variant:4} vs B {dict(transitions(mine, 'B', variant, live_right))}")
        by_class = defaultdict(Counter)
        for row in mine:
            by_class[row["gold"]]["B"] += live_right(row, "B")
            by_class[row["gold"]]["O"] += live_right(row, "O")
            by_class[row["gold"]]["n"] += 1
        print("  by gold class (B -> O right):", {k: f"{v['B']}->{v['O']}/{v['n']}" for k, v in by_class.items()})

    def v7_right(row, variant):
        return row["calls"][variant]["outcome"] == "correct"

    print(f"\n== v7: {len(v7_rows)} readings; B right {sum(v7_right(r, 'B') for r in v7_rows)}")
    for variant in ("forms", "extras", "O"):
        print(f"  {variant:6} vs B {dict(transitions(v7_rows, 'B', variant, v7_right))}")


if __name__ == "__main__":
    main(sys.argv[1])
