"""Allow-listed NetZoo workflow adapters, including DRAGON's Python API adapter."""

from __future__ import annotations

import shlex
from pathlib import Path

import numpy as np

from . import settings


from .contracts import (
    tool,
)
from .contracts.results import PUMA_EXPRESSION_HEADER_UNSUPPORTED

from .command import (
    _run_command,
)

from .data.inspection import (
    expression_sample_count as _expression_sample_count,
    inspect_condor_inputs_impl as _inspect_condor_inputs_impl,
)
from .data.cobra import inspect_cobra_inputs_impl
from .data.sambar import inspect_sambar_inputs_impl
from .data.dragon import (
    DRAGON_OUTPUT_FORMATS,
    inspect_dragon_inputs_impl,
    load_and_align_dragon_layers,
    write_dragon_edge_list,
    write_dragon_matrix,
)
from .data.giraffe import (
    GiraffeInputError,
    giraffe_output_paths,
    inspect_giraffe_inputs_impl,
    load_giraffe_inputs,
    validate_giraffe_output,
    write_giraffe_outputs,
)
from .data.coexpression import read_coexpression_matrix
from .data.otter import inspect_otter_inputs_impl, load_otter_inputs, write_otter_output
from .execution_bonobo import inspect_bonobo_inputs, run_bonobo

from .data.tables import (
    _drop_common_header,
    _inspect_panda_inputs_impl,
    _read_checked_table,
    _resolve_user_path,
    _validate_expression,
)
from .data.paths import condor_artifact_paths

from .tool_adapters import (
    convert_expression_to_coexpression,
    format_expression_for_netzoo,
    inspect_cobra_inputs,
    inspect_dragon_inputs,
    inspect_netzoo_inputs,
)

__all__ = [
    "run_panda",
    "run_puma",
    "_expression_sample_count",
    "_derived_lioness_expression_path",
    "_prepare_lioness_expression",
    "_run_lioness_command",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "_inspect_condor_inputs_impl",
    "inspect_condor_inputs",
    "run_condor",
    "run_cobra",
    "inspect_sambar_inputs",
    "run_sambar",
    "run_dragon",
    "inspect_giraffe_inputs",
    "run_giraffe",
    "inspect_bonobo_inputs",
    "run_bonobo",
    "inspect_otter_inputs",
    "run_otter",
    "LOCAL_TOOL_EXECUTORS",
]


@tool
def run_panda(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    output_file: str,
    with_header: bool = False,
    extra_args: str = "",
    coexpression_file: str = "",
) -> str:
    """Run PANDA through the container wrapper."""
    validation_report, inputs_ok, inferred_header = _inspect_panda_inputs_impl(
        expression_file=expression_file,
        motif_file=motif_file,
        ppi_file=ppi_file,
    )
    if not inputs_ok:
        return (
            "PANDA input validation failed; no command was executed.\n\n"
            f"{validation_report}"
        )

    coexpression_report = ""
    if coexpression_file:
        try:
            coexpression = read_coexpression_matrix(coexpression_file)
        except ValueError as error:
            return (
                "PANDA input validation failed; no command was executed.\n\n"
                f"{validation_report}\n"
                f"- co-expression: {coexpression_file}\n"
                f"  error: {error}"
            )
        coexpression_report = (
            f"- co-expression: {coexpression_file}\n"
            f"  format: labeled symmetric gene-by-gene matrix\n"
            f"  shape: {coexpression.shape[0]} genes x {coexpression.shape[1]} genes\n"
            "  handoff: replaces PANDA's Pearson co-expression construction"
        )

    command = [
        "run-panda-precomputed" if coexpression_file else "run-panda",
        "-e",
        expression_file,
        "-m",
        motif_file,
        "-p",
        ppi_file,
        "-o",
        output_file,
    ]
    if coexpression_file:
        command.extend(["-c", coexpression_file])
    if with_header or inferred_header:
        command.append("--with_header")
    if extra_args:
        command.extend(shlex.split(extra_args))
    report = validation_report + ("\n" + coexpression_report if coexpression_report else "")
    return report + "\n\n" + _run_command(command, output_file=output_file)


