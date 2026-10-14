"""Item 6 (FREEZE.md): the executability score and the plan's acceptance thresholds for a labelled accept24 round.

Usage (repository root):
  python docs/research-log/final-acceptance-2026-10-14/analyze24.py <tag> spotcheck   # the sessions I must review
  python docs/research-log/final-acceptance-2026-10-14/analyze24.py <tag> score

Log 411's analyze17.py with three changes frozen in FREEZE.md: the main score uses rep 1 only (rep 2 gives agreement);
`needs_fact` requirements are kept out of FAR/FRR and scored as the ask class (ASKED, and my review confirms the
question is the deciding one: `right_question` in live/<tag>-labels-checked.json); I review every session with a
misjudged requirement, a contradiction or an ask-class requirement, plus a random 10% of the rest (seed 2414).
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
sys.path.insert(0, str(HERE))
from plan24 import ITEMS, jobs  # noqa: E402

SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
UNDECIDED = {"UNCONFIRMED", "ASKED", "OMITTED"}
LABELS = SAYS_GIVEN | UNDECIDED | {"PARTLY", "NOT_GIVEN"}
CHECK_MODEL = "nemotron"
RUN_PREFIX = "run_"


def load(tag, name):
    path = LIVE / f"{tag}-{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def negative(layer):
    return layer["expect"] == "not_supported"


def ask(layer):
    return layer["expect"] == "needs_fact"


def excluded(layer):
    return layer["expect"] == "excluded"  # ADJUDICATION.md: two correct behaviours, not scored


def misjudged(layer, label):
    if excluded(layer):
        return False
    if ask(layer):
        return label != "ASKED"
    return label in SAYS_GIVEN | {"PARTLY"} if negative(layer) else label == "NOT_GIVEN"


def novel(row, index):
    return False  # accept24 marks no novel types


def contradiction(label):
    return str(label.get("contradiction", "no")).startswith("yes")


def to_review(rows, key, labels):
    flagged = {code for code, sid in key.items()
               if contradiction(labels[code]) or any(ask(layer) for layer in rows[sid]["layers"])
               or any(misjudged(layer, given) for layer, given in zip(rows[sid]["layers"], labels[code]["R"]))}
    rest = sorted(set(key) - flagged)
    random.seed(2414)
    sample = set(random.sample(rest, math.ceil(0.1 * len(rest)))) if rest else set()
    return sorted(flagged | sample)


def validate(rows, key, labels, checked):
    expected = Counter(("live", item, rep) for item, rep in jobs())
    if Counter((row.get("arm"), row.get("item"), row.get("rep")) for row in rows.values()) != expected:
        raise ValueError("Incomplete or duplicate round coverage")
    if set(key.values()) != set(rows) or set(labels) != set(key):
        raise ValueError("Blinding map or labels do not cover every session once")
    for sid, row in rows.items():
        if row.get("missing") or row.get("replay_equal") is False:  # None: a run turn, its recorded reply
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
    asks, recognised, runs, agreement = Counter(), Counter(), Counter(), Counter()
    by_rep = defaultdict(dict)
    for sid, row in sorted(rows.items()):
        label = final[sid]
        by_rep[row["item"]][row["rep"]] = label["R"]
        if row["rep"] != 1:
            continue
        c["sessions"] += 1
        action = row.get("action") or ""
        runs["planned"] += action.startswith(RUN_PREFIX)
        runs["planned_on_negative"] += action.startswith(RUN_PREFIX) and any(negative(x) for x in row["layers"])
        runs["held"] += bool((row.get("run") or {}).get("held"))
        runs["replanned"] += bool((row.get("run") or {}).get("replanned"))
        for layer in row["layers"]:
            if excluded(layer):
                continue
            recognised["n"] += 1
            recognised["understood"] += bool(layer.get("understood"))
        c["provider_error"] += bool(row.get("errors"))
        c["check_by_model"] += any(CHECK_MODEL in str(m) and s == "success" for m, s in row["check_calls"])
        c["contradiction"] += contradiction(label)
        for index, (layer, given) in enumerate(zip(row["layers"], label["R"])):
            if excluded(layer):
                continue
            if ask(layer):
                asks["n"] += 1
                asks[given] += 1
                review = checked.get(next(code for code, s in key.items() if s == sid), {})
                asks["right"] += given == "ASKED" and bool(review.get("right_question"))
                if given != "ASKED":
                    misses.append(f"{sid} [{given}] (ask) {layer['words']}")
                continue
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
    say("Plan thresholds (FREEZE.md):")
    say(f"  not over-promising, FAR <= 3%: {rate(fa, c['neg'])}")
    say(f"  not over-refusing, FRR <= 5%: {rate(fr, c['pos'])}")
    say(f"  helpful (positives given clearly) >= 95%: {rate(pos_given, c['pos'])}")
    say(f"  asks when a fact decides (ASKED, right question) >= 90%: {rate(asks['right'], asks['n'])}; "
        f"labels {dict((k, v) for k, v in asks.items() if k not in ('n', 'right'))}")
    say(f"  requirements read (L1, English) >= 95%: {rate(recognised['understood'], recognised['n'])}")
    say(f"  runs: planned {runs['planned']} (on an item with a not-doable requirement: "
        f"{runs['planned_on_negative']}), held {runs['held']}, re-planned {runs['replanned']}")
    for item, reps in by_rep.items():
        if 2 in reps and 1 in reps:
            agreement["n"] += 1
            agreement["same"] += reps[1] == reps[2]
    say(f"  rep-2 agreement (same labels for every requirement): {rate(agreement['same'], agreement['n'])}")
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
