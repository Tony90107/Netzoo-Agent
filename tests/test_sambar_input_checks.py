"""SAMBAR inspection names the samples upstream drops and reports a small gene overlap."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.sambar import inspect_sambar_inputs_impl  # noqa: E402


def _bundle(tmp_path: Path, rows: dict[str, list[int]], genes: list[str], *, extra_mutation_genes: int = 0):
    all_genes = genes + [f"X{index}" for index in range(extra_mutation_genes)]
    mutation = tmp_path / "mutation.csv"
    mutation.write_text(
        "sample," + ",".join(all_genes) + "\n"
        + "".join(f"{name}," + ",".join(map(str, values + [1] * extra_mutation_genes)) + "\n" for name, values in rows.items()),
        encoding="utf-8",
    )
    exon = tmp_path / "exon.csv"
    exon.write_text("id," + ",".join(genes) + "\nlength," + ",".join("1000" for _ in genes) + "\n", encoding="utf-8")
    cancer = tmp_path / "cancer.txt"
    cancer.write_text("\t".join(genes) + "\n", encoding="utf-8")
    gmt = tmp_path / "pathways.gmt"
    gmt.write_text(f"P1\tdesc\t" + "\t".join(genes) + "\n", encoding="utf-8")
    return str(mutation), str(exon), str(cancer), str(gmt)


GENES = [f"G{index}" for index in range(60)]


def test_samples_without_mutations_in_the_scored_genes_are_named(tmp_path):
    rows = {f"P{index}": [1 if gene == index else 0 for gene in range(60)] for index in range(4)}
    rows.update({f"Z{index}": [0] * 60 for index in range(7)})
    report, ok = inspect_sambar_inputs_impl(*_bundle(tmp_path, rows, GENES), {"kmin": 2, "kmax": 3})
    # Upstream drops these samples itself (corgenelength), so the run may go ahead -- but they are named.
    assert ok
    assert "7 of 11 samples have no mutations in the 60 pathway cancer genes with an exon size" in report
    assert "Z0, Z1, Z2, Z3, Z4 (and 2 more)" in report
    assert "netZooPy SAMBAR drops them" in report


def test_mutations_only_outside_the_overlap_count_as_zero(tmp_path):
    # Every sample has a mutation in X0 (not in exon sizes), so the raw row sum hides the problem.
    rows = {"P0": [1] + [0] * 59, "P1": [0, 1] + [0] * 58, "P2": [0] * 60}
    report, ok = inspect_sambar_inputs_impl(*_bundle(tmp_path, rows, GENES, extra_mutation_genes=1))
    assert ok
    assert "1 of 3 samples have no mutations in the 60 pathway cancer genes with an exon size that SAMBAR scores: P2;" in report


def test_mutations_only_in_genes_outside_every_pathway_are_named(tmp_path):
    # upstream desparsify drops a sample whose pathway scores are all zero
    mutation, exon, cancer, gmt = _bundle(tmp_path, {"P0": [1] + [0] * 59, "P1": [0] * 59 + [1]}, GENES)
    Path(gmt).write_text("P1\tdesc\t" + "\t".join(GENES[:59]) + "\n", encoding="utf-8")
    report, ok = inspect_sambar_inputs_impl(mutation, exon, cancer, gmt)
    assert ok
    assert "1 of 2 samples have no mutations in the 59 pathway" in report and ": P1;" in report


def test_small_overlap_is_a_warning_with_the_numbers(tmp_path):
    genes = GENES[:10]
    rows = {f"P{index}": [1] * 10 for index in range(3)}
    report, ok = inspect_sambar_inputs_impl(*_bundle(tmp_path, rows, genes, extra_mutation_genes=5))
    assert ok
    assert "warning: only 10 genes are shared by all four inputs, out of 10 mutation genes in the cancer-gene list" in report


def test_official_ucec_toy_has_no_overlap_warning():
    # Whole-exome mutations against a cancer-gene list: 4.5% of mutation genes overlap, by design.
    toy = Path(__file__).parents[1] / "data" / "sambar-official-toy"
    report, ok = inspect_sambar_inputs_impl(
        str(toy / "mut.ucec.csv"), str(toy / "esizef.csv"), str(toy / "genes.txt"), str(toy / "h.all.v6.1.symbols.gmt")
    )
    assert ok
    assert "are shared by all four inputs" not in report


def test_large_overlap_has_no_warning(tmp_path):
    rows = {f"P{index}": [1] * 60 for index in range(3)}
    report, ok = inspect_sambar_inputs_impl(*_bundle(tmp_path, rows, GENES))
    assert ok and "warning" not in report
