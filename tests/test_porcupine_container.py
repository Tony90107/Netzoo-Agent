"""Opt-in regression: the current PORCUPINE runner and R script in the image's R environment.

The repository's scripts are mounted over the image, so this checks today's code against the pinned PORCUPINE
package without a rebuild. Run with NETZOO_RUN_DOCKER_TESTS=1 (image: NETZOO_PORCUPINE_IMAGE, default
netzoo_agent:porcupine).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.data.porcupine import validate_porcupine_output  # noqa: E402

IMAGE = os.environ.get("NETZOO_PORCUPINE_IMAGE", "netzoo_agent:porcupine")
RUN_DOCKER_TESTS = os.environ.get("NETZOO_RUN_DOCKER_TESTS") == "1"
TOY = ROOT / "data" / "porcupine-toy"


def _run(output: Path, n_cores: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{ROOT / 'scripts'}:/src:ro", "-v", f"{TOY}:/in:ro", "-v", f"{output}:/out",
            "--entrypoint", "/opt/conda/envs/netzoo/bin/python", IMAGE,
            "/src/run_porcupine.py", "-n", "/in/lioness_panda_network.txt", "-p", "/in/pathways.gmt",
            "-o", "/out", "--n-permutations", "30", "--n-cores", str(n_cores), "--seed", "7",
        ],
        check=True, capture_output=True, text=True, timeout=600,
    )


@pytest.mark.skipif(
    not RUN_DOCKER_TESTS or shutil.which("docker") is None,
    reason="set NETZOO_RUN_DOCKER_TESTS=1 to run the PORCUPINE image regression",
)
def test_porcupine_runs_in_the_image_and_is_the_same_for_any_core_count(tmp_path):
    one, two = tmp_path / "one_core", tmp_path / "two_cores"
    _run(one, 1)
    _run(two, 2)
    ok, errors, _, metrics = validate_porcupine_output(str(one), str(TOY / "lioness_panda_network.txt"))
    assert ok, errors
    assert metrics["porcupine_pathways_tested"] > 0
    # The null gene sets are drawn before any PCA, so the core count cannot change them or the statistics.
    for name in ("porcupine_random_null.tsv", "porcupine_pathways.tsv"):
        assert (one / name).read_bytes() == (two / name).read_bytes(), name
