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


def _in_container(argv: list[str], *, timeout: int) -> subprocess.CompletedProcess:
    """Run one command in the pinned image, and say why when it fails.

    `check=True` raises `CalledProcessError`, whose message carries the exit
    code and the whole argv but not the container's own stderr, and pytest
    prints that message and nothing more. Two reference runs failed exactly that
    way during a full-gate pass -- both passed when run on their own -- and
    nothing recorded anywhere could say what had differed. A numeric check whose
    failures are undiagnosable is not much of a check.

    The tail is bounded because a netZooPy traceback can be long, and it is the
    end of it that says what went wrong.
    """
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise AssertionError(
            f"the pinned image exited {result.returncode}.\n"
            f"--- container stderr (last 2000 characters) ---\n"
            f"{result.stderr[-2000:] or '(the container wrote nothing to stderr)'}"
        )
    return result


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
        _in_container(
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
            timeout=900,
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
        _in_container(
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
            timeout=900,
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
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "python", "/out/build.py",
            ],
            timeout=1800,
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
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "python /out/build.py"
                " && cp /opt/netZooPy/tests/giraffe/Toygiraffe_R_hat.txt"
                " /opt/netZooPy/tests/giraffe/Toygiraffe_TFA_hat.txt /out/",
            ],
            timeout=1800,
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
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "python /out/build.py && cp /opt/netZooPy/tests/condor/*.txt /out/",
            ],
            timeout=900,
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


# --- LIONESS -------------------------------------------------------------------

# Upstream's own `test_lioness.py` compares its ground-truth fixtures
# (`tests/lioness/lioness.1.npy`, `lioness.1.coexpression.npy`) against a
# `Panda`/`Lioness` construction that passes `modeProcess="legacy"` explicitly.
# Our production path (`docker/run-lioness panda|coexpression` ->
# `netZooPy/panda/run_panda.py`) never sets `modeProcess`, so it gets `Panda`'s
# own default, `"union"` -- a different gene/TF intersection policy that would
# make those fixtures the wrong ground truth (comparing two different networks,
# not validating the same one). The same is true for LIONESS-PUMA's toy run.
#
# So this follows the OTTER/GIRAFFE precedent instead of the SAMBAR/COBRA one:
# where upstream's *file* doesn't match what we actually run, upstream's *code*
# called with our production defaults is the ground truth. Each build script
# below constructs `Panda`/`Puma` + `Lioness`/`LionessPuma` directly, copying
# `run_panda.py`/`run_puma.py`'s own argument list verbatim, and compares that
# against the registered tool run through the real CLI wrapper. The tolerance
# is `np.allclose`'s default (`rtol=1e-05, atol=1e-08`) because that is what
# upstream's own three real assertions use (test_lioness.py lines 127, 148,
# 161) -- they call `np.allclose(gt, res)` with no explicit tolerance, so the
# default *is* the authors' judgement, not an omission to fill in ourselves.
LIONESS_TOY = "/opt/netZooPy/tests/puma/ToyData"

LIONESS_PANDA_BUILD = r'''
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netZooPy.panda.panda import Panda
from netZooPy.lioness.lioness import Lioness
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

# Ground truth: netZooPy/panda/run_panda.py's own argument list, verbatim,
# followed by netZooPy/lioness/lioness.py's export path for a lioness_file.
panda_obj = Panda(f"{{toy}}/ToyExpressionData.txt", f"{{toy}}/ToyMotifData.txt",
                   f"{{toy}}/ToyPPIData.txt", save_tmp=True, remove_missing=False,
                   keep_expression_matrix=True, save_memory=False)
panda_obj.save_panda_results("/out/reference_panda.txt")
Lioness(panda_obj, export_filename="/out/reference.csv")

# Produced: the registered tool, through the real CLI wrapper.
configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_lioness_panda.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    output_file="/out/panda_out.txt",
    lioness_output="/out/produced.csv"))
assert "Exit code: 0" in report, report
'''