@tool
def run_puma(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str,
    output_file: str,
    extra_args: str = "",
    coexpression_file: str = "",
    mode_process: str = "",
) -> str:
    """Run PUMA using a one-regulator-per-line miRNA list.

    `mode_process` selects how the priors' genes and TFs are combined --
    "union" (the long-standing behaviour, and what is used when this is left
    empty), "legacy", or "intersection". It exists because netZooPy's own
    reference network is built under "legacy" and the path had no way to reach
    it, so the capability's numbers could never be compared against a
    third-party file. Leaving it empty changes nothing.
    """
    validation_report, inputs_ok, inferred_header = _inspect_panda_inputs_impl(
        expression_file=expression_file,
        motif_file=motif_file,
        ppi_file=ppi_file,
        mirna_file=mirna_file,
    )
    if inferred_header:
        return (
            "PUMA input validation failed; no command was executed.\n\n"
            f"{validation_report}\n"
            f"Error code: {PUMA_EXPRESSION_HEADER_UNSUPPORTED}\n"
            "  error: legacy netZooPy PUMA does not accept an expression header; "
            "use format_expression with with_header=false."
        )
    if not inputs_ok:
        return (
            "PUMA input validation failed; no command was executed.\n\n"
            f"{validation_report}"
        )

    command = [
        "run-puma-precomputed" if coexpression_file else "run-puma",
        "-e",
        expression_file,
        "-m",
        motif_file,
        "-p",
        ppi_file,
        "-i",
        mirna_file,
        "-o",
        output_file,
    ]
    if coexpression_file:
        try:
            coexpression = read_coexpression_matrix(coexpression_file)
        except ValueError as error:
            return (
                "PUMA input validation failed; no command was executed.\n\n"
                f"{validation_report}\n"
                f"- co-expression: {coexpression_file}\n"
                f"  error: {error}"
            )
        command.extend(["-c", coexpression_file])
        validation_report += (
            f"\n- co-expression: {coexpression_file}\n"
            "  format: labeled symmetric gene-by-gene matrix\n"
            f"  shape: {coexpression.shape[0]} genes x {coexpression.shape[1]} genes\n"
            "  handoff: replaces PUMA's Pearson co-expression construction"
        )
    if mode_process:
        command.extend(["--mode_process", mode_process])
    if extra_args:
        command.extend(shlex.split(extra_args))
    return validation_report + "\n\n" + _run_command(command, output_file=output_file)




def _derived_lioness_expression_path(expression_file: str, lioness_output: str) -> Path:
    source_path = _resolve_user_path(expression_file)
    output_path = _resolve_user_path(lioness_output)
    return output_path.parent / f"{source_path.stem}.lioness-expression.tsv"


def _prepare_lioness_expression(
    expression_file: str,
    lioness_output: str,
) -> tuple[str, str, int, bool, str | None]:
    expression = _validate_expression(
        _read_checked_table("expression", expression_file)
    )
    if expression.frame is None or expression.errors:
        return expression_file, "", 0, expression.has_header, None

    frame, has_header = _drop_common_header(expression.frame)
    sample_count = max(frame.shape[1] - 1, 0)
    needs_formatting = (
        has_header
        or expression.delimiter_name != "TSV"
        or expression.skipped_annotation_rows > 0
    )
    if not needs_formatting:
        return expression_file, "", sample_count, False, None

    derived_path = _derived_lioness_expression_path(expression_file, lioness_output)
    genes_axis = "auto" if has_header else "rows"
    result = format_expression_for_netzoo.invoke(
        {
            "expression_file": expression_file,
            "output_file": str(derived_path),
            "genes_axis": genes_axis,
            "with_header": False,
        }
    )
    if "- error:" in result:
        return (
            expression_file,
            result,
            sample_count,
            has_header,
            "LIONESS expression auto-preparation failed.",
        )

    report = (
        "LIONESS expression auto-preparation:\n"
        f"- reason: {'header detected; ' if has_header else ''}"
        f"{'non-TSV input; ' if expression.delimiter_name != 'TSV' else ''}"
        f"{'leading annotation rows; ' if expression.skipped_annotation_rows else ''}".rstrip(
            "; "
        )
        + f"\n- prepared expression: {derived_path}\n"
        + result
    )
    return str(derived_path), report, sample_count, False, None


