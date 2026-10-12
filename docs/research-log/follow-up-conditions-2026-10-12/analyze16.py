"""Log 410: metrics and the frozen gates of FREEZE410.md for a labelled heldout16 round.

Usage (repository root):
  python docs/research-log/follow-up-conditions-2026-10-12/analyze16.py <tag> spotcheck
  python docs/research-log/follow-up-conditions-2026-10-12/analyze16.py <tag> gates

One blind labeller (live/<tag>-labels-A.json); I review every misjudged requirement, every contradiction and
every session of an item whose arms differ, recording each review in live/<tag>-labels-checked.json.
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
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout16.json").read_text())["items"]}
REPEATS = {"base": 1, "cand": 2}
QUESTION_FAMILIES = {"NC", "PC", "QS", "QN"}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def outcome(layer, label):
    if layer["expect"] == "not_supported":
        return "FA" if label in SAYS_GIVEN | {"PARTLY"} else "clear" if label == "NOT_GIVEN" else "unclear"
    return "FR" if label == "NOT_GIVEN" else "clear" if label in SAYS_GIVEN else "unclear"


def signature(label):
    return (tuple(label.get("R") or []), str(label.get("contradiction", "no")).startswith("yes"))


def to_review(rows, key, labels):
    by_item = defaultdict(lambda: {"base": Counter(), "cand": Counter()})
    flagged = set()
    for code, sid in key.items():
        row, label = rows[sid], labels[code]
        by_item[row["item"]][row["arm"]][signature(label)] += 1
        if str(label.get("contradiction", "no")).startswith("yes") or any(
                outcome(layer, given) in ("FA", "FR") for layer, given in zip(row["layers"], label["R"])):
            flagged.add(code)
    differ = {item for item, arms in by_item.items()
              if set(arms["base"]) != set(arms["cand"])}  # outcomes, not counts: the arms have 1 and 2 runs
    return sorted(flagged | {code for code, sid in key.items() if rows[sid]["item"] in differ})


def main(tag, mode):
    rows = json.loads((LIVE / f"{tag}-structure.json").read_text())
    key, labels, checked = load(tag, "blind-key"), load(tag, "labels-A"), load(tag, "labels-checked")
    if mode == "spotcheck":
        codes = to_review(rows, key, labels)
        (LIVE / f"{tag}-to-review.json").write_text(json.dumps(codes))
        print(f"{len(codes)} sessions to review -> live/{tag}-to-review.json")
        return
    expected = Counter((arm, item, rep) for item in ITEMS for arm in REPEATS for rep in range(1, REPEATS[arm] + 1))
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

    c = {arm: Counter() for arm in REPEATS}
    per_item = defaultdict(lambda: defaultdict(list))
    for sid, row in rows.items():
        arm, label = row["arm"], final[sid]
        x = c[arm]
        x["sessions"] += 1
        x["provider_error"] += bool(row.get("errors"))
        x["backup_check"] += any("nemotron" not in str(m) for m, _ in row["check_calls"])
        x["contradiction"] += str(label.get("contradiction", "no")).startswith("yes")
        if row["family"] == "AK":
            x["AK"] += 1
            x["AK_asked"] += not row["ran_turn_2"] and row["reply_kind"] == "needs_detail"
        if row["family"] in QUESTION_FAMILIES:
            x["G4_n"] += 1
            x["G4_composed"] += row["composed"]
        for layer, given in zip(row["layers"], label["R"]):
            side = "neg" if layer["expect"] == "not_supported" else "pos"
            x[side] += 1
            x[f"{side}:{outcome(layer, given)}"] += 1
            per_item[row["item"]][arm].append(given)
    for arm, x in c.items():
        say(f"{arm}: sessions {x['sessions']}, provider errors {x['provider_error']}, backup checks {x['backup_check']}; "
            f"negatives FA {x['neg:FA']}/{x['neg']}, clear {x['neg:clear']}, unclear {x['neg:unclear']}; "
            f"positives FR {x['pos:FR']}/{x['pos']}, clear {x['pos:clear']}, unclear {x['pos:unclear']}; "
            f"contradictions {x['contradiction']}; AK asked {x['AK_asked']}/{x['AK']}; "
            f"turn 2 read with turn 1 {x['G4_composed']}/{x['G4_n']}")
    b, k = c["base"], c["cand"]

    def rate(x, part, whole):
        return x[part] / x[whole] if x[whole] else 0.0

    gates = {
        "V1": all(x["provider_error"] <= 3 and x["backup_check"] <= 3 for x in c.values()),
        "G1": rate(k, "neg:FA", "neg") <= rate(b, "neg:FA", "neg"),
        "G2": rate(k, "pos:FR", "pos") <= rate(b, "pos:FR", "pos") + 0.10,
        "G3": k["AK_asked"] == k["AK"] == 4,
        "G4": k["G4_composed"] == k["G4_n"],
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
