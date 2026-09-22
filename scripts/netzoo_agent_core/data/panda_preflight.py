"""PANDA-family input validation with bundled-demo provenance policy."""

from __future__ import annotations

from .demo_provenance import (
    bundled_demo_authority_note,
    is_verified_bundled_demo,
)
from .tables import _inspect_panda_inputs_impl

__all__: list[str] = []


def inspect_panda_inputs_with_provenance(
    action: str,
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
    taxon: str = "",
) -> tuple[str, bool, bool, bool]:
    """Validate inputs and report whether a registered demo authorized the bypass."""

    inputs = {
        "expression_file": expression_file,
        "motif_file": motif_file,
        "ppi_file": ppi_file,
    }
    if mirna_file:
        inputs["mirna_file"] = mirna_file
    bundled_demo = is_verified_bundled_demo(action, inputs)
    report, ok, inferred_header = _inspect_panda_inputs_impl(
        expression_file,
        motif_file,
        ppi_file,
        mirna_file,
        taxon=taxon,
        check_gene_authority=not bundled_demo,
    )
    if bundled_demo:
        report += "\n- " + bundled_demo_authority_note()
    return report, ok, inferred_header, bundled_demo
