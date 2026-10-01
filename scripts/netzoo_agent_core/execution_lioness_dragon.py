"""LIONESS-DRAGON: sample-specific DRAGON networks from the verified netZooPy API.

The inputs, their validation and the layer alignment are DRAGON's. The
computation is netZooPy ``lioness_for_dragon.py``'s, written against the same
DRAGON functions the DRAGON executor calls, so the outputs carry the same
layer-qualified node IDs as a DRAGON run.
"""

from __future__ import annotations

from . import settings
from .contracts import tool
from .data.dragon import inspect_dragon_inputs_impl, load_and_align_dragon_layers, write_dragon_matrix
from .data.lioness_dragon import (
    LIONESS_DRAGON_MAX_VALUES,
    LIONESS_DRAGON_MIN_SAMPLES,
    lioness_dragon_networks,
    lioness_dragon_size,
    write_lioness_dragon_table,
)
from .data.paths import _resolve_user_path

__all__ = ["run_lioness_dragon"]


def _load_dragon_api():
    """Import only the verified public netZooPy DRAGON module at execution time."""
    import importlib

    return importlib.import_module("netZooPy.dragon")


def _refusal(reason: str) -> str:
    return f"LIONESS-DRAGON execution failed; error: {reason}"


@tool
def run_lioness_dragon(
    omics_layer_1: str,
    omics_layer_2: str,
    output_file: str,
    lioness_output: str,
    lambda1: float | None = None,
    lambda2: float | None = None,
) -> str:
    """Run LIONESS-DRAGON: one partial-correlation network per sample across two omics layers."""
    try:
        if (lambda1 is None) != (lambda2 is None):
            return _refusal("lambda1 and lambda2 must be supplied together.")
        input_report, inputs_ok = inspect_dragon_inputs_impl(omics_layer_1, omics_layer_2)
        if not inputs_ok:
            return "LIONESS-DRAGON input validation failed; no API call was made.\n\n" + input_report
        layer1, layer2, errors = load_and_align_dragon_layers(omics_layer_1, omics_layer_2)
        if errors or layer1 is None or layer2 is None:
            return "LIONESS-DRAGON input validation failed; no API call was made.\n\n" + input_report
        inputs = {_resolve_user_path(omics_layer_1), _resolve_user_path(omics_layer_2)}
        outputs = [_resolve_user_path(output_file), _resolve_user_path(lioness_output)]
        if any(path in inputs for path in outputs):
            return _refusal("an output would overwrite an omics input.")
        if outputs[0] == outputs[1]:
            return _refusal("output_file and lioness_output must be different files.")
        n_samples = int(layer1.shape[0])
        n_features = int(layer1.shape[1] + layer2.shape[1])
        if n_samples < LIONESS_DRAGON_MIN_SAMPLES:
            return _refusal(
                f"LIONESS needs at least {LIONESS_DRAGON_MIN_SAMPLES} samples to leave one out; "
                f"the layers share {n_samples}."
            )
        values = lioness_dragon_size(n_samples, n_features)
        if values > LIONESS_DRAGON_MAX_VALUES:
            return _refusal(
                f"{n_samples} samples x {n_features} features make {values:,} per-sample values, "
                f"above the {LIONESS_DRAGON_MAX_VALUES:,} this workflow writes. Reduce the features "
                "(for example the most variable ones) or run DRAGON for one aggregate network."
            )
        lambda_text = (
            f"manual lambdas=({lambda1}, {lambda2})" if lambda1 is not None
            else "lambdas estimated once on all samples by estimate_penalty_parameters_dragon"
        )
        preview = (
            "LIONESS-DRAGON Python API preview:\n"
            "- import: netZooPy.dragon\n"
            f"- {lambda_text}\n"
            f"- calls: get_partial_correlation_dragon on all {n_samples} samples, then once per "
            "sample with that sample left out; N_k = n * (N_all - N_without_k) + N_without_k\n"
            f"- outputs: aggregate matrix at {outputs[0]}; {values:,} per-sample values "
            f"({n_features * (n_features - 1) // 2:,} feature pairs x {n_samples} samples) at {outputs[1]}\n"
            "- no analysis was executed and no artifact was written (dry-run)."
        )
        if not settings.EXECUTE_TOOLS:
            return input_report + "\n\n" + preview

        api = _load_dragon_api()
        x1 = layer1.to_numpy(dtype=float)
        x2 = layer2.to_numpy(dtype=float)
        if lambda1 is None:
            lambdas, _ = api.estimate_penalty_parameters_dragon(x1, x2)
        else:
            lambdas = [lambda1, lambda2]
        full, networks = lioness_dragon_networks(api.get_partial_correlation_dragon, x1, x2, lambdas)
        node_ids = [f"layer1::{value}" for value in layer1.columns] + [
            f"layer2::{value}" for value in layer2.columns
        ]
        aggregate = write_dragon_matrix(output_file, full, node_ids)
        per_sample = write_lioness_dragon_table(
            lioness_output, [str(sample) for sample in layer1.index], node_ids, networks,
        )
        return (
            input_report
            + "\n\nLIONESS-DRAGON API execution completed.\n"
            f"- lambdas: {list(map(float, lambdas))}\n"
            f"- aggregate network: {aggregate}\n"
            f"- per-sample networks: {per_sample} ({n_samples} samples)\n"
            "- interpretation: one undirected association network per sample; partial "
            "correlation is not a causal effect, and a sample's edges are estimated from how "
            "removing it changes the cohort network."
        )
    except Exception as error:  # noqa: BLE001 - tool failures are returned as typed text results.
        return _refusal(f"no trusted result was returned: {type(error).__name__}: {error}")
