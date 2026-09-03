"""Test the test gate itself using isolated, intentionally skipped tests."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("strict,expected", [(False, 0), (True, 1)])
def test_optional_skip_gate_reports_unexecuted_coverage(strict, expected, tmp_path):
    # Isolate collection from all project tests and any configured provider.
    (tmp_path / "conftest.py").write_text(Path(__file__).with_name("conftest.py").read_text())
    (tmp_path / "test_skipped.py").write_text(
        'import pytest\n\n@pytest.mark.skip(reason="intentional gate fixture")\ndef test_not_run():\n    pass\n'
    )
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *( ["--fail-on-skip"] if strict else []), str(tmp_path)],
        cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30,
    )

    assert result.returncode == expected, result.stdout + result.stderr
    assert "1 skipped" in result.stdout
    assert ("--fail-on-skip detected" in result.stdout) is strict


def test_skip_gate_also_catches_collection_skips(tmp_path):
    (tmp_path / "conftest.py").write_text(Path(__file__).with_name("conftest.py").read_text())
    (tmp_path / "test_skipped.py").write_text(
        'import pytest\npytest.skip("missing integration dependency", allow_module_level=True)\n'
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--fail-on-skip", str(tmp_path)],
        cwd=tmp_path,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""},
        text=True, capture_output=True, timeout=30,
    )

    assert result.returncode != 0
    assert "--fail-on-skip detected" in result.stdout
