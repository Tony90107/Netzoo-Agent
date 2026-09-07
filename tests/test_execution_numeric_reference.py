"""Run a workflow for real and compare its numbers to upstream's own reference.

Everything else in this suite stops at the routing layer or at the *structure*
of a recorded output. This is the first check that a workflow, invoked through
the production wrapper, produces the values its upstream authors say it should.

It is opt-in for the same reason `test_sambar_container.py` is: it needs the
pinned image, where netZooPy lives. The default offline gate stays fast.

What makes the reference trustworthy is that we did not write it. netZooPy ships
`tests/sambar/ToyData/sambar_gt.csv` with the inputs that produce it, so the
comparison is against the method's authors rather than against our own earlier
output. The recorded artifact in `outputs/` is checked too, which turns it from
"a file we once produced" into "a file that still reproduces".
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).parents[1]
IMAGE = os.environ.get("NETZOO_IMAGE", "netzoo_agent:latest")
RUN_DOCKER_TESTS = os.environ.get("NETZOO_RUN_DOCKER_TESTS") == "1"

TOY = "/opt/netZooPy/tests/sambar/ToyData"
# Justified: the observed disagreement with upstream is 3.5e-18, i.e. double
# rounding. This is six orders of magnitude looser than that and still far
# tighter than any difference that could change a biological reading of a
# pathway score, so it separates "same computation" from "different result"
# without pinning bit patterns across BLAS builds.
TOLERANCE = 1e-12

pytestmark = pytest.mark.skipif(
    not RUN_DOCKER_TESTS or shutil.which("docker") is None,
    reason="set NETZOO_RUN_DOCKER_TESTS=1 to run the pinned-image numeric checks",
)


def _table(path: Path) -> tuple[list[str], dict[str, list[float]]]:
    with path.open() as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = {row[0]: [float(value) for value in row[1:]] for row in reader if row}
    return header[1:], rows


@pytest.fixture(scope="module")
def sambar_run() -> dict[str, object]:
    """Run SAMBAR through the production wrapper on upstream's toy inputs."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "cd /opt/netzoo-app && python scripts/run_sambar.py"
                f" -m {TOY}/mut.ucec.csv -e {TOY}/esizef.csv"
                f" -g {TOY}/genes.txt -p {TOY}/h.all.v6.1.symbols.gmt"
                f" -o /out && cp {TOY}/sambar_gt.csv /out/upstream_gt.csv",
            ],
            check=True, capture_output=True, timeout=900,
        )
        produced, upstream = _table(out / "pt_out.csv"), _table(out / "upstream_gt.csv")
        gene_columns, gene_rows = _table(out / "mt_out.csv")
        manifest = json.loads((out / "manifest.json").read_text())
    return {
        "produced": produced,
        "upstream": upstream,
        "gene_axes": (gene_columns, list(gene_rows)),
        "manifest": manifest,
    }


def test_the_pathway_scores_match_upstreams_own_ground_truth(sambar_run):
    (columns, rows), (gt_columns, gt_rows) = sambar_run["produced"], sambar_run["upstream"]

    assert columns == gt_columns
    assert set(rows) == set(gt_rows)
    worst = max(
        abs(value - reference)
        for pathway, values in rows.items()
        for value, reference in zip(values, gt_rows[pathway])
    )
    assert worst < TOLERANCE, f"largest disagreement with upstream: {worst:.3e}"


def test_the_recorded_artifact_still_reproduces(sambar_run):
    """The committed reference is a claim about reproducibility, so check it."""
    columns, rows = sambar_run["produced"]
    recorded_columns, recorded_rows = _table(
        ROOT / "tests" / "fixtures" / "execution" / "sambar.pathway_mutation_matrix.csv"
    )

    assert columns == recorded_columns
    assert set(rows) == set(recorded_rows)
    worst = max(
        abs(value - recorded)
        for pathway, values in rows.items()
        for value, recorded in zip(values, recorded_rows[pathway])
    )
    assert worst < TOLERANCE


