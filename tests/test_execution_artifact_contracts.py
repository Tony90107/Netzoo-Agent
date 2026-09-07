"""Check recorded workflow outputs against the artifact contracts routing relies on.

Everything else in this suite tests routing: whether the request maps to the
right capability and a self-consistent typed outcome. None of it ever looked at
what the workflows actually produce. So the ontology's claims about each artifact
-- what a `pathway_mutation_matrix` is, what makes a network `sample_specific` --
have never been checked against a real run, and an internally consistent outcome
can still describe an artifact the tool does not emit in that shape.

This module closes the smallest useful part of that gap using outputs recorded
from pinned runs (see `fixtures/execution/README.md`).

**Scope, stated so it is not overclaimed.** These are structural checks:
identifier families, axis orientation, sample coverage, and required versus
forbidden columns, all against outputs recorded earlier.

Numeric comparison against upstream's own reference values now exists for one
workflow, in `test_execution_numeric_reference.py`, which runs SAMBAR in the
pinned image and agrees with netZooPy's ground truth to 3.5e-18. What still
does not exist is per-workflow *biological* assertion for the other eleven
capabilities.
"""
import csv
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "execution"


def _table(name, delimiter):
    with (FIXTURES / name).open() as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader)
        rows = [row for row in reader if row]
    return header, rows


def _axes(name, delimiter=","):
    header, rows = _table(name, delimiter)
    return header[1:], [row[0] for row in rows]


# --- what the ontology claims, asserted against a real run --------------------

def test_pathway_scores_really_are_pathway_by_sample():
    """`pathway_mutation_matrix` is declared "Pathway-by-sample"."""
    assert "Pathway-by-sample" in ARTIFACT_SEMANTICS["pathway_mutation_matrix"].description
    columns, rows = _axes("sambar.pathway_mutation_matrix.csv")

    assert rows and all(name.startswith("HALLMARK_") for name in rows)
    assert columns and all(name.startswith("TCGA-") for name in columns)


def test_the_declared_orientation_of_gene_scores_disagrees_with_the_run():
    """`gene_mutation_scores` says "Gene-by-sample"; the run emits sample-by-gene.

    Recorded rather than corrected. The description is prose, so this may be a
    documentation defect and not a behavioural one -- but nothing in the system
    could tell the difference, which is the point of having this check at all.
    """
    assert "Gene-by-sample" in ARTIFACT_SEMANTICS["gene_mutation_scores"].description
    axes = json.loads((FIXTURES / "sambar.gene_mutation_scores.axes.json").read_text())

    assert all(name.startswith("TCGA-") for name in axes["rows"])
    assert not any(name.startswith("TCGA-") for name in axes["columns"])


def test_sambar_drops_one_sample_between_its_own_two_artifacts():
    """Sample coverage is not preserved, and the agent never says so.

    Routing correctness says nothing about output completeness. The pathway
    scores cover 247 of the 248 samples present in the gene-level artifact.

    **Resolved since this was written.** It is the method, not our pipeline:
    upstream netZooPy's own ground truth carries the same 247 columns, which
    `test_execution_numeric_reference.py` asserts against a real run. A patient
    whose retained mutations sum to zero cannot be normalised by mutation
    burden. Still worth surfacing to a requester -- the agent never mentions it
    -- but not a defect to fix here. Pinned so a change in it is visible.
    """
    columns, _ = _axes("sambar.pathway_mutation_matrix.csv")
    axes = json.loads((FIXTURES / "sambar.gene_mutation_scores.axes.json").read_text())

    assert set(columns) < set(axes["rows"])
    assert len(axes["rows"]) - len(columns) == 1


def test_the_regulatory_network_artifact_has_no_consistent_serialisation():
    """Three workflows declare `regulatory_network` and emit three formats.

    The routing layer treats the artifact type as one thing and recommends it as
    one thing. At the file level it is not: PANDA writes a tab-separated header,
    PUMA writes no header at all, and LIONESS-PUMA writes a space-separated
    header above tab-separated rows. A consumer cannot parse them uniformly, and
    no routing-level check could ever have noticed.

    Recorded, not corrected: fixing the emitters is a separate change, and this
    pins the state so that fixing one of them shows up here.
    """
    panda = (FIXTURES / "panda.aggregate_regulatory_network.head.tsv").read_text().splitlines()
    puma = (FIXTURES / "puma.aggregate_regulatory_network.tsv").read_text().splitlines()
    lioness = (FIXTURES / "lioness_puma.sample_specific_regulatory_network.tsv").read_text().splitlines()

    assert panda[0].split("\t") == ["tf", "gene", "motif", "force"]
    # No header: the first line is already an edge.
    assert puma[0].split("\t")[0].startswith("TF")
    assert "\t" not in lioness[0] and lioness[0].split()[:2] == ["regulator", "gene"]


@pytest.mark.parametrize(
    "name",
    ["panda.aggregate_regulatory_network.head.tsv", "puma.aggregate_regulatory_network.tsv"],
)
def test_an_aggregate_regulatory_network_carries_one_value_per_edge(name):
    """What makes a network aggregate: one value per edge, for the whole cohort.

    Checked on the data rows, which both files agree on, rather than on the
    header, which they do not.
    """
    rows = [
        line.split("\t") for line in (FIXTURES / name).read_text().splitlines()
        if line and not line.startswith(("tf\t", "regulator"))
    ]

    assert rows
    # regulator, target, prior, one value. A per-sample network has more.
    assert all(len(row) == 4 for row in rows[:50])


def test_a_sample_specific_regulatory_network_carries_one_column_per_sample():
    header_line = (FIXTURES / "lioness_puma.sample_specific_regulatory_network.tsv").read_text().splitlines()[0]
    # Recorded defect: the header is space-separated while the data rows are
    # tab-separated, so a consumer splitting on tabs reads one column here.
    assert "\t" not in header_line
    header = header_line.split()
    _, rows = _table("lioness_puma.sample_specific_regulatory_network.tsv", "\t")

    assert header[:3] == ["regulator", "gene", "prior_weight"]
    sample_columns = header[3:]
    assert len(sample_columns) >= 2
    assert all(len(row) == len(header) for row in rows)


def test_an_aggregate_coexpression_network_is_square_over_one_entity_family():
    """`coexpression_network` is gene-by-gene; COBRA declares only aggregate."""
    columns, rows = _axes("cobra.aggregate_coexpression_network.tsv", "\t")

    assert columns == rows
    assert not any(name.startswith("TCGA-") for name in rows)


def test_the_pathway_artifact_is_not_shaped_like_a_network():
    """The forbidden half: SAMBAR's output must not be usable as a network."""
    header, _ = _table("sambar.pathway_mutation_matrix.csv", ",")

    assert not {"tf", "regulator", "gene"} & {name.casefold() for name in header}


def test_provenance_is_recorded_with_the_reference_output():
    manifest = json.loads((FIXTURES / "sambar.manifest.json").read_text())

    assert manifest["method"] == "SAMBAR"
    assert manifest["inputs"] and manifest["parameters"]
    assert set(manifest["artifacts"]) == {"mt_out.csv", "pt_out.csv"}
