"""The values a slim read writes (spec 2026-10-19, 0 and 6.1): the payloads the two reads would send for a reading, and
one leaf counter for them and for the old shape's recorded payloads."""

from __future__ import annotations

from ..contracts.slim_reading import SlimReading
from .menu_reader import name_key
from .slim_reader import _SPECIAL_OF, FACTS, Needs, chosen

__all__ = ["wire_payloads", "wire_values"]


def wire_payloads(slim: SlimReading, needs: Needs, names: tuple[str, ...] = ()) -> tuple[dict, dict | None]:
    """The payloads steps 1 and 3 would send for this reading -- to count the values written (spec 6.1, S1/S2)."""
    core: dict = {"items": [{"quote": r.quote, "asks": r.said, "result": r.value, "results": list(r.values),
                             "outside_name": r.outside_name} for r in slim.results]}
    if names:
        core["names"] = {name_key(name): {"role": slim.roles.get(name, "target")} for name in names}
    core["data"] = [{"kind": d.name, "status": d.value, "quote": d.quote} for d in slim.data]
    core["only_these"] = slim.only_quote
    core["run"], core["run_quote"] = slim.run, slim.run_quote
    wire_of = {dimension: name for name, (_field, dimension, _menu) in FACTS.items() if dimension}
    facts = []
    for f in slim.stated:
        if f.field in ("C4",):
            values = [_SPECIAL_OF.get((f.name, v), v) for v in f.values]
            facts.append({"field": "special_data", "value": "" if values else _SPECIAL_OF.get((f.name, f.value), f.value),
                          "values": values, "quote": f.quote})
        elif f.field in ("C2", "C3", "D1", "D2", "D3", "D4", "D5", "D6", "D7"):
            name = wire_of[f.name]
            value = "" if name in ("outside_action", "raw_files", "groups", "file_doubt") else f.value
            facts.append({"field": name, "value": value, "values": list(f.values), "quote": f.quote})
    core["facts"] = facts
    core["unregistered_methods"] = list(slim.unregistered_methods)
    if not needs.runs:
        return core, None
    focus: dict = {}
    for key, item, dimension in needs.cells():
        focus[key] = {"status": "not_said", "value": None, "values": [], "quote": ""}
    for f in slim.stated:
        if not f.field.startswith("B") or f.field in ("B5", "B6") or not chosen(f, needs):
            continue
        for key, item, dimension in needs.cells():
            same = (dimension == {"integration": "layers", "mirna_driver": "regulators"}.get(f.name, f.name)
                    and f.item in (-1, item)) or (dimension.startswith("setting:") and f.name.startswith("setting:")
                                                 and dimension.endswith(f".{f.name.split(':', 1)[1]}"))
            if same:
                focus[key] = {"status": "unsure" if f.values else "stated", "value": None if f.values else f.value,
                              "values": list(f.values), "quote": f.quote}
    focus["settings"] = [{"quote": f.quote, "workflow": f.workflow, "control": f.name, "value": f.value,
                          "values": list(f.values), "asks_to_set": True} for f in slim.stated if f.field == "B5"]
    if needs.counts:
        focus["counts"] = [{"what": "samples" if f.name == "sample_count" else "features", "layer": "",
                            "value": None if f.values else int(f.value), "values": [int(v) for v in f.values],
                            "quote": f.quote} for f in slim.stated
                           if f.field == "B6" and f.name != "single_feature_count" and chosen(f, needs)]
    return core, focus


_EMPTY = (None, "", "not_stated", "not_mentioned", "not_said", "none", False, "unspecified", "nothing")


def wire_values(payload) -> tuple[int, int]:
    """(values written, values with content) of a payload: every leaf, an empty list counting once (phase 1's count:
    56 bench items x 2 reads, median 207.5 and 25)."""
    leaves = []

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            if not node:
                leaves.append([])
            for value in node:
                walk(value)
        else:
            leaves.append(node)

    walk(payload or {})
    return len(leaves), sum(1 for v in leaves if v != [] and v not in _EMPTY)