def test_the_dropped_sample_is_upstream_behaviour_not_ours(sambar_run):
    """Resolves a finding the structural checks could only hypothesise about.

    The pathway artifact covers one fewer sample than the gene-level artifact
    from the same run. That looked like a silent loss introduced somewhere in
    our pipeline. Upstream's own ground truth carries the same 247 columns, so
    it is the method: a patient whose retained mutations sum to zero cannot be
    normalised by mutation burden. Still worth surfacing to a requester, but it
    is not a defect to fix here.
    """
    columns, _ = sambar_run["produced"]
    gt_columns, _ = sambar_run["upstream"]
    _, gene_samples = sambar_run["gene_axes"]

    assert set(columns) < set(gene_samples)
    assert len(gene_samples) - len(columns) == 1
    assert columns == gt_columns


def test_the_run_records_its_own_provenance(sambar_run):
    manifest = sambar_run["manifest"]

    assert manifest["method"] == "SAMBAR"
    assert manifest["inputs"] and manifest["parameters"]
    assert set(manifest["artifacts"]) >= {"mt_out.csv", "pt_out.csv"}


# --- COBRA -------------------------------------------------------------------

COBRA_TOY = "/opt/netZooPy/tests/cobra"


def _assert_matches_upstream(produced, expected) -> None:
    """Apply upstream's own assertion for this method, verbatim.

    `tests/test_cobra.py` compares every component with
    `pd.testing.assert_frame_equal(..., rtol=1e-10, check_exact=False)`. Using
    that call rather than a hand-rolled bound keeps the tolerance the method
    authors' judgement about their own reference files, and it matters here:
    pandas applies its default `atol=1e-8` alongside `rtol`, which is what
    absorbs the trailing eigenvalue. With 400 samples and 4000 genes the
    covariance is rank-deficient, so that eigenvalue is zero in exact
    arithmetic and floating-point dust in practice (ours 1.3e-13, upstream
    -6.3e-14). A relative comparison against zero is undefined; upstream's
    combined criterion is the correct instrument, not a looser one.
    """
    import pandas as pd

    pd.testing.assert_frame_equal(
        pd.DataFrame(produced), pd.DataFrame(expected),
        rtol=1e-10, check_exact=False,
    )


