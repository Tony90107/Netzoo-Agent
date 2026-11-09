"""PORCUPINE integration contracts: input format, planning, execution preview, and artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402
from porcupine_io import MIN_SAMPLES, read_gmt, read_sample_network  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, executor_arguments  # noqa: E402
from netzoo_agent_core.data.artifacts import validate_output_artifacts  # noqa: E402
from netzoo_agent_core.data.porcupine import inspect_porcupine_inputs_impl  # noqa: E402
from netzoo_agent_core.data.preflight import validate_workflow_inputs  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

ROOT = Path(__file__).parents[1]
TOY = ROOT / "data" / "porcupine-toy"
NETWORK = TOY / "lioness_panda_network.txt"
GMT = TOY / "pathways.gmt"
SAMPLES = [f"TCGA-S{i:02d}" for i in range(1, 13)]


@pytest.fixture(autouse=True)
def synthetic_gene_labels(monkeypatch):
    # The toy bundle uses placeholder gene labels (GENE01...); these tests cover
    # the workflow contract, not the gene-authority lookup.
    monkeypatch.setattr(agent.settings, "TEST_DATA_MODE", True)


def decision(**overrides):
    values = {
        "action": "run_porcupine", "in_scope": True, "should_execute": True,
        "confidence": 1.0, "reason": "Run PORCUPINE.",
        "sample_network_file": str(NETWORK), "pathway_file": str(GMT),
        "output_dir": "outputs/porcupine-test",
    }
    values.update(overrides)
    return agent.TaskDecision(**values)


def _network(tmp_path: Path, header: str, rows: list[str], name: str = "net.txt") -> Path:
    path = tmp_path / name
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


# --- registry / policy ---------------------------------------------------------------------------------------------


def test_policy_and_registry_agree_and_lioness_hands_off_to_porcupine():
    policy = ProjectPolicyLoader(ROOT).load()
    spec = policy.workflows["run_porcupine"]
    definition = ACTION_DEFINITIONS["run_porcupine"]
    assert spec.required_inputs == list(definition.required_inputs)
    assert spec.optional_inputs == list(definition.optional_inputs)
    assert spec.validation_steps == ["inspect_porcupine_inputs"]
    assert [control.name for control in spec.controls] == [control.name for control in definition.controls]
    capability = spec.output_capability
    assert capability.accepted_input_granularities == ["sample_specific"]
    assert set(capability.incompatible_input_artifacts) >= {"expression_matrix", "coexpression_network"}
    producers = {action for action, other in policy.workflows.items()
                 if "run_porcupine" in other.output_capability.handoff_targets}
    # 2026-11-08: SCORPION per-donor networks (single cells) are an edges-by-networks table too.
    assert producers == {"run_lioness_panda", "run_lioness_puma", "run_scorpion"}
    for producer in producers:
        assert "sample_specific" in OUTPUT_CAPABILITIES[producer].granularities
    # A gene-gene co-expression producer is never a handoff source.
    assert "run_porcupine" not in policy.workflows["run_lioness_coexpression"].output_capability.handoff_targets


def test_executor_accepts_exactly_the_declared_fields():
    arguments = executor_arguments("run_porcupine", decision())
    assert set(arguments) == set(ACTION_DEFINITIONS["run_porcupine"].executor_fields)
    assert arguments["n_permutations"] == 1000 and arguments["min_effect_size"] == 2.0


# --- input format (rows = edges, columns = samples) ----------------------------------------------------------------


def test_lioness_panda_export_is_read_as_edges_by_samples():
    network = read_sample_network(NETWORK)
    assert not network.errors
    assert network.samples == SAMPLES
    assert network.n_edges == 600 and network.prior_column is None
    assert network.regulators.iloc[0] == "TF1" and network.targets.iloc[0] == "GENE01"


def test_lioness_puma_export_keeps_the_prior_column_out_of_the_samples(tmp_path):
    rows = [f"TF{t} G{g} 1 " + " ".join(str(v) for v in range(1, MIN_SAMPLES + 1)) for t in range(2) for g in range(3)]
    header = "regulator gene prior_weight " + " ".join(str(i) for i in range(1, MIN_SAMPLES + 1))
    network = read_sample_network(_network(tmp_path, header, rows))
    assert not network.errors
    assert network.prior_column == "prior_weight"
    assert network.samples == [str(i) for i in range(1, MIN_SAMPLES + 1)]


@pytest.mark.parametrize("header, rows, message", [
    ("gene1 gene2 S1 S2", ["A B 1 2"], "gene-gene co-expression"),
    ("S1 S2 S3", ["1 2 3"], "header must start with a regulator column"),
    ("tf gene S1 S1", ["T G 1 2"], "sample IDs (column names) must be unique"),
    ("tf gene S1 S2", ["T G 1 2", "T G 3 4"], "one row per unique regulator->target edge"),
    ("tf gene S1 S2", ["T G 1 x"], "finite numeric values"),
    ("tf gene", ["T G"], "header must start with a regulator column"),
])
def test_malformed_network_tables_are_rejected(tmp_path, header, rows, message):
    network = read_sample_network(_network(tmp_path, header, rows))
    assert any(message in error for error in network.errors), network.errors


def test_binary_lioness_export_is_rejected_because_it_has_no_edge_labels(tmp_path):
    path = tmp_path / "lioness.npy"
    np.save(path, np.zeros((4, 9)))
    assert "binary LIONESS exports carry no regulator/target labels" in read_sample_network(path).errors[0]


def test_gmt_must_be_tab_separated_with_unique_pathways(tmp_path):
    pathways, errors = read_gmt(GMT)
    assert not errors and len(pathways["P_DRIVEN"]) == 8
    bad = tmp_path / "bad.gmt"
    bad.write_text("P1 desc G1 G2\nP2\tdesc\tG1\nP2\tdesc\tG2\n", encoding="utf-8")
    _, errors = read_gmt(bad)
    assert any("line 1 must be GMT" in error for error in errors)
    assert any("pathway names must be unique" in error for error in errors)


# --- inspection / preflight -----------------------------------------------------------------------------------------


def test_toy_bundle_passes_inspection_and_reports_its_shape():
    report, ok = inspect_porcupine_inputs_impl(str(NETWORK), str(GMT))
    assert ok, report
    assert "600 edges x 12 samples" in report
    assert "pathways testable with 5 <= size <= 150: 8" in report


def test_too_few_samples_fail_closed(tmp_path):
    header = "tf gene " + " ".join(f"S{i}" for i in range(MIN_SAMPLES - 1))
    rows = [f"TF1 GENE{g:02d} " + " ".join(str(v + g) for v in range(MIN_SAMPLES - 1)) for g in range(1, 9)]
    report, ok = inspect_porcupine_inputs_impl(str(_network(tmp_path, header, rows)), str(GMT))
    assert not ok and f"at least {MIN_SAMPLES} samples" in report


def test_gene_namespace_mismatch_between_gmt_and_network_fails_closed(tmp_path):
    gmt = tmp_path / "ensembl.gmt"
    gmt.write_text("P1\tdesc\tENSG00000000003\tENSG00000000005\n", encoding="utf-8")
    report, ok = inspect_porcupine_inputs_impl(str(NETWORK), str(gmt))
    assert not ok and "same gene identifier namespace" in report


def test_inverted_pathway_size_range_fails_closed():
    report, ok = inspect_porcupine_inputs_impl(str(NETWORK), str(GMT), {"min_pathway_size": 20, "max_pathway_size": 10})
    assert not ok and "max_pathway_size must be greater than or equal to min_pathway_size" in report


def test_preflight_gate_dispatches_to_the_porcupine_validator(tmp_path):
    assert validate_workflow_inputs("run_porcupine", decision()) == []
    errors = validate_workflow_inputs("run_porcupine", decision(pathway_file=str(tmp_path / "missing.gmt")))
    assert errors and any("pathway_file" in error for error in errors)


# --- planning / execution preview -----------------------------------------------------------------------------------


def test_porcupine_plans_with_explicit_role_paths_and_has_a_dry_run_preview():
    task = (f"Run PORCUPINE with sample_network_file={NETWORK} pathway_file={GMT} "
            "output_dir=outputs/porcupine-test")
    plan = agent.build_workflow_plan(decision(), task)
    assert plan.status == "ready"
    assert [step.action for step in plan.steps] == ["inspect_porcupine_inputs", "run_porcupine"]
    result = agent.run_porcupine.invoke(executor_arguments("run_porcupine", decision()))
    assert "Dry run only" in result
    assert "run-porcupine" in result and "--n-permutations 1000" in result
    assert "None" not in result


def test_missing_input_never_becomes_ready():
    plan = agent.build_workflow_plan(decision(pathway_file=None), f"Run PORCUPINE with sample_network_file={NETWORK}")
    assert plan.status == "needs_input"


def test_demo_bundle_is_the_toy_network_and_gmt():
    values, reason = agent.discover_demo_bundle("run_porcupine")
    assert values["sample_network_file"].endswith("lioness_panda_network.txt")
    assert values["pathway_file"].endswith("pathways.gmt")
    assert "PORCUPINE" in reason


# --- output artifacts -----------------------------------------------------------------------------------------------


def _write_outputs(root: Path, *, samples=SAMPLES, significant=("P_DRIVEN",), loadings_for=("P_DRIVEN",)):
    root.mkdir(parents=True, exist_ok=True)
    pathways = ["P_DRIVEN", "P_RANDOM_1"]
    pd.DataFrame({
        "pathway": pathways, "pathway_size": [8, 11], "n_edges": [80, 110],
        "pc1_variance_pct": [94.3, 13.9], "null_mean_pc1_variance_pct": [24.2, 24.7],
        "pvalue": [1e-40, 0.99], "padj": [2e-40, 0.99], "effect_size": [8.7, 1.3],
        "significant": ["TRUE" if name in significant else "FALSE" for name in pathways],
    }).to_csv(root / "porcupine_pathways.tsv", sep="\t", index=False)
    pd.DataFrame({"pathway_size": [8, 11], "n_edges": [80, 110], "pc1_variance_pct": [20.1, 22.3]}).to_csv(
        root / "porcupine_random_null.tsv", sep="\t", index=False)
    scores = pd.DataFrame(np.arange(len(pathways) * len(samples), dtype=float).reshape(len(pathways), -1), columns=samples)
    scores.insert(0, "pathway", pathways)
    scores.to_csv(root / "porcupine_pc1_sample_scores.tsv", sep="\t", index=False)
    pd.DataFrame({"pathway": list(loadings_for), "regulator": ["TF1"] * len(loadings_for),
                  "target": ["GENE01"] * len(loadings_for), "pc1_loading": [0.1] * len(loadings_for),
                  "pc2_loading": [-0.1] * len(loadings_for)}).to_csv(
        root / "porcupine_edge_loadings.tsv", sep="\t", index=False)
    (root / "manifest.json").write_text(json.dumps({"method": "PORCUPINE"}), encoding="utf-8")


def test_valid_outputs_pass_the_artifact_contract(tmp_path):
    _write_outputs(tmp_path / "out")
    result = validate_output_artifacts("run_porcupine", decision(output_dir=str(tmp_path / "out")))
    assert result.ok, result.errors
    assert result.metrics["porcupine_significant_pathways"] == 1
    assert result.metrics["porcupine_score_samples"] == 12


def test_scores_must_keep_the_input_sample_columns_in_order(tmp_path):
    _write_outputs(tmp_path / "out", samples=list(reversed(SAMPLES)))
    result = validate_output_artifacts("run_porcupine", decision(output_dir=str(tmp_path / "out")))
    assert not result.ok
    assert any("same order" in error for error in result.errors)


def test_loadings_may_only_cover_significant_pathways(tmp_path):
    _write_outputs(tmp_path / "out", loadings_for=("P_RANDOM_1",))
    result = validate_output_artifacts("run_porcupine", decision(output_dir=str(tmp_path / "out")))
    assert not result.ok
    assert any("only cover significant pathways" in error for error in result.errors)


def test_missing_artifact_is_reported(tmp_path):
    _write_outputs(tmp_path / "out")
    (tmp_path / "out" / "porcupine_random_null.tsv").unlink()
    result = validate_output_artifacts("run_porcupine", decision(output_dir=str(tmp_path / "out")))
    assert not result.ok and any("missing or empty" in error for error in result.errors)


def test_gene_check_skips_regulators_so_puma_mirnas_pass(tmp_path):
    # PORCUPINE matches pathways on targets only; a LIONESS-PUMA network's regulators include miRNAs.
    from netzoo_agent_core.data.porcupine import porcupine_gene_axes

    labels = [label for _, label in porcupine_gene_axes(str(NETWORK), str(GMT))]
    assert labels == ["PORCUPINE network target genes", "PORCUPINE pathway genes"]


# --- memory: checks stream the table; the runner streams it to R ---------------------------------------------------


def test_chunked_scan_matches_a_full_read(tmp_path, monkeypatch):
    import porcupine_io

    header = "tf gene " + " ".join(f"S{i}" for i in range(MIN_SAMPLES))
    rows = [f"TF{t} G{g} " + " ".join(str(5 if g == 0 else (t + 1) * (g + s)) for s in range(MIN_SAMPLES))
            for t in range(3) for g in range(7)]
    path = _network(tmp_path, header, rows)
    monkeypatch.setattr(porcupine_io, "SCAN_CHUNK_ROWS", 4)  # 21 edges in 6 chunks
    scan = porcupine_io.scan_sample_network(path)
    full = read_sample_network(path)
    assert not scan.errors and scan.values.empty
    assert scan.n_edges == full.n_edges == 21 and scan.samples == full.samples
    assert list(scan.targets) == list(full.targets)
    assert scan.constant_edges == 3  # the three G0 edges

    out = tmp_path / "matrix.tsv"
    written, dropped, targets = porcupine_io.write_r_matrix(path, out, drop_constant=True)
    assert (written, dropped) == (18, 3) and "G0" not in targets
    matrix = pd.read_csv(out, sep="\t")
    assert list(matrix.columns[:2]) == ["regulator", "target"] and matrix.shape == (18, 2 + MIN_SAMPLES)


def test_a_non_numeric_weight_in_a_later_chunk_is_reported(tmp_path, monkeypatch):
    import porcupine_io

    rows = [f"TF G{g} " + " ".join("1" for _ in range(MIN_SAMPLES)) for g in range(9)] + [
        "TF G9 " + " ".join(["NA"] + ["1"] * (MIN_SAMPLES - 1))]
    path = _network(tmp_path, "tf gene " + " ".join(f"S{i}" for i in range(MIN_SAMPLES)), rows)
    monkeypatch.setattr(porcupine_io, "SCAN_CHUNK_ROWS", 3)
    assert any("finite numeric values" in error for error in porcupine_io.scan_sample_network(path).errors)


# --- pathway size floor: irlba's 3-component PCA stops below 4 edges -----------------------------------------------


def test_pathways_smaller_than_four_genes_are_refused():
    from porcupine_io import parameter_errors

    assert any("at least 4" in error for error in parameter_errors({"min_pathway_size": 3}))
    assert not parameter_errors({"min_pathway_size": 4})


def test_a_pathway_holding_every_gmt_gene_is_refused(tmp_path):
    """Its random sets would all equal it and the R t-test stops (review 2026-11-05)."""
    first = GMT.read_text(encoding="utf-8").splitlines()[0]
    single = tmp_path / "one.gmt"
    single.write_text(first + "\n", encoding="utf-8")
    report, ok = inspect_porcupine_inputs_impl(str(NETWORK), str(single))
    assert not ok
    assert "every random set would equal this pathway" in report
    _, ok = inspect_porcupine_inputs_impl(str(NETWORK), str(GMT))
    assert ok


def test_lioness_puma_tsv_with_a_space_separated_header_is_read(tmp_path):
    """add-puma-lioness-header wrote a space header over netZooPy's tab body before 2026-11-05."""
    rows = ["\t".join([f"TF{t}", f"G{g}", "1", *(str(v + t + g) for v in range(MIN_SAMPLES))])
            for t in range(2) for g in range(3)]
    header = "regulator gene prior_weight " + " ".join(str(i) for i in range(1, MIN_SAMPLES + 1))
    network = read_sample_network(_network(tmp_path, header, rows, name="lioness.tsv"))
    assert not network.errors, network.errors
    assert network.prior_column == "prior_weight"
    assert network.samples == [str(i) for i in range(1, MIN_SAMPLES + 1)]


