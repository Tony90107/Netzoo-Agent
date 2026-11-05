"""Input contract for between-sample normalization of a count-scale expression matrix.

Five methods, one per run:
- ``snail``: SNAIL smooth-quantile normalization with PySNAIL (Kuijjer lab), within sample groups
  (tissues, conditions). It runs in its own process (``run-pysnail``) because importing PySNAIL starts
  pandarallel workers.
- ``rle`` (DESeq2 median of ratios), ``tmm`` (edgeR) and ``quantile`` (preprocessCore): the comparison arms of
  the PySNAIL manuscript, run with those Bioconductor packages by ``run-normalize-r``.
- ``fpkm``: edgeR ``rpkm`` on the raw library sizes (no TMM), which needs each gene's length in bases from a
  gene-lengths file; also run by ``run-normalize-r``.
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
    "default_snail_reason",
    "raw_count_signal",
    "raw_counts_line",
]

SNAIL_AGGREGATIONS = ("median", "mean", "auto")
NORMALIZATION_METHODS = ("snail", "rle", "tmm", "quantile", "fpkm")
METHOD_LABELS = {
    "snail": "SNAIL (PySNAIL)",
    "rle": "RLE (DESeq2 median of ratios)",
    "tmm": "TMM (edgeR)",
    "quantile": "quantile (preprocessCore)",
    "fpkm": "FPKM (edgeR rpkm)",
}

# A matrix whose largest value is at most this, with mostly non-integer values, reads
# as log-scale (log2 of counts rarely exceeds ~20). Reported as a stop, because SNAIL
# on log values is a different, unpublished use of the method.
_LOG_SCALE_MAX = 20.0
_LOG_SCALE_NONINTEGER_SHARE = 0.5
# Non-integer columns whose totals agree this closely (relative range) are
# TPM/CPM-like: real sequencing depths differ by far more than 1%.
_NORMALIZED_TOTAL_SPREAD = 0.01


@dataclass
class NormalizationInputs:
    expression_path: Path | None = None
    groups_path: Path | None = None
    output_path: Path | None = None
    expression: pd.DataFrame | None = None
    groups: pd.Series | None = None
    lengths_path: Path | None = None
    lengths: pd.Series | None = None
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
    fractional = np.abs(matrix - np.round(matrix)) > 1e-9
    non_integer_share = float(fractional.mean())
    maximum = float(matrix.max()) if matrix.size else 0.0
    # Judge the non-zero values: log2(count + 1) keeps every zero count a whole
    # zero, so a sparse log matrix is mostly integers overall.
    nonzero = matrix > 0
    nonzero_fractional_share = float(fractional[nonzero].mean()) if nonzero.any() else 0.0
    if maximum <= _LOG_SCALE_MAX and nonzero_fractional_share >= _LOG_SCALE_NONINTEGER_SHARE:
        errors.append(
            f"every value is at most {maximum:.3g} and {nonzero_fractional_share:.0%} of the non-zero "
            f"values are non-integer, which reads as log-scale data; {label} expects count-scale data "
            "(raw or expected counts). Give the counts before any log transform."
        )
        return
    totals = matrix.sum(axis=0)
    # Quantile normalization (preprocessCore normalize.quantiles) only ranks values, so
    # TPM or CPM input is ordinary for it; the other methods model counts.
    if (
        label != "quantile"
        and matrix.shape[1] >= 2
        and non_integer_share > 0
        and float(np.median(totals)) > 0
        and float((totals.max() - totals.min()) / np.median(totals)) < _NORMALIZED_TOTAL_SPREAD
    ):
        errors.append(
            f"every sample sums to about {float(np.median(totals)):,.6g} (within "
            f"{_NORMALIZED_TOTAL_SPREAD:.0%}), as TPM, CPM or other already-normalized values do; "
            f"{label} expects count-scale data (raw or expected counts), and normalizing normalized "
            "values twice distorts them. Give the counts before normalization."
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
    singletons = sorted(str(name) for name, count in sizes.items() if count == 1)
    if singletons and len(sizes) > 1:
        inputs.notes.append(
            f"warning: {len(singletons)} group(s) have a single sample ({', '.join(singletons[:5])}); "
            "SNAIL keeps each group's own quantiles in proportion to the between-group difference, and "
            "a one-sample group's quantiles are that sample itself, so its technical deviations "
            "(depth, composition) are kept as if they were a real group difference. Merge it with a "
            "related group or drop it."
        )
    inputs.groups = groups


def _read_lengths(path: Path, genes: list[str], inputs: NormalizationInputs) -> None:
    """Gene lengths in bases: two tab-separated columns (gene, length), an optional header row."""
    errors = inputs.errors
    try:
        table = pd.read_csv(path, sep="\t", header=None, dtype=str)
    except Exception as error:  # noqa: BLE001
        errors.append(f"gene-lengths file could not be read as a tab-separated table: {error}")
        return
    if table.shape[1] != 2:
        errors.append(f"gene-lengths file must have exactly two tab-separated columns (gene, length); found {table.shape[1]}.")
        return
    table = table.apply(lambda column: column.str.strip())
    if pd.to_numeric(table.iloc[:1, 1], errors="coerce").isna().all():
        table = table.iloc[1:]  # a header row
    lengths = pd.to_numeric(table[1], errors="coerce")
    if lengths.isna().any():
        errors.append(f"gene-lengths file has {int(lengths.isna().sum())} lengths that are not numbers.")
        return
    duplicated = table[0][table[0].duplicated()].unique()
    if len(duplicated):
        errors.append("gene-lengths file lists a gene more than once: " + ", ".join(duplicated[:5]))
        return
    lengths = pd.Series(lengths.to_numpy(dtype=float), index=table[0].to_numpy())
    missing = [gene for gene in genes if gene not in lengths.index]
    if missing:
        errors.append(
            f"{len(missing)} expression genes have no length (first: {', '.join(missing[:5])}); "
            "FPKM needs the length of every gene."
        )
        return
    lengths = lengths.loc[genes]
    if (lengths <= 0).any():
        errors.append("gene lengths must be positive: " + ", ".join(lengths.index[lengths <= 0][:5]))
        return
    inputs.notes.append(f"gene lengths: {len(lengths)} genes, {lengths.min():.0f}-{lengths.max():.0f} bases")
    inputs.lengths = lengths


def load_normalization_inputs(
    expression_file: str,
    output_file: str,
    groups_file: str = "",
    method: str = "snail",
    lengths_file: str = "",
) -> NormalizationInputs:
    """Read and check the expression matrix, SNAIL's optional groups file and FPKM's gene-lengths file."""
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
    lengths_path = _resolve_user_path(lengths_file) if lengths_file else None
    inputs.lengths_path = lengths_path
    if output_path in {expression_path, groups_path, lengths_path} or normalization_record_path(output_path) in {
        expression_path, groups_path, lengths_path,
    }:
        inputs.errors.append("output path must be different from the inputs.")
        return inputs
    if groups_path is not None and not groups_path.is_file():
        inputs.errors.append("groups file does not exist or is not a file.")
        return inputs
    if method == "fpkm" and lengths_path is None:
        inputs.errors.append("FPKM needs a gene-lengths file (gene, length in bases); give its path.")
        return inputs
    if method == "fpkm" and not lengths_path.is_file():
        inputs.errors.append("gene-lengths file does not exist or is not a file.")
        return inputs

    frame = _read_expression(expression_path, inputs.errors)
    if frame is None:
        return inputs
    frame.index = frame.index.astype(str).str.strip()
    frame.columns = frame.columns.astype(str).str.strip()
    _check_expression(frame, inputs, METHOD_LABELS.get(method, method).split(" ")[0])
    if inputs.errors:
        return inputs
    if method != "fpkm" and lengths_path is not None:
        inputs.notes.append(f"the gene-lengths file is used only by FPKM; {METHOD_LABELS[method]} ignores it.")
        inputs.lengths_path = None
    if method == "fpkm":
        _read_lengths(lengths_path, list(frame.index), inputs)
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
    lengths_file: str = "",
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
    inputs = load_normalization_inputs(expression_file, output_file, groups_file, method, lengths_file)
    if inputs.expression_path is not None:
        lines.append(f"- expression: {inputs.expression_path}")
    if inputs.groups_path is not None:
        lines.append(f"- groups: {inputs.groups_path}")
    if inputs.lengths_path is not None:
        lines.append(f"- gene lengths: {inputs.lengths_path}")
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


def default_snail_reason(has_groups: bool) -> str:
    """Why SNAIL suits a request that names no method and states no need -- from what PySNAIL is published to do
    (its README: smooth quantile normalization can create false co-expression between lowly expressed genes, which
    affects co-expression network analysis; SNAIL corrects it), and from the groups the request did or did not give."""
    base = (
        "SNAIL avoids the false co-expression between lowly expressed genes that ordinary smooth quantile "
        "normalization can create, and NetZoo's network methods (PANDA, LIONESS and others) build on gene co-expression"
    )
    if has_groups:
        # Not "real group differences are kept" (toy comparison 2026-11-05): PySNAIL mixes the pooled and the group
        # distributions with weight 1 - SSB/SST, which on raw counts with uneven depth was 0.92-0.97 (nearly pooled).
        return base + ("; with your groups file each group keeps its own value distribution only in proportion to how "
                       "much the groups differ beyond the spread within them, so on raw counts with uneven sequencing "
                       "depth the groups can still be made nearly alike.")
    return base + "; without a groups file it treats all samples as one group (see the groups line above)."


# "Looks like raw counts" (2026-11-05): before a workflow reads an expression matrix, a matrix of whole numbers
# with very different sample totals is pointed out, with the numbers, and normalizing first is offered.
_RAW_WHOLE_SHARE = 0.99   # share of values that are whole numbers
_RAW_MIN_MAX = 100.0      # a largest value below this is no count matrix worth flagging
_RAW_TOTAL_RATIO = 1.5    # largest / smallest sample total


def raw_count_signal(expression_file: str):
    """A RawCountSignal when the matrix reads as raw counts with uneven sample totals, else None.

    Whole numbers only (expected counts, CPM and every normalized output here are non-integer), none negative,
    a largest value of at least 100, and sample totals at least 1.5-fold apart. Never raises: an unreadable
    file gets no note (the workflow's own input check reports it).
    """
    from ..contracts.planning import RawCountSignal

    try:
        path = _resolve_user_path(expression_file)
        if not path.is_file():
            return None
        frame = pd.read_csv(path, sep="\t", index_col=0, header=0)
        matrix = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    except Exception:  # noqa: BLE001 - a note, never a failure
        return None
    if matrix.ndim != 2 or matrix.shape[1] < 2 or matrix.size == 0 or not np.isfinite(matrix).all():
        return None
    if (matrix < 0).any() or float(matrix.max()) < _RAW_MIN_MAX:
        return None
    if float((np.abs(matrix - np.round(matrix)) <= 1e-9).mean()) < _RAW_WHOLE_SHARE:
        return None
    totals = matrix.sum(axis=0)
    if float(totals.min()) <= 0 or float(totals.max() / totals.min()) < _RAW_TOTAL_RATIO:
        return None
    return RawCountSignal(
        expression_file=expression_file, samples=int(matrix.shape[1]), max_value=float(matrix.max()),
        total_min=float(totals.min()), total_max=float(totals.max()),
    )


def raw_counts_line(signal, workflow: str) -> str:
    """The preview line for a RawCountSignal: the numbers read from the file, what they mean, and the offer."""
    return (
        f"- Expression values: look like raw counts -- whole numbers up to {signal.max_value:,.0f}, and the "
        f"{signal.samples} sample totals range from {signal.total_min:,.0f} to {signal.total_max:,.0f} "
        f"({signal.total_max / signal.total_min:.1f}-fold). In raw counts every gene of a sample scales with its "
        "sequencing depth, so depth alone can make genes vary together across samples. "
        f"'Normalize first' normalizes this matrix (SNAIL by default), then plans {workflow} on the normalized matrix."
    )
