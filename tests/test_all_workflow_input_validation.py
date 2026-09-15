from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.preflight import validate_workflow_inputs  # noqa: E402


@pytest.mark.parametrize(
    ("action", "file_fields"),
    [
        ("run_panda", ("expression_file", "motif_file", "ppi_file")),
        ("run_puma", ("expression_file", "motif_file", "ppi_file", "mirna_file")),
        ("run_lioness_panda", ("expression_file", "motif_file", "ppi_file")),
        ("run_lioness_puma", ("expression_file", "motif_file", "ppi_file", "mirna_file")),
        ("run_lioness_coexpression", ("expression_file",)),
        ("run_condor", ("network_file",)),
        ("run_cobra", ("expression_file", "design_file")),
        (
            "run_sambar",
            ("mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file"),
        ),
        ("run_dragon", ("omics_layer_1", "omics_layer_2")),
        ("run_otter", ("expression_file", "motif_file", "ppi_file")),
        ("run_giraffe", ("expression_file", "motif_file", "ppi_file")),
        ("run_bonobo", ("expression_file",)),
    ],
)
def test_all_registered_workflows_reject_malformed_content(
    tmp_path: Path, action: str, file_fields: tuple[str, ...]
):
    malformed = tmp_path / "looks-plausible.tsv"
    malformed.write_text("this is not a valid workflow input\n", encoding="utf-8")
    decision = {field: str(malformed) for field in file_fields}
    decision.update(
        {
            "output_dir": str(tmp_path / "out"),
            "output_file": str(tmp_path / "out.tsv"),
            "lioness_output": str(tmp_path / "lioness"),
            "genes_axis": "rows",
            "log_transformed": True,
            "centered": True,
        }
    )

    errors = validate_workflow_inputs(action, decision)

    assert errors, f"{action} silently accepted malformed content"