@pytest.fixture(scope="module")
def cobra_run() -> dict[str, object]:
    """Run COBRA through the production wrapper on upstream's toy inputs.

    Two adaptations to upstream's fixture, both preserving its meaning:

    * Upstream calls `cobra.cobra(X, expression)` directly and pairs design
      rows with expression columns **by position**; its `X.csv` index is
      `1, 2, 3...` while the expression columns are `V1, V2, ...`. Our wrapper
      refuses that: it requires the design's first column to be sample IDs
      matching the expression columns exactly, so a covariate cannot be
      silently attached to the wrong sample. The fixture makes upstream's
      positional pairing explicit rather than relaxing that check.
    * Upstream's design carries an all-ones intercept column; our wrapper adds
      its own, so the fixture drops the duplicate. `psi` then has upstream's
      three rows rather than four, which is how the shapes check out below.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "python - <<'PY'\n"
                "import pandas as pd\n"
                f"e = pd.read_csv('{COBRA_TOY}/expression.csv', index_col=0)\n"
                f"x = pd.read_csv('{COBRA_TOY}/X.csv', index_col=0)\n"
                "x = x.drop(columns=[x.columns[0]])\n"
                "x.insert(0, 'sample_id', list(e.columns))\n"
                "x.to_csv('/out/design.csv', index=False)\n"
                "PY\n"
                "cd /opt/netzoo-app && python scripts/run_cobra.py"
                f" -e {COBRA_TOY}/expression.csv -d /out/design.csv -o /out"
                f" && cp {COBRA_TOY}/psi.csv {COBRA_TOY}/Q.csv"
                f" {COBRA_TOY}/D.csv {COBRA_TOY}/G.csv /out/",
            ],
            check=True, capture_output=True, timeout=900,
        )
        import numpy as np
        import pandas as pd

        components = dict(np.load(out / "components.npz"))
        upstream = {
            name: pd.read_csv(out / f"{name}.csv", index_col=0).to_numpy()
            for name in ("psi", "Q", "D", "G")
        }
    return {"components": components, "upstream": upstream}


@pytest.mark.parametrize(("component", "reference"), [("psi", "psi"), ("g", "G")])
def test_cobra_components_match_upstreams_ground_truth(cobra_run, component, reference):
    produced = cobra_run["components"][component]
    expected = cobra_run["upstream"][reference]

    assert produced.shape == expected.shape
    _assert_matches_upstream(produced, expected)


def test_cobra_eigenvalues_match_upstreams_ground_truth(cobra_run):
    """`D` is one column upstream and a vector here; the values are the check."""
    produced = cobra_run["components"]["d"]
    expected = cobra_run["upstream"]["D"].ravel()

    assert produced.shape == expected.shape
    _assert_matches_upstream(produced, expected)


def test_cobra_eigenvectors_are_compared_through_a_reconstruction(cobra_run):
    """Eigenvectors are sign-ambiguous, so `Q` is checked the way upstream does.

    Upstream's own test never compares `Q` elementwise: it reconstructs a
    covariance from `Q` and `psi` and compares that. Comparing `Q` directly
    would fail on a sign flip that changes nothing about the decomposition.
    """
    import numpy as np

    q, psi = cobra_run["components"]["Q"], cobra_run["components"]["psi"]
    q_gt, psi_gt = cobra_run["upstream"]["Q"], cobra_run["upstream"]["psi"]

    assert psi.shape[0] == psi_gt.shape[0]
    for index in range(psi_gt.shape[0]):
        _assert_matches_upstream(
            q.dot(np.diag(psi[index, :])).dot(q.T),
            q_gt.dot(np.diag(psi_gt[index, :])).dot(q_gt.T),
        )


# --- OTTER -------------------------------------------------------------------

OTTER_TOY = "/opt/netZooPy/tests/otter"

# Upstream's own OTTER test asserts `rtol=1e-10`, and this uses the same
# criterion. What it CANNOT use is upstream's `test_otter.csv`: that reference
# was produced from a *weighted* PPI matrix, while the registry commits this
# adapter to "a binary adjacency projection" (workflows/otter.yaml), so P here
# holds adjacency and not interaction confidences. Reproducing upstream's file
# would require abandoning that documented choice. The reference below is
# therefore netZooPy's own `otter()` called directly on independently
# constructed matrices -- upstream's *code* as ground truth where its *file* is
# unreachable -- which checks everything our adapter contributes: identifier
# mapping, gene and TF ordering, orientation, and the projection itself.
OTTER_BUILD = r'''
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import settings, execution
from netZooPy.otter.otter import otter

w = pd.read_csv("{toy}/w.csv", header=None).to_numpy(float)
p = pd.read_csv("{toy}/p.csv", header=None).to_numpy(float)
c = pd.read_csv("{toy}/c.csv", header=None).to_numpy(float)
tfs = [f"TF{{i:05d}}" for i in range(w.shape[0])]
genes = [f"G{{i:05d}}" for i in range(w.shape[1])]

# Upstream ships unlabeled matrices; our adapter requires identifiers, so the
# fixture attaches names to upstream's positional convention without altering
# a single value.
pd.DataFrame({{"source": np.repeat(tfs, len(genes)),
               "target": np.tile(genes, len(tfs)),
               "weight": w.ravel()}}).to_csv("/out/w_edges.csv", index=False)
pd.DataFrame({{"source": np.repeat(tfs, len(tfs)),
               "target": np.tile(tfs, len(tfs)),
               "weight": p.ravel()}}).to_csv("/out/p_edges.csv", index=False)
frame = pd.DataFrame(c, index=genes, columns=genes); frame.index.name = "gene"
frame.to_csv("/out/c_matrix.csv")

# Independently written binarization, not read from the adapter under test.
expected_p = (p > 0.0).astype(float)
np.fill_diagonal(expected_p, 1.0)
np.save("/out/reference.npy",
        otter(w.copy(), expected_p.copy(), c.copy(), Iter=1, lam=0.0035, gamma=0.335))
np.save("/out/expected_p.npy", expected_p)

# The adapter's own projection, saved so the comparison is against a matrix
# built by the code under test rather than recomputed beside it.
from netzoo_agent_core.data.otter import load_otter_inputs
np.save("/out/adapter_p.npy", load_otter_inputs(
    coexpression_file="/out/c_matrix.csv", motif_file="/out/w_edges.csv",
    ppi_file="/out/p_edges.csv").P)

settings.EXECUTE_TOOLS = True
report = execution.run_otter.invoke(dict(
    coexpression_file="/out/c_matrix.csv", motif_file="/out/w_edges.csv",
    ppi_file="/out/p_edges.csv", output_file="/out/otter_out.csv",
    lam=0.0035, gamma=0.335, iterations=1))
assert "execution completed" in report, report
'''


@pytest.fixture(scope="module")
def otter_run() -> dict[str, object]:
    """Run OTTER through the registered tool on upstream's toy matrices."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(OTTER_BUILD.format(toy=OTTER_TOY), encoding="utf-8")
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "python", "/out/build.py",
            ],
            check=True, capture_output=True, timeout=1800,
        )
        import numpy as np
        import pandas as pd

        return {
            "produced": pd.read_csv(out / "otter_out.csv", index_col=0),
            "reference": np.load(out / "reference.npy"),
            "expected_p": np.load(out / "expected_p.npy"),
            "adapter_p": np.load(out / "adapter_p.npy"),
        }


