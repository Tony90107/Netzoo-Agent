"""Identifier and header edge cases in preprocessing (PAR_Y, versions, numeric headers)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data import gene_validation  # noqa: E402
from netzoo_agent_core.data.dragon import load_and_align_dragon_layers  # noqa: E402
from netzoo_agent_core.data.giraffe import (  # noqa: E402
    GiraffeInputError,
    load_giraffe_inputs,
)
from netzoo_agent_core.data.tables import _identifier_namespace  # noqa: E402


# --- 1. GENCODE _PAR_Y identifiers -------------------------------------------


def test_gencode_par_y_gene_ids_stay_in_the_ensembl_gene_namespace():
    ids = ["ENSG00000002586.20", "ENSG00000002586.20_PAR_Y", "ENSG00000141510"]
    assert _identifier_namespace(ids) == "ensembl_gene"
    assert _identifier_namespace(["ENST00000381192.10_PAR_Y", "ENST00000269305"]) == (
        "ensembl_transcript"
    )
    # A real gene/transcript mix is still reported as mixed.
    assert _identifier_namespace(["ENSG00000002586.20_PAR_Y", "ENST00000269305"]) == (
        "mixed_ensembl"
    )


# --- 2. Versioned Ensembl IDs at the REST lookup ------------------------------


def test_ensembl_lookup_strips_versions_for_the_query_but_reports_the_original(monkeypatch):
    seen: dict[str, object] = {}

    def fake_query(url, method="GET", payload=None, **kwargs):
        seen["ids"] = list(payload["ids"])
        return {
            "ENSG00000141510": {
                "id": "ENSG00000141510",
                "object_type": "Gene",
                "species": "homo_sapiens",
                "display_name": "TP53",
            },
            "ENSG00000002586": {
                "id": "ENSG00000002586",
                "object_type": "Gene",
                "species": "homo_sapiens",
                "display_name": "CD99",
            },
        }

    monkeypatch.setattr(gene_validation, "_query_authority_json", fake_query)
    records = gene_validation._structured_gene_lookup(
        ["ENSG00000141510.12", "ENSG00000002586.20_PAR_Y"], "ensembl_gene", "Homo sapiens"
    )

    assert seen["ids"] == ["ENSG00000141510", "ENSG00000002586"]
    assert [record.identifier for record in records] == [
        "ENSG00000141510.12",
        "ENSG00000002586.20_PAR_Y",
    ]
    assert [record.status for record in records] == ["valid", "valid"]
    assert records[0].canonical_id == "ensembl_gene:ENSG00000141510"
    assert records[0].normalized_identifier == "ensg00000141510.12"


# --- 3. GIRAFFE numeric sample headers ----------------------------------------


def _giraffe_side_files(tmp_path: Path, genes: tuple[str, str] = ("g1", "g2")) -> tuple[Path, Path]:
    motif = tmp_path / "motif.tsv"
    motif.write_text(
        "source\ttarget\tweight\n"
        f"TF1\t{genes[0]}\t1\nTF1\t{genes[1]}\t0.5\n"
        f"TF2\t{genes[0]}\t0.25\nTF2\t{genes[1]}\t1\n",
        encoding="utf-8",
    )
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("source\ttarget\tweight\nTF1\tTF2\t0.5\n", encoding="utf-8")
    return motif, ppi


@pytest.mark.parametrize("first_cell", ["", "symbol", "gene_symbol"])
def test_giraffe_numeric_sample_header_with_gene_axis_label_or_blank(tmp_path, first_cell):
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        f"{first_cell}\t1001\t1002\t1003\ng1\t1\t2\t3\ng2\t3\t2\t1\n", encoding="utf-8"
    )
    motif, ppi = _giraffe_side_files(tmp_path)

    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))

    assert bundle.sample_ids == ("1001", "1002", "1003")
    assert bundle.gene_ids == ("g1", "g2")


def test_giraffe_numeric_sample_header_over_continuous_values(tmp_path):
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "probe\t1001\t1002\t1003\ng1\t1.5\t2.25\t3.1\ng2\t3.2\t2.7\t1.05\n",
        encoding="utf-8",
    )
    motif, ppi = _giraffe_side_files(tmp_path)

    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))

    assert bundle.sample_ids == ("1001", "1002", "1003")
    assert bundle.gene_ids == ("g1", "g2")


def test_giraffe_genuine_first_data_row_is_not_taken_as_a_header(tmp_path):
    expression = tmp_path / "expression.tsv"
    expression.write_text("g1\t1\t2\t3\ng2\t3\t2\t1\n", encoding="utf-8")
    motif, ppi = _giraffe_side_files(tmp_path)

    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))

    assert bundle.gene_ids == ("g1", "g2")
    assert bundle.sample_ids == ("sample_1", "sample_2", "sample_3")


# --- 4. Version/case-only identifier mismatches -------------------------------


def test_giraffe_diagnoses_a_version_suffix_only_gene_mismatch(tmp_path):
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene_id\ts1\ts2\ts3\n"
        "ENSG00000141510.12\t1\t2\t3\nENSG00000002586.20\t3\t2\t1\n",
        encoding="utf-8",
    )
    motif, ppi = _giraffe_side_files(tmp_path, ("ENSG00000141510", "ENSG00000002586"))

    with pytest.raises(GiraffeInputError, match="match after removing version suffixes"):
        load_giraffe_inputs(str(expression), str(motif), str(ppi))


def test_giraffe_diagnoses_a_letter_case_only_tf_mismatch(tmp_path):
    expression = tmp_path / "expression.tsv"
    expression.write_text("gene_id\ts1\ts2\ts3\ng1\t1\t2\t3\ng2\t3\t2\t1\n", encoding="utf-8")
    motif, _ = _giraffe_side_files(tmp_path)
    ppi = tmp_path / "ppi_lower.tsv"
    ppi.write_text("source\ttarget\tweight\ntf1\ttf2\t0.5\n", encoding="utf-8")

    with pytest.raises(GiraffeInputError, match="letter case"):
        load_giraffe_inputs(str(expression), str(motif), str(ppi))


def test_giraffe_genuine_gene_mismatch_has_no_normalisation_hint(tmp_path):
    expression = tmp_path / "expression.tsv"
    expression.write_text("gene_id\ts1\ts2\ts3\ng1\t1\t2\t3\ng3\t3\t2\t1\n", encoding="utf-8")
    motif, ppi = _giraffe_side_files(tmp_path)

    with pytest.raises(GiraffeInputError) as error:
        load_giraffe_inputs(str(expression), str(motif), str(ppi))
    assert "version suffixes" not in str(error.value)
    assert "letter case" not in str(error.value)


def test_dragon_diagnoses_a_letter_case_only_sample_mismatch(tmp_path):
    layer1 = tmp_path / "layer1.tsv"
    layer1.write_text("sample\ta\tb\nS1\t1\t2\nS2\t2\t5\nS3\t3\t1\n", encoding="utf-8")
    layer2 = tmp_path / "layer2.tsv"
    layer2.write_text("sample\tc\td\ns1\t1\t2\ns2\t2\t5\ns3\t3\t1\n", encoding="utf-8")

    _, _, errors = load_and_align_dragon_layers(str(layer1), str(layer2))

    assert any("letter case" in error for error in errors), errors


# --- 5. DRAGON integer (Entrez) feature headers -------------------------------


def test_dragon_accepts_entrez_feature_headers_under_a_sample_label(tmp_path):
    layer1 = tmp_path / "layer1.tsv"
    layer1.write_text(
        "sample_id\t7157\t672\nTCGA-01\t1.5\t2.1\nTCGA-02\t2.2\t5.3\nTCGA-03\t3.9\t1.4\n",
        encoding="utf-8",
    )
    layer2 = tmp_path / "layer2.tsv"
    layer2.write_text(
        "sample_id\tcg00000029\tcg00000108\nTCGA-01\t0.1\t0.2\n"
        "TCGA-02\t0.4\t0.5\nTCGA-03\t0.3\t0.9\n",
        encoding="utf-8",
    )

    first, _, errors = load_and_align_dragon_layers(str(layer1), str(layer2))

    assert errors == []
    assert list(first.columns) == ["7157", "672"]


@pytest.mark.parametrize(
    "body",
    [
        "S1\t0.5\t1.5\nS2\t2.2\t5.3\nS3\t3.9\t1.4\nS4\t1.1\t0.7\n",
        "S1\t5\t7\nS2\t2\t5\nS3\t3\t1\nS4\t8\t2\n",
    ],
)
def test_dragon_still_rejects_a_headerless_layer(tmp_path, body):
    layer1 = tmp_path / "layer1.tsv"
    layer1.write_text(body, encoding="utf-8")
    layer2 = tmp_path / "layer2.tsv"
    layer2.write_text("sample\tc\td\nS2\t1\t2\nS3\t2\t5\nS4\t3\t1\n", encoding="utf-8")

    _, _, errors = load_and_align_dragon_layers(str(layer1), str(layer2))

    assert any("no feature header" in error for error in errors), errors


# --- 6. DRAGON near-constant features -----------------------------------------


def test_dragon_rejects_and_names_near_constant_features(tmp_path):
    layer1 = tmp_path / "layer1.tsv"
    layer1.write_text(
        "sample\tflat\tok\n"
        "S1\t5.0\t1\nS2\t5.000000000000001\t2\nS3\t5.0\t4\n",
        encoding="utf-8",
    )
    layer2 = tmp_path / "layer2.tsv"
    layer2.write_text("sample\tc\td\nS1\t1\t2\nS2\t2\t5\nS3\t3\t1\n", encoding="utf-8")

    _, _, errors = load_and_align_dragon_layers(str(layer1), str(layer2))

    assert any("near-constant" in error and "flat" in error for error in errors), errors
    assert not any("'ok'" in error for error in errors)


def test_dragon_keeps_small_scale_features_with_real_variation(tmp_path):
    layer1 = tmp_path / "layer1.tsv"
    layer1.write_text(
        "sample\ttiny\tok\nS1\t1e-9\t1\nS2\t3e-9\t2\nS3\t2e-9\t4\n", encoding="utf-8"
    )
    layer2 = tmp_path / "layer2.tsv"
    layer2.write_text("sample\tc\td\nS1\t1\t2\nS2\t2\t5\nS3\t3\t1\n", encoding="utf-8")

    _, _, errors = load_and_align_dragon_layers(str(layer1), str(layer2))

    assert errors == []
