"""Side-effect-free input validation shared by Planning and /execute."""

from __future__ import annotations

from typing import Any, Callable

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS

from .. import settings
from ..runtime_constraints import runtime_control_constraints
from .cobra import inspect_cobra_inputs_impl, load_cobra_inputs
from .bonobo import inspect_bonobo_inputs_impl, load_bonobo_inputs
from .dragon import inspect_dragon_inputs_impl
from .giraffe import inspect_giraffe_inputs_impl, load_giraffe_inputs
from .gene_validation import (
    TAXON_REQUIRED_SOURCE,
    UNRECOGNIZED_PHRASE,
    _identifier_preview,
    validate_gene_identifiers,
)
from .coexpression import read_coexpression_matrix
from .demo_provenance import is_verified_bundled_demo
from .inspection import inspect_condor_inputs_impl
from .otter import inspect_otter_inputs_impl, load_otter_inputs
from .panda_preflight import inspect_panda_inputs_with_provenance
from .tables import (
    _identifier_namespace,
    _read_checked_table,
    _validate_expression,
)
from .sambar import (
    _read_cancer_genes,
    _read_csv,
    _read_gmt,
    inspect_sambar_inputs_impl,
)
from .transforms import (
    convert_expression_to_coexpression_impl,
    format_expression_for_netzoo_impl,
)

# CONDOR accepts arbitrary bipartite node labels and DRAGON accepts arbitrary
# omics feature labels. Every other registered workflow has explicit gene axes.
WORKFLOW_GENE_EXTRACTORS: dict[str, str] = {
    "run_panda": "panda_bundle",
    "run_puma": "panda_bundle",
    "run_lioness_panda": "panda_bundle",
    "run_lioness_puma": "panda_bundle",
    "run_lioness_coexpression": "expression_genes",
    "run_cobra": "cobra_expression_genes",
    "run_sambar": "sambar_gene_sets",
    "run_otter": "otter_gene_and_tf_ids",
    "run_giraffe": "giraffe_gene_and_tf_ids",
    "run_bonobo": "bonobo_expression_genes",
}

__all__ = [
    "WORKFLOW_GENE_EXTRACTORS",
    "WORKFLOW_INPUT_VALIDATORS",
    "validate_workflow_inputs",
]


def _value(decision: Any, field_name: str) -> str:
    if isinstance(decision, dict):
        return str(decision.get(field_name) or "")
    return str(getattr(decision, field_name, None) or "")


def _report_errors(label: str, report: str, ok: bool) -> list[str]:
    if ok:
        return []
    errors = [
        line.strip()
        for line in report.splitlines()
        if "error:" in line.casefold()
    ]
    return [f"{label}: {error}" for error in errors] or [
        f"{label}: validation failed."
    ]


def _validate_expression_file(path: str, label: str = "expression") -> list[str]:
    check = _validate_expression(_read_checked_table(label, path))
    return [f"{label}: {error}" for error in check.errors]


def _validate_lioness_sample_count(path: str) -> list[str]:
    check = _validate_expression(_read_checked_table("expression", path))
    if check.errors or check.frame is None:
        return []
    sample_count = max(check.frame.shape[1] - 1, 0)
    if sample_count < 3:
        return [
            "expression: LIONESS requires at least three samples so each "
            "leave-one-out correlation still has at least two samples."
        ]
    return []