def test_otter_network_matches_netzoopy_called_directly(otter_run):
    produced, reference = otter_run["produced"], otter_run["reference"]

    assert produced.shape == reference.shape
    _assert_matches_upstream(produced.to_numpy(float), reference)


def test_otter_output_keeps_upstreams_identifier_order(otter_run):
    """A transposition or reorder would still match numerically row-by-row."""
    produced = otter_run["produced"]

    assert list(produced.index[:3]) == ["TF00000", "TF00001", "TF00002"]
    assert list(produced.columns[:3]) == ["G00000", "G00001", "G00002"]
    assert produced.index.name == "tf"


def test_otter_ppi_projection_matches_an_independent_binarization(otter_run):
    """The check that catches a projection defect at upstream's scale.

    Upstream's P written out as an edge list is a dense grid of 436,921 pairs,
    most of them weighted 0. Before the zero-weight fix the adapter projected
    every listed pair to 1.0, so 350,312 of the 436,260 off-diagonal cells
    disagreed with this independent binarization: 80.3% of the network was
    fabricated as interacting, and a fully connected PPI network stood in for a
    sparse one. Neither the routing layer nor any structural contract check can
    see that -- the request was routed correctly and every field validated.
    """
    import numpy as np

    adapter, expected = otter_run["adapter_p"], otter_run["expected_p"]

    assert adapter.shape == expected.shape == (661, 661)
    assert set(np.unique(adapter).tolist()) <= {0.0, 1.0}
    assert int((adapter != expected).sum()) == 0
    # A guard on the fixture itself: if upstream's P were dense-positive, the
    # comparison above would hold trivially and prove nothing.
    assert 0.0 in set(np.unique(expected).tolist())


# --- GIRAFFE -----------------------------------------------------------------

