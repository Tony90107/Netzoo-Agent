"""Which workflows a request's data unit admits: single cells or bulk samples (2026-11-08, SCORPION).

SCORPION is the one registered workflow built for single cells; every other workflow that reads an expression
matrix is built for bulk samples. Both build TF-to-gene networks, so the typed reading of the result cannot tell
them apart -- the request's own words about the data can. Code decides it from those words, before the registry
match: a request that says its data are single cells (scRNA-seq, snRNA-seq, 10x, single nuclei) is matched only
against SCORPION and the workflows that read no expression matrix (CONDOR, PORCUPINE, SAMBAR); any other request
is matched as before, without SCORPION. Naming SCORPION states single cells; pseudo-bulk profiles are bulk samples.
"""

from __future__ import annotations

import re
from typing import Literal, Mapping, TypeVar

from workflow_registry import ACTION_DEFINITIONS, SINGLE_CELL_ACTIONS, SINGLE_CELL_WITNESS

__all__ = [
    "BULK_EXPRESSION_ACTIONS", "SINGLE_CELL_ACTIONS", "excluded_actions", "data_unit_of", "scoped_capabilities",
    "single_cell_request",
]

T = TypeVar("T")

_EXPRESSION_FIELDS = frozenset({"expression_file", "omics_layer_1", "omics_layer_2"})
#: Run workflows that read a bulk expression (or continuous omics) matrix.
BULK_EXPRESSION_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items()
    if definition.run and action not in SINGLE_CELL_ACTIONS and _EXPRESSION_FIELDS & {
        *definition.required_inputs, *definition.optional_inputs,
        *(name for group in definition.required_input_groups for name in group),
    }
)
_SINGLE_CELL = re.compile(SINGLE_CELL_WITNESS, re.I)
# Cells summed per donor or state are bulk samples; a negated mention says the data are not single cells.
_PSEUDO_BULK = re.compile(r"pseudo[- ]?bulk|偽\s*bulk|擬\s*bulk|summed\s+(?:the\s+)?cells|aggregated\s+(?:the\s+)?cells", re.I)
_NEGATED = re.compile(
    r"\b(?:not|no|isn't|aren't|without|rather\s+than|instead\s+of)\s+(?:\w+\s+){0,2}(?:" + SINGLE_CELL_WITNESS + ")"
    r"|(?:不是|並非|非|沒有)\s*(?:單細胞|单细胞)",
    re.I,
)


_SCORPION_NAMED = re.compile(r"(?<![A-Za-z0-9])SCORPION(?![A-Za-z0-9])", re.I)


def single_cell_request(task: str) -> bool:
    """The request's own words say its data are single cells (and not pseudo-bulk profiles), or it names SCORPION,
    which takes nothing else."""
    if _PSEUDO_BULK.search(task) or _NEGATED.search(task):
        return False
    return bool(_SINGLE_CELL.search(task) or _SCORPION_NAMED.search(task))


def data_unit_of(task: str) -> Literal["single_cells", "bulk_samples"]:
    return "single_cells" if single_cell_request(task) else "bulk_samples"


def excluded_actions(task: str) -> frozenset[str]:
    """The run actions the request's data unit leaves out of the registry match."""
    return BULK_EXPRESSION_ACTIONS if single_cell_request(task) else SINGLE_CELL_ACTIONS


def scoped_capabilities(task: str, capabilities: Mapping[str, T]) -> dict[str, T]:
    """The capabilities the request's data unit admits (see the module docstring).

    `capabilities` is normally the registry's `OUTPUT_CAPABILITIES`, whose iteration already leaves the
    single-cell workflows out; a single-cell request adds them back with `including`.
    """
    excluded = excluded_actions(task)
    if single_cell_request(task) and hasattr(capabilities, "including"):
        capabilities = capabilities.including(SINGLE_CELL_ACTIONS)
    return {action: capability for action, capability in capabilities.items() if action not in excluded}