def _gene_axis_errors(
    identifiers: Any,
    label: str,
    taxon: str,
) -> list[str]:
    values = [str(value).strip() for value in identifiers if str(value).strip()]
    namespace = _identifier_namespace(values)
    if namespace == "ensembl_transcript":
        return [f"{label}: transcript IDs were supplied where gene IDs are required."]
    if namespace == "mixed_ensembl":
        return [f"{label}: gene and transcript identifier types are mixed."]
    if namespace in {"unknown", "opaque"}:
        if settings.TEST_DATA_MODE:
            return []
        return [
            f"{label}: identifiers do not form a supported gene namespace "
            "(gene symbol, NCBI Gene ID, or Ensembl gene ID)."
        ]

    summary = validate_gene_identifiers(values, namespace, taxon)
    invalid = sorted(
        record.identifier
        for record in summary.records.values()
        if record.status == "invalid"
    )
    taxon_required = sorted(
        record.identifier
        for record in summary.records.values()
        if record.source == TAXON_REQUIRED_SOURCE
    )
    ambiguous = sorted(
        record.identifier
        for record in summary.records.values()
        if record.status == "ambiguous" and record.source != TAXON_REQUIRED_SOURCE
    )
    online_unverified = sorted(
        record.identifier
        for record in summary.records.values()
        if record.status == "unverified"
        and record.source not in {"offline", "stale_cache"}
    )
    offline_unverified = sorted(
        record.identifier
        for record in summary.records.values()
        if record.status == "unverified" and record.source == "offline"
    )
    if settings.TEST_DATA_MODE:
        # Synthetic Test mode deliberately permits unresolved or ambiguous gene
        # labels. Structural and cross-file checks still run in their callers.
        return []

    errors: list[str] = []
    if taxon_required:
        errors.append(
            # The species is read as an assignment, never from prose, so the
            # message gives the spelling that is actually parsed. Asking to
            # "set taxon" invited prose, prose was not matched, and the
            # request then failed here again with no clue as to why.
            f"{label}: gene symbols cannot be verified without a species. "
            "Write it as an assignment - taxon=human, taxon=Homo sapiens or "
            "taxon=9606 - ending it with a comma or semicolon if more text "
            "follows. Or supply NCBI/Ensembl gene IDs instead: "
            + ", ".join(taxon_required[:5])
        )
    if invalid:
        errors.append(
            f"{label}: {UNRECOGNIZED_PHRASE}" + _identifier_preview(invalid)
        )
    if ambiguous:
        errors.append(
            f"{label}: ambiguous gene identifiers; provide taxon or canonical IDs: "
            + ", ".join(ambiguous[:5])
        )
    if online_unverified:
        errors.append(
            f"{label}: structured NCBI/Ensembl verification was unavailable; "
            "Websearch cannot authorize execution for: "
            + ", ".join(online_unverified[:5])
        )
    if offline_unverified:
        errors.append(
            f"{label}: identifiers could not be authoritatively verified offline; "
            "production validation requires NCBI/Ensembl confirmation: "
            + ", ".join(offline_unverified[:5])
        )
    return errors


def _workflow_gene_errors(action: str, decision: Any, taxon: str) -> list[str]:
    """Extract and validate every declared gene axis after structural preflight."""
    if action not in WORKFLOW_GENE_EXTRACTORS or action in {
        "run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma"
    }:
        # PANDA-family inspectors validate all of their axes in-place so their
        # canonical maps remain available to cross-file compatibility checks.
        return []

    expression = _value(decision, "expression_file")
    if action == "run_lioness_coexpression":
        check = _validate_expression(_read_checked_table("expression", expression))
        return _gene_axis_errors(check.identifiers, "expression genes", taxon)
    if action == "run_cobra":
        matrix, _ = load_cobra_inputs(expression, _value(decision, "design_file"))
        return _gene_axis_errors(matrix.index, "COBRA expression genes", taxon)
    if action == "run_sambar":
        mutation, _ = _read_csv(_value(decision, "mutation_file"), "mutation_file")
        lengths, _ = _read_csv(_value(decision, "exon_size_file"), "exon_size_file")
        cancer_genes, _ = _read_cancer_genes(_value(decision, "cancer_gene_file"))
        pathway_genes, _, _ = _read_gmt(_value(decision, "pathway_file"))
        axes = [
            (mutation.columns if mutation is not None else [], "SAMBAR mutation genes"),
            (lengths.columns if lengths is not None else [], "SAMBAR exon-size genes"),
            (cancer_genes, "SAMBAR cancer genes"),
            (pathway_genes, "SAMBAR pathway genes"),
        ]
        return [
            error
            for identifiers, label in axes
            for error in _gene_axis_errors(identifiers, label, taxon)
        ]
    if action == "run_otter":
        bundle = load_otter_inputs(
            expression,
            _value(decision, "coexpression_file"),
            _value(decision, "motif_file"),
            _value(decision, "ppi_file"),
            _value(decision, "precision") or "double",
        )
        return [
            *_gene_axis_errors(bundle.gene_ids, "OTTER target genes", taxon),
            *_gene_axis_errors(bundle.tf_ids, "OTTER regulator genes", taxon),
        ]
    if action == "run_giraffe":
        bundle = load_giraffe_inputs(
            expression,
            _value(decision, "motif_file"),
            _value(decision, "ppi_file"),
        )
        return [
            *_gene_axis_errors(bundle.gene_ids, "GIRAFFE target genes", taxon),
            *_gene_axis_errors(bundle.tf_ids, "GIRAFFE regulator genes", taxon),
        ]
    if action == "run_bonobo":
        if isinstance(decision, dict):
            sample_names = decision.get("sample_names", [])
            genes_axis = decision.get("genes_axis", "auto")
            log_transformed = decision.get("log_transformed")
            centered = decision.get("centered")
        else:
            sample_names = getattr(decision, "sample_names", [])
            genes_axis = getattr(decision, "genes_axis", "auto")
            log_transformed = getattr(decision, "log_transformed", None)
            centered = getattr(decision, "centered", None)
        bundle = load_bonobo_inputs(
            expression,
            sample_names,
            genes_axis=genes_axis,
            log_transformed=log_transformed,
            centered=centered,
        )
        return _gene_axis_errors(bundle.gene_ids, "BONOBO expression genes", taxon)
    return [f"{action}: registered gene-axis extractor is not implemented."]