# Upstream's GIRAFFE test asserts `np.testing.assert_allclose(..., atol=1e-5)`,
# a different criterion from the pandas one used above, so it is applied as
# upstream writes it.
GIRAFFE_ATOL = 1e-5
GIRAFFE_BUILD = r'''
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netZooPy.panda import Panda
from netzoo_agent_core import settings, execution

# Upstream's own recipe: its GIRAFFE reference is generated from PANDA's
# intersection-mode preprocessing of the PUMA toy data, not from the raw files.
# Starting from the same preprocessed matrices isolates what this wrapper
# contributes from what PANDA's preprocessing contributes.
toy = "/opt/netZooPy/tests/puma/ToyData"
panda = Panda(f"{toy}/ToyExpressionData.txt", f"{toy}/ToyMotifData.txt",
              f"{toy}/ToyPPIData.txt", modeProcess="intersection",
              with_header=False, process_data_only=True)
expression = np.asarray(panda.expression, dtype=float)
motif = np.asarray(panda.motif_matrix_unnormalized, dtype=float)   # TF-by-gene
ppi = np.asarray(panda.ppi_matrix, dtype=float)

genes = [f"G{i:05d}" for i in range(expression.shape[0])]
samples = [f"S{i:03d}" for i in range(expression.shape[1])]
tfs = [f"TF{i:05d}" for i in range(motif.shape[0])]
pd.DataFrame(expression, index=genes, columns=samples).rename_axis("gene").to_csv(
    "/out/expression.tsv", sep="\t")
pd.DataFrame(motif, index=tfs, columns=genes).rename_axis("tf").to_csv(
    "/out/motif.tsv", sep="\t")
pd.DataFrame(ppi, index=tfs, columns=tfs).rename_axis("tf").to_csv(
    "/out/ppi.tsv", sep="\t")

settings.EXECUTE_TOOLS = True
report = execution.run_giraffe.invoke(dict(
    expression_file="/out/expression.tsv", motif_file="/out/motif.tsv",
    ppi_file="/out/ppi.tsv", output_file="/out/giraffe.tsv"))
assert "API execution completed" in report, report
'''


@pytest.fixture(scope="module")
def giraffe_run() -> dict[str, object]:
    """Run GIRAFFE through the registered tool on upstream's toy inputs."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(GIRAFFE_BUILD, encoding="utf-8")
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "python /out/build.py"
                " && cp /opt/netZooPy/tests/giraffe/Toygiraffe_R_hat.txt"
                " /opt/netZooPy/tests/giraffe/Toygiraffe_TFA_hat.txt /out/",
            ],
            check=True, capture_output=True, timeout=1800,
        )
        import pandas as pd

        return {
            "regulation": pd.read_csv(out / "giraffe.tsv", sep="\t", index_col=0),
            "tfa": pd.read_csv(out / "giraffe.tfa.tsv", sep="\t", index_col=0),
            "regulation_gt": pd.read_csv(
                out / "Toygiraffe_R_hat.txt", sep="\t", index_col=0),
            "tfa_gt": pd.read_csv(
                out / "Toygiraffe_TFA_hat.txt", sep="\t", index_col=0, header=None),
        }


def test_giraffe_regulation_matches_upstreams_ground_truth(giraffe_run):
    """Upstream's `R_hat` is gene-by-TF; this workflow writes TF-by-gene.

    The orientation difference is the whole point of the comparison: passing the
    prior untransposed made this call fail inside the API for every input whose
    gene count differed from its TF count.
    """
    import numpy as np

    produced = giraffe_run["regulation"]
    expected = giraffe_run["regulation_gt"]

    assert produced.shape == expected.shape[::-1]
    np.testing.assert_allclose(
        expected.values, produced.to_numpy(float).T, atol=GIRAFFE_ATOL
    )


def test_giraffe_tfa_matches_upstreams_ground_truth(giraffe_run):
    import numpy as np

    produced = giraffe_run["tfa"]
    expected = giraffe_run["tfa_gt"]

    assert produced.shape == expected.shape
    np.testing.assert_allclose(
        expected.values, produced.to_numpy(float), atol=GIRAFFE_ATOL
    )


def test_giraffe_outputs_carry_the_declared_identifiers(giraffe_run):
    """A transposed write would still compare equal after a transpose above."""
    regulation, tfa = giraffe_run["regulation"], giraffe_run["tfa"]

    assert regulation.index.name == "tf_id"
    assert list(regulation.index[:2]) == ["TF00000", "TF00001"]
    assert list(regulation.columns[:2]) == ["G00000", "G00001"]
    assert list(tfa.index[:2]) == ["TF00000", "TF00001"]
    assert list(tfa.columns[:2]) == ["S000", "S001"]


# --- CONDOR ------------------------------------------------------------------

CONDOR_BUILD = r'''
import os, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

# Upstream's tutorial CSV omits a name for its leading R index column, so its
# header carries three names while the rows carry four fields, and its columns
# are named for the study (pollinator/plant/interactions) rather than for the
# contract. The fixture rewrites it as the documented three columns without
# changing a value.
network = pd.read_csv("/opt/netZooPy/tutorials/condor/toynetwork.csv", index_col=0)
network.columns = ["source", "target", "weight"]
network.to_csv("/out/toynetwork.csv", index=False)

configure_runtime(EXECUTE_TOOLS=True)
for run in ("first", "second"):
    os.makedirs(f"/out/{run}", exist_ok=True)
    report = execution.run_condor.invoke(dict(
        network_file="/out/toynetwork.csv", output_dir=f"/out/{run}", prefix="condor"))
    assert os.listdir(f"/out/{run}"), report
'''


@pytest.fixture(scope="module")
def condor_run() -> dict[str, object]:
    """Run CONDOR twice through the registered tool on upstream's toy network."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(CONDOR_BUILD, encoding="utf-8")
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "python /out/build.py && cp /opt/netZooPy/tests/condor/*.txt /out/",
            ],
            check=True, capture_output=True, timeout=900,
        )
        import pandas as pd

        def membership(directory: str, side: str):
            frame = pd.read_csv(out / directory / f"condor-{side}_memb.tsv", sep="\t")
            return frame.set_index(side)["community"]

        def reference(name: str, side: str):
            return pd.read_csv(out / name, index_col=0).set_index(side)["community"]

        return {
            "first": {side: membership("first", side) for side in ("tar", "reg")},
            "second": {side: membership("second", side) for side in ("tar", "reg")},
            "gt": {side: reference(f"gh_{side}_memb.txt", side) for side in ("tar", "reg")},
            "gt_igraph9": {
                side: reference(f"gh_{side}_memb_v9igraph.txt", side)
                for side in ("tar", "reg")
            },
        }


