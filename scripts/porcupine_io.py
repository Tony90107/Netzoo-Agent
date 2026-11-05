"""Read and validate the PORCUPINE input contract (no side effects).

PORCUPINE analyses a population of sample-specific regulator->target networks.
The accepted layout is the labelled edge table that netZooPy writes for
LIONESS-PANDA (``tf gene <sample ...>``) and that the harness writes for
LIONESS-PUMA (``regulator gene prior_weight <sample ...>``):

* rows are edges, one unique (regulator, target) pair per row;
* the first two columns are the regulator (TF) and target gene identifiers;
* an optional third prior column (``prior``/``prior_weight``/``motif``) is an
  edge annotation, never a sample;
* every remaining column is one sample; sample IDs must be unique and every
  value finite and numeric.

Gene-gene co-expression tables (``gene1 gene2 ...``) and headerless or NumPy
LIONESS exports are rejected because they lack TF->gene edge labels.
The pathway file is a GMT: pathway name, description, gene IDs (tab separated).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REGULATOR_NAMES = frozenset({"tf", "regulator", "reg", "source", "tf_id"})
TARGET_NAMES = frozenset({"gene", "target", "tar", "target_gene"})
PRIOR_NAMES = frozenset({"prior", "prior_weight", "motif"})
COEXPRESSION_NAMES = frozenset({"gene1", "gene2"})
MIN_SAMPLES = 8
#: irlba::prcomp_irlba computes 3 components and stops below 4 edges; every target gene kept for R has at least
#: one usable edge, so 4 genes guarantee 4 edges for a pathway and for every random gene set of that size.
MIN_PATHWAY_GENES = 4
DEFAULTS = {
    "min_pathway_size": 5,
    "max_pathway_size": 150,
    "n_permutations": 1000,
    "n_cores": 1,
    "scale_data": True,
    "center_data": True,
    "fdr_threshold": 0.05,
    "min_effect_size": 2.0,
    "seed": 1,
}

__all__ = [
    "DEFAULTS",
    "MIN_SAMPLES",
    "PorcupineNetwork",
    "parameter_errors",
    "read_gmt",
    "read_sample_network",
    "scan_sample_network",
    "write_r_matrix",
]


@dataclass
class PorcupineNetwork:
    regulators: pd.Series
    targets: pd.Series
    values: pd.DataFrame  # edges x samples, numeric; empty when only scanned
    prior_column: str | None = None
    errors: list[str] = field(default_factory=list)
    sample_names: list[str] = field(default_factory=list)
    constant_edges: int = 0  # edges whose weight is identical in every sample

    @property
    def n_edges(self) -> int:
        return int(self.targets.shape[0])

    @property
    def samples(self) -> list[str]:
        return list(self.sample_names)


#: Rows parsed at a time when the matrix is only checked, so memory stays at one chunk
#: plus the edge labels however large the network (a genome-scale LIONESS table is
#: ~11M edges x samples).
SCAN_CHUNK_ROWS = 200_000


def _separator(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        return ","
    if suffix == ".tsv":
        return "\t"
    with path.open("r", encoding="utf-8") as handle:
        first = handle.readline()
    return "\t" if "\t" in first else r"\s+"


def _layout(resolved: Path, empty: PorcupineNetwork) -> tuple[str, list[str], str | None, list[str]] | None:
    """Separator, header names, prior column and sample columns -- or None with the error in `empty`."""
    if not resolved.is_file():
        empty.errors.append(f"sample_network_file must be an existing regular file: {resolved}")
        return None
    if resolved.suffix.casefold() in {".npy", ".npz", ".mat", ".h5"}:
        empty.errors.append(
            "sample_network_file must be a labelled text table (tf, gene, sample columns); "
            "binary LIONESS exports carry no regulator/target labels. Re-export LIONESS as .txt/.tsv/.csv."
        )
        return None
    try:
        separator = _separator(resolved)
        # The names come from the raw line: pandas would rename a repeated header ("S1", "S1" -> "S1.1").
        with resolved.open("r", encoding="utf-8") as handle:
            raw_header = handle.readline().rstrip("\r\n")
    except (OSError, UnicodeDecodeError) as error:
        empty.errors.append(f"sample_network_file could not be read: {error}")
        return None
    # LIONESS-PUMA .tsv/.csv files headed by the harness before 2026-11-05 have a space-separated header.
    space_header = separator == r"\s+" or (separator not in raw_header and len(raw_header.split()) >= 3)
    columns = [name.strip() for name in (
        re.split(r"\s+", raw_header.strip()) if space_header else raw_header.split(separator)
    )]
    lowered = [name.casefold() for name in columns]
    if lowered[:2] and set(lowered[:2]) == COEXPRESSION_NAMES:
        empty.errors.append(
            "sample_network_file is a gene-gene co-expression network (gene1, gene2); "
            "PORCUPINE needs regulator->target (TF->gene) edges such as LIONESS-PANDA or LIONESS-PUMA output"
        )
        return None
    if len(columns) < 3 or lowered[0] not in REGULATOR_NAMES or lowered[1] not in TARGET_NAMES:
        empty.errors.append(
            "sample_network_file header must start with a regulator column (tf/regulator) and a target "
            "column (gene/target), followed by one column per sample; got: " + ", ".join(columns[:4])
        )
        return None
    prior = columns[2] if lowered[2] in PRIOR_NAMES else None
    return separator, columns, prior, columns[3:] if prior else columns[2:]


def _chunks(resolved: Path, separator: str, columns: list[str], *, nrows: int | None, chunksize: int | None):
    """The table parsed with the C engine: labels as text, everything else as float64 (positional names)."""
    names = [f"c{index}" for index in range(len(columns))]
    dtype = {name: (str if index < 2 else "float64") for index, name in enumerate(names)}
    return pd.read_csv(
        resolved, sep=separator, engine="c", header=0, names=names, dtype=dtype, nrows=nrows,
        chunksize=chunksize, keep_default_na=True, na_filter=True,
    )


def _check_labels_and_samples(network: PorcupineNetwork, sample_columns: list[str]) -> None:
    errors = network.errors
    if any(not name or name.startswith("Unnamed:") for name in sample_columns):
        errors.append("sample_network_file sample column names must be non-empty")
    if len(set(sample_columns)) != len(sample_columns):
        errors.append("sample_network_file sample IDs (column names) must be unique")
    if network.targets.empty:
        errors.append("sample_network_file contains no edge rows")
        return
    if (network.regulators == "").any() or (network.targets == "").any():
        errors.append("sample_network_file regulator and target identifiers must be non-empty")
    if pd.MultiIndex.from_arrays([network.regulators, network.targets]).duplicated().any():
        errors.append("sample_network_file must have one row per unique regulator->target edge")


_NON_NUMERIC = "sample_network_file edge weights must all be finite numeric values"


def _read(path: str | Path, *, nrows: int | None, keep_values: bool) -> PorcupineNetwork:
    resolved = Path(path)
    empty = PorcupineNetwork(pd.Series(dtype=str), pd.Series(dtype=str), pd.DataFrame())
    layout = _layout(resolved, empty)
    if layout is None:
        return empty
    separator, columns, prior, sample_columns = layout
    network = PorcupineNetwork(pd.Series(dtype=str), pd.Series(dtype=str), pd.DataFrame(),
                               prior_column=prior, sample_names=sample_columns)
    if not sample_columns:
        network.errors.append("sample_network_file has no sample columns")
        return network
    first_sample = len(columns) - len(sample_columns)
    regulators, targets, blocks = [], [], []
    finite, constant = True, 0
    try:
        reader = _chunks(resolved, separator, columns, nrows=nrows, chunksize=None if keep_values else SCAN_CHUNK_ROWS)
        for chunk in ([reader] if keep_values else reader):
            regulators.append(chunk.iloc[:, 0].astype(str).str.strip())
            targets.append(chunk.iloc[:, 1].astype(str).str.strip())
            block = chunk.iloc[:, first_sample:]
            values = block.to_numpy(dtype=float)
            finite = finite and bool(np.isfinite(values).all())
            if values.size:
                constant += int((np.nanmax(values, axis=1) == np.nanmin(values, axis=1)).sum()) if finite else 0
            if keep_values:
                blocks.append(block)
    except ValueError as error:
        # The C parser refuses a non-numeric weight, and a row with the wrong number of fields.
        network.errors.append(
            _NON_NUMERIC if "could not convert" in str(error) or "Unable to parse" in str(error)
            else f"sample_network_file could not be parsed as a delimited table: {error}"
        )
        return network
    except (OSError, pd.errors.ParserError) as error:
        network.errors.append(f"sample_network_file could not be parsed as a delimited table: {error}")
        return network
    network.regulators = pd.concat(regulators, ignore_index=True) if regulators else pd.Series(dtype=str)
    network.targets = pd.concat(targets, ignore_index=True) if targets else pd.Series(dtype=str)
    network.constant_edges = constant
    if keep_values and blocks:
        values = pd.concat(blocks, ignore_index=True)
        values.columns = sample_columns
        network.values = values
    _check_labels_and_samples(network, sample_columns)
    if not finite:
        network.errors.append(_NON_NUMERIC)
    return network


def read_sample_network(path: str | Path, *, nrows: int | None = None) -> PorcupineNetwork:
    """Parse a labelled edges-by-samples network table with its values; errors are collected, not raised."""
    return _read(path, nrows=nrows, keep_values=True)


def scan_sample_network(path: str | Path) -> PorcupineNetwork:
    """Check the whole table chunk by chunk, keeping only the edge labels (``values`` stays empty).

    The input checks need the labels, the sample names, whether every weight is finite and how many edges are
    constant -- not the matrix itself, which only the runner loads.
    """
    return _read(path, nrows=None, keep_values=False)


def write_r_matrix(path: str | Path, out_path: str | Path, *, drop_constant: bool) -> tuple[int, int, set[str]]:
    """Stream the checked network into the ``regulator, target, <samples>`` TSV PORCUPINE's R script reads.

    Chunk by chunk, so the matrix is never held in Python. With ``drop_constant`` (scale_data), an edge whose
    weight is identical in every sample is left out: it cannot be scaled to unit variance and would abort the
    PCA. Returns (edges written, edges dropped, target genes written). Call it on a table that passed
    ``scan_sample_network``.
    """
    resolved = Path(path)
    layout = _layout(resolved, PorcupineNetwork(pd.Series(dtype=str), pd.Series(dtype=str), pd.DataFrame()))
    if layout is None:
        raise ValueError("sample_network_file failed its input check")
    separator, columns, _, sample_columns = layout
    first_sample = len(columns) - len(sample_columns)
    written = dropped = 0
    targets: set[str] = set()
    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(["regulator", "target", *sample_columns]) + "\n")
        for chunk in _chunks(resolved, separator, columns, nrows=None, chunksize=SCAN_CHUNK_ROWS):
            values = chunk.iloc[:, first_sample:]
            keep = (values.max(axis=1) != values.min(axis=1)) if drop_constant else pd.Series(True, index=chunk.index)
            out = values[keep].copy()
            out.insert(0, "target", chunk.iloc[:, 1].astype(str).str.strip()[keep].to_numpy())
            out.insert(0, "regulator", chunk.iloc[:, 0].astype(str).str.strip()[keep].to_numpy())
            out.to_csv(handle, sep="\t", header=False, index=False, float_format="%.10g")
            written += int(keep.sum())
            dropped += int((~keep).sum())
            targets.update(out["target"])
    return written, dropped, targets


def read_gmt(path: str | Path) -> tuple[dict[str, list[str]], list[str]]:
    resolved = Path(path)
    if not resolved.is_file():
        return {}, [f"pathway_file must be an existing regular file: {resolved}"]
    try:
        lines = resolved.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return {}, [f"pathway_file could not be read: {error}"]
    pathways: dict[str, list[str]] = {}
    errors: list[str] = []
    for number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        fields = [value.strip() for value in raw.split("\t")]
        genes = [gene for gene in fields[2:] if gene]
        if len(fields) < 3 or not fields[0] or not genes:
            errors.append(f"pathway_file line {number} must be GMT: pathway name, description, and at least one gene (tab separated)")
            continue
        if fields[0] in pathways:
            errors.append(f"pathway_file pathway names must be unique: {fields[0]}")
            continue
        pathways[fields[0]] = list(dict.fromkeys(genes))
    if not pathways and not errors:
        errors.append("pathway_file contains no GMT pathways")
    return pathways, errors


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def parameter_errors(params: dict) -> list[str]:
    get = lambda name: params.get(name, DEFAULTS[name])  # noqa: E731
    errors: list[str] = []
    low, high = get("min_pathway_size"), get("max_pathway_size")
    if not _is_int(low) or low < MIN_PATHWAY_GENES:
        errors.append(
            f"min_pathway_size must be an integer of at least {MIN_PATHWAY_GENES}: PORCUPINE's PCA (irlba, 3 components) "
            "needs at least 4 edges, and a pathway or random gene set of 4 genes is sure to have them"
        )
    if not _is_int(high) or high < MIN_PATHWAY_GENES:
        errors.append(f"max_pathway_size must be an integer of at least {MIN_PATHWAY_GENES}")
    if not errors and high < low:
        errors.append("max_pathway_size must be greater than or equal to min_pathway_size")
    if not _is_int(get("n_permutations")) or get("n_permutations") < 2:
        errors.append("n_permutations must be an integer of at least 2 (the t-test needs a random null)")
    if not _is_int(get("n_cores")) or get("n_cores") < 1:
        errors.append("n_cores must be a positive integer")
    if not _is_int(get("seed")):
        errors.append("seed must be an integer")
    for name in ("scale_data", "center_data"):
        if not isinstance(get(name), bool):
            errors.append(f"{name} must be true or false")
    fdr = get("fdr_threshold")
    if isinstance(fdr, bool) or not isinstance(fdr, (int, float)) or not 0 < fdr <= 1:
        errors.append("fdr_threshold must be a number in (0, 1]")
    es = get("min_effect_size")
    if isinstance(es, bool) or not isinstance(es, (int, float)) or es < 0:
        errors.append("min_effect_size must be a non-negative number")
    return errors
