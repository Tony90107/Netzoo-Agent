"""Workflow-aware structural validation of generated NetZoo artifacts."""

from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

from netzoo_table_io import read_condor_edges, read_table

from ..contracts.decisions import TaskDecision
from ..contracts.results import ArtifactValidationResult
from .paths import condor_artifact_paths
from .paths import _resolve_user_path
from .coexpression import read_coexpression_matrix
from .dragon import validate_dragon_output
from .otter import load_otter_inputs, validate_otter_output

__all__ = [
    "ARTIFACT_WRITE_ACTIONS",
    "validate_output_artifacts",
]


ARTIFACT_WRITE_ACTIONS = frozenset(
    {
        "format_expression",
        "convert_expression",
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
        "run_cobra",
        "run_dragon",
        "run_otter",
    }
)


def _readable_nonempty_file(path: Path, label: str, errors: list[str]) -> bool:
    if not path.is_file():
        errors.append(f"{label} is missing or not a regular file: {path}")
        return False
    if path.stat().st_size == 0:
        errors.append(f"{label} is empty: {path}")
        return False
    try:
        with path.open("rb") as handle:
            handle.read(1)
    except OSError as error:
        errors.append(f"{label} is not readable: {error}")
        return False
    return True


def _table(path: Path, label: str, errors: list[str]) -> pd.DataFrame | None:
    if not _readable_nonempty_file(path, label, errors):
        return None
    try:
        frame = read_table(path, min_fields=2)
    except Exception as error:  # noqa: BLE001 - parsing failures are validation data.
        errors.append(f"{label} could not be parsed as a table: {error}")
        return None
    if frame.empty or frame.shape[1] < 2:
        errors.append(f"{label} must contain rows with at least two columns: {path}")
        return None
    return frame