LIONESS_PUMA_BUILD = r'''
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netZooPy.puma import Puma
from netZooPy.lioness.lioness_for_puma import LionessPuma
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

# Ground truth: netZooPy/puma/run_puma.py's own argument list, verbatim.
# `.txt` rather than `.csv`: LionessPuma.save_lioness_results writes a plain
# `np.savetxt` body with no header at all, and only the `.txt` case keeps the
# body's own delimiter (space) consistent with the header our production path
# adds afterwards (docker/add-puma-lioness-header always joins the header
# with spaces, regardless of the file's chosen delimiter -- a `.csv`/`.tsv`
# output would carry a space-delimited header over a comma/tab-delimited
# body, which is a separate finding, not something to route around silently).
puma_obj = Puma(f"{{toy}}/ToyExpressionData.txt", f"{{toy}}/ToyMotifData.txt",
                 f"{{toy}}/ToyPPIData.txt", f"{{toy}}/ToyMiRList.txt",
                 save_tmp=True, remove_missing=False, keep_expression_matrix=True)
puma_obj.save_puma_results("/out/reference_puma.txt")
lioness_obj = LionessPuma(puma_obj)
lioness_obj.save_lioness_results("/out/reference.txt")

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_lioness_puma.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    mirna_file=f"{{toy}}/ToyMiRList.txt",
    output_file="/out/puma_out.txt",
    lioness_output="/out/produced.txt"))
assert "Exit code: 0" in report, report
'''

LIONESS_COEXPRESSION_BUILD = r'''
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netZooPy.panda.panda import Panda
from netZooPy.lioness.lioness import Lioness
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

# Ground truth: run_panda.py's argument list with motif omitted, which is how
# `docker/run-lioness coexpression` invokes the same legacy script.
panda_obj = Panda(f"{{toy}}/ToyExpressionData.txt", None,
                   f"{{toy}}/ToyPPIData.txt", save_tmp=True, remove_missing=False,
                   keep_expression_matrix=True, save_memory=False)
panda_obj.save_panda_results("/out/reference_panda.txt")
Lioness(panda_obj, export_filename="/out/reference.csv")

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_lioness_coexpression.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    output_file="/out/coexpression_out.txt",
    lioness_output="/out/produced.csv"))
assert "Exit code: 0" in report, report
'''


def _run_lioness_build(
    build_script: str,
    *,
    produced_name: str = "produced.csv",
    reference_name: str = "reference.csv",
    reference_has_header: bool = True,
    id_columns: tuple[str, str] = ("tf", "gene"),
) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(
            build_script.format(toy=LIONESS_TOY), encoding="utf-8"
        )
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "python", "/out/build.py",
            ],
            timeout=1800,
        )
        import pandas as pd

        sep = r"\s+" if not reference_has_header else ","
        produced = pd.read_csv(out / produced_name, sep=sep, engine="python")
        if reference_has_header:
            reference = pd.read_csv(out / reference_name, sep=sep, engine="python")
        else:
            # LionessPuma.save_lioness_results writes no header at all; the
            # CLI wrapper's header (regulator, gene, prior_weight, samples...)
            # is added afterwards by docker/add-puma-lioness-header, not by
            # netZooPy itself, so the reference file needs the same names
            # assigned by hand to compare like-for-like.
            reference = pd.read_csv(
                out / reference_name, sep=r"\s+", engine="python", header=None
            )
            reference.columns = list(produced.columns)
    return {"produced": produced, "reference": reference, "id_columns": id_columns}


@pytest.fixture(scope="module")
def lioness_panda_run() -> dict[str, object]:
    return _run_lioness_build(LIONESS_PANDA_BUILD, id_columns=("tf", "gene"))


@pytest.fixture(scope="module")
def lioness_puma_run() -> dict[str, object]:
    return _run_lioness_build(
        LIONESS_PUMA_BUILD,
        produced_name="produced.txt",
        reference_name="reference.txt",
        reference_has_header=False,
        id_columns=("regulator", "gene"),
    )