def _run_lioness_command(
    mode: str,
    expression_file: str,
    output_file: str,
    lioness_output: str,
    motif_file: str = "",
    ppi_file: str = "",
    mirna_file: str = "",
    mode_process: str = "",
) -> str:
    lioness_suffix = Path(lioness_output).suffix.casefold()
    allowed_suffixes = (
        {".txt", ".csv", ".tsv"}
        if mode in {"panda", "coexpression"}
        else {".txt", ".csv", ".tsv", ".npy"}
    )
    if lioness_suffix not in allowed_suffixes:
        return (
            f"LIONESS-{mode} output extension {lioness_suffix or '(none)'} is unsupported. "
            "Use one of: " + ", ".join(sorted(allowed_suffixes))
        )

    (
        command_expression_file,
        preparation_report,
        sample_count,
        has_header,
        prep_error,
    ) = _prepare_lioness_expression(expression_file, lioness_output)
    if prep_error:
        return prep_error + "\n\n" + preparation_report
    if has_header:
        return (
            "LIONESS input validation failed; legacy PANDA/PUMA LIONESS requires "
            "a headerless expression matrix. Run format_expression with with_header=false."
        )
    if sample_count < 3:
        return (
            "LIONESS input validation failed; at least three samples are required "
            "so each leave-one-out correlation still has at least two samples."
        )

    if mode in {"panda", "puma"}:
        validation_expression_file = (
            command_expression_file
            if Path(command_expression_file).exists()
            else expression_file
        )
        validation_report, inputs_ok, _ = _inspect_panda_inputs_impl(
            validation_expression_file,
            motif_file,
            ppi_file,
            mirna_file if mode == "puma" else "",
        )
        if not inputs_ok:
            return (
                f"LIONESS-{mode.upper()} input validation failed; no command was executed.\n\n"
                + validation_report
            )
    else:
        expression = _validate_expression(
            _read_checked_table(
                "expression",
                (
                    command_expression_file
                    if Path(command_expression_file).exists()
                    else expression_file
                ),
            )
        )
        if expression.errors:
            return "LIONESS co-expression input validation failed:\n- " + "\n- ".join(
                expression.errors
            )
        validation_report = "Expression validation passed."

    command = [
        "run-lioness",
        mode,
        "-e",
        command_expression_file,
    ]
    if motif_file:
        command.extend(["-m", motif_file])
    if ppi_file:
        command.extend(["-p", ppi_file])
    if mirna_file:
        command.extend(["-i", mirna_file])
    if mode_process:
        command.extend(["--mode_process", mode_process])
    command.extend(["-o", output_file, "-q", lioness_output])
    sections = [
        section for section in [preparation_report, validation_report] if section
    ]
    return (
        "\n\n".join(sections)
        + "\n\n"
        + _run_command(
            command,
            output_file=output_file,
            additional_output_files=[lioness_output],
        )
    )


@tool
def run_lioness_panda(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    output_file: str,
    lioness_output: str,
) -> str:
    """Run aggregate PANDA plus LIONESS-PANDA sample-specific networks."""
    return _run_lioness_command(
        "panda",
        expression_file,
        output_file,
        lioness_output,
        motif_file,
        ppi_file,
    )


@tool
def run_lioness_puma(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str,
    output_file: str,
    lioness_output: str,
    mode_process: str = "",
) -> str:
    """Run aggregate PUMA plus LIONESS-PUMA sample-specific networks.

    `mode_process` selects how the priors' genes and TFs are combined for the
    aggregate PUMA step -- "union" (the long-standing behaviour, and what an
    empty value keeps), "legacy", or "intersection". The step could not choose
    before, which is why it had no comparison against upstream's own reference
    network. The sample-specific step follows whatever the aggregate produced.
    """
    return _run_lioness_command(
        "puma",
        expression_file,
        output_file,
        lioness_output,
        motif_file,
        ppi_file,
        mirna_file,
        mode_process=mode_process,
    )


