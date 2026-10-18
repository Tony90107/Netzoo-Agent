"""Closed-menu phase 1, the one bench measurement (spec section 6): 56 items x 2 reads, never used to tune.

The 56 items are core-judgment-2026-10-15/items.json minus C01, C02, C03, C05; their gold readings are
closed-menu-phase0-2026-10-18/gold_readings.yaml. Each item is read twice by gpt-4o-mini (reader shape frozen in
FREEZE.md), and each read is followed by the focused re-read of its candidates (step 4). Two arms are scored:
`first` (the first reading alone) and `focused` (the first reading with the re-read merged in, where it ran).

Measured per arm:
- field accuracy against the gold readings, per field and overall (pairs where gold or the read is not default);
- recall on limit fields (settings, counts, data the user lacks -- `only_data` in the gold is its data_absent) and on
  doubt fields (unsure or conflicting anywhere, unsure settings, unsure files), separately; false fills on do items;
- kind agreement between the two reads (target >= 90%), and spec 3.6's conservative merge of the two;
- code-scored calls: `decide_menu` with the item's prompt and phase0_gate.score; vague declined (<= 1); dont
  declined right (today: p5r 10/13, p4b and p4c 11/13).

Usage: bench.py read TAG    -> live/TAG/bench.json (announce first: 112 reads + their re-reads)
       bench.py score TAG   -> live/TAG/score.json and the tables RESULTS-P1.md reports
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

import yaml

from p1common import HERE, LOGS, git_head, read_many, write

sys.path.insert(0, str(LOGS / "closed-menu-phase0-2026-10-18"))
from phase0_gate import reading as gold_reading, score as gate_score  # noqa: E402

ITEMS = {i["id"]: i for i in json.loads((LOGS / "core-judgment-2026-10-15/items.json").read_text())["items"]
         if i["id"] not in ("C01", "C02", "C03", "C05")}
GOLD = yaml.safe_load((LOGS / "closed-menu-phase0-2026-10-18/gold_readings.yaml").read_text(encoding="utf-8"))
WANTED = ("artifact", "integration", "granularity", "regulators", "layers", "signed", "compare")
DOUBT = ("unsure", "conflicting")
EXPECTED = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}


def read(tag: str) -> None:
    from netzoo_agent_core.interpretation.menu_reader import READER_SHAPE
    assert set(ITEMS) == set(GOLD) and len(ITEMS) == 56
    jobs = [(ITEMS[key], rep) for key in sorted(ITEMS) for rep in (0, 1)]
    rows = read_many(jobs, focus=True)
    write(HERE / "live" / tag / "bench.json", {"commit": git_head(), "shape": READER_SHAPE, "rows": rows})


# --- comparing one reading with its gold -------------------------------------------------------------------------

def _said(said) -> tuple:
    """A Said as compared: (stated, value) or (doubt, values); unsure and conflicting are both a doubt."""
    if said.status == "stated":
        return ("stated", said.value)
    if said.status in DOUBT:
        return ("doubt", frozenset(said.values))
    return ("not_stated", None)


def _count(count) -> tuple:
    if count.status == "stated":
        return ("stated", count.value)
    if count.status in DOUBT:
        return ("doubt", frozenset(count.values))
    return ("not_stated", None)


def _norm_value(control: str, value: str) -> str:
    from netzoo_agent_core.workflow_conditions import boolean_value, stated_numbers
    text = str(value or "").strip().casefold()
    numbers = stated_numbers(text)
    if numbers and len(numbers) == 1 and re.fullmatch(r"[\d.,e+\-k ]+", text):
        return f"{numbers[0]:g}"
    if text in ("true", "false", "yes", "no", "on", "off"):
        return str(boolean_value(text)).casefold()
    return re.sub(r"[^a-z0-9]+", "", text.replace("hdf5", ".h5"))


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").casefold()))


def _setting_match(gold, model) -> bool:
    if gold.workflow and model.workflow and gold.workflow != model.workflow:
        return False
    if gold.control != model.control:
        return False
    if gold.control == "unregistered":
        a, b = _tokens(gold.quote), _tokens(model.quote)
        return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.5
    if gold.unsure or model.unsure:
        return gold.unsure and model.unsure
    return not gold.value or _norm_value(gold.control, gold.value) == _norm_value(model.control, model.value)


def _deliverables(reading) -> list:
    return [w for w in reading.wanted if w.form == "deliverable"]


def _pair(gold_items, model_items) -> list[tuple]:
    """Each gold deliverable with its closest read deliverable (same result, else most shared words)."""
    pairs = []
    for g in gold_items:
        best = max(model_items, key=lambda m: (_said(m.artifact) == _said(g.artifact),
                                              len(_tokens(m.quote) & _tokens(g.quote))), default=None)
        pairs.append((g, best))
    return pairs


def compare(gold, model) -> dict:
    """field -> (gold value, read value, match) for every field where either is not default."""
    out = {}

    def put(name, g, m, match=None):
        if g in (None, ("not_stated", None), frozenset(), False, 0) and m in (None, ("not_stated", None),
                                                                              frozenset(), False, 0):
            return
        out[name] = (g, m, g == m if match is None else match)

    put("has_deliverable", bool(_deliverables(gold)), bool(_deliverables(model)))
    for index, (g, m) in enumerate(_pair(_deliverables(gold), _deliverables(model))):
        for name in WANTED:
            put(f"wanted.{name}", _said(getattr(g, name)), _said(getattr(m, name)) if m else ("not_stated", None))
        put("wanted.outside_name", bool(g.outside_name), bool(m and m.outside_name))
        put("wanted.requirements", bool(g.requirements), bool(m and m.requirements))
    for name in sorted(set(gold.conditions) | set(model.conditions)):
        from netzoo_agent_core.contracts.menu_reading import Said
        put(f"conditions.{name}", _said(gold.conditions.get(name, Said())), _said(model.conditions.get(name, Said())))
    put("data", frozenset(gold.data), frozenset(model.data))
    put("data_absent", frozenset(gold.data_absent), frozenset(model.data_absent))
    put("groups", bool(gold.groups), bool(model.groups))
    put("sample_count", _count(gold.sample_count), _count(model.sample_count))
    put("feature_count", _count(gold.feature_count), _count(model.feature_count))
    put("single_feature_count", gold.single_feature_count, model.single_feature_count)
    put("claims", _said(gold.claims), _said(model.claims))
    put("delivery", _said(gold.delivery), _said(model.delivery))
    put("unregistered_methods", bool(gold.unregistered_methods), bool(model.unregistered_methods))
    put("context_mentions", frozenset(gold.context_mentions), frozenset(model.context_mentions))
    put("unsure_files", bool(gold.unsure_files), bool(model.unsure_files))
    put("run_requested", gold.run_requested, model.run_requested)
    matched = sum(any(_setting_match(g, m) for m in model.settings) for g in gold.settings)
    put("settings", len(gold.settings), len(model.settings),
        matched == len(gold.settings) and len(model.settings) == len(gold.settings))
    return out


def limits_and_doubts(gold, model) -> dict:
    """Recall units: each gold limit and each gold doubt, read or missed; and the read's own extra ones."""
    found = {"limit": [], "doubt": [], "extra_limit": 0, "extra_doubt": 0}
    for g in gold.settings:
        hit = any(_setting_match(g, m) for m in model.settings)
        found["doubt" if g.unsure else "limit"].append((f"setting:{g.control}", hit))
    found["extra_limit"] += sum(not any(_setting_match(g, m) for g in gold.settings) and not m.unsure
                                for m in model.settings)
    found["extra_doubt"] += sum(m.unsure and not any(_setting_match(g, m) for g in gold.settings)
                                for m in model.settings)
    for name in ("sample_count", "feature_count"):
        g, m = getattr(gold, name), getattr(model, name)
        if g.status == "stated":
            found["limit"].append((name, m.status == "stated" and m.value == g.value))
        elif g.status in DOUBT:
            found["doubt"].append((name, m.status in DOUBT))
        if m.status in DOUBT and g.status not in DOUBT:
            found["extra_doubt"] += 1
        if m.status == "stated" and g.status == "not_stated":
            found["extra_limit"] += 1
    if gold.single_feature_count is not None:
        found["limit"].append(("single_feature_count", model.single_feature_count == gold.single_feature_count))
    for kind in gold.data_absent:
        found["limit"].append((f"lacks:{kind}", kind in model.data_absent))
    found["extra_limit"] += len(set(model.data_absent) - set(gold.data_absent))
    saids = [(f"conditions.{n}", gold.conditions[n], model.conditions.get(n)) for n in gold.conditions]
    for index, (g, m) in enumerate(_pair(_deliverables(gold), _deliverables(model))):
        saids += [(f"wanted.{n}", getattr(g, n), getattr(m, n) if m else None) for n in WANTED]
    for name, g, m in saids:
        if g.status in DOUBT:
            found["doubt"].append((name, m is not None and m.status in DOUBT))
    gold_doubts = {name for name, g, _m in saids if g.status in DOUBT}
    model_saids = [(f"conditions.{n}", s) for n, s in model.conditions.items()] + [
        (f"wanted.{n}", getattr(w, n)) for w in _deliverables(model) for n in WANTED]
    found["extra_doubt"] += sum(s.status in DOUBT and name not in gold_doubts for name, s in model_saids)
    if gold.unsure_files:
        found["doubt"].append(("unsure_files", bool(model.unsure_files)))
    elif model.unsure_files:
        found["extra_doubt"] += 1
    return found


