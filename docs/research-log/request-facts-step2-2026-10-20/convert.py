"""ROUND-04 offline conversion check (collab/ROUND-04-PLAN.md section 2): no model calls.

Each recorded shape-1 reading (the ROUND-03 replay's rebuilt set) is converted to shape 2 by code -- an ask's own
counts and settings become request facts scoped to that ask, the request's own become facts for every result -- and
checked again. The two checks are compared result by result. This shows the code path; it says nothing about how a
model reads shape 2. A re-read's asks lose their counts and settings in the conversion (they cannot be scoped to
the first reading's results), so a re-read's results are left out of the comparison.

Usage: python3 -I convert.py CHECKS.json OUT.json   (CHECKS.json: `../request-facts-round03-2026-10-20/replay.py checks`)
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))

from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402

ASK_ONLY = ("settings", "sample_count", "sample_count_quote", "feature_counts")


def _reads(item: dict):
    if item.get("sample_count") is not None:
        yield "samples", (item.get("sample_count_quote", ""), item["sample_count"])
    for found in item.get("feature_counts") or []:
        yield "features", (found["quote"], found["count"])
    for found in item.get("settings") or []:
        yield "settings", (found["name"], found["quote"], found.get("value_quote", ""))


def _without(conditions: dict, own: set) -> dict:
    """The request-level reads no ask also made."""
    kept = {"sample_count": conditions.get("sample_count"), "sample_count_quote": conditions.get("sample_count_quote")}
    if ("samples", (kept["sample_count_quote"], kept["sample_count"])) in own:
        kept = {"sample_count": None, "sample_count_quote": ""}
    kept["feature_counts"] = [f for f in conditions.get("feature_counts") or []
                              if ("features", (f["quote"], f["count"])) not in own]
    kept["settings"] = [s for s in conditions.get("settings") or []
                        if ("settings", (s["name"], s["quote"], s.get("value_quote", ""))) not in own]
    return kept


def to_shape2(payload: dict) -> dict:
    proposal = copy.deepcopy(payload)
    conditions = {**unstated_conditions(1), **(proposal.get("conditions") or {})}
    samples, features, settings = [], [], []

    def take(item: dict, scope):
        if item.get("sample_count") is not None:
            samples.append({"count": item["sample_count"], "quote": item.get("sample_count_quote", ""),
                            "applies_to": scope})
        features.extend({"count": f["count"], "quote": f["quote"], "belongs_to": "", "applies_to": scope}
                        for f in item.get("feature_counts") or [])
        settings.extend({**s, "applies_to": scope} for s in item.get("settings") or [])

    asks = [ask for name, sentence in proposal.items() if name[1:].isdigit() for ask in sentence["asks"]]
    # A shape-1 request-level read means "stated somewhere", not "for every result": where an ask read the same words,
    # the ask's scope is the one the reading gave it.
    own = {(kind, words) for ask in asks for kind, words in _reads(ask)}
    take({**conditions, **_without(conditions, own)}, None)
    for ask in asks:
        take(ask, [ask["quote"]])
        for key in ASK_ONLY:
            ask.pop(key, None)
    for choice in conditions.get("open_choices") or []:
        for option in choice.get("options", []):
            for key in ASK_ONLY:
                option.pop(key, None)
    for key in ("sample_count", "sample_count_quote"):
        conditions.pop(key, None)
    proposal["conditions"] = {**conditions, "sample_counts": samples, "feature_counts": features,
                              "settings": settings}
    return proposal


def _view(item: dict) -> dict:
    return {key: item[key] for key in ("quote", "status", "delivered_by", "limits", "defaults", "instead",
                                       "depends_on", "outcomes")}


def _method(item: dict) -> dict:
    method = item["method"]
    return {"samples": method.get("samples"), "features": method.get("features"),
            "settings": sorted((s["name"], s.get("value", "")) for s in method.get("settings", []))}


def main(checks_path: str, out: str):
    data = json.loads(Path(checks_path).read_text())
    tally, rows = Counter(), []
    for key, row in data.items():
        payload = row["proposal"]
        count = sum(1 for name in payload if name[1:].isdigit())
        try:
            converted = to_shape2(payload)
            try:
                proposal = proposal_model(count, version=2).model_validate(converted)
            except ValueError:  # a backup-model reading (compact names)
                proposal = proposal_model(count, compact=True, version=2).model_validate(converted)
            check, _rejected = build_capability_check(row["task"], proposal)
        except Exception as error:  # noqa: BLE001
            tally[f"error {type(error).__name__}"] += 1
            continue
        tally["readings"] += 1
        before = {(item["kind"], item["quote"]): item for item in row["check"]["requirements"]}
        after = {(item.kind, item.quote): item.model_dump(mode="json") for item in check.requirements}
        if before.keys() != after.keys():
            # The recorded rebuild merged a re-read; its extra results are not this one-pass check's.
            tally["readings with re-read results (compared on shared results)"] += 1
        pairs = [(before[key], after[key]) for key in before if key in after]
        changed_method = [(b["quote"][:70], _method(b), _method(a)) for b, a in pairs
                          if b["kind"] == "result" and _method(b) != _method(a)]
        changed_call = [(b["quote"][:70], b["status"], a["status"], b["delivered_by"], a["delivered_by"])
                        for b, a in pairs if _view(b) != _view(a)]
        if changed_method:
            tally["readings whose result methods changed"] += 1
        if changed_call:
            tally["readings whose result calls changed"] += 1
        if changed_method or changed_call:
            rows.append({"key": key, "where": row["where"], "task": row["task"], "methods": changed_method,
                         "calls": changed_call, "conflicts": [c.model_dump() for c in check.fact_conflicts]})
    Path(out).write_text(json.dumps({"tally": tally, "rows": rows}, indent=1))
    print(json.dumps(tally, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
