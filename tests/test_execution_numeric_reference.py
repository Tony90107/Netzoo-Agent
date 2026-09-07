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