@tool
def run_lioness_coexpression(
    expression_file: str,
    output_file: str,
    lioness_output: str,
) -> str:
    """Run aggregate Pearson and LIONESS sample-specific co-expression networks."""
    return _run_lioness_command(
        "coexpression",
        expression_file,
        output_file,
        lioness_output,
    )




@tool
def inspect_condor_inputs(network_file: str) -> str:
    """Inspect a CONDOR bipartite edge list before running community detection."""
    report, _ = _inspect_condor_inputs_impl(network_file)
    return report


@tool
def run_condor(
    network_file: str,
    output_dir: str,
    prefix: str = "condor",
) -> str:
    """Run CONDOR community detection on a bipartite source-target-weight edge list."""
    validation_report, inputs_ok = _inspect_condor_inputs_impl(network_file)
    if not inputs_ok:
        return (
            "CONDOR input validation failed; no command was executed.\n\n"
            f"{validation_report}"
        )
    output_path = _resolve_user_path(output_dir)
    artifact_paths = condor_artifact_paths(output_path, prefix or "condor")
    resolved_input = _resolve_user_path(network_file)
    colliding = [path for path in artifact_paths.values() if path == resolved_input]
    if colliding:
        raise ValueError(
            "CONDOR output artifact would overwrite the network_file input: "
            + str(colliding[0])
        )
    command = [
        "run-condor",
        "-i",
        network_file,
        "-o",
        str(output_path),
        "--prefix",
        prefix or "condor",
    ]
    expected_outputs = [str(path) for path in artifact_paths.values()]
    run_plan = "\n".join(
        [
            "CONDOR run plan:",
            f"- output directory: {output_path}",
            f"- prefix: {prefix or 'condor'}",
        ]
    )
    return (
        validation_report
        + "\n\n"
        + run_plan
        + "\n\n"
        + _run_command(
            command,
            additional_output_files=expected_outputs,
        )
    )


@tool
def run_cobra(expression_file: str, design_file: str, output_dir: str) -> str:
    """Run covariate-aware COBRA co-expression decomposition."""
    validation_report, inputs_ok = inspect_cobra_inputs_impl(expression_file, design_file)
    if not inputs_ok:
        return "COBRA input validation failed; no command was executed.\n\n" + validation_report
    output_path = _resolve_user_path(output_dir)
    command = ["run-cobra", "-e", expression_file, "-d", design_file, "-o", str(output_path)]
    return validation_report + "\n\n" + _run_command(
        command,
        additional_output_files=[
            str(output_path / "manifest.json"),
            str(output_path / "components.npz"),
            str(output_path / "summary.tsv"),
            str(output_path / "adjusted_coexpression.tsv"),
            str(output_path / "adjusted_coexpression.npz"),
        ],
    )


@tool
def inspect_sambar_inputs(
    mutation_file: str,
    exon_size_file: str,
    cancer_gene_file: str,
    pathway_file: str,
    kmin: int = 2,
    kmax: int = 4,
    cluster: bool = True,
) -> str:
    """Inspect SAMBAR files before a subtype-analysis run."""
    report, _ = inspect_sambar_inputs_impl(
        mutation_file, exon_size_file, cancer_gene_file, pathway_file,
        {"kmin": kmin, "kmax": kmax, "cluster": cluster},
    )
    return report


@tool
def inspect_otter_inputs(
    expression_file: str = "",
    coexpression_file: str = "",
    motif_file: str = "",
    ppi_file: str = "",
    precision: str = "double",
) -> str:
    """Inspect the exact W/P/C orientation and identifier contract for OTTER."""
    report, _ = inspect_otter_inputs_impl(
        expression_file,
        coexpression_file,
        motif_file,
        ppi_file,
        precision,
    )
    return report


