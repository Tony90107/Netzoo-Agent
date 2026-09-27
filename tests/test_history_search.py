"""Searching saved sessions is paged across history, not just its first page."""
import json
import os
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core.server import history
from netzoo_agent_core.server.app import create_app

AUTH = {"Authorization": "Bearer history-search"}


@pytest.fixture
def saved(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "SESSION_ROOT", tmp_path)

    def write(name, title="Request", workflow="PANDA", status="ready", evaluation=None, results=None, at=1):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps({"session_id": name, "messages": [{"role": "user", "content": title}],
            "plan": {"workflow": workflow, "status": status}, "evaluation": evaluation,
            "tool_results": results or []}))
        os.utime(path, (at, at))

    with TestClient(create_app(token="history-search")) as client:
        yield client, write


def test_reports_execution_outcome_instead_of_ready_plan(saved):
    _, write = saved
    write("success", evaluation={"status": "completed"})
    write("failure", evaluation={"status": "failed"})
    write("preview", evaluation={"status": "completed"}, results=[{"action": "inspect_inputs", "status": "success"}, {"action": "run_panda", "status": "dry_run"}])
    statuses = {row.session_id: row.status for row in history.list_sessions()}
    assert statuses == {"success": "completed", "failure": "failed", "preview": "dry_run"}


def test_waiting_state_takes_priority_and_legacy_is_not_called_complete(saved):
    _, write = saved
    write("waiting", status="needs_input", evaluation={"status": "completed"})
    write("approval", status="needs_confirmation", evaluation={"status": "failed"})
    write("legacy")
    states = {row.session_id: row for row in history.list_sessions()}
    assert states["waiting"].status == "needs_input" and states["waiting"].resumable
    assert states["approval"].status == "needs_confirmation" and states["approval"].resumable
    assert states["legacy"].status == "ready" and not states["legacy"].resumable


def test_search_filters_before_paging_and_is_case_insensitive(saved):
    client, write = saved
    for i in range(65):
        write(f"s{i}", title=f"Earlier goal {i}", workflow="LIONESS-PUMA", evaluation={"status": "completed"}, at=i + 1)
    write("latest", title="Unrelated", evaluation={"status": "failed"}, at=100)
    page = client.get("/v1/history", params={"limit": 2, "query": "lioness-puma", "status": "completed"}, headers=AUTH).json()
    assert [r["session_id"] for r in page["sessions"]] == ["s64", "s63"]
    assert page["has_more"] and page["next_offset"] == 2
    older = client.get("/v1/history", params={"limit": 2, "offset": 64, "query": "EARLIER", "status": "completed"}, headers=AUTH).json()
    assert older["sessions"][0]["session_id"] == "s0" and not older["has_more"]
    assert older["next_offset"] is None
    assert client.get("/v1/history", params={"query": "latest"}, headers=AUTH).json()["sessions"][0]["status"] == "failed"


def test_auth_bounds_empty_results_and_bad_checkpoint(saved, tmp_path):
    client, write = saved
    write("okay")
    (tmp_path / "malformed.json").write_text("[]")
    (tmp_path / "invalid.json").write_text("{")
    assert client.get("/v1/history", params={"query": "secret"}).status_code == 401
    assert client.get("/v1/history", params={"offset": -1}, headers=AUTH).status_code == 422
    assert client.get("/v1/history", params={"status": "invented"}, headers=AUTH).status_code == 422
    response = client.get("/v1/history", params={"query": "nonexistent"}, headers=AUTH)
    assert response.status_code == 200 and response.json()["sessions"] == []