def test_puma_header_helper_uses_the_body_delimiter(tmp_path):
    import importlib.machinery
    import importlib.util

    loader = importlib.machinery.SourceFileLoader("add_header", str(ROOT / "docker" / "add-puma-lioness-header"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader("add_header", loader))
    loader.exec_module(module)
    expression = tmp_path / "expr.txt"
    expression.write_text("G1 1 2 3\n", encoding="utf-8")
    for suffix, delimiter in ((".tsv", "\t"), (".csv", ","), (".txt", " ")):
        lioness = tmp_path / f"lioness{suffix}"
        lioness.write_text(delimiter.join(["TF", "G1", "1", "0.1", "0.2", "0.3"]) + "\n", encoding="utf-8")
        assert module.add_header(expression, lioness)
        header = lioness.read_text(encoding="utf-8").splitlines()[0]
        assert header == delimiter.join(["regulator", "gene", "prior_weight", "1", "2", "3"])
        assert not module.add_header(expression, lioness)  # already headed


def test_gmt_genes_outside_the_network_are_not_gene_checked(tmp_path):
    """A withdrawn symbol in an unrelated pathway must not refuse the run (review 2026-11-05)."""
    from netzoo_agent_core.data.porcupine import porcupine_gene_axes

    gmt = tmp_path / "extra.gmt"
    gmt.write_text(GMT.read_text(encoding="utf-8") + "P_OTHER\ttoy\tWITHDRAWN1\tFAM123Z\n", encoding="utf-8")
    axes = dict((label, ids) for ids, label in porcupine_gene_axes(str(NETWORK), str(gmt)))
    assert "WITHDRAWN1" not in axes["PORCUPINE pathway genes"]
    assert set(axes["PORCUPINE pathway genes"]) <= set(axes["PORCUPINE network target genes"])