@tool
def run_sambar(
    mutation_file: str,
    exon_size_file: str,
    cancer_gene_file: str,
    pathway_file: str,
    output_dir: str,
    norm_patient: bool = True,
    kmin: int = 2,
    kmax: int = 4,
    gmt_msigdb: bool = True,
    subset_cancer_genes: bool = True,
    distance: str = "binomial",
    linkage: str = "complete",
    cluster: bool = True,
) -> str:
    """Run SAMBAR using only declared, validated registry parameters."""
    inspection, ok = inspect_sambar_inputs_impl(
        mutation_file, exon_size_file, cancer_gene_file, pathway_file,
        {"norm_patient": norm_patient, "kmin": kmin, "kmax": kmax,
         "gmt_msigdb": gmt_msigdb, "subset_cancer_genes": subset_cancer_genes,
         "distance": distance, "linkage": linkage, "cluster": cluster},
    )
    if not ok:
        return "SAMBAR input validation failed; no command was executed.\n\n" + inspection
    root = _resolve_user_path(output_dir)
    inputs = {_resolve_user_path(path) for path in (mutation_file, exon_size_file, cancer_gene_file, pathway_file)}
    outputs = [root / "mt_out.csv", root / "pt_out.csv", root / "manifest.json"]
    if cluster:
        outputs.extend([root / "clustergroups.csv", root / "dist_matrix.csv"])
    collision = next((path for path in outputs if path in inputs), None)
    if collision is not None:
        return "SAMBAR input validation failed; no command was executed.\n\n  error: output would overwrite input: " + str(collision)
    command = [
        "run-sambar", "-m", mutation_file, "-e", exon_size_file, "-g", cancer_gene_file,
        "-p", pathway_file, "-o", str(root), "--kmin", str(kmin), "--kmax", str(kmax),
        "--distance", distance, "--linkage", linkage,
    ]
    if not norm_patient:
        command.append("--no-norm-patient")
    if not gmt_msigdb:
        command.append("--no-gmt-msigdb")
    if not subset_cancer_genes:
        command.append("--no-subset-cancer-genes")
    if not cluster:
        command.append("--no-cluster")
    return inspection + "\n\n" + _run_command(command, additional_output_files=[str(path) for path in outputs])


def _load_otter_api():
    """Import the verified public low-level OTTER module at execution time."""
    import importlib

    return importlib.import_module("netZooPy.otter.otter")


@tool
def run_otter(
    expression_file: str = "",
    coexpression_file: str = "",
    motif_file: str = "",
    ppi_file: str = "",
    output_file: str = "",
    output_format: str = "matrix",
    computing: str = "cpu",
    precision: str = "double",
    lam: float = 0.035,
    gamma: float = 0.335,
    iterations: int = 60,
    eta: float = 0.00001,
    bexp: float = 1.0,
) -> str:
    """Run the verified netZooPy OTTER(W, P, C) API with labeled artifacts."""
    try:
        if computing != "cpu":
            return "OTTER execution failed; error: only computing=cpu is enabled in this runtime."
        report, inputs_ok = inspect_otter_inputs_impl(
            expression_file,
            coexpression_file,
            motif_file,
            ppi_file,
            precision,
        )
        if not inputs_ok:
            return "OTTER input validation failed; no API call was made.\n\n" + report
        bundle = load_otter_inputs(
            expression_file,
            coexpression_file,
            motif_file,
            ppi_file,
            precision,
        )
        preview = (
            "OTTER Python API preview:\n"
            "- import: netZooPy.otter.otter\n"
            "- call: otter(W, P, C, lam, gamma, Iter, eta, bexp)\n"
            f"- shapes: W={bundle.W.shape}, P={bundle.P.shape}, C={bundle.C.shape}\n"
            f"- weights: co-expression lam={lam}, PPI={1.0 - lam}; gamma={gamma} regularization\n"
            f"- optimization: Iter={iterations}, eta={eta}, bexp={bexp}, precision={precision}\n"
            f"- output: {output_format} at {_resolve_user_path(output_file)}\n"
            "- no analysis was executed and no artifact was written (dry-run)."
        )
        if not settings.EXECUTE_TOOLS:
            return report + "\n\n" + preview
        if _resolve_user_path(output_file) in {
            _resolve_user_path(value)
            for value in (expression_file, coexpression_file, motif_file, ppi_file)
            if value
        }:
            return "OTTER execution failed; error: output_file would overwrite an input."
        api = _load_otter_api()
        network = api.otter(
            bundle.W,
            bundle.P,
            bundle.C,
            lam=lam,
            gamma=gamma,
            Iter=iterations,
            eta=eta,
            bexp=bexp,
        )
        written = write_otter_output(
            output_file,
            network,
            bundle.tf_ids,
            bundle.gene_ids,
            output_format,
        )
        return (
            report
            + "\n\nOTTER API execution completed.\n"
            f"- output: {written}\n"
            f"- interpretation: aggregate TF-to-gene regulatory network; edge weights are optimized OTTER W scores; "
            f"PPI weight={1.0 - lam:g}, co-expression weight={lam:g}."
        )
    except SystemExit as error:
        return f"OTTER execution failed; error: netZooPy exited during validation: {error}"
    except Exception as error:  # noqa: BLE001 - tool failures are returned as typed text results.
        return f"OTTER execution failed; error: no trusted result was returned: {type(error).__name__}: {error}"