def _drop_text_header(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    first = frame.iloc[0].astype(str).str.casefold().tolist()
    header_tokens = {"gene", "genes", "tf", "source", "node", "regulator"}
    if first and first[0].strip() in header_tokens:
        return frame.iloc[1:].reset_index(drop=True)
    return frame


def _validate_numeric_network(
    path: Path,
    label: str,
    errors: list[str],
) -> int:
    frame = _table(path, label, errors)
    if frame is None:
        return 0
    frame = _drop_text_header(frame)
    if frame.empty or frame.shape[1] < 3:
        errors.append(f"{label} must contain identifiers and numeric network values")
        return 0
    numeric = frame.iloc[:, 2:].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        errors.append(f"{label} contains non-numeric network values: {path}")
        return 0
    return int(frame.shape[0])


def _validate_expression(path: Path, errors: list[str]) -> int:
    frame = _table(path, "formatted expression", errors)
    if frame is None:
        return 0
    frame = _drop_text_header(frame)
    if frame.empty:
        errors.append("formatted expression contains no data rows")
        return 0
    numeric = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    if numeric.empty or numeric.isna().any().any():
        errors.append("formatted expression values must all be numeric")
        return 0
    return int(frame.shape[0])


def _validate_coexpression(path: Path, errors: list[str]) -> int:
    frame = _table(path, "co-expression output", errors)
    if frame is None:
        return 0
    frame = _drop_text_header(frame)
    values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    if frame.empty or values.empty or values.isna().any().any():
        errors.append("co-expression output must contain a numeric matrix")
        return 0
    if values.shape[0] != values.shape[1]:
        errors.append("co-expression output matrix must be square")
        return 0
    return int(values.shape[0])


def _validate_lioness(path: Path, errors: list[str]) -> int:
    if path.suffix.casefold() == ".npy":
        if not _readable_nonempty_file(path, "LIONESS output", errors):
            return 0
        try:
            array = np.load(path, allow_pickle=False)
        except Exception as error:  # noqa: BLE001 - malformed arrays are reported.
            errors.append(f"LIONESS NumPy output could not be loaded: {error}")
            return 0
        if (
            array.size == 0
            or array.ndim not in {2, 3}
            or not np.issubdtype(array.dtype, np.number)
        ):
            errors.append(
                "LIONESS NumPy output must be a non-empty numeric 2D/3D array"
            )
            return 0
        return int(array.size)
    return _validate_numeric_network(path, "LIONESS text output", errors)


def _validate_membership(path: Path, label: str, errors: list[str]) -> int:
    frame = _table(path, label, errors)
    if frame is None:
        return 0
    frame = _drop_text_header(frame)
    if frame.empty:
        errors.append(f"{label} contains no membership rows")
        return 0
    communities = pd.to_numeric(frame.iloc[:, 1], errors="coerce")
    if communities.isna().any():
        errors.append(f"{label} community values must be numeric")
        return 0
    return int(frame.shape[0])


def validate_output_artifacts(
    action: str,
    decision: TaskDecision,
) -> ArtifactValidationResult:
    """Validate the concrete output contract for a completed write action."""
    errors: list[str] = []
    warnings: list[str] = []
    artifacts: list[str] = []
    metrics: dict[str, int | float | str | bool] = {}

    if action not in ARTIFACT_WRITE_ACTIONS:
        return ArtifactValidationResult(
            ok=True,
            warnings=[f"No artifact contract is defined for {action}."],
        )

    if action == "run_cobra":
        if not decision.output_dir:
            errors.append("COBRA output_dir is missing")
        else:
            root = _resolve_user_path(decision.output_dir)
            manifest, components, summary = (
                root / "manifest.json",
                root / "components.npz",
                root / "summary.tsv",
            )
            adjusted_tsv, adjusted_npz = (
                root / "adjusted_coexpression.tsv",
                root / "adjusted_coexpression.npz",
            )
            artifacts = [
                str(manifest),
                str(components),
                str(summary),
                str(adjusted_tsv),
                str(adjusted_npz),
            ]
            if _readable_nonempty_file(manifest, "COBRA manifest", errors):
                try:
                    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
                    if manifest_data.get("method") != "COBRA":
                        errors.append("COBRA manifest method must be COBRA")
                    if not manifest_data.get("adjusted_coexpression"):
                        errors.append(
                            "COBRA manifest must describe the adjusted co-expression artifact"
                        )
                except (OSError, ValueError) as error:
                    errors.append(f"COBRA manifest is malformed: {error}")
            if _readable_nonempty_file(components, "COBRA components", errors):
                try:
                    arrays = np.load(components, allow_pickle=False)
                    if set(arrays.files) != {"psi", "Q", "d", "g"}:
                        errors.append("COBRA components must contain psi, Q, d, and g")
                except Exception as error:  # noqa: BLE001
                    errors.append(f"COBRA components could not be loaded: {error}")
            if _readable_nonempty_file(summary, "COBRA summary", errors):
                frame = _table(summary, "COBRA summary", errors)
                if frame is not None:
                    metrics["cobra_components"] = int(len(frame))
            if _readable_nonempty_file(
                adjusted_tsv, "COBRA adjusted co-expression TSV", errors
            ):
                try:
                    adjusted = read_coexpression_matrix(str(adjusted_tsv))
                    metrics["cobra_adjusted_coexpression_genes"] = int(
                        adjusted.shape[0]
                    )
                except ValueError as error:
                    errors.append(f"COBRA adjusted co-expression is malformed: {error}")
            if _readable_nonempty_file(
                adjusted_npz, "COBRA adjusted co-expression NPZ", errors
            ):
                try:
                    arrays = np.load(adjusted_npz, allow_pickle=False)
                    if set(arrays.files) != {"matrix", "gene_ids"}:
                        errors.append(
                            "COBRA adjusted co-expression NPZ must contain matrix and gene_ids"
                        )
                    elif arrays["matrix"].ndim != 2 or arrays["matrix"].shape[0] != arrays["matrix"].shape[1]:
                        errors.append(
                            "COBRA adjusted co-expression NPZ matrix must be square"
                        )
                except Exception as error:  # noqa: BLE001 - malformed arrays are reported.
                    errors.append(
                        f"COBRA adjusted co-expression NPZ could not be loaded: {error}"
                    )
    elif action == "run_condor":
        if not decision.output_dir:
            errors.append("CONDOR output_dir is missing")
        else:
            try:
                paths = condor_artifact_paths(
                    decision.output_dir,
                    decision.prefix or "condor",
                )
            except ValueError as error:
                errors.append(str(error))
            else:
                artifacts = [str(path) for path in paths.values()]
                edge_path = paths["edges.tsv"]
                if _readable_nonempty_file(edge_path, "CONDOR edges", errors):
                    try:
                        edges, _ = read_condor_edges(edge_path)
                        metrics["condor_edges"] = int(len(edges))
                    except (OSError, ValueError) as error:
                        errors.append(f"CONDOR edges are malformed: {error}")
                metrics["condor_reg_memberships"] = _validate_membership(
                    paths["reg_memb.tsv"], "CONDOR reg_memb", errors
                )
                metrics["condor_tar_memberships"] = _validate_membership(
                    paths["tar_memb.tsv"], "CONDOR tar_memb", errors
                )
                _readable_nonempty_file(paths["summary.txt"], "CONDOR summary", errors)
    elif action == "run_dragon":
        if not decision.output_file:
            errors.append("DRAGON output_file is missing")
        else:
            output = _resolve_user_path(decision.output_file)
            artifacts.append(str(output))
            ok, dragon_errors, dragon_metrics = validate_dragon_output(
                decision.output_file,
                decision.output_format,
            )
            if not ok:
                errors.extend(dragon_errors)
            metrics.update(dragon_metrics)
    elif action == "run_otter":
        if not decision.output_file:
            errors.append("OTTER output_file is missing")
        else:
            output = _resolve_user_path(decision.output_file)
            artifacts.append(str(output))
            try:
                bundle = load_otter_inputs(
                    decision.expression_file or "",
                    decision.coexpression_file or "",
                    decision.motif_file or "",
                    decision.ppi_file or "",
                    decision.precision,
                )
                ok, otter_errors, otter_metrics = validate_otter_output(
                    decision.output_file,
                    decision.output_format,
                    bundle.tf_ids,
                    bundle.gene_ids,
                )
                if not ok:
                    errors.extend(otter_errors)
                metrics.update(otter_metrics)
            except (OSError, ValueError) as error:
                errors.append(f"OTTER output contract could not be checked: {error}")
    else:
        if not decision.output_file:
            errors.append(f"{action} output_file is missing")
        else:
            output = _resolve_user_path(decision.output_file)
            artifacts.append(str(output))
            if action == "format_expression":
                metrics["expression_rows"] = _validate_expression(output, errors)
            elif action == "convert_expression":
                metrics["coexpression_genes"] = _validate_coexpression(output, errors)
            else:
                metrics["aggregate_rows"] = _validate_numeric_network(
                    output, "aggregate network output", errors
                )

        if action.startswith("run_lioness_"):
            if not decision.lioness_output:
                errors.append(f"{action} lioness_output is missing")
            else:
                lioness = _resolve_user_path(decision.lioness_output)
                artifacts.append(str(lioness))
                metrics["lioness_values"] = _validate_lioness(lioness, errors)

    metrics["validated_artifacts"] = len(artifacts) if not errors else 0
    return ArtifactValidationResult(
        ok=not errors,
        artifacts=artifacts,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )
