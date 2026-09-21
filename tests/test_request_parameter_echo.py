from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.request_parameters import (  # noqa: E402
    extract_explicit_request_parameters,
    render_explicit_request_parameters,
)

_DATASET = "manual_tests/gene_existence/dataset_a"
_FILES = (
    f"{_DATASET}/expression.tsv {_DATASET}/motif.tsv {_DATASET}/ppi.tsv"
)


def test_an_output_file_is_not_captured_as_a_directory():
    """"輸出到 X" and "output to X" must not disagree about what X is."""
    chinese = extract_explicit_request_parameters(
        f"用 {_FILES} 跑 PANDA，輸出到 outputs/result.tsv"
    )
    english = extract_explicit_request_parameters(
        f"Run PANDA with {_FILES}, output to outputs/result.tsv"
    )

    assert chinese.get("output_file") == "outputs/result.tsv"
    assert english.get("output_file") == "outputs/result.tsv"
    assert "output_dir" not in chinese
    assert "output_dir" not in english


def test_a_real_directory_is_still_a_directory():
    parameters = extract_explicit_request_parameters(
        "跑 BONOBO，expression_file=data/bonobo-toy/expression.tsv，輸出資料夾 outputs/bonobo"
    )

    assert parameters["output_dir"] == "outputs/bonobo"
    assert "output_file" not in parameters


def test_listed_input_files_are_echoed_rather_than_dropped():
    """The echo promised to carry inputs forward while reporting none."""
    echo = render_explicit_request_parameters(
        f"用 {_FILES} 這三個檔案跑 PANDA，物種是 human，輸出到 outputs/result.tsv"
    )

    assert f"{_DATASET}/expression.tsv" in echo
    assert f"{_DATASET}/motif.tsv" in echo
    assert f"{_DATASET}/ppi.tsv" in echo
    assert "role not stated" in echo


def test_a_stated_role_is_not_repeated_as_a_recognized_file():
    echo = render_explicit_request_parameters(
        f"跑 PANDA，expression_file={_DATASET}/expression.tsv"
    )

    assert echo.count(f"{_DATASET}/expression.tsv") == 1
    assert "role not stated" not in echo


def test_a_request_naming_nothing_still_echoes_nothing():
    assert render_explicit_request_parameters("What can NetZoo do?") is None


def test_gpu_preference_is_extracted_as_a_typed_workflow_control():
    assert extract_explicit_request_parameters(
        "Prefer GPU acceleration if the selected workflow supports it."
    )["computing"] == "gpu"
    assert extract_explicit_request_parameters(
        "Run OTTER with computing=cpu and precision=single."
    ) == {"computing": "cpu", "precision": "single"}