@pytest.fixture(scope="module")
def lioness_coexpression_run() -> dict[str, object]:
    return _run_lioness_build(LIONESS_COEXPRESSION_BUILD, id_columns=("gene1", "gene2"))


def _assert_lioness_tables_match(produced, reference, id_columns) -> None:
    """Align on the (regulator, gene) identifier columns, then compare values.

    Both files are written pre-sorted by their own identifier columns (see
    `export_lioness_table` for PANDA/co-expression and `LionessPuma`'s column
    stack for PUMA), but this re-sorts explicitly rather than depending on
    that -- the point of the comparison is the values, not incidental row
    order agreement.
    """
    import numpy as np

    assert list(produced.columns) == list(reference.columns)
    produced_sorted = produced.sort_values(by=id_columns).reset_index(drop=True)
    reference_sorted = reference.sort_values(by=id_columns).reset_index(drop=True)
    assert list(produced_sorted[id_columns[0]]) == list(reference_sorted[id_columns[0]])
    assert list(produced_sorted[id_columns[1]]) == list(reference_sorted[id_columns[1]])

    value_columns = [c for c in produced.columns if c not in id_columns]
    produced_values = produced_sorted[value_columns].to_numpy(dtype=float)
    reference_values = reference_sorted[value_columns].to_numpy(dtype=float)
    assert produced_values.shape == reference_values.shape
    assert np.allclose(reference_values, produced_values), (
        f"largest disagreement: "
        f"{np.max(np.abs(produced_values - reference_values)):.3e}"
    )


def test_lioness_panda_matches_netzoopy_called_directly(lioness_panda_run):
    _assert_lioness_tables_match(
        lioness_panda_run["produced"], lioness_panda_run["reference"],
        id_columns=list(lioness_panda_run["id_columns"]),
    )


def test_lioness_puma_matches_netzoopy_called_directly(lioness_puma_run):
    _assert_lioness_tables_match(
        lioness_puma_run["produced"], lioness_puma_run["reference"],
        id_columns=list(lioness_puma_run["id_columns"]),
    )


def test_lioness_coexpression_matches_netzoopy_called_directly(lioness_coexpression_run):
    _assert_lioness_tables_match(
        lioness_coexpression_run["produced"], lioness_coexpression_run["reference"],
        id_columns=list(lioness_coexpression_run["id_columns"]),
    )


def test_a_failed_container_run_says_what_the_container_said():
    """Otherwise a numeric check that breaks cannot be diagnosed at all.

    Two reference runs failed during a full-gate pass and passed when run alone,
    and the only thing recorded was `returned non-zero exit status 1` -- the
    container's own stderr was captured and then dropped. This is cheap: one
    container, one deliberate failure.
    """
    with pytest.raises(AssertionError) as raised:
        _in_container(
            ["docker", "run", "--rm", IMAGE, "python", "-c",
             "import sys; sys.stderr.write('netzoo-diagnostic-marker'); sys.exit(3)"],
            timeout=120,
        )

    assert "exited 3" in str(raised.value)
    assert "netzoo-diagnostic-marker" in str(raised.value)


# --- PANDA against upstream's MATLAB ground truth ----------------------------

PANDA_TOY = "/opt/netZooPy/tests/puma/ToyData"
PANDA_GT = "/opt/netZooPy/tests/panda/panda_gt_matlab.csv"

# The flags upstream's own comparison runs under. netZooPy's CLI is a thin
# constructor call -- `command_line.panda` builds `Panda(...)` from its options
# verbatim -- so these reproduce upstream's block 4 exactly rather than
# approximating it: save_memory gives the TF-by-gene adjacency the MATLAB file
# is in, and modeProcess=legacy is the mode that file was produced under.
PANDA_MATLAB_FLAGS = "--save_memory --mode_process legacy --save_tmp --keep_expr"

PANDA_BUILD = r'''
import sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_panda.invoke(dict(
    expression_file="{toy}/ToyExpressionData.txt",
    motif_file="{toy}/ToyMotifData.txt",
    ppi_file="{toy}/ToyPPIData.txt",
    output_file="/out/produced.txt",
    extra_args="{flags}"))
assert "Exit code: 0" in report, report
'''


@pytest.fixture(scope="module")
def panda_matlab_run() -> dict[str, object]:
    """Run PANDA through the production wrapper and read upstream's MATLAB file.

    This is the third-party comparison the capability did not have. Upstream's
    own CLI test asserts only `returncode == 0`, so nothing until now checked
    that the numbers our path produces are PANDA's numbers -- the same gap that
    let OTTER emit a silently wrong network.
    """
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(
            PANDA_BUILD.format(toy=PANDA_TOY, flags=PANDA_MATLAB_FLAGS),
            encoding="utf-8",
        )
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                f"python /out/build.py && cp {PANDA_GT} /out/ground_truth.csv",
            ],
            timeout=1800,
        )
        produced = pd.read_csv(out / "produced.txt", sep=" ", engine="python")
        produced = produced.set_index(produced.columns[0])
        ground_truth = pd.read_csv(out / "ground_truth.csv", sep=",", index_col=0, header=0)
    return {"produced": produced, "ground_truth": ground_truth}


def test_panda_network_matches_upstreams_matlab_ground_truth(panda_matlab_run):
    """Upstream's own assertion, called with its own tolerances, unchanged.

    `tests/test_panda.py` compares its legacy-mode network to this same file
    with exactly this call; copying it is what keeps the tolerance the method
    authors' and not ours.
    """
    import pandas as pd

    # Two empty frames compare equal, so the size of what was compared is
    # asserted before the comparison rather than trusted.
    assert panda_matlab_run["produced"].shape == (87, 1000)

    pd.testing.assert_frame_equal(
        panda_matlab_run["produced"], panda_matlab_run["ground_truth"],
        rtol=1e-12, atol=1e-12, check_exact=False, check_names=False,
    )


# --- PUMA against the class API the production script itself calls -----------

# Upstream's third-party reference (`tests/puma/matlablike_test_puma.txt`) is
# produced under `modeProcess="legacy"`. The production path runs netZooPy's
# legacy `run_puma.py`, which constructs `Puma(...)` without a modeProcess
# argument at all -- so it runs the class default, "union" -- and exposes no
# flag to change it. The third-party comparison is therefore unreachable
# through the wrapper as it stands, and this checks the reachable thing instead:
# that our path reproduces the class API called with the arguments that script
# passes. That is a check on our plumbing, not on PUMA's mathematics, and it is
# the kind that caught OTTER emitting a silently wrong network.
PUMA_BUILD = r'''
import sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netZooPy.puma.puma import Puma
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

# netZooPy/puma/run_puma.py line 76, verbatim: no modeProcess, save_tmp=True,
# keep_expression_matrix=bool(lioness_file) which is False with no lioness output.
reference = Puma(f"{{toy}}/ToyExpressionData.txt", f"{{toy}}/ToyMotifData.txt",
                 f"{{toy}}/ToyPPIData.txt", f"{{toy}}/ToyMiRList.txt",
                 save_tmp=True, remove_missing=False, keep_expression_matrix=False)
reference.save_puma_results("/out/reference.txt")

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_puma.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    mirna_file=f"{{toy}}/ToyMiRList.txt",
    output_file="/out/produced.txt"))
assert "Exit code: 0" in report, report
'''


@pytest.fixture(scope="module")
def puma_run() -> dict[str, object]:
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(
            PUMA_BUILD.format(toy=PANDA_TOY), encoding="utf-8"
        )
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "python", "/out/build.py",
            ],
            timeout=1800,
        )
        read = lambda name: pd.read_csv(out / name, sep=" ", header=None)  # noqa: E731
        return {"produced": read("produced.txt"), "reference": read("reference.txt")}


PUMA_GT = "/opt/netZooPy/tests/puma/matlablike_test_puma.txt"

# Upstream's reference is built under `modeProcess="legacy"`. The path could not
# select a mode until it was given one, so this file was unreachable and PUMA
# had no third-party comparison at all.
PUMA_LEGACY_BUILD = r"""
import sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_puma.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    mirna_file=f"{{toy}}/ToyMiRList.txt",
    output_file="/out/produced.txt",
    mode_process="legacy"))
assert "Exit code: 0" in report, report
"""

# The equivalence argument, run rather than asserted: the same inputs through
# the script this replaced, in its own directory because both write temp files.
PUMA_UPSTREAM_BUILD = r"""
import subprocess, sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

subprocess.run(
    ["python", "/opt/netZooPy/netZooPy/puma/run_puma.py",
     "-e", f"{{toy}}/ToyExpressionData.txt", "-m", f"{{toy}}/ToyMotifData.txt",
     "-p", f"{{toy}}/ToyPPIData.txt", "-i", f"{{toy}}/ToyMiRList.txt",
     "-o", "/out/upstream.txt"],
    check=True, cwd="/tmp",
)

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_puma.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    mirna_file=f"{{toy}}/ToyMiRList.txt",
    output_file="/out/produced.txt"))
assert "Exit code: 0" in report, report
"""


def _puma_build(script: str, copy_ground_truth: bool = False) -> dict[str, object]:
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(script.format(toy=PANDA_TOY), encoding="utf-8")
        command = "python /out/build.py"
        if copy_ground_truth:
            command += f" && cp {PUMA_GT} /out/ground_truth.txt"
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c", command,
            ],
            timeout=1800,
        )
        read = lambda name: pd.read_csv(out / name, sep=" ", header=None)  # noqa: E731
        produced = read("produced.txt")
        other = read("ground_truth.txt" if copy_ground_truth else "upstream.txt")
    return {"produced": produced, "other": other}


@pytest.fixture(scope="module")
def puma_legacy_run() -> dict[str, object]:
    return _puma_build(PUMA_LEGACY_BUILD, copy_ground_truth=True)


@pytest.fixture(scope="module")
def puma_default_vs_upstream() -> dict[str, object]:
    return _puma_build(PUMA_UPSTREAM_BUILD)


def test_the_default_path_still_reproduces_the_script_it_replaced(
    puma_default_vs_upstream,
):
    """Adding the option must move nothing, and this is the proof, not a claim.

    Value for value, not within a tolerance: the same inputs through the same
    class with the same arguments should agree exactly, and anything less would
    mean the replacement did something the original did not.
    """
    import pandas as pd

    assert len(puma_default_vs_upstream["produced"]) > 10_000

    pd.testing.assert_frame_equal(
        puma_default_vs_upstream["produced"], puma_default_vs_upstream["other"],
        check_exact=True,
    )


def test_puma_in_legacy_mode_matches_upstreams_reference_network(puma_legacy_run):
    """The comparison the fixed processing mode used to put out of reach.

    Upstream's own tolerance for this file (`rtol=1e-5`), from its own test.
    """
    import pandas as pd

    assert len(puma_legacy_run["produced"]) > 10_000

    pd.testing.assert_frame_equal(
        puma_legacy_run["produced"], puma_legacy_run["other"],
        rtol=1e-5, check_exact=False,
    )