def _same_partition(left, right) -> bool:
    """Whether two labellings induce the same partition, ignoring label names.

    Community numbers are arbitrary, so this is the equivalence that carries
    scientific meaning: every one of our communities maps onto exactly one of
    theirs and vice versa.
    """
    import pandas as pd

    table = pd.crosstab(left, right).astype(bool)
    return bool(table.sum(axis=1).max() == 1 and table.sum(axis=0).max() == 1)


@pytest.mark.parametrize("side", ["tar", "reg"])
def test_condor_membership_matches_upstreams_ground_truth(condor_run, side):
    """Upstream compares these membership files label-for-label; so does this."""
    import pandas as pd

    produced = condor_run["first"][side]
    expected = condor_run["gt"][side]

    assert set(produced.index) == set(expected.index)
    pd.testing.assert_series_equal(
        produced.loc[expected.index], expected, check_exact=False, check_names=False
    )


@pytest.mark.parametrize("side", ["tar", "reg"])
def test_condor_partition_survives_the_igraph_version_upstream_hedged_against(
    condor_run, side
):
    """Upstream ships a second reference for igraph 9, and this image has 1.0.0.

    The two references do not agree label-for-label, which is why upstream keeps
    both. They do describe the same partition: the version difference changes
    community *numbering*, not which nodes group together. Asserting the
    partition rather than the labels states the claim that actually holds, and
    is the claim a biologist depends on.
    """
    produced = condor_run["first"][side]
    other_version = condor_run["gt_igraph9"][side]

    assert not (produced.loc[other_version.index] == other_version).all(), (
        "labels now agree with the igraph 9 reference; this test's premise, "
        "that the two references differ only by numbering, needs rechecking"
    )
    assert _same_partition(produced.loc[other_version.index], other_version)


@pytest.mark.parametrize("side", ["tar", "reg"])
def test_condor_is_deterministic_across_runs(condor_run, side):
    """Community detection is randomised in general; this wrapper's is not."""
    import pandas as pd

    pd.testing.assert_series_equal(
        condor_run["first"][side], condor_run["second"][side]
    )