def _validate_workflow_inputs_impl(action: str, decision: Any) -> list[str]:
    """Return actionable content/format errors without writing any files.

    The same function is called after Planning resolves inputs and immediately
    before ``/execute`` grants one-shot execution authority. Runtime executors
    still validate again as the final defense at the tool boundary.
    """

    errors: list[str] = []
    expression = _value(decision, "expression_file")
    motif = _value(decision, "motif_file")
    ppi = _value(decision, "ppi_file")
    mirna = _value(decision, "mirna_file")
    taxon = _value(decision, "taxon")
    coexpression = _value(decision, "coexpression_file")
    candidate_inputs = {
        "expression_file": expression,
        "motif_file": motif,
        "ppi_file": ppi,
        "mirna_file": mirna,
        "design_file": _value(decision, "design_file"),
    }
    bundled_demo = is_verified_bundled_demo(action, candidate_inputs)

    if action in {"inspect_inputs", "run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma"}:
        report, ok, inferred_header, panda_bundled_demo = inspect_panda_inputs_with_provenance(
            action,
            expression,
            motif,
            ppi,
            mirna if action in {"inspect_inputs", "run_puma", "run_lioness_puma"} else "",
            taxon,
        )
        bundled_demo = bundled_demo or panda_bundled_demo
        errors.extend(_report_errors("PANDA/PUMA inputs", report, ok))
        if action == "run_puma" and inferred_header:
            errors.append(
                "expression: PUMA requires a headerless expression matrix; "
                "run format_expression with with_header=false first."
            )
        if action in {"run_lioness_panda", "run_lioness_puma"}:
            errors.extend(_validate_lioness_sample_count(expression))
    elif action in {"inspect_condor_inputs", "run_condor"}:
        report, ok = inspect_condor_inputs_impl(_value(decision, "network_file"))
        errors.extend(_report_errors("CONDOR network", report, ok))
    elif action in {"inspect_cobra_inputs", "run_cobra"}:
        report, ok = inspect_cobra_inputs_impl(expression, _value(decision, "design_file"))
        errors.extend(_report_errors("COBRA inputs", report, ok))
    elif action in {"inspect_sambar_inputs", "run_sambar"}:
        report, ok = inspect_sambar_inputs_impl(
            _value(decision, "mutation_file"),
            _value(decision, "exon_size_file"),
            _value(decision, "cancer_gene_file"),
            _value(decision, "pathway_file"),
            decision,
        )
        errors.extend(_report_errors("SAMBAR inputs", report, ok))
    elif action in {"inspect_dragon_inputs", "run_dragon", "run_lioness_dragon"}:
        report, ok = inspect_dragon_inputs_impl(
            _value(decision, "omics_layer_1"),
            _value(decision, "omics_layer_2"),
        )
        errors.extend(_report_errors("DRAGON inputs", report, ok))
    elif action in {"inspect_giraffe_inputs", "run_giraffe"}:
        report, ok = inspect_giraffe_inputs_impl(
            _value(decision, "expression_file"),
            _value(decision, "motif_file"),
            _value(decision, "ppi_file"),
        )
        errors.extend(_report_errors("GIRAFFE inputs", report, ok))
    elif action in {"inspect_bonobo_inputs", "run_bonobo"}:
        if isinstance(decision, dict):
            sample_names = decision.get("sample_names", [])
            output_format = decision.get("bonobo_output_format", ".h5")
            sparsify = bool(decision.get("sparsify", False))
            confidence = float(decision.get("bonobo_confidence", 0.05))
            save_pvals = bool(decision.get("save_pvals", False))
            genes_axis = decision.get("genes_axis", "auto")
            log_transformed = decision.get("log_transformed")
            centered = decision.get("centered")
        else:
            sample_names = getattr(decision, "sample_names", [])
            output_format = getattr(decision, "bonobo_output_format", ".h5")
            sparsify = bool(getattr(decision, "sparsify", False))
            confidence = float(getattr(decision, "bonobo_confidence", 0.05))
            save_pvals = bool(getattr(decision, "save_pvals", False))
            genes_axis = getattr(decision, "genes_axis", "auto")
            log_transformed = getattr(decision, "log_transformed", None)
            centered = getattr(decision, "centered", None)
        report, ok = inspect_bonobo_inputs_impl(
            _value(decision, "expression_file"),
            sample_names,
            output_dir=_value(decision, "output_dir"),
            output_format=output_format,
            sparsify=sparsify,
            confidence=confidence,
            save_pvals=save_pvals,
            genes_axis=genes_axis,
            log_transformed=log_transformed,
            centered=centered,
        )
        errors.extend(_report_errors("BONOBO inputs", report, ok))
    elif action in {"inspect_otter_inputs", "run_otter"}:
        report, ok = inspect_otter_inputs_impl(
            expression,
            coexpression,
            motif,
            ppi,
            _value(decision, "precision") or "double",
        )
        errors.extend(_report_errors("OTTER inputs", report, ok))
        computing_constraint = runtime_control_constraints(action).get("computing")
        if computing_constraint is not None:
            issue = computing_constraint.issue(_value(decision, "computing"))
            if issue is not None:
                errors.append(issue)
    elif action == "run_lioness_coexpression":
        errors.extend(_validate_expression_file(expression))
        errors.extend(_validate_lioness_sample_count(expression))
    elif action == "format_expression":
        report = format_expression_for_netzoo_impl(
            expression,
            _value(decision, "output_file"),
            _value(decision, "genes_axis") or "auto",
            bool(decision.get("with_header", False))
            if isinstance(decision, dict)
            else bool(getattr(decision, "with_header", False)),
            execute=False,
        )
        errors.extend(_report_errors("Expression formatting", report, "- error:" not in report))
    elif action == "convert_expression":
        report = convert_expression_to_coexpression_impl(
            expression,
            _value(decision, "output_file"),
            execute=False,
        )
        errors.extend(_report_errors("Expression conversion", report, "- error:" not in report))

    if action in {"run_panda", "run_puma"} and coexpression:
        try:
            read_coexpression_matrix(coexpression)
        except (OSError, ValueError) as error:
            errors.append(f"coexpression_file: {error}")

    if action in WORKFLOW_GENE_EXTRACTORS and not errors and not bundled_demo:
        try:
            errors.extend(_workflow_gene_errors(action, decision, taxon))
        except (OSError, ValueError) as error:
            errors.append(f"{action}: gene-axis validation failed: {error}")

    return list(dict.fromkeys(errors))