def test_an_unknown_processing_mode_is_refused_rather_than_ignored():
    """A silent fallback would let the test above pass with the flag doing nothing.

    Then it would be pinning the default under another name, which is worse than
    having no test: it would read as evidence for something never exercised.
    """
    with pytest.raises(AssertionError) as raised:
        _in_container(
            ["docker", "run", "--rm", IMAGE, "run-puma",
             "-e", f"{PANDA_TOY}/ToyExpressionData.txt",
             "-m", f"{PANDA_TOY}/ToyMotifData.txt",
             "-p", f"{PANDA_TOY}/ToyPPIData.txt",
             "-i", f"{PANDA_TOY}/ToyMiRList.txt",
             "-o", "/tmp/out.txt", "--mode_process", "sideways"],
            timeout=300,
        )

    assert "sideways" in str(raised.value)


def test_puma_network_matches_netzoopy_called_directly(puma_run):
    """Upstream's own tolerance for PUMA (`rtol=1e-5`), taken from its test."""
    import pandas as pd

    assert puma_run["produced"].shape == puma_run["reference"].shape
    assert len(puma_run["produced"]) > 10_000, "the toy network did not build"

    pd.testing.assert_frame_equal(
        puma_run["produced"], puma_run["reference"], rtol=1e-5, check_exact=False,
    )


def test_the_two_processing_modes_actually_produce_different_networks(
    puma_legacy_run, puma_default_vs_upstream,
):
    """Without this, the legacy comparison above proves nothing.

    If union and legacy happened to agree, that test would pass with the flag
    doing nothing at all -- it would be pinning the default under another name.
    The modes combine the priors' genes and TFs differently, so they should
    disagree, and the check is that they do.
    """
    import pandas as pd

    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(
            puma_default_vs_upstream["produced"], puma_legacy_run["other"],
            rtol=1e-5, check_exact=False,
        )


# --- the two flags that used to lie, and the step that could not choose ------

LIONESS_PUMA_LEGACY_BUILD = r'''
import sys
sys.path.insert(0, "/opt/netzoo-app/scripts")
from netzoo_agent_core import execution
from netzoo_agent_core.runtime import configure_runtime

toy = "{toy}"

configure_runtime(EXECUTE_TOOLS=True)
report = execution.run_lioness_puma.invoke(dict(
    expression_file=f"{{toy}}/ToyExpressionData.txt",
    motif_file=f"{{toy}}/ToyMotifData.txt",
    ppi_file=f"{{toy}}/ToyPPIData.txt",
    mirna_file=f"{{toy}}/ToyMiRList.txt",
    output_file="/out/produced.txt",
    lioness_output="/out/lioness.txt",
    mode_process="{mode}"))
assert "Exit code: 0" in report, report
'''


def _lioness_puma_aggregate(mode: str) -> "object":
    """The aggregate PUMA network the LIONESS-PUMA path produces."""
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(
            LIONESS_PUMA_LEGACY_BUILD.format(toy=PANDA_TOY, mode=mode), encoding="utf-8"
        )
        _in_container(
            [
                "docker", "run", "--rm",
                "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                f"python /out/build.py && cp {PUMA_GT} /out/ground_truth.txt",
            ],
            timeout=1800,
        )
        return {
            "aggregate": pd.read_csv(out / "produced.txt", sep=" ", header=None),
            "ground_truth": pd.read_csv(out / "ground_truth.txt", sep=" ", header=None),
        }


@pytest.fixture(scope="module")
def lioness_puma_legacy() -> dict:
    return _lioness_puma_aggregate("legacy")


def test_the_lioness_puma_aggregate_can_now_reach_upstreams_reference(
    lioness_puma_legacy,
):
    """The step that could not choose a processing mode, compared at last.

    LIONESS-PUMA's aggregate stage ran netZooPy's legacy script, which fixed the
    mode to the class default, so upstream's own reference network -- built
    under `legacy` -- was unreachable from this path specifically. The
    sample-specific stage follows whatever the aggregate produced, so this is
    where the comparison has to happen.
    """
    import pandas as pd

    assert len(lioness_puma_legacy["aggregate"]) > 10_000

    pd.testing.assert_frame_equal(
        lioness_puma_legacy["aggregate"], lioness_puma_legacy["ground_truth"],
        rtol=1e-5, check_exact=False,
    )


