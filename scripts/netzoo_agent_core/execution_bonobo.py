"""BONOBO's verified Python API adapter and output-contract gate."""

from __future__ import annotations

import math
from numbers import Real

from . import settings
from .contracts import tool
from .data.bonobo import (
    BONOBO_OUTPUT_FORMATS,
    bonobo_api_output_folder,
    bonobo_artifact_paths,
    bonobo_upstream_format,
    inspect_bonobo_inputs_impl,
    load_bonobo_inputs,
    validate_bonobo_output,
    write_bonobo_manifest,
)
from .data.paths import _resolve_user_path
from workflow_registry import resolve_conditional_output

__all__ = ["inspect_bonobo_inputs", "run_bonobo"]


def _load_bonobo_api():
    """Load the exact public BONOBO API from the Docker runtime."""
    import importlib

    netzoopy = importlib.import_module("netZooPy")
    version = getattr(netzoopy, "__version__", None)
    if version != "0.11.0":
        raise RuntimeError(
            f"unsupported netZooPy version {version!r}; the validated BONOBO contract requires 0.11.0"
        )
    module = importlib.import_module("netZooPy.bonobo")
    bonobo_class = getattr(module, "Bonobo", None)
    if bonobo_class is None or not callable(bonobo_class):
        raise AttributeError("netZooPy.bonobo.Bonobo is not available")
    return bonobo_class, version


def _bonobo_failure(code: str, problem: str, needed: str) -> str:
    return (
        "BONOBO execution failed.\n"
        f"error code: {code}\n"
        f"error: {problem}\n"
        f"needed: {needed}"
    )


def _bonobo_delta(delta, sparsify: bool) -> tuple[float | None, str | None]:
    """The delta to pass upstream as a Python float, or why it cannot be used (Log 224).

    netZooPy 0.11.0 asserts `type(delta) == float`. With sparsify its per-edge
    variance uses d - g - 3 = 1/delta - 3: at delta >= 1/3 every variance is
    negative or undefined, so every p-value is NaN and the thresholded network
    silently loses every edge, and delta = 0 divides by zero. The estimated
    delta, 1/(3 + 2*mean(sd)/var(diag)), is always below 1/3.
    """
    if delta is None:
        return None, None
    if isinstance(delta, bool) or not isinstance(delta, Real):
        return None, f"delta must be a number, not {type(delta).__name__}"
    value = float(delta)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        return None, f"delta must be between 0 and 1, got {delta!r}"
    if sparsify and not 0.0 < value < 1.0 / 3.0:
        return None, (
            f"with sparsify, delta must be above 0 and below 1/3, got {delta!r}: at 1/3 or above "
            "every per-edge p-value is NaN and the sparsified network loses every edge, and at 0 "
            "the variance is undefined"
        )
    return value, None


def _bonobo_sparsity_behavior(sparsify: bool, save_pvals: bool) -> str:
    rule = resolve_conditional_output(
        "run_bonobo",
        {"sparsify": sparsify, "save_pvals": save_pvals},
    )
    return rule.semantics if rule is not None else "unregistered BONOBO output combination"


@tool
def inspect_bonobo_inputs(
    expression_file: str,
    output_dir: str = "",
    bonobo_output_format: str = ".h5",
    sample_names: list[str] | None = None,
    sparsify: bool = False,
    bonobo_confidence: float = 0.05,
    save_pvals: bool = False,
    genes_axis: str = "auto",
    log_transformed: bool | None = None,
    centered: bool | None = None,
) -> str:
    """Inspect BONOBO's labelled expression and output contract."""
    report, _ = inspect_bonobo_inputs_impl(
        expression_file,
        sample_names or [],
        output_dir=output_dir,
        output_format=bonobo_output_format,
        sparsify=sparsify,
        confidence=bonobo_confidence,
        save_pvals=save_pvals,
        genes_axis=genes_axis,
        log_transformed=log_transformed,
        centered=centered,
    )
    return report


