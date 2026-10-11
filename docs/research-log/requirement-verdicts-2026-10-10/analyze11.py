"""Log 403 gates (FREEZE403.md) from two blind labellers, my resolution of their disagreements, and code layers.

Usage: python docs/research-log/requirement-verdicts-2026-10-10/analyze11.py <tag> <normal|outage>
       python docs/research-log/requirement-verdicts-2026-10-10/analyze11.py <tag> disagreements

Reads live/<tag>-structure.json, -blind-key.json, -labels-A.json, -labels-B.json and, for the final labels,
-labels-resolved.json (code -> {"R": [...], "contradiction": ..., "ambiguity": ...}, only for sessions the two
labellers disagree on). Writes live/<tag>-analysis.txt. Nothing calls a model.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LIVE = Path(__file__).resolve().parent / "live"
POSITIVE = {"supported", "with_step", "needs_input"}
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
LABELS = SAYS_GIVEN | {"PARTLY", "NOT_GIVEN", "UNCONFIRMED", "ASKED", "OMITTED"}
AMBIGUITY_LABELS = {"OPTIONS", "DISCRIMINATING_QUESTION", "VAGUE_QUESTION", "SINGLE", "REFUSED"}
FROZEN_RUNS = {"n11": ("normal", 3), "s11": ("outage", 2)}
FROZEN_ITEMS = {item["id"]: len(item["requirements"]) for item in
                json.loads((Path(__file__).parent / "heldout11.json").read_text())["items"]}


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def label_class(label: str) -> str:
    return "pos" if label in SAYS_GIVEN else "neg" if label == "NOT_GIVEN" else "other"


def disagreements(tag):
    a, b = load(tag, "labels-A"), load(tag, "labels-B")
    out = {}
    for code in sorted(set(a) | set(b)):
        x, y = a.get(code) or {}, b.get(code) or {}
        if x.get("R") != y.get("R") or (x.get("contradiction", "no") == "no") != (y.get("contradiction", "no") == "no") \
                or x.get("ambiguity") != y.get("ambiguity"):
            out[code] = {"A": x, "B": y}
    return out


def final_labels(tag):
    a, b, resolved = load(tag, "labels-A"), load(tag, "labels-B"), load(tag, "labels-resolved")
    split = disagreements(tag)
    final, unresolved = {}, []
    for code in set(a) | set(b):
        if code in split:
            if code in resolved:
                final[code] = resolved[code]
            else:
                unresolved.append(code)
        else:
            final[code] = a[code]
    return final, unresolved, split


def validate_evidence(tag, mode, rows, key):
    """Require complete independent labels and identical replay before reporting any gate.

    Missing labels used to contribute zero errors, and zip() silently dropped an
    unlabelled requirement. An unfinished outage round could therefore pass all
    four promotion gates. Validation is separate from the frozen metric thresholds.
    """
    recipe = FROZEN_RUNS.get(tag)
    if recipe is None or recipe[0] != mode:
        raise ValueError("Unknown experiment or mode differs from the frozen round")
    expected = Counter((arm, item, rep) for arm in ("base", "cand") for item in FROZEN_ITEMS
                       for rep in range(1, recipe[1] + 1))
    observed = Counter((row.get("arm"), row.get("item"), row.get("rep")) for row in rows.values())
    if observed != expected:
        raise ValueError("Incomplete or duplicate frozen round coverage")
    if (not rows or set(key.values()) != set(rows) or len(key) != len(rows)
            or {row.get("arm") for row in rows.values()} != {"base", "cand"}):
        raise ValueError("Incomplete or duplicate session coverage in the blinding map")
    for sid, row in rows.items():
        if row.get("missing") or not row.get("replay_equal"):
            raise ValueError(f"Missing session or unequal replay: {sid}")
        if len(row["layers"]) != FROZEN_ITEMS[row["item"]]:
            raise ValueError(f"Incomplete requirement coverage: {sid}")

    def validate_label(code, label, role):
        row = rows[key[code]]
        values = label.get("R") if isinstance(label, dict) else None
        if (not isinstance(values, list) or len(values) != len(row["layers"])
                or any(not isinstance(value, str) or value not in LABELS for value in values)):
            raise ValueError(f"Invalid requirement labels: {role} {code}")
        contradiction = label.get("contradiction")
        if not (contradiction == "no" or isinstance(contradiction, str)
                and contradiction.startswith("yes:") and contradiction[4:].strip()):
            raise ValueError(f"Invalid contradiction label: {role} {code}")
        if row["family"] == "A" and label.get("ambiguity") not in AMBIGUITY_LABELS:
            raise ValueError(f"Invalid ambiguity label: {role} {code}")

    for role in ("A", "B"):
        labels = load(tag, f"labels-{role}")
        if set(labels) != set(key):
            raise ValueError(f"Incomplete label coverage: labeller {role}")
        for code, label in labels.items():
            validate_label(code, label, role)
    split = disagreements(tag)
    resolved = load(tag, "labels-resolved")
    if set(resolved) != set(split):
        raise ValueError("There are unresolved or stale labeller disagreements")
    for code, label in resolved.items():
        validate_label(code, label, "resolved")


def main(tag, mode):
    if mode == "disagreements":
        split = disagreements(tag)
        (LIVE / f"{tag}-disagreements.json").write_text(json.dumps(split, indent=1, ensure_ascii=False))
        print(f"{len(split)} sessions disagree -> live/{tag}-disagreements.json")
        return
    rows = json.loads((LIVE / f"{tag}-structure.json").read_text())
    key = load(tag, "blind-key")
    validate_evidence(tag, mode, rows, key)
    final, unresolved, split = final_labels(tag)
    by_sid = {key[code]: value for code, value in final.items()}
    out = []

    def say(text=""):
        out.append(text)
        print(text)

    counts = {arm: Counter() for arm in ("base", "cand")}
    per_item = defaultdict(Counter)
    twins = defaultdict(dict)
    contradiction_code = Counter()
    contradiction_label = Counter()
    pc = Counter()
    mt = Counter()
    amb = defaultdict(Counter)
    l2 = {arm: Counter() for arm in ("base", "cand")}
    for sid, row in rows.items():
        arm = row["arm"]
        if row.get("missing"):
            counts[arm]["missing"] += 1
            continue
        if row.get("errors"):
            counts[arm]["provider_error"] += 1
        if row["action"] == "no_tool" and not any(status == "success" for _, status in row["check_calls"]):
            counts[arm]["unchecked"] += 1
        if row["contradictions"]:
            contradiction_code[arm] += 1
        label = by_sid.get(sid)
        for layer in row["layers"]:
            positive = layer["expect"] in POSITIVE
            checked = layer["checked"]
            if checked is None:
                l2[arm]["L1_missed"] += 1
            elif checked == "unconfirmed":
                l2[arm]["L2_unconfirmed"] += 1
            elif positive and checked == "not_available":
                l2[arm]["L2_false_negative"] += 1
            elif not positive and checked in ("available", "with_step"):
                l2[arm]["L2_over_credit"] += 1
            elif not positive and checked == "partial":
                l2[arm]["L2_partial_on_negative"] += 1
        if label is None:
            counts[arm]["unlabelled"] += 1
            continue
        if str(label.get("contradiction", "no")).startswith("yes"):
            contradiction_label[arm] += 1
        labels = label.get("R") or []
        classes = []
        for layer, given in zip(row["layers"], labels):
            positive = layer["expect"] in POSITIVE
            counts[arm]["req"] += 1
            counts[arm]["pos_req" if positive else "neg_req"] += 1
            if not positive and given in SAYS_GIVEN:
                counts[arm]["FC"] += 1
            if not positive and given == "PARTLY":
                counts[arm]["FC_soft"] += 1
            if positive and given == "NOT_GIVEN":
                counts[arm]["FR"] += 1
            if positive and given == "PARTLY":
                counts[arm]["FR_soft"] += 1
            if given == "OMITTED":
                counts[arm]["OM"] += 1
            if given == "UNCONFIRMED":
                counts[arm]["UC"] += 1
            if given == "ASKED" and row["family"] in "CNUP":
                counts[arm]["AK"] += 1
            if row["family"] == "M" and given == "NOT_GIVEN":
                counts[arm]["M_not_given"] += 1
            per_item[(arm, row["item"])][given] += 1
            classes.append(label_class(given))
        if row["family"] == "P":
            ok = all((label_class(g) == "pos") if layer["expect"] in POSITIVE else g == "NOT_GIVEN"
                     for layer, g in zip(row["layers"], labels))
            pc[(arm, ok)] += 1
        if row["family"] == "T":
            gold = "pos" if row["layers"][0]["expect"] in POSITIVE else "neg"
            mt[(arm, bool(classes) and classes[0] == gold)] += 1
        if row["family"] == "A":
            amb[arm][label.get("ambiguity", "?")] += 1
        if row.get("twin"):
            twins[(arm, row["twin"], row["rep"])][row["form"]] = classes
    tw = Counter()
    for (arm, _twin, _rep), forms in twins.items():
        if "statement" in forms and "question" in forms:
            tw[(arm, forms["statement"] == forms["question"])] += 1
    rate = {arm: tw[(arm, True)] / max(1, tw[(arm, True)] + tw[(arm, False)]) for arm in ("base", "cand")}
    for arm in ("base", "cand"):
        c = counts[arm]
        say(f"{arm}: sessions missing {c['missing']}, provider errors {c['provider_error']}, unchecked {c['unchecked']}, "
            f"unlabelled {c['unlabelled']}")
        say(f"  requirements {c['req']} (positive {c['pos_req']}, negative {c['neg_req']})")
        say(f"  FC {c['FC']} (+soft {c['FC_soft']}) = {c['FC'] / max(1, c['neg_req']):.2f} of negatives; "
            f"FR {c['FR']} (+soft {c['FR_soft']}) = {c['FR'] / max(1, c['pos_req']):.2f} of positives")
        say(f"  OM {c['OM']}, UC {c['UC']}, AK (C/N/U/P) {c['AK']}, M NOT_GIVEN {c['M_not_given']}")
        say(f"  PC {pc[(arm, True)]}/{pc[(arm, True)] + pc[(arm, False)]}; TW {tw[(arm, True)]}/"
            f"{tw[(arm, True)] + tw[(arm, False)]} = {rate[arm]:.2f}; MT {mt[(arm, True)]}/{mt[(arm, True)] + mt[(arm, False)]}")
        say(f"  CS code {contradiction_code[arm]}, labeller contradictions {contradiction_label[arm]}; "
            f"ambiguity {dict(amb[arm])}")
        say(f"  code layers: {dict(l2[arm])}")
    b, c = counts["base"], counts["cand"]
    if mode == "normal":
        gates = {
            "N-V1": all(counts[arm]["provider_error"] <= 10 and counts[arm]["unchecked"] <= 10 for arm in counts),
            "N-G1": c["FC"] <= 0.6 * b["FC"],
            "N-G2": c["FR"] <= b["FR"] + 2,
            "N-G3": c["OM"] <= b["OM"] + 2,
            "N-G4": pc[("cand", True)] >= pc[("base", True)],
            "N-G5": rate["cand"] >= rate["base"] and rate["cand"] >= 0.80,
            "N-G6": c["AK"] <= b["AK"] + 3,
            "N-G7": c["M_not_given"] <= b["M_not_given"],
            "N-G8": contradiction_code["cand"] == 0 and contradiction_label["cand"] <= contradiction_label["base"],
            "N-G9": mt[("cand", True)] >= mt[("base", True)],
        }
    else:
        promised = sum(1 for row in rows.values() if row.get("arm") == "cand" and any(
            text.startswith("unconfirmed check") for text in row.get("contradictions") or []))
        uncovered = sum(1 for row in rows.values() if row.get("arm") == "cand" and row.get("action") == "no_tool"
                        and not (row["check"].get("provisional") or row["check"].get("unavailable")
                                 or row["check"].get("gap_unconfirmed")))
        say(f"outage: cand sessions presenting an unconfirmed answer {promised}; cand no_tool sessions without a "
            f"backup or unavailable check {uncovered}")
        gates = {"S-G1": promised == 0, "S-G2": c["FR"] <= b["FR"] + 2, "S-G3": c["FC"] <= b["FC"],
                 "S-G4": uncovered == 0}
    for name, ok in gates.items():
        say(f"{name} -> {'PASS' if ok else 'FAIL'}")
    say("")
    say(f"labeller disagreements: {len(split)} sessions; unresolved {len(unresolved)}")
    say("Per item (base | cand):")
    for item in dict.fromkeys(row["item"] for row in rows.values()):
        say(f"{item}: {dict(per_item[('base', item)])} | {dict(per_item[('cand', item)])}")
    (LIVE / f"{tag}-analysis.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
