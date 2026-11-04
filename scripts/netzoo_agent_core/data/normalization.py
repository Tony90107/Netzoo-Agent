"""Input contract for between-sample normalization of a count-scale expression matrix.

Four methods, one per run:
- ``snail``: SNAIL smooth-quantile normalization with PySNAIL (Kuijjer lab), within sample groups
  (tissues, conditions). It runs in its own process (``run-pysnail``) because importing PySNAIL starts
  pandarallel workers.
- ``rle`` (DESeq2 median of ratios), ``tmm`` (edgeR) and ``quantile`` (preprocessCore): the comparison arms of
  the PySNAIL manuscript, run with those Bioconductor packages by ``run-normalize-r``.
The checks here run in the agent process with pandas only.

Facts the report states were checked on PySNAIL 55bfe710 (2026-11-04):
- without a groups file every sample is one group, and the result is a quantile
  normalization (each sample takes the same reference distribution, apart from ties);
- PySNAIL's own example matrix is non-integer (expected counts), so count scale is
  read as "non-negative and not log-like", not "integers only".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .paths import _resolve_user_path

__all__ = [
    "NORMALIZATION_METHODS",
    "METHOD_LABELS",
    "SNAIL_AGGREGATIONS",
    "NormalizationInputs",
    "load_normalization_inputs",
    "normalization_input_report",
    "normalization_record_path",
]

SNAIL_AGGREGATIONS = ("median", "mean", "auto")
NORMALIZATION_METHODS = ("snail", "rle", "tmm", "quantile")
METHOD_LABELS = {
    "snail": "SNAIL (PySNAIL)",
    "rle": "RLE (DESeq2 median of ratios)",
    "tmm": "TMM (edgeR)",
    "quantile": "quantile (preprocessCore)",
}

# A matrix whose largest value is at most this, with mostly non-integer values, reads
# as log-scale (log2 of counts rarely exceeds ~20). Reported as a stop, because SNAIL
# on log values is a different, unpublished use of the method.
_LOG_SCALE_MAX = 20.0
_LOG_SCALE_NONINTEGER_SHARE = 0.5


@dataclass
class NormalizationInputs:
    expression_path: Path | None = None
    groups_path: Path | None = None
    output_path: Path | None = None
    expression: pd.DataFrame | None = None
    groups: pd.Series | None = None
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def normalization_record_path(output_file: str | Path) -> Path:
    """The JSON record written next to the normalized matrix (method, software version, factors, checksums)."""
    output = Path(output_file)
    return output.with_name(output.name + ".normalization.json")


def _read_expression(path: Path, errors: list[str]) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path, sep="\t", index_col=0, header=0)
    except Exception as error:  # noqa: BLE001 - report any parse failure as a contract error.
        errors.append(f"expression input could not be read as a tab-separated table: {error}")
        return None
    if frame.shape[1] == 0 or frame.shape[0] == 0:
        errors.append(
            "expression must be tab-separated with sample names in the first row and gene IDs "
            "in the first column."
        )
        return None
    return frame


def _check_expression(frame: pd.DataFrame, inputs: NormalizationInputs, label: str = "SNAIL") -> None:
    errors, notes = inputs.errors, inputs.notes
    genes = frame.index.astype(str).str.strip()
    samples = frame.columns.astype(str).str.strip()
    if genes.duplicated().any():
        errors.append("gene IDs must be unique: " + ", ".join(genes[genes.duplicated()].unique()[:5]))
    if samples.duplicated().any():
        errors.append("sample names must be unique: " + ", ".join(samples[samples.duplicated()].unique()[:5]))
    if frame.shape[1] < 2:
        errors.append("at least two samples are required for between-sample normalization.")
    values = frame.apply(pd.to_numeric, errors="coerce")
    bad = int(values.isna().sum().sum())
    if bad:
        errors.append(f"expression contains {bad} missing or non-numeric values.")
        return
    matrix = values.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        errors.append("expression contains infinite values.")
        return
    negatives = int((matrix < 0).sum())
    if negatives:
        errors.append(
            f"expression contains {negatives} negative values; {label} expects count-scale data "
            "(raw or expected counts), not log-transformed or centered values."
        )
        return
    non_integer_share = float((np.abs(matrix - np.round(matrix)) > 1e-9).mean())
    maximum = float(matrix.max()) if matrix.size else 0.0
    if maximum <= _LOG_SCALE_MAX and non_integer_share >= _LOG_SCALE_NONINTEGER_SHARE:
        errors.append(
            f"every value is at most {maximum:.3g} and {non_integer_share:.0%} are non-integer, "
            f"which reads as log-scale data; {label} expects count-scale data (raw or expected counts). "
            "Give the counts before any log transform."
        )
        return
    notes.append(
        "count scale: non-negative values"
        + (", all integers" if non_integer_share == 0 else f", {non_integer_share:.0%} non-integer (expected counts are accepted)")
    )
    inputs.expression = values


def _read_groups(path: Path, samples: list[str], inputs: NormalizationInputs) -> None:
    errors = inputs.errors
    try:
        table = pd.read_csv(path, sep="\t", header=None, dtype=str)
    except Exception as error:  # noqa: BLE001
        errors.append(f"groups file could not be read as a tab-separated table: {error}")
        return
    if table.shape[1] != 2:
        errors.append(
            f"groups file must have exactly two tab-separated columns (sample, group) and no header; "
            f"found {table.shape[1]}."
        )
        return
    table = table.apply(lambda column: column.str.strip())
    if table.isna().any().any() or (table == "").any().any():
        errors.append("groups file has empty sample or group cells.")
        return
    duplicated = table[0][table[0].duplicated()].unique()
    if len(duplicated):
        errors.append("groups file lists a sample more than once: " + ", ".join(duplicated[:5]))
        return
    groups = pd.Series(table[1].values, index=table[0].values)
    missing = [sample for sample in samples if sample not in groups.index]
    if missing:
        errors.append(
            f"{len(missing)} expression samples have no group (first: {', '.join(missing[:5])}); "
            "the groups file must name every sample column of the expression file."
        )
        return
    extra = [sample for sample in groups.index if sample not in set(samples)]
    if extra:
        inputs.notes.append(f"groups file names {len(extra)} samples not in the expression file; they are ignored.")
    groups = groups.loc[samples]
    sizes = groups.value_counts()
    inputs.notes.append(
        f"groups: {len(sizes)} ("
        + ", ".join(f"{name} {count}" for name, count in sizes.sort_index().items())
        + ")"
    )
    if len(sizes) == 1:
        inputs.notes.append(
            "only one group: SNAIL then behaves like quantile normalization (every sample "
            "takes the same distribution, apart from tied values)."
        )
    inputs.groups = groups


def load_normalization_inputs(
    expression_file: str,
    output_file: str,
    groups_file: str = "",
    method: str = "snail",
) -> NormalizationInputs:
    """Read and check the expression matrix and, for SNAIL, the optional groups file."""
    inputs = NormalizationInputs()
    expression_path = _resolve_user_path(expression_file) if expression_file else None
    if expression_path is None or not expression_path.is_file():
        inputs.errors.append("expression input does not exist or is not a file.")
        return inputs
    inputs.expression_path = expression_path
    if not output_file:
        inputs.errors.append("output_file is required.")
        return inputs
    output_path = _resolve_user_path(output_file)
    inputs.output_path = output_path
    groups_path = _resolve_user_path(groups_file) if groups_file else None
    inputs.groups_path = groups_path
    if output_path in {expression_path, groups_path} or normalization_record_path(output_path) in {
        expression_path, groups_path,
    }:
        inputs.errors.append("output path must be different from the inputs.")
        return inputs
    if groups_path is not None and not groups_path.is_file():
        inputs.errors.append("groups file does not exist or is not a file.")
        return inputs

    frame = _read_expression(expression_path, inputs.errors)
    if frame is None:
        return inputs
    frame.index = frame.index.astype(str).str.strip()
    frame.columns = frame.columns.astype(str).str.strip()
    _check_expression(frame, inputs, METHOD_LABELS.get(method, method).split(" ")[0])
    if inputs.errors:
        return inputs
    if method != "snail":
        if groups_path is not None:
            inputs.notes.append(f"the groups file is used only by SNAIL; {METHOD_LABELS[method]} ignores it.")
            inputs.groups_path = None
        return inputs
    if groups_path is None:
        inputs.notes.append(
            "no groups file: all samples form one group, so the result is a quantile "
            "normalization; give a sample-to-group file (tissue or condition) for SNAIL's "
            "group-aware smoothing."
        )
    else:
        _read_groups(groups_path, list(frame.columns), inputs)
    return inputs


def normalization_input_report(
    expression_file: str,
    output_file: str,
    groups_file: str = "",
    aggregation: str = "median",
    method: str = "snail",
) -> tuple[str, bool, NormalizationInputs]:
    """A report of the input checks, whether they passed, and the loaded inputs."""
    if method not in NORMALIZATION_METHODS:
        return (
            f"Normalization inputs:\n- error: method must be one of {', '.join(NORMALIZATION_METHODS)}; got {method!r}.",
            False, NormalizationInputs(),
        )
    lines = [f"{METHOD_LABELS[method]} normalization inputs:"]
    if method == "snail" and aggregation not in SNAIL_AGGREGATIONS:
        lines.append(f"- error: aggregation must be one of {', '.join(SNAIL_AGGREGATIONS)}; got {aggregation!r}.")
        return "\n".join(lines), False, NormalizationInputs()
    inputs = load_normalization_inputs(expression_file, output_file, groups_file, method)
    if inputs.expression_path is not None:
        lines.append(f"- expression: {inputs.expression_path}")
    if inputs.groups_path is not None:
        lines.append(f"- groups: {inputs.groups_path}")
    if inputs.output_path is not None:
        lines.append(f"- output: {inputs.output_path}")
        lines.append(f"- record: {normalization_record_path(inputs.output_path)}")
    if inputs.expression is not None:
        lines.append(f"- genes: {inputs.expression.shape[0]}")
        lines.append(f"- samples: {inputs.expression.shape[1]}")
    if method == "snail":
        lines.append(f"- tied values: {aggregation} aggregation")
    lines.extend(f"- note: {note}" for note in inputs.notes)
    lines.extend(f"- error: {error}" for error in inputs.errors)
    ok = not inputs.errors
    if not ok:
        lines.append("- no output file was written.")
    return "\n".join(lines), ok, inputs
