"""The daemon serves the browser build of the window without loosening any API route."""
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core.server.app import create_app


def test_the_web_build_is_served_and_the_api_still_needs_the_token(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>NetZoo Agent</title>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('ui')")
    monkeypatch.setenv("NETZOO_WEB_UI_DIR", str(tmp_path))
    browser = TestClient(create_app(token="web-ui-token"))
    assert "NetZoo Agent" in browser.get("/").text
    assert browser.get("/assets/app.js").status_code == 200
    assert browser.get("/health").json()["status"] == "ok"
    assert browser.get("/v1/sessions").status_code == 401
    assert browser.get("/v1/sessions", headers={"Authorization": "Bearer web-ui-token"}).status_code == 200


def test_without_a_web_build_nothing_is_served_at_the_root(monkeypatch, tmp_path):
    monkeypatch.setenv("NETZOO_WEB_UI_DIR", str(tmp_path))  # no index.html: a half-built image
    assert TestClient(create_app(token="t")).get("/").status_code == 404
    monkeypatch.delenv("NETZOO_WEB_UI_DIR")
    assert TestClient(create_app(token="t")).get("/").status_code == 404
