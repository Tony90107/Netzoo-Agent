#!/usr/bin/env python3
"""Report how a review's field changes relate to the evidence for those fields.

Offline only: reads routing reports and contacts no provider.

Across three consecutive live rounds the review changed a dimension and the run
then failed on that dimension's evidence. This pairs each recorded
`review_patch.changed_fields` with the attempt-2 issues, so the relationship can
be measured instead of assumed, and it reports the dimensions the patch did NOT
change as a control: without that column there is no way to tell a consequence
of changing a field from a rate the corpus produces anyway.

Usage:
    analyze_patch_evidence.py REPORT.json [REPORT.json ...]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Patch field -> the evidence dimension its values are cited under. Mirrors
# netzoo_agent_core.interpretation.semantic_patch, deliberately by value so a
# report over archived rounds does not depend on the current code.
DIMENSION_OF = {
    "operation": "operation",
    "input_artifacts": "input_artifact",
    "artifact_type": "artifact_type",
    "entity_types": "entity_type",
    "regulator_types": "regulator_type",
    "target_types": "target_type",
    "granularity": "granularity",
    "selection_tags": "selection_tag",
}
OUTCOMES = ("missing", "ungrounded", "conflicting", "clean")
_ISSUE = re.compile(r"(missing_evidence|ungrounded_evidence|conflicting_evidence):([a-z_]+)=")


def _final_issues(row: dict) -> set[str]:
    attempts = [entry.get("attempt") for entry in row.get("diagnostic_details", [])]
    if not attempts:
        return set()
    last = max(a for a in attempts if a is not None)
    return {
        issue
        for entry in row["diagnostic_details"]
        if entry.get("attempt") == last
        for issue in entry.get("issues", [])
    }


def _evidence_state(issues: set[str], dimension: str) -> str:
    kinds = {match[1] for issue in issues if (match := _ISSUE.search(issue)) and match[2] == dimension}
    for kind, name in (("conflicting_evidence", "conflicting"),
                       ("ungrounded_evidence", "ungrounded"),
                       ("missing_evidence", "missing")):
        if kind in kinds:
            return name
    return "clean"


def main(paths: list[Path]) -> int:
    changed: dict[str, Counter] = {d: Counter() for d in DIMENSION_OF.values()}
    carried: dict[str, Counter] = {d: Counter() for d in DIMENSION_OF.values()}
    trials = patched = 0
    for path in paths:
        for row in json.loads(path.read_text(encoding="utf-8"))["results"]:
            trials += 1
            patch = row.get("review_patch")
            if not patch:
                continue
            patched += 1
            issues = _final_issues(row)
            names = set(patch.get("changed_fields") or [])
            for field, dimension in DIMENSION_OF.items():
                table = changed if field in names else carried
                table[dimension][_evidence_state(issues, dimension)] += 1

    print(f"reports {len(paths)}   trials {trials}   with a recorded patch {patched}\n")
    header = f"{'dimension':<16}{'':<3}" + "".join(f"{name:>13}" for name in OUTCOMES) + f"{'not clean':>12}"
    print(header)
    print("-" * len(header))
    totals = {"changed": Counter(), "carried": Counter()}
    for dimension in DIMENSION_OF.values():
        for label, table in (("CH", changed), ("--", carried)):
            counts = table[dimension]
            total = sum(counts.values())
            if not total:
                continue
            bad = total - counts["clean"]
            totals["changed" if label == "CH" else "carried"].update(counts)
            print(f"{dimension:<16}{label:<3}"
                  + "".join(f"{counts[name]:>13}" for name in OUTCOMES)
                  + f"{bad / total:>11.0%}")
    print("-" * len(header))
    for label, key in (("CH", "changed"), ("--", "carried")):
        counts = totals[key]
        total = sum(counts.values())
        bad = total - counts["clean"]
        print(f"{'ALL':<16}{label:<3}"
              + "".join(f"{counts[name]:>13}" for name in OUTCOMES)
              + f"{(bad / total if total else 0):>11.0%}")
    print("\nCH = the patch changed this dimension;  -- = it was carried forward.")
    print("The gap between those two rows is the effect a change has on evidence.")

    malformed = Counter()
    for path in paths:
        for row in json.loads(path.read_text(encoding="utf-8"))["results"]:
            for entry in row.get("diagnostic_details", []):
                for issue in entry.get("issues", []):
                    if issue.startswith("schema_validation:"):
                        malformed[issue.split(":", 1)[1]] += 1
    print("\nreview replies the contract could not parse at all:")
    for name, count in malformed.most_common() or [("(none)", 0)]:
        print(f"   {count:>3}  {name}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main([Path(arg) for arg in sys.argv[1:]]))
