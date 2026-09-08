#!/usr/bin/env python3
"""What became of each value whose quote the request did not contain.

Offline only: reads archived routing reports and contacts no provider.

Three documents state that accepted outcomes carry `unknown` in `operation` or
`artifact_type` in 8-12% of trials, and attribute that rate to the review
resolving an `ungrounded_evidence` issue by dropping the field -- `unknown`
needs no evidence, so dropping always validates where quoting may be impossible.
The rate and the mechanism were measured on different populations and no record
connected them. This script connects what the archives can connect:

- the rate itself, per round, so any redefinition of it shows up immediately;
- every first-pass `ungrounded_evidence` entry, paired with what the accepted
  outcome ended up holding for that dimension.

What the archives cannot answer is stated rather than guessed: where no
`ungrounded_evidence` names a dimension, they do not record whether the first
pass committed to it, so an `unknown` there is `unrecorded`, not `never_stated`.
Rounds run after the live instrument landed carry `outcome_downgrades` and are
read from it instead.

Usage:
    analyze_unknown_downgrades.py REPORT.json [REPORT.json ...]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Evidence dimension -> the outcome field carrying its values. Held by value, as
# in analyze_patch_evidence.py: a report over archived rounds must not change
# meaning when the current code does.
FIELD_OF = {
    "operation": "operation",
    "input_artifact": "input_artifacts",
    "artifact_type": "artifact_type",
    "entity_type": "entity_types",
    "regulator_type": "regulator_types",
    "target_type": "target_types",
    "granularity": "granularity",
    "selection_tag": "selection_tags",
}

# The two dimensions whose loss widens the candidate set from one capability to
# four. Fixed here so the measured rate cannot change its own denominator.
CORE_DIMENSIONS = ("operation", "artifact_type")

UNCOMMITTED = {"unknown", "not_applicable"}


def _first_pass_shapes(row: dict) -> list[dict]:
    """Deduplicate the shapes attempt 1 reports through more than one event."""
    for entry in row.get("diagnostic_details", []):
        if entry.get("attempt") == 1 and entry.get("evidence_shapes"):
            return list(entry["evidence_shapes"])
    return []


def _fate(outcome: dict, dimension: str, value: str) -> str:
    """What the accepted outcome holds for the dimension this value was cited under."""
    if not outcome:
        return "no_accepted_outcome"
    field = FIELD_OF.get(dimension)
    if field is None:
        return "unknown_dimension"
    held = outcome.get(field)
    if isinstance(held, list):
        if value in held:
            return "retained"
        return "abandoned" if not [
            item for item in held if item not in UNCOMMITTED
        ] else "replaced"
    if held == value:
        return "retained"
    return "abandoned" if held in UNCOMMITTED or held is None else "replaced"


def _unknown_core(row: dict) -> list[tuple[str, str]]:
    """(dimension, origin) for each core dimension the accepted outcome left open."""
    outcome = row.get("outcome") or {}
    # A round produced after the live instrument landed states the origin itself.
    if row.get("unknown_core") is not None:
        return [(item["dimension"], item["origin"]) for item in row["unknown_core"]]
    ungrounded = {
        str(shape.get("dimension")) for shape in _first_pass_shapes(row)
    }
    return [
        (
            dimension,
            # The archives record the first pass's value only where it was
            # reported ungrounded. Everywhere else the origin is simply not in
            # the record, and calling it "never stated" would be inventing it.
            "downgraded_after_ungrounded" if dimension in ungrounded else "unrecorded",
        )
        for dimension in CORE_DIMENSIONS
        if outcome.get(dimension) == "unknown"
    ]


def summarize(report: dict) -> dict:
    rows = report["results"]
    fates: Counter = Counter()
    origins: Counter = Counter()
    for row in rows:
        outcome = row.get("outcome") or {}
        for shape in _first_pass_shapes(row):
            fates[(
                str(shape.get("dimension")),
                str(shape.get("span")),
                _fate(outcome, str(shape.get("dimension")), str(shape.get("value"))),
            )] += 1
        origins.update(_unknown_core(row))
    return {
        "trials": len(rows),
        "corpus_sha256": report["metadata"]["corpus_sha256"][:10],
        "model": report["metadata"]["model"],
        "unknown_core_trials": sum(
            1 for row in rows
            if (row.get("outcome") or {}).get("operation") == "unknown"
            or (row.get("outcome") or {}).get("artifact_type") == "unknown"
        ),
        "unknown_core_origins": origins,
        "first_pass_ungrounded_fates": fates,
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    for path in argv:
        summary = summarize(json.loads(Path(path).read_text(encoding="utf-8")))
        print(f"\n{Path(path).name}  [{summary['model']}, corpus {summary['corpus_sha256']}]")
        rate = summary["unknown_core_trials"] / summary["trials"]
        print(
            f"  accepted outcome leaves operation or artifact_type open: "
            f"{summary['unknown_core_trials']}/{summary['trials']} = {rate:.1%}"
        )
        for (dimension, origin), count in sorted(summary["unknown_core_origins"].items()):
            print(f"    {dimension:14s} {origin:28s} {count}")
        if not summary["first_pass_ungrounded_fates"]:
            print("  no first-pass ungrounded evidence recorded in this round")
            continue
        print("  fate of every value the first pass could not ground:")
        for (dimension, span, fate), count in sorted(
            summary["first_pass_ungrounded_fates"].items()
        ):
            print(f"    {dimension:14s} span={span:10s} {fate:20s} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
