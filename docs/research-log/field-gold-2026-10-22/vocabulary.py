"""ROUND-26 phase 0 (`collab/ROUND-26-PLAN.md` 1.2): the registry vocabulary the field-gold labellers link to, built from
the registry itself -- the settings the reading may name, the capability sheet's PRODUCES / near-miss / registry-wide
entries, and each workflow's input slots from its YAML. Also writes one batch file per item set holding only ids and
prompts (no class, no gold, no reading).

Usage: python3 vocabulary.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.method_names import setting_meanings  # noqa: E402

LOGS = HERE.parent
_NOT_DATA = {"output_file", "output_dir", "lioness_output", "taxon", "with_header", "prefix"}


def input_slots() -> dict[str, dict]:
    slots: dict[str, dict] = {}
    for path in sorted((ROOT / "workflows").glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        controls = {control["name"] for control in spec.get("controls", [])}
        for required, names in ((True, spec.get("required_inputs", [])), (False, spec.get("optional_inputs", []))):
            for name in names:
                if name in _NOT_DATA or name in controls:
                    continue
                slot = slots.setdefault(name, {"required_by": [], "optional_for": []})
                slot["required_by" if required else "optional_for"].append(spec["workflow"])
    return slots


def main():
    entries = sheet_entries()
    vocabulary = {
        "settings": setting_meanings(),
        "produces": [{"id": e.id, "workflow": e.workflow, "text": e.text} for e in entries.values()
                     if e.kind == "produces"],
        "near_miss": [{"id": e.id, "workflow": e.workflow, "text": e.text, "why_not": e.why_not}
                      for e in entries.values() if e.kind == "near_miss"],
        "registry_wide": [{"id": e.id, "text": e.text, "why_not": e.why_not}
                          for e in entries.values() if e.kind == "registry_wide"],
        "input_slots": input_slots(),
    }
    (HERE / "vocabulary.json").write_text(json.dumps(vocabulary, indent=1, ensure_ascii=False))
    lines = ["# Registry vocabulary for field-gold labelling", "",
             "Built by `vocabulary.py` from the registry (setting meanings, capability sheet, workflow YAMLs).", "",
             "## Settings (`WORKFLOW.setting: what it does`)", ""]
    lines += [f"- {meaning}" for meaning in vocabulary["settings"]]
    lines += ["", "## PRODUCES entries (results a registered workflow gives)", ""]
    lines += [f"- `{e['id']}` ({e['workflow']}): {e['text']}" for e in vocabulary["produces"]]
    lines += ["", "## Near-miss entries (results a workflow does NOT give, and why)", ""]
    lines += [f"- `{e['id']}` ({e['workflow']}): {e['text']} -- why not: {e['why_not']}" for e in vocabulary["near_miss"]]
    lines += ["", "## Registry-wide limits (no registered workflow gives these)", ""]
    lines += [f"- `{e['id']}`: {e['text']} -- why not: {e['why_not']}" for e in vocabulary["registry_wide"]]
    lines += ["", "## Input slots (data a workflow takes, from each YAML's required_inputs / optional_inputs)", ""]
    lines += [f"- `{name}`: required by {', '.join(slot['required_by']) or '-'}; optional for "
              f"{', '.join(slot['optional_for']) or '-'}" for name, slot in vocabulary["input_slots"].items()]
    (HERE / "vocabulary.md").write_text("\n".join(lines) + "\n")

    sets = {"core": [], "h1": [], "h2": [], "h3": [], "h4": [], "h5": []}
    core = json.loads((LOGS / "core-judgment-2026-10-15/items.json").read_text())["items"]
    sets["core"] = [(item["id"], item["prompt"]) for item in (core.values() if isinstance(core, dict) else core)]
    for item in json.loads((LOGS / "strictness-audit-2026-10-20/audit.json").read_text())["items"].values():
        sets["h2" if item["set"] == "h2main" else "h3" if item["set"] == "h3main" else
             "h4" if item["set"] == "h4main" else item["set"]].append((item["id"], item["prompt"]))
    sets["h5"] = [(item["id"], item["prompt"])
                  for item in json.loads((LOGS / "heldout-h5-2026-10-21/items.json").read_text())["items"]]
    for name, rows in sets.items():
        (HERE / f"batch-{name}.json").write_text(json.dumps(
            {"set": name, "items": [{"id": i, "prompt": p} for i, p in sorted(rows)]}, indent=1, ensure_ascii=False))
    print({name: len(rows) for name, rows in sets.items()}, "items;",
          {key: len(value) for key, value in vocabulary.items()})


if __name__ == "__main__":
    main()
