"""Whether a named folder's prior mixes miRNA regulators with TFs (Log 186).

Log 154 recommends among tied workflows only when exactly one candidate's
inputs validate: a folder holding a miRNA list equips both PANDA and PUMA, so
it said nothing. What separates them is not whether a miRNA list exists but
whether the prior uses it -- PUMA models miRNA regulators, while a TF-only
method would read every regulator in the prior as a transcription factor.

The signal is read from content only: the miRNA-capable candidate must be
equipped by its own validator (`equipped_candidates`), and the regulator
column of the file validated as its prior must contain names from the file
validated as its miRNA list, and the TF-only counterpart must not be equipped
once that prior is set aside: a folder that also holds a clean TF prior (like
the toy folder with both `motif-panda.tsv` and `prior-puma.tsv`) says nothing.
Candidates are told apart by their registered regulator types, never by name.
Advisory only: nothing is eliminated.
"""

from __future__ import annotations

import re
from pathlib import Path

from workflow_registry import OUTPUT_CAPABILITIES, REQUIRED_INPUTS

from ..contracts.outcomes import AdvisoryCondition

__all__ = ["MIXED_PRIOR", "mirna_capable_candidate", "mixed_prior_conditions", "tf_only_counterpart"]

MIXED_PRIOR = "mixed_prior"


def mirna_capable_candidate(candidates: list[str], family: frozenset[str]) -> str | None:
    """The one tied candidate that models miRNA regulators, when TF-only candidates tie with it."""
    capable = [a for a in candidates if "mirna" in OUTPUT_CAPABILITIES[a].regulator_types]
    tf_only = [a for a in candidates if "mirna" not in OUTPUT_CAPABILITIES[a].regulator_types]
    if len(capable) == 1 and tf_only and capable[0] in family:
        return capable[0]
    return None


def tf_only_counterpart(action: str, family: frozenset[str]) -> str | None:
    """The family workflow needing exactly this one's inputs without the miRNA list."""
    wanted = set(REQUIRED_INPUTS[action]) - {"mirna_file"}
    matches = [a for a in sorted(family) if set(REQUIRED_INPUTS[a]) == wanted]
    return matches[0] if len(matches) == 1 else None


def _names(path: Path, column: int | None) -> set[str]:
    names = set()
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            cells = re.split(r"\t|,", line.rstrip("\r\n"))
            names.add((cells[0] if column == 0 else line).strip())
    return names


def mixed_prior_conditions(values: dict[str, Path], written: str) -> list[AdvisoryCondition]:
    """Conditions recording a content-validated input set whose prior uses its miRNA list."""
    try:
        overlap = _names(values["mirna_file"], None) & _names(values["motif_file"], 0)
    except (KeyError, OSError):
        return []
    if not overlap:
        return []
    return [
        AdvisoryCondition(axis="inspected_inputs", value=f"validated:{field}={path.name}", text_span=written)
        for field, path in values.items()
    ] + [AdvisoryCondition(axis="inspected_inputs", value=f"{MIXED_PRIOR}:{len(overlap)}", text_span=written)]
