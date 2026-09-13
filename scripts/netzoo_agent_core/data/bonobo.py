"""BONOBO input, output, and artifact contracts.

The public netZooPy 0.11.0 BONOBO API reads a labelled gene-by-sample table
through ``Bonobo(expression_file)`` and writes one square matrix per selected
sample.  The upstream writer does not persist row labels, so this module keeps
the gene axis and sample-to-file mapping in an agent-owned manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from .paths import _resolve_user_path
from workflow_registry import resolve_conditional_output

BONOBO_OUTPUT_FORMATS = frozenset({".h5", ".hdf", ".txt", ".csv"})
BONOBO_MANIFEST = "manifest.json"
_SAFE_SAMPLE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._ -]*\Z")


@dataclass(frozen=True, slots=True)
class BonoboInputBundle:
    expression: pd.DataFrame
    gene_ids: tuple[str, ...]
    sample_ids: tuple[str, ...]
    selected_sample_ids: tuple[str, ...]


def _read_bonobo_expression(path: Path) -> pd.DataFrame:
    """Read the labelled table in the format consumed by netZooPy Bonobo.

    The verified upstream reader uses tab separation for ``.txt``/``.tsv`` and
    a literal space separator for ``.csv``.  Keeping that distinction here
    prevents a standard comma CSV from silently being interpreted as one
    expression column by the package.
    """
    suffix = path.suffix.casefold()
    if suffix not in {".txt", ".tsv", ".csv"}:
        raise ValueError("BONOBO expression_file must end in .txt, .tsv, or .csv")
    separator = " " if suffix == ".csv" else "\t"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first_line = handle.readline().rstrip("\r\n")
    if not first_line:
        raise ValueError("BONOBO expression_file must contain a labelled header")
    raw_header = first_line.split(separator)
    if len(raw_header) < 2 or any(not item.strip() for item in raw_header):
        raise ValueError(
            "BONOBO expression_file must have a first-column gene header and "
            "at least one sample header"
        )
    raw_sample_ids = [item.strip() for item in raw_header[1:]]
    if len(raw_sample_ids) != len(set(raw_sample_ids)):
        raise ValueError("BONOBO sample IDs must be unique in the expression header")
    return pd.read_csv(path, sep=separator, header=0, index_col=0)


def _normalise_sample_names(sample_names: Any) -> tuple[str, ...]:
    if sample_names in (None, ""):
        return ()
    if isinstance(sample_names, str):
        values = [item.strip() for item in sample_names.split(",")]
    else:
        try:
            values = [str(item).strip() for item in sample_names]
        except TypeError as error:
            raise ValueError("sample_names must be a comma-separated string or list") from error
    if any(not value for value in values):
        raise ValueError("sample_names must not contain empty names")
    if len(values) != len(set(values)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        raise ValueError("sample_names contains duplicates: " + ", ".join(duplicates[:5]))
    return tuple(values)


def _sample_output_path(output_dir: str | Path, sample_id: str, output_format: str) -> Path:
    root = _resolve_user_path(str(output_dir))
    if output_format not in BONOBO_OUTPUT_FORMATS:
        raise ValueError(
            f"BONOBO output_format must be one of {sorted(BONOBO_OUTPUT_FORMATS)}"
        )
    if not _SAFE_SAMPLE_ID.fullmatch(sample_id) or sample_id in {".", ".."}:
        raise ValueError(
            f"sample ID {sample_id!r} cannot safely be used in a BONOBO filename; "
            "use a simple identifier without path separators"
        )
    path = (root / f"bonobo_{sample_id}{output_format}").resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("BONOBO output path escapes output_dir")
    return path


def _pval_output_path(output_dir: str | Path, sample_id: str, output_format: str) -> Path:
    root = _resolve_user_path(str(output_dir))
    path = (root / f"pvals_{sample_id}{output_format}").resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("BONOBO p-value output path escapes output_dir")
    return path


def bonobo_artifact_paths(
    output_dir: str | Path,
    sample_ids: tuple[str, ...] | list[str],
    output_format: str,
    save_pvals: bool = False,
) -> dict[str, list[Path] | Path]:
    samples = tuple(str(item) for item in sample_ids)
    paths: dict[str, list[Path] | Path] = {
        "networks": [_sample_output_path(output_dir, item, output_format) for item in samples],
        "manifest": _resolve_user_path(str(output_dir)) / BONOBO_MANIFEST,
    }
    if save_pvals:
        paths["pvalues"] = [_pval_output_path(output_dir, item, output_format) for item in samples]
    return paths


def _format_path(path: Path) -> str:
    return str(path)


def load_bonobo_inputs(
    expression_file: str,
    sample_names: Any = None,
    *,
    genes_axis: str = "auto",
    log_transformed: bool | None = None,
    centered: bool | None = None,
) -> BonoboInputBundle:
    path = _resolve_user_path(expression_file)
    if not path.is_file():
        raise ValueError(f"BONOBO expression_file does not exist: {path}")
    try:
        frame = _read_bonobo_expression(path)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"BONOBO expression_file could not be parsed: {error}") from error
    if frame.empty or frame.shape[0] == 0 or frame.shape[1] == 0:
        raise ValueError("BONOBO expression matrix must have at least one gene and one sample")
    if genes_axis not in {"auto", "rows"}:
        if genes_axis == "columns":
            raise ValueError(
                "BONOBO requires gene IDs on rows and sample IDs in columns; "
                "transpose the matrix before execution"
            )
        raise ValueError("BONOBO genes_axis must be auto or rows")
    index_header = str(frame.index.name or "").strip().casefold()
    if index_header in {"sample", "sample_id", "samples", "subject", "patient"}:
        raise ValueError(
            "BONOBO expression matrix appears sample-by-gene: its first column is "
            f"labelled {frame.index.name!r}; gene IDs must be on rows"
        )

    raw_gene_ids = frame.index.astype(str)
    raw_sample_ids = pd.Index([str(item) for item in frame.columns])
    gene_ids = raw_gene_ids.str.strip()
    sample_ids = pd.Index([item.strip() for item in raw_sample_ids])
    if any(not item for item in gene_ids) or any(not item for item in sample_ids):
        raise ValueError("BONOBO gene IDs and sample IDs must be non-empty")
    if any(raw != clean for raw, clean in zip(raw_gene_ids, gene_ids)) or any(
        raw != clean for raw, clean in zip(raw_sample_ids, sample_ids)
    ):
        raise ValueError(
            "BONOBO gene IDs and sample IDs must not have surrounding whitespace; "
            "clean the expression header and index first"
        )
    if gene_ids.duplicated().any():
        duplicates = sorted(set(gene_ids[gene_ids.duplicated()].tolist()))
        raise ValueError("BONOBO gene IDs must be unique; duplicates: " + ", ".join(duplicates[:5]))
    if sample_ids.duplicated().any():
        duplicates = sorted(set(sample_ids[sample_ids.duplicated()].tolist()))
        raise ValueError("BONOBO sample IDs must be unique; duplicates: " + ", ".join(duplicates[:5]))

    numeric = frame.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("BONOBO expression values must be numeric and contain no missing values")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("BONOBO expression values must be finite")
    if frame.shape[1] < 3:
        raise ValueError(
            "BONOBO requires at least three total samples so each sample-specific "
            "covariance has at least two background samples"
        )
    if log_transformed is not True:
        raise ValueError(
            "BONOBO requires log-transformed expression data; declare log_transformed=true "
            "after preprocessing"
        )
    if centered is not True:
        raise ValueError(
            "BONOBO requires centered expression data; declare centered=true after preprocessing"
        )

    requested = _normalise_sample_names(sample_names)
    missing = sorted(set(requested).difference(sample_ids))
    if missing:
        raise ValueError(
            "BONOBO sample_names contains IDs not present in the expression header: "
            + ", ".join(missing[:10])
        )
    selected = requested or tuple(sample_ids.tolist())
    return BonoboInputBundle(
        expression=numeric.set_axis(gene_ids, axis="index").set_axis(sample_ids, axis="columns"),
        gene_ids=tuple(gene_ids.tolist()),
        sample_ids=tuple(sample_ids.tolist()),
        selected_sample_ids=tuple(selected),
    )


def inspect_bonobo_inputs_impl(
    expression_file: str,
    sample_names: Any = None,
    *,
    genes_axis: str = "auto",
    log_transformed: bool | None = None,
    centered: bool | None = None,
    output_dir: str | None = None,
    output_format: str = ".h5",
    sparsify: bool = False,
    confidence: float = 0.05,
    save_pvals: bool = False,
) -> tuple[str, bool]:
    lines = [
        "BONOBO input inspection:",
        f"- expression_file: {_resolve_user_path(expression_file)}",
        "  required format: labelled gene-by-sample matrix",
        "  required header: first column is gene ID; remaining column names are sample IDs",
        "  preprocessing: log-transformed and centered values must be declared",
    ]
    try:
        requested = _normalise_sample_names(sample_names)
        bundle = load_bonobo_inputs(
            expression_file,
            requested,
            genes_axis=genes_axis,
            log_transformed=log_transformed,
            centered=centered,
        )
        lines.extend(
            [
                f"  genes: {len(bundle.gene_ids)} (unique)",
                f"  samples: {len(bundle.sample_ids)} (unique)",
                f"  selected samples: {', '.join(bundle.selected_sample_ids)}",
                f"  sample subset: {'requested' if requested else 'all samples'}",
            ]
        )
        if len(bundle.sample_ids) < 5:
            lines.append("  warning: fewer than five samples may make sample-specific estimates unstable")
        if output_dir is not None:
            root = _resolve_user_path(output_dir)
            if root.exists() and not root.is_dir():
                raise ValueError(f"BONOBO output_dir is not a directory: {root}")
            if output_format not in BONOBO_OUTPUT_FORMATS:
                raise ValueError(
                    f"BONOBO output_format must be one of {sorted(BONOBO_OUTPUT_FORMATS)}"
                )
            if not 0.0 < float(confidence) < 1.0:
                raise ValueError("BONOBO confidence must be strictly between 0 and 1")
            output_rule = resolve_conditional_output(
                "run_bonobo", {"sparsify": sparsify, "save_pvals": save_pvals}
            )
            if output_rule is None or not output_rule.valid:
                raise ValueError(
                    output_rule.semantics
                    if output_rule is not None
                    else "BONOBO output combination is not registered"
                )
            paths = bonobo_artifact_paths(
                output_dir,
                bundle.selected_sample_ids,
                output_format,
                save_pvals=save_pvals,
            )
            lines.append(f"  output folder: {root}")
            lines.append(f"  output format: {output_format}")
            lines.append(
                "  p-values: enabled" if save_pvals else "  p-values: not requested"
            )
            lines.append(f"  output semantics: {output_rule.semantics}")
            lines.append(
                "  expected network files: "
                + ", ".join(_format_path(item) for item in paths["networks"])
            )
    except (OSError, ValueError, TypeError) as error:
        lines.append(f"  error: {error}")
        return "\n".join(lines), False
    return "\n".join(lines), True


def _read_matrix_artifact(path: Path, key: str | None) -> pd.DataFrame:
    if path.suffix.casefold() in {".h5", ".hdf"}:
        return pd.read_hdf(path, key=key or "bonobo")
    separator = "\t" if path.suffix.casefold() == ".txt" else ","
    return pd.read_csv(path, sep=separator)


def _validate_matrix_artifact(
    path: Path,
    label: str,
    gene_ids: tuple[str, ...],
    key: str,
    errors: list[str],
) -> bool:
    if not path.is_file():
        errors.append(f"{label} is missing: {path}")
        return False
    if path.stat().st_size == 0:
        errors.append(f"{label} is empty: {path}")
        return False
    try:
        frame = _read_matrix_artifact(path, key)
    except Exception as error:  # noqa: BLE001 - malformed external artifacts are reported.
        errors.append(f"{label} could not be read: {error}")
        return False
    expected = list(gene_ids)
    error_count = len(errors)
    if frame.shape != (len(expected), len(expected)):
        errors.append(
            f"{label} must be a {len(expected)}x{len(expected)} matrix; got {frame.shape}"
        )
        return False
    columns = [str(item).strip() for item in frame.columns]
    values = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if columns != expected:
        errors.append(f"{label} columns must preserve the expression gene order")
    if len(set(columns)) != len(columns):
        errors.append(f"{label} gene columns must be unique")
    if not np.isfinite(values).all():
        errors.append(f"{label} values must be finite numeric values")
    return len(errors) == error_count


def validate_bonobo_output(
    output_dir: str,
    gene_ids: tuple[str, ...],
    sample_ids: tuple[str, ...],
    output_format: str,
    *,
    save_pvals: bool = False,
    sparsify: bool = False,
) -> tuple[bool, list[str], list[str], dict[str, int | float | str | bool]]:
    errors: list[str] = []
    artifacts: list[str] = []
    metrics: dict[str, int | float | str | bool] = {}
    root = _resolve_user_path(output_dir)
    if not root.is_dir():
        errors.append(f"BONOBO output folder is missing or not a directory: {root}")
        return False, errors, artifacts, metrics
    output_rule = resolve_conditional_output(
        "run_bonobo", {"sparsify": sparsify, "save_pvals": save_pvals}
    )
    if output_rule is None or not output_rule.valid:
        errors.append(
            output_rule.semantics
            if output_rule is not None
            else "BONOBO output combination is not registered"
        )
    try:
        paths = bonobo_artifact_paths(root, sample_ids, output_format, save_pvals=save_pvals)
    except ValueError as error:
        errors.append(str(error))
        return False, errors, artifacts, metrics
    for sample, path in zip(sample_ids, paths["networks"]):
        artifacts.append(str(path))
        _validate_matrix_artifact(path, f"BONOBO network for sample {sample}", gene_ids, "bonobo", errors)
    if save_pvals:
        for sample, path in zip(sample_ids, paths["pvalues"]):
            artifacts.append(str(path))
            _validate_matrix_artifact(path, f"BONOBO p-values for sample {sample}", gene_ids, "pvals", errors)
    manifest_path = paths["manifest"]
    artifacts.append(str(manifest_path))
    if not manifest_path.is_file():
        errors.append(f"BONOBO manifest is missing: {manifest_path}")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("method") != "BONOBO":
                errors.append("BONOBO manifest method must be BONOBO")
            if manifest.get("sample_ids") != list(sample_ids):
                errors.append("BONOBO manifest sample_ids must preserve the selected sample order")
            if manifest.get("gene_ids") != list(gene_ids):
                errors.append("BONOBO manifest gene_ids must preserve the expression gene order")
            if manifest.get("output_format") != output_format:
                errors.append("BONOBO manifest output_format does not match the plan")
            expected_network_map = {
                sample: str(path)
                for sample, path in zip(sample_ids, paths["networks"])
            }
            if manifest.get("sample_to_network") != expected_network_map:
                errors.append("BONOBO manifest sample_to_network does not match the selected samples")
            expected_pvalue_map = (
                {
                    sample: str(path)
                    for sample, path in zip(sample_ids, paths["pvalues"])
                }
                if save_pvals
                else {}
            )
            if manifest.get("sample_to_pvalues") != expected_pvalue_map:
                errors.append("BONOBO manifest sample_to_pvalues does not match the p-value contract")
            if bool(manifest.get("save_pvals")) != bool(save_pvals):
                errors.append("BONOBO manifest save_pvals does not match the plan")
            if output_rule is not None:
                for field_name, expected in output_rule.manifest_expectations.items():
                    if manifest.get(field_name) != expected:
                        errors.append(
                            f"BONOBO manifest {field_name} does not match the registered output contract"
                        )
                if manifest.get("output_semantics") != output_rule.semantics:
                    errors.append("BONOBO manifest output_semantics does not match the registered output contract")
                if sorted(manifest.get("produced_artifacts", [])) != sorted(
                    output_rule.produced_artifacts
                ):
                    errors.append("BONOBO manifest produced_artifacts does not match the registered output contract")
            if manifest.get("aggregate_network") is not None or manifest.get("prior_network") is not None:
                errors.append("BONOBO must not claim an aggregate or prior network artifact")
        except (OSError, ValueError, TypeError) as error:
            errors.append(f"BONOBO manifest is malformed: {error}")
    metrics.update(
        {
            "bonobo_genes": len(gene_ids),
            "bonobo_samples": len(sample_ids),
            "bonobo_networks": len(sample_ids) if not errors else 0,
            "bonobo_pvalues": len(sample_ids) if save_pvals and not errors else 0,
        }
    )
    return not errors, errors, artifacts, metrics


def materialize_bonobo_sample_coexpression(
    output_dir: str,
    sample_id: str,
    output_file: str,
) -> Path:
    """Explicitly select one sample and add labels for PANDA/PUMA readers."""
    root = _resolve_user_path(output_dir)
    manifest_path = root / BONOBO_MANIFEST
    if not manifest_path.is_file():
        raise ValueError(f"BONOBO manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(f"BONOBO manifest is malformed: {error}") from error
    sample_ids = tuple(str(item) for item in manifest.get("sample_ids", []))
    if sample_id not in sample_ids:
        raise ValueError(
            f"sample_id {sample_id!r} is not selected; available samples: "
            + ", ".join(sample_ids)
        )
    output_format = str(manifest.get("output_format", ".h5"))
    gene_ids = tuple(str(item) for item in manifest.get("gene_ids", []))
    network_path = _sample_output_path(root, sample_id, output_format)
    frame = _read_matrix_artifact(network_path, "bonobo")
    if [str(item).strip() for item in frame.columns] != list(gene_ids):
        raise ValueError("BONOBO sample matrix gene columns do not match its manifest")
    values = frame.apply(pd.to_numeric, errors="coerce")
    if values.shape != (len(gene_ids), len(gene_ids)) or values.isna().any().any():
        raise ValueError("BONOBO sample matrix is not a complete square numeric matrix")
    selected = pd.DataFrame(values.to_numpy(dtype=float), columns=gene_ids)
    selected.insert(0, "gene_id", gene_ids)
    destination = _resolve_user_path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(destination, sep="\t", index=False)
    return destination


def write_bonobo_manifest(
    output_dir: str,
    expression_file: str,
    bundle: BonoboInputBundle,
    output_format: str,
    *,
    genes_axis: str = "auto",
    sparsify: bool,
    confidence: float,
    save_pvals: bool,
    precision: str,
    keep_in_memory: bool,
    delta: float | None,
) -> Path:
    root = _resolve_user_path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = bonobo_artifact_paths(root, bundle.selected_sample_ids, output_format, save_pvals=save_pvals)
    output_rule = resolve_conditional_output(
        "run_bonobo", {"sparsify": sparsify, "save_pvals": save_pvals}
    )
    if output_rule is None or not output_rule.valid:
        raise ValueError(
            output_rule.semantics
            if output_rule is not None
            else "BONOBO output combination is not registered"
        )
    payload = {
        "method": "BONOBO",
        "api": "netZooPy.bonobo.Bonobo.run_bonobo",
        "netzoopy_version": "0.11.0",
        "expression_file": str(_resolve_user_path(expression_file)),
        "output_folder": str(root),
        "output_format": output_format,
        "genes_axis": genes_axis,
        "gene_ids": list(bundle.gene_ids),
        "sample_ids": list(bundle.selected_sample_ids),
        "all_expression_sample_ids": list(bundle.sample_ids),
        "sample_to_network": {
            sample: str(path) for sample, path in zip(bundle.selected_sample_ids, paths["networks"])
        },
        "sample_to_pvalues": (
            {sample: str(path) for sample, path in zip(bundle.selected_sample_ids, paths["pvalues"])}
            if save_pvals
            else {}
        ),
        "sparsify": bool(sparsify),
        "confidence": float(confidence),
        "save_pvals": bool(save_pvals),
        "precision": precision,
        "keep_in_memory": bool(keep_in_memory),
        "delta": delta,
        "aggregate_network": None,
        "prior_network": None,
        "interpretation": "sample-specific gene-gene co-expression association matrices; not a GRN or causal network",
        "produced_artifacts": sorted(output_rule.produced_artifacts),
        "output_semantics": output_rule.semantics,
    }
    payload.update(output_rule.manifest_expectations)
    manifest = root / BONOBO_MANIFEST
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def bonobo_api_output_folder(output_dir: str) -> str:
    """Return the trailing-separator string required by upstream concatenation."""
    root = _resolve_user_path(output_dir)
    return str(root) + os.sep


__all__ = [
    "BONOBO_MANIFEST",
    "BONOBO_OUTPUT_FORMATS",
    "BonoboInputBundle",
    "bonobo_api_output_folder",
    "bonobo_artifact_paths",
    "inspect_bonobo_inputs_impl",
    "load_bonobo_inputs",
    "materialize_bonobo_sample_coexpression",
    "validate_bonobo_output",
    "write_bonobo_manifest",
]
