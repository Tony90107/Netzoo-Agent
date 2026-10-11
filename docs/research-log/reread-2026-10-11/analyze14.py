"""Log 406: metrics and the frozen gates of FREEZE406.md for a labelled heldout14 round.

Usage (repository root):
  python docs/research-log/reread-2026-10-11/analyze14.py <tag> spotcheck   # the sessions I must review
  python docs/research-log/reread-2026-10-11/analyze14.py <tag> gates

One blind labeller (live/<tag>-labels-A.json) labels every session; I review every session of every item
whose label counts differ between the arms and record any correction, with its reason, in
live/<tag>-labels-checked.json (code -> label). No gate is printed unless every session is labelled, every
listed session was reviewed (an entry, even if unchanged), the round is complete and every replay equals
its recording.
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
REPEATS = 2
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout14.json").read_text())["items"]}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def signature(label):
    return (tuple(label.get("R") or []), label.get("consult"), str(label.get("contradiction", "no")).startswith("yes"))


def to_review(rows, key, labels):
    """Every session of every item whose labels differ between the arms."""
    by_item = defaultdict(lambda: {"base": Counter(), "cand": Counter()})
    for code, sid in key.items():
        row = rows[sid]
        by_item[row["item"]][row["arm"]][signature(labels[code])] += 1
    differ = {item for item, arms in by_item.items() if arms["base"] != arms["cand"]}
    return sorted(code for code, sid in key.items() if rows[sid]["item"] in differ)


def validate(rows, key, labels, checked):
    expected = Counter((arm, item, rep) for arm in ("base", "cand") for item in ITEMS for rep in range(1, REPEATS + 1))
    if Counter((row.get("arm"), row.get("item"), row.get("rep")) for row in rows.values()) != expected:
        raise ValueError("Incomplete or duplicate frozen round coverage")
    if set(key.values()) != set(rows) or set(labels) != set(key):
        raise ValueError("Blinding map or labels do not cover every session once")
    for sid, row in rows.items():
        if row.get("missing") or not row.get("replay_equal"):
            raise ValueError(f"Missing session or unequal replay: {sid}")
    for code, label in [*labels.items(), *checked.items()]:
        row = rows[key[code]]
        if not isinstance(label.get("R"), list) or len(label["R"]) != len(row["layers"]) or any(
                v not in LABELS for v in label["R"]):
            raise ValueError(f"Invalid requirement labels: {code}")
        if row["family"] == "M" and label.get("consult") not in CONSULT:
            raise ValueError(f"Invalid consult label: {code}")
    missing = set(to_review(rows, key, labels)) - set(checked)
    if missing:
        raise ValueError(f"Spot check incomplete: {sorted(missing)}")


def main(tag, mode):
    rows = json.loads((LIVE / f"{tag}-structure.json").read_text())
    key, labels, checked = load(tag, "blind-key"), load(tag, "labels-A"), load(tag, "labels-checked")
    if mode == "spotcheck":
        codes = to_review(rows, key, labels)
        (LIVE / f"{tag}-to-review.json").write_text(json.dumps(codes))
        print(f"{len(codes)} sessions to review -> live/{tag}-to-review.json")
        return
    validate(rows, key, labels, checked)
    final = {key[code]: checked.get(code, labels[code]) for code in key}
    out = []

    def say(text=""):
        out.append(text)
        print(text)

    c = {arm: Counter() for arm in ("base", "cand")}
    per_item = defaultdict(Counter)
    for sid, row in rows.items():
        arm, family, label = row["arm"], row["family"], final[sid]
        c[arm]["provider_error"] += bool(row.get("errors"))
        c[arm]["unchecked"] += row["action"] == "no_tool" and not any(s == "success" for _, s in row["check_calls"])
        c[arm]["reread"] += bool(row.get("reread"))
        c[arm]["reread_seconds"] += row.get("reread_seconds") or 0
        c[arm]["CS_label"] += str(label.get("contradiction", "no")).startswith("yes")
        if family == "M":
            per_item[(arm, row["item"])][label["consult"]] += 1
            c[arm]["CL"] += label["consult"] in ("LISTED_ONLY", "REFUSED")
        for layer, given in zip(row["layers"], label["R"]):
            per_item[(arm, row["item"])][given] += 1
            if layer["expect"] in POSITIVE:
                c[arm]["pos"] += 1
                c[arm]["POS_GIVEN"] += given in SAYS_GIVEN
                c[arm]["FR"] += given == "NOT_GIVEN"
            else:
                c[arm]["neg"] += 1
                c[arm]["REFUSED"] += given == "NOT_GIVEN"
                c[arm]["FC"] += given in SAYS_GIVEN
            c[arm]["OM"] += given == "OMITTED"
    for arm in ("base", "cand"):
        x = c[arm]
        say(f"{arm}: provider errors {x['provider_error']}, unchecked {x['unchecked']}; negatives refused "
            f"{x['REFUSED']}/{x['neg']}, FC {x['FC']}; positives given {x['POS_GIVEN']}/{x['pos']}, FR {x['FR']}; "
            f"OM {x['OM']}; consult unanswered {x['CL']}; contradictions {x['CS_label']}; re-read in {x['reread']} "
            f"sessions, {x['reread_seconds']:.0f} s in all")
    b, k = c["base"], c["cand"]
    gates = {
        "V1": all(c[arm]["provider_error"] <= 6 and c[arm]["unchecked"] <= 6 for arm in c),
        "G1": k["REFUSED"] >= b["REFUSED"] + 4,
        "G2": k["FC"] <= b["FC"],
        "G3": k["POS_GIVEN"] >= b["POS_GIVEN"] - 2 and k["FR"] <= b["FR"] + 1,
        "G4": k["CL"] <= b["CL"] + 1,
        "G5": k["CS_label"] <= b["CS_label"] + 1,
        "A1": k["OM"] <= b["OM"] + 2,
    }
    for name, ok in gates.items():
        say(f"{name} -> {'PASS' if ok else 'FAIL'}")
    say(f"keep: {all(gates.values())}")
    say()
    say("Per item (base | cand):")
    for item in ITEMS:
        say(f"{item}: {dict(per_item[('base', item)])} | {dict(per_item[('cand', item)])}")
    (LIVE / f"{tag}-analysis.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