# --- scoring -------------------------------------------------------------------------------------------------------

def _conservative(a: str, b: str) -> str:
    """Spec 3.6: two reads that differ -> CLARIFY if either is; DO vs DECLINE -> ASK; else the one that asks."""
    if a == b:
        return a
    if "CLARIFY" in (a, b):
        return "CLARIFY"
    if "UNCHECKED" in (a, b):
        return "UNCHECKED"
    return "ASK"


def score(tag: str) -> None:
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    data = json.loads((HERE / "live" / tag / "bench.json").read_text())
    rows = data["rows"]
    result = {"commit": data["commit"], "shape": data["shape"], "arms": {}}
    for arm in ("first", "focused"):
        fields, recall = defaultdict(lambda: [0, 0]), {"limit": defaultdict(lambda: [0, 0]),
                                                        "doubt": defaultdict(lambda: [0, 0])}
        extra = Counter()
        calls, kinds, outcomes, failed = defaultdict(list), defaultdict(dict), Counter(), 0
        for row in rows:
            source = row["focus"] if arm == "focused" and row.get("focus", {}).get("ran") else row
            item, gold_raw = ITEMS[row["id"]], GOLD[row["id"]]
            gold = gold_reading(gold_raw)
            if row["status"] == "failed":
                failed += 1
                model = MenuReading(status="failed")
            else:
                model = MenuReading.model_validate(source["reading"])
            decision = decide_menu(model, item["prompt"])
            outcome = gate_score(item, decision, gold_raw.get("fact"))
            calls[item["class"]].append(outcome == "correct")
            outcomes[(item["class"], outcome)] += 1
            kinds[row["id"]][row["rep"]] = decision.kind
            kinds[row["id"]][f"right{row['rep']}"] = outcome == "correct"
            if model.status == "failed":
                continue
            for name, (_g, _m, match) in compare(gold, model).items():
                fields[name][0] += match
                fields[name][1] += 1
            found = limits_and_doubts(gold, model)
            for family in ("limit", "doubt"):
                for name, hit in found[family]:
                    key = name.split(":")[0]
                    recall[family][key][0] += hit
                    recall[family][key][1] += 1
            if item["class"] == "do":
                extra["limit"] += found["extra_limit"]
                extra["doubt"] += found["extra_doubt"]
        agree = sum(k.get(0) == k.get(1) for k in kinds.values())
        merged = Counter()
        for key, k in kinds.items():  # agreeing reads keep their scored call; differing ones take the conservative kind
            right = k["right0"] if k.get(0) == k.get(1) else \
                _conservative(k.get(0), k.get(1)) == EXPECTED[ITEMS[key]["class"]]
            merged[(ITEMS[key]["class"], right)] += 1
        total = [sum(v[0] for v in fields.values()), sum(v[1] for v in fields.values())]
        result["arms"][arm] = {
            "failed_reads": failed,
            "field_accuracy": {"overall": total, **{k: v for k, v in sorted(fields.items())}},
            "limit_recall": {"overall": [sum(v[0] for v in recall["limit"].values()),
                                         sum(v[1] for v in recall["limit"].values())], **recall["limit"]},
            "doubt_recall": {"overall": [sum(v[0] for v in recall["doubt"].values()),
                                         sum(v[1] for v in recall["doubt"].values())], **recall["doubt"]},
            "do_items_extra": {"limit": extra["limit"], "doubt": extra["doubt"]},
            "kind_agreement": [agree, len(kinds)],
            "calls_per_read": {cls: [sum(v), len(v)] for cls, v in sorted(calls.items())},
            "outcomes": {f"{c}:{o}": n for (c, o), n in sorted(outcomes.items())},
            "vague_declined_per_read": outcomes[("vague", "refused_without_asking")],
            "dont_declined_right_per_read": [sum(calls["dont"][i] for i in range(0, len(calls["dont"]), 2)),
                                             sum(calls["dont"][i] for i in range(1, len(calls["dont"]), 2))],
            "two_read_merge_right": {cls: sum(n for (c, ok), n in merged.items() if c == cls and ok)
                                     for cls in ("do", "dont", "ask", "vague")},
            "kinds": {key: [k.get(0), k.get(1), k.get("right0"), k.get("right1")] for key, k in sorted(kinds.items())},
        }
    write(HERE / "live" / tag / "score.json", result)
    for arm, r in result["arms"].items():
        print(f"== {arm}: failed {r['failed_reads']}, field accuracy {r['field_accuracy']['overall']}, "
              f"limit recall {r['limit_recall']['overall']}, doubt recall {r['doubt_recall']['overall']}, "
              f"kind agreement {r['kind_agreement']}, do-item extras {r['do_items_extra']}")
        print("   calls (both reads):", r["calls_per_read"], "| vague declined:", r["vague_declined_per_read"],
              "| dont declined right per read:", r["dont_declined_right_per_read"],
              "| two-read merge right:", r["two_read_merge_right"])


if __name__ == "__main__":
    {"read": read, "score": score}[sys.argv[1]](sys.argv[2])
