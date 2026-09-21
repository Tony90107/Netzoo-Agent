from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.runtime_constraints import (  # noqa: E402
    runtime_control_constraints,
)


def test_otter_gpu_constraint_is_shared_as_typed_runtime_policy():
    constraints = runtime_control_constraints("run_otter")

    computing = constraints["computing"]
    assert computing.issue("cpu") is None
    assert computing.issue("gpu") == (
        "OTTER computing=gpu is not enabled by this Docker runtime; "
        "use computing=cpu."
    )
    assert computing.fallback == "cpu"


def test_unconstrained_workflow_has_no_runtime_control_policy():
    assert runtime_control_constraints("run_panda") == {}
