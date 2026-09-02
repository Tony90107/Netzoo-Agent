"""Opt-in release regression for the real SAMBAR Docker entry point."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
IMAGE = os.environ.get("NETZOO_IMAGE", "netzoo_agent:latest")
RUN_DOCKER_TESTS = os.environ.get("NETZOO_RUN_DOCKER_TESTS") == "1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.skipif(
    not RUN_DOCKER_TESTS or shutil.which("docker") is None,
    reason="set NETZOO_RUN_DOCKER_TESTS=1 to run the SAMBAR image regression",
)
def test_current_image_executes_sambar_and_validates_declared_artifacts():
    runtime_files = {
        "/opt/netzoo-app/scripts/run_sambar.py": ROOT / "scripts" / "run_sambar.py",
        "/opt/netzoo-app/scripts/netzoo_agent_core/data/sambar.py": (
            ROOT / "scripts" / "netzoo_agent_core" / "data" / "sambar.py"
        ),
        "/opt/netzoo-app/scripts/netzoo_agent_core/data/artifacts.py": (
            ROOT / "scripts" / "netzoo_agent_core" / "data" / "artifacts.py"
        ),
    }
    image_hashes = subprocess.run(
        ["docker", "run", "--rm", IMAGE, "sha256sum", *runtime_files],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.splitlines()
    actual = {
        image_path: digest
        for digest, image_path in (line.split(maxsplit=1) for line in image_hashes)
    }
    expected = {
        image_path: _sha256(host_path)
        for image_path, host_path in runtime_files.items()
    }
    assert actual == expected, "Docker image must be rebuilt from the current SAMBAR runtime"

    smoke = r'''
import json
import subprocess

from netzoo_agent_core import TaskDecision
from netzoo_agent_core.data.artifacts import validate_output_artifacts

args = [
    "run-sambar",
    "-m", "/work/data/sambar-toy/mutation.csv",
    "-e", "/work/data/sambar-toy/exon_size.csv",
    "-g", "/work/data/sambar-toy/cancer_genes.txt",
    "-p", "/work/data/sambar-toy/pathways.gmt",
    "-o", "/tmp/sambar-smoke",
    "--kmin", "2",
    "--kmax", "3",
]
subprocess.run(args, check=True)
decision = TaskDecision(
    action="run_sambar",
    in_scope=True,
    should_execute=True,
    confidence=1.0,
    reason="container smoke regression",
    mutation_file=args[2],
    exon_size_file=args[4],
    cancer_gene_file=args[6],
    pathway_file=args[8],
    output_dir=args[10],
    kmin=2,
    kmax=3,
)
result = validate_output_artifacts("run_sambar", decision)
print(json.dumps(result.model_dump(), sort_keys=True))

# Official netZooPy ToyData regression.  The upstream implementation legitimately
# omits samples whose mutation-score row is all zero from pt_out.csv; the validator
# must accept that subset while still rejecting unknown or non-zero omissions.
official_args = [
    "run-sambar",
    "-m", "/work/data/sambar-official-toy/mut.ucec.csv",
    "-e", "/work/data/sambar-official-toy/esizef.csv",
    "-g", "/work/data/sambar-official-toy/genes.txt",
    "-p", "/work/data/sambar-official-toy/h.all.v6.1.symbols.gmt",
    "-o", "/tmp/sambar-official",
    "--kmin", "2",
    "--kmax", "4",
    "--no-cluster",
]
subprocess.run(official_args, check=True)
official_decision = TaskDecision(
    action="run_sambar",
    in_scope=True,
    should_execute=True,
    confidence=1.0,
    reason="official netZooPy ToyData regression",
    mutation_file=official_args[2],
    exon_size_file=official_args[4],
    cancer_gene_file=official_args[6],
    pathway_file=official_args[8],
    output_dir=official_args[10],
    kmin=2,
    kmax=4,
    cluster=False,
)
official_result = validate_output_artifacts("run_sambar", official_decision)
print(json.dumps(official_result.model_dump(), sort_keys=True))
raise SystemExit(0 if result.ok and official_result.ok else 2)
'''
    completed = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-e",
            "PYTHONPATH=/work/scripts:/opt/netZooPy:/opt/netzoo-harness",
            "-v",
            f"{ROOT}:/work:ro",
            IMAGE,
            "python",
            "-c",
            smoke,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '"ok": true' in completed.stdout
    for artifact in (
        "manifest.json",
        "mt_out.csv",
        "pt_out.csv",
        "clustergroups.csv",
        "dist_matrix.csv",
    ):
        assert artifact in completed.stdout
    assert '"sambar_pathway_score_samples": 247' in completed.stdout
