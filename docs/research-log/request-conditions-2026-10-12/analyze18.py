"""Log 412: metrics and the frozen gates of FREEZE412.md for a labelled heldout18 round.

Usage (repository root):
  python docs/research-log/request-conditions-2026-10-12/analyze18.py <tag> spotcheck
  python docs/research-log/request-conditions-2026-10-12/analyze18.py <tag> gates

One blind labeller per packet (live/<tag>-labels-A.json); I review every misjudged requirement, every
contradiction and every session of an item whose arms differ, recording each review in
live/<tag>-labels-checked.json (code -> label, with `reason` when changed).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE / "live"
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
LABELS = SAYS_GIVEN | {"PARTLY", "NOT_GIVEN", "UNCONFIRMED", "ASKED", "OMITTED"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout18.json").read_text())["items"]}
REPEATS = 2
TARGET, ADJACENT, CONTROLS = {"CS", "CK"}, {"CP"}, {"XP", "XN"}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def outcome(layer, label):
    if layer["expect"] == "not_supported":
        return "FA" if label in SAYS_GIVEN | {"PARTLY"} else "clear" if label == "NOT_GIVEN" else "unclear"
    return "FR" if label == "NOT_GIVEN" else "clear" if label in SAYS_GIVEN else "unclear"


def signature(label):
    return (tuple(label.get("R") or []), str(label.get("contradiction", "no")).startswith("yes"))


def check_failed(row) -> bool:
    check = row.get("check") or {}
    return bool(check.get("unavailable") or check.get("provisional") or check.get("gap_unconfirmed")
                or not any(status == "success" for _, status in row.get("check_calls") or []))


def to_review(rows, key, labels):
    by_item = defaultdict(lambda: {"base": Counter(), "cand": Counter()})
    flagged = set()
    for code, sid in key.items():
        row, label = rows[sid], labels[code]
        by_item[row["item"]][row["arm"]][signature(label)] += 1
        if str(label.get("contradiction", "no")).startswith("yes") or any(
                outcome(layer, given) in ("FA", "FR") for layer, given in zip(row["layers"], label["R"])):
            flagged.add(code)
    differ = {item for item, arms in by_item.items() if arms["base"] != arms["cand"]}
    return sorted(flagged | {code for code, sid in key.items() if rows[sid]["item"] in differ})


def main(tag, mode):
    rows = json.loads((LIVE / f"{tag}-structure.json").read_text())
    key, labels, checked = load(tag, "blind-key"), load(tag, "labels-A"), load(tag, "labels-checked")
    if mode == "spotcheck":
        codes = to_review(rows, key, labels)
        (LIVE / f"{tag}-to-review.json").write_text(json.dumps(codes))
        print(f"{len(codes)} sessions to review -> live/{tag}-to-review.json")
        return
    expected = Counter((arm, item, rep) for item in ITEMS for arm in ("base", "cand") for rep in range(1, REPEATS + 1))
    if Counter((r.get("arm"), r.get("item"), r.get("rep")) for r in rows.values()) != expected:
        raise ValueError("Incomplete round")
    if set(key.values()) != set(rows) or set(labels) != set(key):
        raise ValueError("Blinding map or labels do not cover every session once")
    for code, label in [*labels.items(), *checked.items()]:
        row = rows[key[code]]
        if len(label.get("R") or []) != len(row["layers"]) or any(v not in LABELS for v in label["R"]):
            raise ValueError(f"Invalid labels: {code}")
    missing = set(to_review(rows, key, labels)) - set(checked)
    if missing or any(r.get("missing") or not r["replay_equal"] for r in rows.values()):
        raise ValueError(f"Spot check incomplete or replay unequal: {sorted(missing)}")
    final = {key[code]: checked.get(code, labels[code]) for code in key}
    out = []

    def say(text=""):
        out.append(text)
        print(text)

    c = {arm: Counter() for arm in ("base", "cand")}
    per_item = defaultdict(lambda: defaultdict(list))
    for sid, row in rows.items():
        arm, label = row["arm"], final[sid]
        x = c[arm]
        x["provider_error"] += bool(row.get("errors"))
        x["backup"] += any("nemotron" not in str(m) for m, _ in row["check_calls"])
        x["check_failed"] += check_failed(row)
        x["contradiction"] += str(label.get("contradiction", "no")).startswith("yes")
        x["conditions_applied"] += bool(row.get("conditions"))
        group = ("target" if row["family"] in TARGET else "adjacent" if row["family"] in ADJACENT else "control")
        for layer, given in zip(row["layers"], label["R"]):
            side = "neg" if layer["expect"] == "not_supported" else "pos"
            result = outcome(layer, given)
            x[f"{group}:{side}"] += 1
            x[f"{group}:{side}:{result}"] += 1
            per_item[row["item"]][arm].append(given)
    for arm, x in c.items():
        say(f"{arm}: provider errors {x['provider_error']}, backup checks {x['backup']}, check failed {x['check_failed']}, "
            f"conditions applied {x['conditions_applied']}, contradictions {x['contradiction']}")
        say(f"  target negatives (CS+CK): FA {x['target:neg:FA']}/{x['target:neg']}, clear {x['target:neg:clear']}, "
            f"unclear {x['target:neg:unclear']}")
        say(f"  adjacent positives (CP): FR {x['adjacent:pos:FR']}/{x['adjacent:pos']}, clear {x['adjacent:pos:clear']}, "
            f"unclear {x['adjacent:pos:unclear']}")
        say(f"  controls: positives FR {x['control:pos:FR']}/{x['control:pos']}, clear {x['control:pos:clear']}; "
            f"negatives FA {x['control:neg:FA']}/{x['control:neg']}, clear {x['control:neg:clear']}")
    b, k = c["base"], c["cand"]
    gates = {
        "V1": all(x["provider_error"] <= 6 and x["backup"] <= 3 for x in c.values()),
        "G1": k["target:neg:FA"] <= b["target:neg:FA"] - 4,
        "G2": k["target:neg:clear"] >= b["target:neg:clear"] + 4,
        "G3": k["adjacent:pos:FR"] <= b["adjacent:pos:FR"] + 1,
        "G4": k["control:pos:FR"] <= b["control:pos:FR"] + 1 and k["control:neg:FA"] <= b["control:neg:FA"] + 1,
        "G5": k["check_failed"] <= b["check_failed"] + 3,
    }
    for name, ok in gates.items():
        say(f"{name} -> {'PASS' if ok else 'FAIL'}")
    say(f"keep: {all(gates.values())}")
    say()
    for item in ITEMS:
        say(f"{item}: base {per_item[item]['base']} | cand {per_item[item]['cand']}")
    (LIVE / f"{tag}-analysis.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
