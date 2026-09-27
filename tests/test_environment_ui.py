"""Diagnostics are read-only and the new desktop routes retain token checks."""
import json
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core import environment, settings
from netzoo_agent_core.cli.slash_commands import handle_slash_command
from netzoo_agent_core.server import files
from netzoo_agent_core.server.app import create_app


def test_doctor_explains_missing_dependencies_without_secrets_or_execution(monkeypatch, tmp_path):
    def missing(_name):
        raise environment.metadata.PackageNotFoundError
    monkeypatch.setattr(environment.metadata, "distribution", missing)
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-never-print-this")
    monkeypatch.setattr(settings, "EXECUTE_TOOLS", False)
    result = handle_slash_command("/doctor")
    assert result.handled and not result.execute_once
    assert "sk-never-print-this" not in result.message
    assert "not installed" in result.message
    assert "docker compose build netzoo" in result.message
    assert settings.EXECUTE_TOOLS is False
    assert not (tmp_path / "outputs").exists()


def test_source_module_checks_use_the_actual_package_directory(monkeypatch, tmp_path):
    package = tmp_path / "netZooPy"
    package.mkdir()
    for method in environment.METHODS:
        (package / method.lower()).mkdir()
    class Distribution:
        version = "0.11.0"
        def locate_file(self, _path): return package
    monkeypatch.setattr(environment.metadata, "distribution", lambda _name: Distribution())
    monkeypatch.delenv("NETZOOPY_SRC", raising=False)
    report = environment.environment_report()
    assert report["available_methods"] == list(environment.METHODS)
    assert next(check for check in report["checks"] if check["key"] == "modules")["status"] == "passed"


@pytest.fixture
def client(monkeypatch, tmp_path):
    (tmp_path / "outputs").mkdir()
    monkeypatch.setattr(files, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    return TestClient(create_app(token="ui-test-token")), tmp_path


def test_environment_and_preview_routes_require_the_bearer_token(client, monkeypatch):
    browser, root = client
    (root / "outputs" / "net.tsv").write_text("gene\tweight\nA\t1\nB\t2\n")
    monkeypatch.setattr(files, "MAX_ROWS", 1)
    headers = {"Authorization": "Bearer ui-test-token"}
    assert browser.get("/v1/environment").status_code == 401
    assert browser.get("/v1/environment", headers=headers).status_code == 200
    assert browser.get("/v1/files/preview", params={"path": "outputs/net.tsv"}).status_code == 401
    first = browser.get("/v1/files/preview", params={"path": "outputs/net.tsv"}, headers=headers).json()
    assert first["rows"] == [["A", "1"]]
    second = browser.get("/v1/files/preview", params={"path": first["path"], "offset": first["next_offset"], "version": first["version"]}, headers=headers)
    assert second.json()["rows"] == [["B", "2"]]
    (root / "outputs" / "net.tsv").write_text("changed\n")
    stale = browser.get("/v1/files/preview", params={"path": first["path"], "version": first["version"]}, headers=headers)
    assert stale.status_code == 409
    assert browser.get("/v1/files/preview", params={"path": "outputs/missing.tsv"}, headers=headers).status_code == 404
    assert browser.get("/v1/files/preview", params={"path": "../.env"}, headers=headers).status_code == 403
    assert "ui-test-token" not in json.dumps(first)
