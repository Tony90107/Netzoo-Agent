"""File and artifact contracts for sample-specific DRAGON networks (LIONESS-DRAGON).

LIONESS-DRAGON uses the same two paired omics layers as DRAGON and the same
netZooPy DRAGON functions. The shrinkage parameters are estimated once on all
samples (netZooPy ``LionessDragon``'s default), then for each sample k:

    N_k = n * (N_all - N_without_k) + N_without_k

which is netZooPy ``lioness_for_dragon.py``'s formula. Each network has one
value per pair of features, so the per-sample output is an edge-by-sample
table: ``source``, ``target`` and one column per sample, the upper triangle of
every sample's partial-correlation matrix.
"""

from __future__ import annotations

from typing import Callable, Iterator

import numpy as np
import pandas as pd

from .dragon import _delimiter, _output_separator
from .paths import _resolve_user_path

#: LIONESS needs a leave-one-out network for every sample, so it needs a cohort.
LIONESS_DRAGON_MIN_SAMPLES = 3
#: Edges x samples written to the per-sample table; above this the run is refused.
LIONESS_DRAGON_MAX_VALUES = 20_000_000


def lioness_dragon_size(n_samples: int, n_features: int) -> int:
    """Values the per-sample table holds: one per feature pair per sample."""
    return n_features * (n_features - 1) // 2 * n_samples


def lioness_dragon_networks(
    partial: Callable[[np.ndarray, np.ndarray, object], np.ndarray],
    x1: np.ndarray,
    x2: np.ndarray,
    lambdas,
) -> tuple[np.ndarray, Iterator[tuple[int, np.ndarray]]]:
    """The all-sample network, and each sample's LIONESS network in turn.

    ``partial`` is netZooPy's ``get_partial_correlation_dragon``; networks are
    produced one at a time so a large cohort never holds them all at once.
    """
    full = partial(x1, x2, lambdas)
    n = x1.shape[0]

    def each() -> Iterator[tuple[int, np.ndarray]]:
        for k in range(n):
            keep = np.arange(n) != k
            without = partial(x1[keep], x2[keep], lambdas)
            yield k, n * (full - without) + without

    return full, each()


def write_lioness_dragon_table(
    output_path: str,
    sample_ids: list[str],
    node_ids: list[str],
    networks: Iterator[tuple[int, np.ndarray]],
) -> str:
    """Write the edge-by-sample table; one column is filled per network.

    Pairs follow ``write_dragon_edge_list``'s order (``itertools.combinations``
    over the node IDs), so the two outputs line up row for row.
    """
    path = _resolve_user_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = np.triu_indices(len(node_ids), k=1)
    values = np.empty((left.size, len(sample_ids)), dtype=float)
    for k, network in networks:
        values[:, k] = network[left, right]
    frame = pd.DataFrame(values, columns=[str(sample) for sample in sample_ids])
    frame.insert(0, "target", [node_ids[index] for index in right])
    frame.insert(0, "source", [node_ids[index] for index in left])
    frame.to_csv(path, sep=_output_separator(path), index=False, float_format="%.12g")
    return str(path)


def validate_lioness_dragon_output(
    path_value: str,
    expected_samples: int | None = None,
) -> tuple[bool, list[str], dict[str, int | str]]:
    """Validate one edge-by-sample LIONESS-DRAGON table."""
    errors: list[str] = []
    metrics: dict[str, int | str] = {}
    path = _resolve_user_path(path_value)
    if not path.is_file() or path.stat().st_size == 0:
        return False, [f"LIONESS-DRAGON output is missing or empty: {path}"], metrics
    try:
        frame = pd.read_csv(path, sep=_delimiter(path), header=0)
    except Exception as error:  # noqa: BLE001 - malformed output is a typed result.
        return False, [f"LIONESS-DRAGON output could not be parsed: {error}"], metrics
    if list(frame.columns[:2]) != ["source", "target"] or frame.shape[1] < 3:
        return False, ["LIONESS-DRAGON output must start with source and target columns, then one column per sample."], metrics
    samples = frame.shape[1] - 2
    metrics.update({"samples": samples, "edges": int(len(frame))})
    if expected_samples is not None and samples != expected_samples:
        errors.append(f"LIONESS-DRAGON output has {samples} sample columns; expected {expected_samples}.")
    nodes = pd.unique(pd.concat([frame["source"], frame["target"]]).astype(str))
    if len(frame) != len(nodes) * (len(nodes) - 1) // 2:
        errors.append("LIONESS-DRAGON output must hold every feature pair exactly once.")
    if (frame["source"].astype(str) == frame["target"].astype(str)).any():
        errors.append("LIONESS-DRAGON output must not contain self-edges.")
    numeric = frame.iloc[:, 2:].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        errors.append("LIONESS-DRAGON values must be finite numeric values.")
    return not errors, errors, metrics


__all__ = [
    "LIONESS_DRAGON_MAX_VALUES",
    "LIONESS_DRAGON_MIN_SAMPLES",
    "lioness_dragon_networks",
    "lioness_dragon_size",
    "validate_lioness_dragon_output",
    "write_lioness_dragon_table",
]