def _bound_validator(action: str) -> Callable[[Any], list[str]]:
    def validate(decision: Any) -> list[str]:
        return _validate_workflow_inputs_impl(action, decision)

    return validate


# Deliberately explicit: adding a run action without adding its real preflight
# handler makes the set-equality contract fail and blocks execution.
WORKFLOW_INPUT_VALIDATORS: dict[str, Callable[[Any], list[str]]] = {
    "run_panda": _bound_validator("run_panda"),
    "run_puma": _bound_validator("run_puma"),
    "run_lioness_panda": _bound_validator("run_lioness_panda"),
    "run_lioness_puma": _bound_validator("run_lioness_puma"),
    "run_lioness_coexpression": _bound_validator("run_lioness_coexpression"),
    "run_condor": _bound_validator("run_condor"),
    "run_cobra": _bound_validator("run_cobra"),
    "run_sambar": _bound_validator("run_sambar"),
    "run_dragon": _bound_validator("run_dragon"),
    "run_lioness_dragon": _bound_validator("run_lioness_dragon"),
    "run_otter": _bound_validator("run_otter"),
    "run_giraffe": _bound_validator("run_giraffe"),
    "run_bonobo": _bound_validator("run_bonobo"),
}


def validate_workflow_inputs(action: str, decision: Any) -> list[str]:
    """Dispatch registered run actions through a fail-closed semantic gate."""
    if action in RUN_ACTIONS:
        validator = WORKFLOW_INPUT_VALIDATORS.get(action)
        registered_key = ACTION_DEFINITIONS[action].input_validator
        if validator is None or registered_key != action:
            return [
                f"{action}: no matching semantic input validator is registered; "
                "execution is blocked."
            ]
        return validator(decision)
    return _validate_workflow_inputs_impl(action, decision)
