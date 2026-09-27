"""Log 224: BONOBO's delta and `.hdf` output match what netZooPy 0.11.0 actually does.

- With sparsify, upstream's per-edge variance uses 1/delta - 3: at delta >= 1/3
  every p-value is NaN and the thresholded network silently loses every edge,
  and delta = 0 divides by zero. Upstream also asserts `type(delta) == float`.
- Upstream writes only .h5, .csv and .txt; any other suffix is saved as .h5, so
  a `.hdf` request was always reported as missing files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.data.bonobo import load_bonobo_inputs, validate_bonobo_output  # noqa: E402
from netzoo_agent_core.execution import run_bonobo  # noqa: E402
from netzoo_agent_core.execution_bonobo import _bonobo_delta  # noqa: E402
from test_bonobo_workflow import _decision, _expression  # noqa: E402
from workflow_registry import executor_arguments  # noqa: E402


def _upstream_like_bonobo():
    """Writes files the way netZooPy 0.11.0 does: an unrecognised suffix becomes .h5."""

    class UpstreamBonobo:
        calls: list[dict] = []

        def __init__(self, expression_file):
            self.expression_file = expression_file

        def run_bonobo(self, **kwargs):
            assert kwargs.get("delta") is None or type(kwargs["delta"]) is float
            type(self).calls.append(kwargs)
            root = Path(kwargs["output_folder"])
            root.mkdir(parents=True, exist_ok=True)
            fmt = kwargs["output_fmt"]
            suffix = fmt if fmt in {".h5", ".csv", ".txt"} else ".h5"
            for sample in kwargs["sample_names"]:
                matrix = pd.DataFrame(np.eye(3), columns=["g1", "g2", "g3"])
                for stem, key, wanted in (("bonobo", "bonobo", True),
                                          ("pvals", "pvals", kwargs["sparsify"] and kwargs["save_pvals"])):
                    if not wanted:
                        continue
                    path = root / f"{stem}_{sample}{suffix}"
                    if suffix == ".h5":
                        matrix.to_hdf(path, key=key, index=False)
                    else:
                        matrix.to_csv(path, sep="\t" if suffix == ".txt" else ",", index=False)

    return UpstreamBonobo


def _run(tmp_path, execute=True, **overrides):
    """Run the tool; `delta` is passed as a tool argument, since TaskDecision
    itself already requires delta > 0 and a direct tool call does not."""
    expression = _expression(tmp_path)
    output = tmp_path / "out"
    fake = _upstream_like_bonobo()
    fake.calls = []
    delta = overrides.pop("delta", None)
    decision = _decision(expression, output, sample_names=["s2"], **overrides)
    arguments = executor_arguments("run_bonobo", decision)
    if delta is not None:
        arguments["delta"] = delta
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", execute), patch(
        "netzoo_agent_core.execution_bonobo._load_bonobo_api", return_value=(fake, "0.11.0"),
    ):
        raw = run_bonobo.invoke(arguments)
    return raw, fake, expression, output


@pytest.mark.parametrize("delta", [0.0, 1 / 3, 0.5, 1.0])
def test_sparsify_rejects_a_delta_that_empties_or_breaks_the_network(tmp_path, delta):
    raw, fake, _, output = _run(tmp_path, sparsify=True, delta=delta)

    assert "error code: BONOBO_DELTA_INVALID" in raw
    assert "below 1/3" in raw
    assert fake.calls == [] and not output.exists()


@pytest.mark.parametrize("execute", [True, False])
def test_the_delta_check_runs_before_the_dry_run_too(tmp_path, execute):
    raw, fake, _, _ = _run(tmp_path, execute=execute, sparsify=True, delta=0.5)

    assert "BONOBO_DELTA_INVALID" in raw and "dry-run" not in raw
    assert fake.calls == []


@pytest.mark.parametrize("delta", [0.0, 1.0])
def test_without_sparsify_the_whole_registered_range_is_accepted(tmp_path, delta):
    raw, fake, _, _ = _run(tmp_path, delta=delta)

    assert "API execution completed" in raw, raw
    assert fake.calls[0]["delta"] == delta and type(fake.calls[0]["delta"]) is float


@pytest.mark.parametrize("delta, expected", [(0, 0.0), (np.float64(0.1), 0.1), (0.2, 0.2), (None, None)])
def test_numeric_deltas_reach_upstream_as_python_floats(delta, expected):
    value, error = _bonobo_delta(delta, sparsify=bool(delta))

    assert error is None
    assert value == expected and (value is None or type(value) is float)


@pytest.mark.parametrize("delta", [True, float("nan"), 1.5, -0.1, "0.1"])
def test_non_numeric_or_out_of_range_deltas_are_rejected(delta):
    value, error = _bonobo_delta(delta, sparsify=False)

    assert value is None and error


def test_a_passed_delta_is_a_float_in_the_api_call(tmp_path):
    raw, fake, _, _ = _run(tmp_path, sparsify=True, delta=0.2)

    assert "API execution completed" in raw, raw
    assert type(fake.calls[0]["delta"]) is float


@pytest.mark.parametrize("save_pvals", [False, True])
def test_hdf_output_is_the_h5_file_upstream_writes(tmp_path, save_pvals):
    raw, fake, expression, output = _run(
        tmp_path, bonobo_output_format=".hdf", sparsify=True, save_pvals=save_pvals,
    )

    assert "API execution completed" in raw, raw
    assert fake.calls[0]["output_fmt"] == ".h5"
    written = sorted(path.name for path in output.iterdir() if path.name != "manifest.json")
    assert written == (["bonobo_s2.h5", "pvals_s2.h5"] if save_pvals else ["bonobo_s2.h5"])
    bundle = load_bonobo_inputs(str(expression), ["s2"], log_transformed=True, centered=True)
    valid, errors, _, _ = validate_bonobo_output(
        str(output), bundle.gene_ids, bundle.selected_sample_ids, ".hdf",
        save_pvals=save_pvals, sparsify=True,
    )
    assert valid, errors


def test_the_dry_run_says_hdf_is_written_as_h5(tmp_path):
    raw, _, _, _ = _run(tmp_path, execute=False, bonobo_output_format=".hdf")

    assert "- file format: .hdf is written as HDF5 with the .h5 suffix" in raw
    assert "bonobo_s2.h5" in raw
