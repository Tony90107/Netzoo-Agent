"""Log 408: the executability score of FREEZE408.md for a labelled heldout15 round.

Usage (repository root):
  python docs/research-log/executability-score-2026-10-11/analyze15.py <tag> spotcheck   # the sessions I must review
  python docs/research-log/executability-score-2026-10-11/analyze15.py <tag> score

One blind labeller (live/<tag>-labels-A.json) labels every session; I review every session with a
misjudged requirement or a contradiction, plus a random 10% of the rest, and record each review (even
unchanged) in live/<tag>-labels-checked.json (code -> label, with `reason` when changed). No score is
printed unless every session is labelled, every listed session was reviewed, the round is complete and
every replay equals its recording.
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE / "live"
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
UNDECIDED = {"UNCONFIRMED", "ASKED", "OMITTED"}
LABELS = SAYS_GIVEN | UNDECIDED | {"PARTLY", "NOT_GIVEN"}
REPEATS = 2
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout15.json").read_text())["items"]}
CHECK_MODEL = "nemotron"


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def negative(layer):
    return layer["expect"] == "not_supported"


def misjudged(layer, label):
    return label in SAYS_GIVEN | {"PARTLY"} if negative(layer) else label == "NOT_GIVEN"


def novel(row, index):
    item = ITEMS[row["item"]]
    return item["family"] == "NV" or (item.get("novel") and negative(row["layers"][index]))


def contradiction(label):
    return str(label.get("contradiction", "no")).startswith("yes")


def to_review(rows, key, labels):
    flagged = {code for code, sid in key.items()
               if contradiction(labels[code])
               or any(misjudged(layer, given) for layer, given in zip(rows[sid]["layers"], labels[code]["R"]))}
    rest = sorted(set(key) - flagged)
    random.seed(408)
    sample = set(random.sample(rest, math.ceil(0.1 * len(rest)))) if rest else set()
    return sorted(flagged | sample)


def validate(rows, key, labels, checked):
    expected = Counter(("live", item, rep) for item in ITEMS for rep in range(1, REPEATS + 1))
    if Counter((row.get("arm"), row.get("item"), row.get("rep")) for row in rows.values()) != expected:
        raise ValueError("Incomplete or duplicate round coverage")
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
    missing = set(to_review(rows, key, labels)) - set(checked)
    if missing:
        raise ValueError(f"Spot check incomplete: {sorted(missing)}")


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def rate(k, n):
    low, high = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% (95% CI {100 * low:.1f}-{100 * high:.1f}%)" if n else "0/0"


def cost(layer, label):
    if negative(layer):
        return 0 if label == "NOT_GIVEN" else 1 if label in UNDECIDED else 2 if label == "PARTLY" else 3
    return 0 if label in SAYS_GIVEN else 2 if label == "NOT_GIVEN" else 1


def grade(far, frr):
    for name, far_max, frr_max in (("A", .03, .05), ("B", .06, .10), ("C", .12, .15), ("D", .20, 1.0)):
        if far <= far_max and frr <= frr_max:
            return name
    return "F"


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

    c, costs = Counter(), {"neg": [], "pos": []}
    by_family, by_item, misses = defaultdict(Counter), defaultdict(Counter), []
    for sid, row in sorted(rows.items()):
        label = final[sid]
        c["sessions"] += 1
        c["provider_error"] += bool(row.get("errors"))
        c["check_by_model"] += any(CHECK_MODEL in str(m) and s == "success" for m, s in row["check_calls"])
        c["contradiction"] += contradiction(label)
        for index, (layer, given) in enumerate(zip(row["layers"], label["R"])):
            side = "neg" if negative(layer) else "pos"
            costs[side].append(cost(layer, given))
            c[side] += 1
            c[f"{side}:{given}"] += 1
            by_item[row["item"]][given] += 1
            family = row["family"] + ("(novel)" if novel(row, index) else "")
            by_family[(side, family)]["n"] += 1
            by_family[(side, family)]["miss"] += misjudged(layer, given)
            by_family[(side, family)]["clear"] += given == "NOT_GIVEN" if side == "neg" else given in SAYS_GIVEN
            if side == "neg":
                c["neg_novel"] += novel(row, index)
                c["FA_novel"] += novel(row, index) and misjudged(layer, given)
            else:
                c["route_n"] += 1
                c["route_ok"] += bool(row["route_ok"][index])
            check = layer.get("checked")
            agrees = (check == "not_available") if side == "neg" else check in ("available", "with_step")
            c[f"check_agree_{side}"] += agrees
            if misjudged(layer, given):
                misses.append(f"{sid} [{given}] {layer['words']}")
    fa = sum(c[f"neg:{x}"] for x in SAYS_GIVEN | {"PARTLY"})
    fa_strict = sum(c[f"neg:{x}"] for x in SAYS_GIVEN)
    fr = c["pos:NOT_GIVEN"]
    said_given = fa + sum(c[f"pos:{x}"] for x in SAYS_GIVEN)
    pos_given = sum(c[f"pos:{x}"] for x in SAYS_GIVEN)
    far, frr = fa / c["neg"], fr / c["pos"]
    s_neg = 1 - sum(costs["neg"]) / (3 * len(costs["neg"]))
    s_pos = 1 - sum(costs["pos"]) / (2 * len(costs["pos"]))
    say(f"Validity: sessions {c['sessions']}, provider errors {c['provider_error']}, "
        f"checked by {CHECK_MODEL} {c['check_by_model']}/{c['sessions']}")
    say()
    say(f"FAR (said doable for a not-doable requirement, incl. PARTLY): {rate(fa, c['neg'])}")
    say(f"FAR strict (GIVEN* only): {rate(fa_strict, c['neg'])}")
    say(f"FAR on novel trap types: {rate(c['FA_novel'], c['neg_novel'])}")
    say(f"Precision of 'doable': {rate(pos_given, said_given)}")
    say(f"FRR (said not doable for a doable requirement): {rate(fr, c['pos'])}")
    say(f"Negatives refused clearly (NOT_GIVEN): {rate(c['neg:NOT_GIVEN'], c['neg'])}")
    say(f"Positives given clearly: {rate(pos_given, c['pos'])}")
    say(f"Sessions with a contradiction: {c['contradiction']}/{c['sessions']}")
    say()
    say(f"S_neg {s_neg:.3f}, S_pos {s_pos:.3f}, score {100 * (0.6 * s_neg + 0.4 * s_pos):.1f}/100, "
        f"grade {grade(far, frr)}")
    say()
    say("Label counts: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items()) if ":" in k))
    say(f"Code: positives where routing offered a gold workflow {rate(c['route_ok'], c['route_n'])}; "
        f"check verdict agrees with gold: negatives {c['check_agree_neg']}/{c['neg']}, "
        f"positives {c['check_agree_pos']}/{c['pos']}")
    say()
    say("By family (side, family): misjudged / clear / n")
    for (side, family), x in sorted(by_family.items()):
        say(f"  {side} {family}: {x['miss']} / {x['clear']} / {x['n']}")
    say()
    say("Misjudged requirements:")
    for line in misses:
        say(f"  {line}")
    say()
    say("Per item: " + "; ".join(f"{item} {dict(by_item[item])}" for item in ITEMS))
    (LIVE / f"{tag}-score.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
