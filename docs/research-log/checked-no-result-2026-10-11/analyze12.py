"""Log 404: metrics and the frozen gates of FREEZE404.md for a labelled heldout12 round.

Usage (repository root):
  python docs/research-log/checked-no-result-2026-10-11/analyze12.py <tag> disagreements
  python docs/research-log/checked-no-result-2026-10-11/analyze12.py <tag> gates

Reads live/<tag>-structure.json (collect12.py), live/<tag>-blind-key.json, live/<tag>-labels-{A,B}.json and
live/<tag>-labels-resolved.json (my adjudication of every disagreement). No gate is printed unless both
labellers labelled every session and requirement, every disagreement is resolved, the frozen round is
complete and every replay equals its recording.
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
CONSULT = {"EXPLAINED", "LISTED_ONLY", "REFUSED", "OTHER"}
REPEATS = 3
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout12.json").read_text())["items"]}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def disagreements(tag):
    a, b = load(tag, "labels-A"), load(tag, "labels-B")
    out = {}
    for code in sorted(set(a) | set(b)):
        x, y = a.get(code) or {}, b.get(code) or {}
        if (x.get("R") != y.get("R") or (x.get("contradiction", "no") == "no") != (y.get("contradiction", "no") == "no")
                or x.get("consult") != y.get("consult")):
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
        if row["family"] == "M" and label.get("consult") not in CONSULT:
            raise ValueError(f"Invalid consult label: {role} {code}")

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
    so2 = []
    for sid, row in rows.items():
        arm, family, label = row["arm"], row["family"], final[sid]
        if row.get("errors"):
            c[arm]["provider_error"] += 1
        if row["action"] == "no_tool" and not any(status == "success" for _, status in row["check_calls"]):
            c[arm]["unchecked"] += 1
        if row.get("checked_no_result"):
            c[arm]["checked_no_result"] += 1
        if row["contradictions"]:
            c[arm]["CS_code"] += 1
        if str(label.get("contradiction", "no")).startswith("yes"):
            c[arm]["CS_label"] += 1
        if arm == "cand" and row.get("so2"):
            so2.append((sid, row["so2"]))
        if family == "M":
            consult = label["consult"]
            per_item[(arm, row["item"])][consult] += 1
            if consult in ("LISTED_ONLY", "REFUSED"):
                c[arm]["CL"] += 1
                if ITEMS[row["item"]].get("consult") == "named":
                    c[arm]["CL_named"] += 1
        for layer, given in zip(row["layers"], label["R"]):
            positive = layer["expect"] in POSITIVE
            per_item[(arm, row["item"])][given] += 1
            c[arm]["pos" if positive else "neg"] += 1
            if not positive and given in SAYS_GIVEN:
                c[arm]["FC"] += 1
                c[arm][f"FC_{family}"] += 1
            if positive and given == "NOT_GIVEN":
                c[arm]["FR"] += 1
            if positive and given in ("NOT_GIVEN", "PARTLY"):
                c[arm][f"FRsoft_{family}"] += 1
            if positive and given in ("UNCONFIRMED", "NOT_GIVEN", "PARTLY", "OMITTED"):
                c[arm][f"SR_{family}"] += 1
            if given == "OMITTED":
                c[arm]["OM"] += 1
            if given == "UNCONFIRMED":
                c[arm]["UC"] += 1

    for arm in ("base", "cand"):
        x = c[arm]
        say(f"{arm}: provider errors {x['provider_error']}, unchecked {x['unchecked']}, "
            f"checked-no-result turns {x['checked_no_result']}")
        say(f"  requirements: positive {x['pos']}, negative {x['neg']}; FC {x['FC']} (QN {x['FC_QN']}, K {x['FC_K']}, "
            f"P {x['FC_P']}); FR {x['FR']}; OM {x['OM']}; UC {x['UC']}")
        say(f"  SR QP {x['SR_QP']}, K {x['SR_K']}; B FR+soft {x['FRsoft_B']}; CL {x['CL']} (named {x['CL_named']}); "
            f"CS code {x['CS_code']}, labeller {x['CS_label']}")
    say(f"part 2 second opinions fired in cand: {len(so2)} {so2}")

    b, k = c["base"], c["cand"]
    base_fc = b["FC_QN"] + b["FC_K"]
    cand_fc = k["FC_QN"] + k["FC_K"]
    gates = {
        "V1": all(c[arm]["provider_error"] <= 10 and c[arm]["unchecked"] <= 10 for arm in c),
        "1-G1": None if base_fc < 4 else cand_fc <= 0.5 * base_fc,
        "1-G2": k["SR_QP"] + k["SR_K"] <= b["SR_QP"] + b["SR_K"] + 2,
        "1-G3": k["CL"] <= b["CL"] + 1 and k["CL_named"] <= b["CL_named"],
        "1-G4": k["CS_code"] == 0 and k["CS_label"] <= b["CS_label"],
        "2-G1": k["FRsoft_B"] <= b["FRsoft_B"],
        "2-G2": k["FC_P"] <= b["FC_P"],
        "A-G1": k["FR"] <= b["FR"] + 2 and k["OM"] <= b["OM"] + 2,
    }
    say(f"QN+KN FC: base {base_fc}, cand {cand_fc}")
    for name, ok in gates.items():
        say(f"{name} -> {'NO INFORMATION' if ok is None else 'PASS' if ok else 'FAIL'}")
    part1 = gates["V1"] and gates["1-G1"] is not False and all(gates[g] for g in ("1-G2", "1-G3", "1-G4", "A-G1"))
    part2 = gates["V1"] and all(gates[g] for g in ("2-G1", "2-G2", "A-G1"))
    say(f"keep part 1: {part1}; keep part 2: {part2}")
    say()
    say("Per item (base | cand):")
    for item in ITEMS:
        say(f"{item}: {dict(per_item[('base', item)])} | {dict(per_item[('cand', item)])}")
    (LIVE / f"{tag}-analysis.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