def test_rm_missing_now_filters_where_upstream_says_it_can():
    """The flag works, by making upstream's own filter reachable.

    This test previously asserted the opposite -- that `--rm_missing` fails with
    an explanation -- which was the honest repair while the filter looked
    unreachable. It is reachable: `Puma` defines `__remove_missing`, and only the
    name mangling in `Panda.processData` (which `Puma` does not inherit from)
    kept it from being called. Aliasing one mangled name to the other runs
    netZooPy's own code; no filtering logic was added here.

    The filtered network has to differ from the unfiltered one, or the flag is
    still doing nothing -- just failing to do it in a new way.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        _in_container(
            [
                "docker", "run", "--rm", "-v", f"{out}:/out",
                "-v", f"{ROOT / 'scripts'}:/opt/netzoo-app/scripts:ro",
                IMAGE, "sh", "-c",
                "cd /tmp && "
                f"run-puma -e {PANDA_TOY}/ToyExpressionData.txt "
                f"-m {PANDA_TOY}/ToyMotifData.txt -p {PANDA_TOY}/ToyPPIData.txt "
                f"-i {PANDA_TOY}/ToyMiRList.txt -o /out/plain.txt && "
                f"run-puma -e {PANDA_TOY}/ToyExpressionData.txt "
                f"-m {PANDA_TOY}/ToyMotifData.txt -p {PANDA_TOY}/ToyPPIData.txt "
                f"-i {PANDA_TOY}/ToyMiRList.txt -o /out/filtered.txt "
                "--mode_process legacy -r",
            ],
            timeout=1800,
        )
        plain = (out / "plain.txt").read_text().splitlines()
        filtered = (out / "filtered.txt").read_text().splitlines()

    # 87 TFs by 1000 genes, and by the 913 that survive the motif prior -- the
    # same 913 PANDA keeps, which the test below pins independently.
    assert len(plain) == 87 * 1000
    assert len(filtered) == 87 * 913


def test_rm_missing_is_refused_in_the_modes_that_cannot_honour_it():
    """netZooPy's own docstring limits the filter to `legacy`.

    The other modes do not ignore it -- they fail deep inside the priors with a
    `TypeError` about integral indices. Refusing up front states a documented
    limit instead of surfacing it as an accident.
    """
    with pytest.raises(AssertionError) as raised:
        _in_container(
            ["docker", "run", "--rm", IMAGE, "run-puma",
             "-e", f"{PANDA_TOY}/ToyExpressionData.txt",
             "-m", f"{PANDA_TOY}/ToyMotifData.txt",
             "-p", f"{PANDA_TOY}/ToyPPIData.txt",
             "-i", f"{PANDA_TOY}/ToyMiRList.txt",
             "-o", "/tmp/out.txt", "-r"],
            timeout=600,
        )

    assert "--mode_process legacy" in str(raised.value)


def test_panda_still_honours_the_same_flag():
    """The control: the breakage is netZooPy's, and specific to PUMA.

    Without this, "PUMA cannot do it" could equally mean we broke something.
    PANDA filters 1000 genes down to 913 with the same option.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "build.py").write_text(
            "from netZooPy.panda.panda import Panda\n"
            f'obj = Panda("{PANDA_TOY}/ToyExpressionData.txt", '
            f'"{PANDA_TOY}/ToyMotifData.txt", "{PANDA_TOY}/ToyPPIData.txt", '
            "modeProcess='legacy', save_tmp=True, remove_missing=True, "
            "keep_expression_matrix=False)\n"
            'open("/out/shape.txt", "w").write(repr(obj.panda_network.shape))\n',
            encoding="utf-8",
        )
        _in_container(
            ["docker", "run", "--rm", "-v", f"{out}:/out", IMAGE,
             "sh", "-c", "cd /tmp && python /out/build.py"],
            timeout=900,
        )
        assert (out / "shape.txt").read_text() == "(87, 913)"
