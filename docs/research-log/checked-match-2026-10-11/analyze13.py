"""Log 405: metrics and the frozen gates of FREEZE405.md for a labelled heldout13 round.

Usage (repository root):
  python docs/research-log/checked-match-2026-10-11/analyze13.py <tag> disagreements
  python docs/research-log/checked-match-2026-10-11/analyze13.py <tag> gates

Reads live/<tag>-structure.json (collect13.py), the blind key, both labellers' labels and my resolution of
every disagreement. No gate is printed unless every session and requirement is labelled by both labellers,
every disagreement is resolved, the frozen round is complete and every replay equals its recording.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE / "live"
POSITIVE = {"supported", "with_step", "needs_input"}
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
LABELS = SAYS_GIVEN | {"PARTLY", "NOT_GIVEN", "UNCONFIRMED", "ASKED", "OMITTED"}
REPEATS = 3
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout13.json").read_text())["items"]}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def disagreements(tag):
    a, b = load(tag, "labels-A"), load(tag, "labels-B")
    out = {}
    for code in sorted(set(a) | set(b)):
        x, y = a.get(code) or {}, b.get(code) or {}
        if x.get("R") != y.get("R") or (x.get("contradiction", "no") == "no") != (y.get("contradiction", "no") == "no"):
            out[code] = {"A": x, "B": y}
    return out


def validate(tag, rows, key):
    expected = Counter((arm, item, rep) for arm in ("base", "cand") for item in ITEMS for rep in range(1, REPEATS + 1))
    if Counter((row.get("arm"), row.get("item"), row.get("rep")) for row in rows.values()) != expected:
        raise ValueError("Incomplete or duplicate frozen round coverage")
    if set(key.values()) != set(rows) or len(key) != len(rows):
        raise ValueError("Blinding map does not cover every session once")
    for sid, row in rows.items():
        if row.get("missing") or not row.get("replay_equal"):
            raise ValueError(f"Missing session or unequal replay: {sid}")

    def check(code, label, role):
        row = rows[key[code]]
        values = label.get("R")
        if not isinstance(values, list) or len(values) != len(row["layers"]) or any(v not in LABELS for v in values):
            raise ValueError(f"Invalid requirement labels: {role} {code}")
        contradiction = label.get("contradiction")
        if not (contradiction == "no" or isinstance(contradiction, str) and contradiction.startswith("yes:")):
            raise ValueError(f"Invalid contradiction label: {role} {code}")

    for role in ("A", "B"):
        labels = load(tag, f"labels-{role}")
        if set(labels) != set(key):
            raise ValueError(f"Incomplete label coverage: labeller {role}")
        for code, label in labels.items():
            check(code, label, role)
    resolved = load(tag, "labels-resolved")
    if set(resolved) != set(disagreements(tag)):
        raise ValueError("Unresolved or stale labeller disagreements")
    for code, label in resolved.items():
        check(code, label, "resolved")


def adoption_right(item: dict, action: str) -> bool:
    """The adopted workflow gives every requirement of an item that asks for nothing unsupported."""
    name = action.removeprefix("run_").upper().replace("_", "-")
    return all(req["expect"] in POSITIVE and name in req.get("by", []) for req in item["requirements"])


def main(tag, mode):
    if mode == "disagreements":
        split = disagreements(tag)
        (LIVE / f"{tag}-disagreements.json").write_text(json.dumps(split, indent=1, ensure_ascii=False))
        print(f"{len(split)} sessions disagree -> live/{tag}-disagreements.json")
        return
    rows = json.loads((LIVE / f"{tag}-structure.json").read_text())
    key = load(tag, "blind-key")
    validate(tag, rows, key)
    a, resolved = load(tag, "labels-A"), load(tag, "labels-resolved")
    final = {key[code]: resolved.get(code, a[code]) for code in key}
    out = []

    def say(text=""):
        out.append(text)
        print(text)

    c = {arm: Counter() for arm in ("base", "cand")}
    per_item = defaultdict(Counter)
    adoptions = []
    for sid, row in rows.items():
        arm, family, label = row["arm"], row["family"], final[sid]
        if row.get("errors"):
            c[arm]["provider_error"] += 1
        if row["action"] == "no_tool" and not any(status == "success" for _, status in row["check_calls"]):
            c[arm]["unchecked"] += 1
        if row.get("conflicts"):
            c[arm]["conflict_code"] += 1
        if row["contradictions"]:
            c[arm]["CS_code"] += 1
        if str(label.get("contradiction", "no")).startswith("yes"):
            c[arm]["CS_label"] += 1
        if arm == "cand" and row.get("adopted"):
            right = adoption_right(ITEMS[row["item"]], row["adopted"])
            adoptions.append((sid, row["adopted"], right))
        for layer, given in zip(row["layers"], label["R"]):
            positive = layer["expect"] in POSITIVE
            per_item[(arm, row["item"])][given] += 1
            if not positive and given in SAYS_GIVEN:
                c[arm]["FC"] += 1
            if positive and given == "NOT_GIVEN":
                c[arm]["FR"] += 1
            if positive and given in SAYS_GIVEN:
                c[arm]["POS_GIVEN"] += 1
                if family == "CE":
                    c[arm]["CE_GIVEN"] += 1
            if given == "OMITTED":
                c[arm]["OM"] += 1

    for arm in ("base", "cand"):
        x = c[arm]
        say(f"{arm}: provider errors {x['provider_error']}, unchecked {x['unchecked']}; FC {x['FC']}, FR {x['FR']}, "
            f"OM {x['OM']}, positives given {x['POS_GIVEN']} (CE {x['CE_GIVEN']}); contradictions: labeller "
            f"{x['CS_label']}, code {x['CS_code']}, of which check-vs-routing conflicts {x['conflict_code']}")
    right = sum(1 for _, _, ok in adoptions if ok)
    say(f"cand adoptions: {len(adoptions)}, right {right}: {adoptions}")

    b, k = c["base"], c["cand"]
    gates = {
        "V1": all(c[arm]["provider_error"] <= 10 and c[arm]["unchecked"] <= 10 for arm in c),
        "G1": None if b["CS_label"] < 4 else k["CS_label"] <= 0.6 * b["CS_label"],
        "G1c": k["conflict_code"] == 0,
        "G2": k["FC"] <= b["FC"] + 1,
        "G3": k["POS_GIVEN"] >= b["POS_GIVEN"] - 1 and k["FR"] <= b["FR"] + 1,
        "G4": None if len(adoptions) < 3 else right >= 0.9 * len(adoptions),
        "G5": k["CE_GIVEN"] >= b["CE_GIVEN"],
        "A1": k["OM"] <= b["OM"] + 2,
    }
    for name, ok in gates.items():
        say(f"{name} -> {'NO INFORMATION' if ok is None else 'PASS' if ok else 'FAIL'}")
    keep = all(ok is not False for ok in gates.values())
    say(f"keep: {keep}")
    say()
    say("Per item (base | cand):")
    for item in ITEMS:
        say(f"{item}: {dict(per_item[('base', item)])} | {dict(per_item[('cand', item)])}")
    (LIVE / f"{tag}-analysis.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