@tool
def run_bonobo(
    expression_file: str,
    output_dir: str,
    bonobo_output_format: str = ".h5",
    sample_names: list[str] | None = None,
    sparsify: bool = False,
    bonobo_confidence: float = 0.05,
    save_pvals: bool = False,
    precision: str = "single",
    keep_in_memory: bool = False,
    delta: float | None = None,
    genes_axis: str = "auto",
    log_transformed: bool | None = None,
    centered: bool | None = None,
) -> str:
    """Run source-verified netZooPy BONOBO and validate every artifact."""
    try:
        if bonobo_output_format not in BONOBO_OUTPUT_FORMATS:
            return _bonobo_failure(
                "BONOBO_OUTPUT_FORMAT_UNSUPPORTED",
                f"unsupported output format {bonobo_output_format!r}",
                "use .h5/.hdf, .txt, or .csv",
            )
        if precision not in {"single", "double"}:
            return _bonobo_failure(
                "BONOBO_PRECISION_UNSUPPORTED",
                f"unsupported precision {precision!r}",
                "use single or double",
            )
        delta, delta_error = _bonobo_delta(delta, sparsify)
        if delta_error is not None:
            return _bonobo_failure(
                "BONOBO_DELTA_INVALID",
                delta_error,
                "leave delta empty to estimate it per sample, or choose a value in range",
            )
        output_rule = resolve_conditional_output(
            "run_bonobo", {"sparsify": sparsify, "save_pvals": save_pvals}
        )
        if output_rule is None or not output_rule.valid:
            return _bonobo_failure(
                "BONOBO_PVALUES_REQUIRE_SPARSIFY",
                output_rule.semantics
                if output_rule is not None
                else "the requested BONOBO output combination is not registered",
                "enable sparsify when p-value artifacts are requested",
            )
        report, inputs_ok = inspect_bonobo_inputs_impl(
            expression_file,
            sample_names or [],
            output_dir=output_dir,
            output_format=bonobo_output_format,
            sparsify=sparsify,
            confidence=bonobo_confidence,
            save_pvals=save_pvals,
            genes_axis=genes_axis,
            log_transformed=log_transformed,
            centered=centered,
        )
        if not inputs_ok:
            return _bonobo_failure(
                "BONOBO_INPUT_INVALID",
                "the expression or parameter contract failed validation; no API call was made",
                "correct the reported expression/header/sample/preprocessing/output errors",
            ) + "\n\n" + report
        bundle = load_bonobo_inputs(
            expression_file,
            sample_names or [],
            genes_axis=genes_axis,
            log_transformed=log_transformed,
            centered=centered,
        )
        output_root = _resolve_user_path(output_dir)
        paths = bonobo_artifact_paths(
            output_root,
            bundle.selected_sample_ids,
            bonobo_output_format,
            save_pvals=save_pvals,
        )
        input_path = _resolve_user_path(expression_file)
        output_paths = [*paths["networks"], *paths.get("pvalues", []), paths["manifest"]]
        if any(path == input_path for path in output_paths):
            return _bonobo_failure(
                "BONOBO_OUTPUT_OVERWRITES_INPUT",
                "a derived artifact would overwrite expression_file",
                "choose a separate output_dir",
            )
        preview = (
            "BONOBO Python API preview:\n"
            "- runtime: Docker pinned netZooPy 0.11.0\n"
            "- import: from netZooPy.bonobo import Bonobo\n"
            "- call: Bonobo(expression_file).run_bonobo(...)\n"
            f"- expression: {len(bundle.gene_ids)} genes x {len(bundle.sample_ids)} samples; "
            f"selected={list(bundle.selected_sample_ids)}\n"
            f"- parameters: output_fmt={bonobo_output_format}, sparsify={sparsify}, "
            f"confidence={bonobo_confidence}, save_pvals={save_pvals}, precision={precision}, "
            f"keep_in_memory={keep_in_memory}, delta={delta if delta is not None else 'API default'}\n"
            f"- output folder: {output_root}\n"
            + (
                f"- file format: {bonobo_output_format} is written as HDF5 with the "
                f"{bonobo_upstream_format(bonobo_output_format)} suffix\n"
                if bonobo_upstream_format(bonobo_output_format) != bonobo_output_format
                else ""
            )
            + f"- expected sample networks: {', '.join(str(item) for item in paths['networks'])}\n"
            f"- sparsity behavior: {_bonobo_sparsity_behavior(sparsify, save_pvals)}.\n"
            "- BONOBO produces sample-specific gene-gene co-expression matrices only; "
            "no aggregate/prior network or GRN is claimed.\n"
            "- no analysis was executed and no artifact was written (dry-run)."
        )
        if not settings.EXECUTE_TOOLS:
            return report + "\n\n" + preview

        try:
            bonobo_class, version = _load_bonobo_api()
        except ModuleNotFoundError as error:
            return _bonobo_failure(
                "BONOBO_NETZOOPY_MISSING",
                "netZooPy with the BONOBO module is not importable in this runtime",
                "execute inside the Docker image built from this Dockerfile; do not install a second unpinned copy",
            ) + f"\nloader detail: {error}"
        except RuntimeError as error:
            return _bonobo_failure(
                "BONOBO_VERSION_UNSUPPORTED",
                str(error),
                "use netZooPy 0.11.0 / the validated Docker NETZOOPY_REF",
            )
        except (AttributeError, ImportError) as error:
            return _bonobo_failure(
                "BONOBO_API_UNAVAILABLE",
                "the installed netZooPy package does not expose the verified BONOBO API",
                "use the pinned Docker runtime or reverify the selected commit",
            ) + f"\nloader detail: {error}"

        kwargs = {
            "output_folder": bonobo_api_output_folder(output_dir),
            "output_fmt": bonobo_upstream_format(bonobo_output_format),
            "keep_in_memory": keep_in_memory,
            "sparsify": sparsify,
            "confidence": bonobo_confidence,
            "save_pvals": save_pvals,
            "precision": precision,
            "sample_names": list(bundle.selected_sample_ids),
        }
        if delta is not None:
            kwargs["delta"] = delta
        try:
            model = bonobo_class(expression_file)
            model.run_bonobo(**kwargs)
        except SystemExit as error:
            return _bonobo_failure(
                "BONOBO_API_ERROR",
                f"the verified BONOBO API exited during execution: {error}",
                "check the validated expression and pinned netZooPy runtime",
            )
        except Exception as error:  # noqa: BLE001
            return _bonobo_failure(
                "BONOBO_API_ERROR",
                f"the verified BONOBO API call failed: {type(error).__name__}: {error}",
                "check the validated expression and pinned netZooPy runtime",
            )
        try:
            manifest = write_bonobo_manifest(
                output_dir,
                expression_file,
                bundle,
                bonobo_output_format,
                sparsify=sparsify,
                confidence=bonobo_confidence,
                genes_axis=genes_axis,
                save_pvals=save_pvals,
                precision=precision,
                keep_in_memory=keep_in_memory,
                delta=delta,
            )
            valid, errors, _, _ = validate_bonobo_output(
                output_dir,
                bundle.gene_ids,
                bundle.selected_sample_ids,
                bonobo_output_format,
                save_pvals=save_pvals,
                sparsify=sparsify,
            )
        except (OSError, ValueError, TypeError) as error:
            return _bonobo_failure(
                "BONOBO_OUTPUT_ERROR",
                f"the result could not be written or parsed: {error}",
                "choose a writable output_dir and rerun in the pinned Docker runtime",
            )
        if not valid:
            return _bonobo_failure(
                "BONOBO_OUTPUT_INVALID",
                "; ".join(errors),
                "inspect the output folder and use a netZooPy version matching the verified API contract",
            )
        return (
            report
            + f"\n\nBONOBO API execution completed (netZooPy {version}).\n"
            f"- manifest: {manifest}\n"
            f"- networks: {len(bundle.selected_sample_ids)} sample-specific matrices\n"
            f"- p-values: {'saved' if save_pvals else 'not saved'}\n"
            f"- sparsity behavior: {_bonobo_sparsity_behavior(sparsify, save_pvals)}.\n"
            "- interpretation: sample-specific gene-gene co-expression association matrices; not a GRN, TF-gene regulation, or causal network."
        )
    except (OSError, ValueError, TypeError) as error:
        return _bonobo_failure(
            "BONOBO_RUNTIME_ERROR",
            f"unexpected BONOBO validation/runtime failure: {type(error).__name__}: {error}",
            "rerun inside the pinned Docker runtime and inspect the private execution log",
        )
    except Exception as error:  # noqa: BLE001 - keep interactive execution typed and bounded.
        return _bonobo_failure(
            "BONOBO_RUNTIME_ERROR",
            f"an unexpected runtime failure occurred: {type(error).__name__}: {error}",
            "rerun inside the pinned Docker runtime and inspect the private execution log",
        )