def _load_dragon_api():
    """Import only the verified public netZooPy DRAGON module at execution time."""
    import importlib

    return importlib.import_module("netZooPy.dragon")


@tool
def run_dragon(
    omics_layer_1: str,
    omics_layer_2: str,
    output_file: str,
    output_format: str = "matrix",
    lambda1: float | None = None,
    lambda2: float | None = None,
) -> str:
    """Run the verified netZooPy DRAGON Python API on exactly two omics layers."""
    try:
        if output_format not in DRAGON_OUTPUT_FORMATS:
            return f"DRAGON execution failed; error: unsupported output_format: {output_format}."
        if (lambda1 is None) != (lambda2 is None):
            return "DRAGON execution failed; error: lambda1 and lambda2 must be supplied together."
        input_report, inputs_ok = inspect_dragon_inputs_impl(
            omics_layer_1,
            omics_layer_2,
        )
        if not inputs_ok:
            return "DRAGON input validation failed; no API call was made.\n\n" + input_report
        layer1, layer2, errors = load_and_align_dragon_layers(
            omics_layer_1,
            omics_layer_2,
        )
        if errors or layer1 is None or layer2 is None:
            return "DRAGON input validation failed; no API call was made.\n\n" + input_report
        if _resolve_user_path(output_file) in {
            _resolve_user_path(omics_layer_1),
            _resolve_user_path(omics_layer_2),
        }:
            return "DRAGON execution failed; error: output_file would overwrite an omics input."
        lambda_text = (
            f"manual lambdas=({lambda1}, {lambda2})"
            if lambda1 is not None
            else "lambdas estimated by estimate_penalty_parameters_dragon"
        )
        preview = (
            "DRAGON Python API preview:\n"
            "- import: netZooPy.dragon\n"
            "- calls: estimate_penalty_parameters_dragon(X1, X2) -> "
            "get_precision_matrix_dragon(X1, X2, lambdas) and "
            "get_partial_correlation_dragon(X1, X2, lambdas)\n"
            f"- {lambda_text}\n"
            f"- output: {output_format} at {_resolve_user_path(output_file)}\n"
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
        precision, _ = api.get_precision_matrix_dragon(x1, x2, lambdas)
        partial = api.get_partial_correlation_dragon(x1, x2, lambdas)
        node_ids = [f"layer1::{value}" for value in layer1.columns] + [
            f"layer2::{value}" for value in layer2.columns
        ]
        if output_format == "matrix":
            written = write_dragon_matrix(output_file, partial, node_ids)
        else:
            written = write_dragon_edge_list(output_file, partial, precision, node_ids)
        return (
            input_report
            + "\n\nDRAGON API execution completed.\n"
            f"- lambdas: {list(map(float, lambdas))}\n"
            f"- output: {written}\n"
            "- interpretation: undirected aggregate association network; "
            "partial correlation is not a causal effect."
        )
    except Exception as error:  # noqa: BLE001 - tool failures are returned as typed text results.
        return f"DRAGON execution failed; error: no trusted result was returned: {type(error).__name__}: {error}"


def _load_giraffe_api():
    """Load the exact public GIRAFFE API from the Docker runtime."""
    import importlib

    netzoopy = importlib.import_module("netZooPy")
    version = getattr(netzoopy, "__version__", None)
    if version != "0.11.0":
        raise RuntimeError(
            f"unsupported netZooPy version {version!r}; the validated GIRAFFE contract requires 0.11.0"
        )
    module = importlib.import_module("netZooPy.giraffe")
    giraffe_class = getattr(module, "Giraffe", None)
    if giraffe_class is None or not callable(giraffe_class):
        raise AttributeError("netZooPy.giraffe.Giraffe is not available")
    return giraffe_class, version


def _giraffe_failure(code: str, problem: str, needed: str) -> str:
    return (
        "GIRAFFE execution failed.\n"
        f"error code: {code}\n"
        f"error: {problem}\n"
        "confirmed: input files were validated against the source-verified GIRAFFE matrix contract.\n"
        f"needed: {needed}"
    )


@tool
def inspect_giraffe_inputs(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
) -> str:
    """Inspect and align the labelled files required by netZooPy GIRAFFE."""
    report, _ = inspect_giraffe_inputs_impl(expression_file, motif_file, ppi_file)
    return report


@tool
def run_giraffe(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    output_file: str,
) -> str:
    """Run source-verified netZooPy GIRAFFE in the Docker runtime."""
    try:
        input_report, inputs_ok = inspect_giraffe_inputs_impl(
            expression_file, motif_file, ppi_file
        )
        if not inputs_ok:
            return "GIRAFFE input validation failed; no API call was made.\n\n" + input_report
        bundle = load_giraffe_inputs(expression_file, motif_file, ppi_file)
        regulation_path, tfa_path = giraffe_output_paths(output_file)
        inputs = {
            _resolve_user_path(expression_file),
            _resolve_user_path(motif_file),
            _resolve_user_path(ppi_file),
        }
        if regulation_path in inputs or tfa_path in inputs:
            return _giraffe_failure(
                "GIRAFFE_OUTPUT_OVERWRITES_INPUT",
                "an output path would overwrite one of the validated input files",
                "choose a separate output_file path",
            )
        preview = (
            "GIRAFFE Python API preview:\n"
            "- runtime: Docker pinned netZooPy 0.11.0\n"
            "- import: from netZooPy.giraffe import Giraffe\n"
            "- call: Giraffe(expression, prior.T, ppi) -- the API takes the "
            "prior gene-by-TF and returns regulation gene-by-TF; both are "
            "converted to this workflow's TF-by-gene orientation\n"
            "- outputs: model.get_regulation() -> TF-by-gene matrix; "
            "model.get_tfa() -> TF-by-sample matrix\n"
            f"- shapes: expression={bundle.expression.shape}, prior={bundle.prior.shape}, ppi={bundle.ppi.shape}\n"
            f"- output: regulation={regulation_path}; tfa={tfa_path}\n"
            "- no analysis was executed and no artifact was written (dry-run)."
        )
        if not settings.EXECUTE_TOOLS:
            return input_report + "\n\n" + preview
        try:
            giraffe_class, version = _load_giraffe_api()
        except ModuleNotFoundError as error:
            return _giraffe_failure(
                "GIRAFFE_NETZOOPY_MISSING",
                "netZooPy with the GIRAFFE module is not importable in this runtime",
                "execute the agent inside the Docker image built from this Dockerfile; do not install a second unpinned copy",
            ) + f"\nloader detail: {error}"
        except RuntimeError as error:
            return _giraffe_failure(
                "GIRAFFE_VERSION_UNSUPPORTED",
                str(error),
                "use netZooPy 0.11.0 / the validated Docker NETZOOPY_REF, or explicitly update the integration contract",
            )
        except (AttributeError, ImportError) as error:
            return _giraffe_failure(
                "GIRAFFE_API_UNAVAILABLE",
                "the installed netZooPy package does not expose the verified GIRAFFE API",
                "use the pinned Docker runtime or specify a commit whose API is re-verified",
            ) + f"\nloader detail: {error}"
        try:
            # netZooPy's GIRAFFE takes the prior gene-by-TF and returns the
            # regulation matrix the same way round (it documents "Size (G, TF)").
            # The prior is loaded, written and validated here TF-by-gene, so the
            # orientation is converted on the way in and back on the way out.
            # Passing the prior untransposed made every real request fail inside
            # the API on a tensor-size mismatch whenever the gene count differed
            # from the TF count -- that is, always.
            model = giraffe_class(bundle.expression, bundle.prior.T, bundle.ppi)
            regulation = np.asarray(model.get_regulation(), dtype=float).T
            tfa = np.asarray(model.get_tfa(), dtype=float)
        except Exception as error:  # noqa: BLE001 - convert package failures to user-facing results.
            return _giraffe_failure(
                "GIRAFFE_API_ERROR",
                f"the verified GIRAFFE API call failed: {type(error).__name__}: {error}",
                "check the validated matrix shapes/values and the Docker dependency versions",
            )
        if regulation.shape != bundle.prior.shape or tfa.shape != (len(bundle.tf_ids), len(bundle.sample_ids)):
            return _giraffe_failure(
                "GIRAFFE_OUTPUT_SHAPE_INVALID",
                f"GIRAFFE returned regulation shape {regulation.shape} and TFA shape {tfa.shape}, which do not match the input identifiers",
                "use a compatible netZooPy GIRAFFE version or inspect the input orientation",
            )
        try:
            written = write_giraffe_outputs(output_file, regulation, tfa, bundle)
            valid, errors, _ = validate_giraffe_output(output_file, bundle)
        except (OSError, ValueError) as error:
            return _giraffe_failure(
                "GIRAFFE_OUTPUT_ERROR",
                f"the result could not be written or parsed: {error}",
                "choose a writable output path and rerun in the Docker runtime",
            )
        if not valid:
            return _giraffe_failure(
                "GIRAFFE_OUTPUT_INVALID",
                "; ".join(errors),
                "inspect the output files and use a netZooPy version matching the verified API contract",
            )
        return (
            input_report
            + f"\n\nGIRAFFE API execution completed (netZooPy {version}).\n"
            f"- regulation: {written[0]}\n- TFA: {written[1]}"
        )
    except GiraffeInputError as error:
        return _giraffe_failure(
            "GIRAFFE_INPUT_FORMAT_ERROR",
            str(error),
            "provide corrected expression, motif/prior, or PPI files and rerun input confirmation",
        )
    except Exception as error:  # noqa: BLE001 - keep interactive execution typed and bounded.
        return _giraffe_failure(
            "GIRAFFE_RUNTIME_ERROR",
            f"an unexpected runtime failure occurred: {type(error).__name__}: {error}",
            "rerun inside the pinned Docker runtime and inspect the private execution log",
        )


LOCAL_TOOL_EXECUTORS = {
    "inspect_inputs": inspect_netzoo_inputs,
    "inspect_condor_inputs": inspect_condor_inputs,
    "format_expression": format_expression_for_netzoo,
    "convert_expression": convert_expression_to_coexpression,
    "run_panda": run_panda,
    "run_puma": run_puma,
    "run_lioness_panda": run_lioness_panda,
    "run_lioness_puma": run_lioness_puma,
    "run_lioness_coexpression": run_lioness_coexpression,
    "run_condor": run_condor,
    "inspect_cobra_inputs": inspect_cobra_inputs,
    "run_cobra": run_cobra,
    "inspect_sambar_inputs": inspect_sambar_inputs,
    "run_sambar": run_sambar,
    "inspect_dragon_inputs": inspect_dragon_inputs,
    "run_dragon": run_dragon,
    "inspect_giraffe_inputs": inspect_giraffe_inputs,
    "run_giraffe": run_giraffe,
    "inspect_bonobo_inputs": inspect_bonobo_inputs,
    "run_bonobo": run_bonobo,
    "inspect_otter_inputs": inspect_otter_inputs,
    "run_otter": run_otter,
}
