"""Validator contracts for specification-driven workspace resource discovery."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeAlias

from workflow_registry import DiscoverySpec

from .inspection import expression_sample_count, inspect_condor_inputs_impl
from .tables import _inspect_panda_inputs_impl


ResourceValidator: TypeAlias = Callable[
    [Mapping[str, str], DiscoverySpec], tuple[bool, str]
]
ValidatorMap: TypeAlias = Mapping[str, ResourceValidator]

def validate_netzoo_inputs(
    values: Mapping[str, str], spec: DiscoverySpec
) -> tuple[bool, str]:
    _, compatible, _ = _inspect_panda_inputs_impl(
        values["expression_file"],
        values["motif_file"],
        values["ppi_file"],
        values.get("mirna_file", ""),
    )
    if not compatible:
        return False, "identifier_mismatch"
    if spec.min_samples is not None:
        sample_count, _ = expression_sample_count(values["expression_file"])
        if sample_count < spec.min_samples:
            return False, "insufficient_samples"
    return True, "regulatory input identifiers are compatible"


def validate_expression(
    values: Mapping[str, str], spec: DiscoverySpec
) -> tuple[bool, str]:
    sample_count, _ = expression_sample_count(values["expression_file"])
    minimum = spec.min_samples or 1
    if sample_count < minimum:
        return False, "insufficient_samples"
    return True, "expression matrix has sufficient samples"


def validate_condor_inputs(
    values: Mapping[str, str], spec: DiscoverySpec
) -> tuple[bool, str]:
    del spec
    _, compatible = inspect_condor_inputs_impl(values["network_file"])
    if not compatible:
        return False, "invalid_bipartite_edges"
    return True, "CONDOR edge input is compatible"


RESOURCE_VALIDATORS: ValidatorMap = {
    "inspect_netzoo_inputs": validate_netzoo_inputs,
    "inspect_expression": validate_expression,
    "inspect_condor_inputs": validate_condor_inputs,
}

__all__ = [
    "RESOURCE_VALIDATORS",
    "ResourceValidator",
    "ValidatorMap",
    "validate_condor_inputs",
    "validate_expression",
    "validate_netzoo_inputs",
]
