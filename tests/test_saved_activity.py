"""Saved activity stays read-only, isolated, paged and faithful to its chain."""
import json
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core import settings
from netzoo_agent_core.server.app import create_app
from netzoo_agent_core.trace_store import LocalTraceStore

AUTH = {"Authorization": "Bearer saved-test"}


@pytest.fixture
def saved(tmp_path, monkeypatch):
    root = tmp_path / "traces"
    monkeypatch.setattr(settings, "TRACE_ROOT", root)
    store = LocalTraceStore(root)
    run = store.start_run({"session_id": "earlier", "profile_id": "default"})
    store.append(run, "run.started", "cli", {})
    store.append(run, "tool.completed", "execute_tool", {"action": "run_panda", "status": "dry_run", "artifacts": ["outputs/demo.tsv"]})
    store.finish_run(run, "completed", {})
    with TestClient(create_app(token="saved-test")) as client:
        yield client, store, str(run)


def test_auth_and_bounded_parameters(saved):
    client, _, run = saved
    url = f"/v1/history/earlier/activity/{run}"
    assert client.get(url).status_code == 401
    assert client.get("/v1/history/earlier/activity").status_code == 401
    assert client.get(url, params={"limit": 201}, headers=AUTH).status_code == 422
    assert client.get(url, params={"after_sequence": -1}, headers=AUTH).status_code == 422


def test_pages_reassemble_original_events_without_writes(saved):
    client, store, run = saved
    path = store.run_path(run) / "events.jsonl"
    before = path.read_bytes()
    url = f"/v1/history/earlier/activity/{run}"
    first = client.get(url, params={"limit": 2}, headers=AUTH).json()
    assert [e["sequence"] for e in first["events"]] == [1, 2]
    assert first["next_sequence"] == 2
    last = client.get(url, params={"after_sequence": 2, "version": first["version"]}, headers=AUTH).json()
    assert last["next_sequence"] is None and not last["incomplete"]
    assert first["events"] + last["events"] == [e.model_dump(mode="json") for e in store.read_events(run)]
    assert path.read_bytes() == before


def test_wrong_session_invalid_uuid_and_stale_snapshot(saved):
    client, _, run = saved
    assert client.get(f"/v1/history/other/activity/{run}", headers=AUTH).status_code == 404
    assert client.get("/v1/history/earlier/activity/not-a-uuid", headers=AUTH).status_code == 400
    assert client.get(f"/v1/history/earlier/activity/{run}", params={"version": "old"}, headers=AUTH).status_code == 409
    assert client.get(f"/v1/history/earlier/activity/{run}", params={"after_sequence": 999}, headers=AUTH).status_code == 400


def test_manifest_listing_links_only_matching_session_and_pages(saved):
    client, store, first = saved
    second = store.start_run({"session_id": "earlier", "profile_id": "default"})
    store.start_run({"session_id": "other", "profile_id": "default"})
    page = client.get("/v1/history/earlier/activity", params={"limit": 1}, headers=AUTH).json()
    assert page["total"] == 2 and page["has_more"]
    assert page["runs"][0]["run_id"] == str(second)
    last = client.get("/v1/history/earlier/activity", params={"limit": 1, "offset": 1}, headers=AUTH).json()
    assert last["runs"][0]["run_id"] == first and not last["has_more"]
    assert client.get("/v1/history/legacy/activity", headers=AUTH).json()["runs"] == []


@pytest.mark.parametrize("damage", ["hash", "truncate", "append"])
def test_damaged_chain_is_explicit_and_never_repaired(saved, damage):
    client, store, run = saved
    path = store.run_path(run) / "events.jsonl"
    lines = path.read_text().splitlines()
    if damage == "hash":
        changed = json.loads(lines[1]); changed["payload"]["status"] = "success"
        lines[1] = json.dumps(changed)
    elif damage == "truncate":
        lines = lines[:1]
    else:
        lines.append(lines[-1])
    path.write_text("\n".join(lines) + "\n")
    before = path.read_bytes()
    result = client.get(f"/v1/history/earlier/activity/{run}", headers=AUTH).json()
    assert result["incomplete"] and result["note"] and result["next_sequence"] is None
    assert len(result["events"]) == (3 if damage == "append" else 1)
    assert path.read_bytes() == before


@pytest.mark.parametrize("name", ["manifest.json", "events.jsonl"])
def test_activity_rejects_symlinked_files(saved, tmp_path, name):
    client, store, run = saved
    file = store.run_path(run) / name
    outside = tmp_path / "outside"
    file.rename(outside); file.symlink_to(outside)
    assert client.get(f"/v1/history/earlier/activity/{run}", headers=AUTH).status_code == 404


def test_missing_metadata_disclosed(saved):
    client, store, run = saved
    path = store.run_path(run) / "manifest.json"
    path.write_text("broken")
    page = client.get("/v1/history/earlier/activity", headers=AUTH).json()
    assert not page["runs"] and page["unavailable_metadata"] == 1
    assert client.get(f"/v1/history/earlier/activity/{run}", headers=AUTH).status_code == 404


def test_oversized_record_stops_without_reading_the_whole_file(saved, monkeypatch):
    from netzoo_agent_core.server import activity
    client, _, run = saved
    monkeypatch.setattr(activity, "MAX_EVENT_BYTES", 50)
    result = client.get(f"/v1/history/earlier/activity/{run}", headers=AUTH).json()
    assert result["incomplete"] and "oversized" in result["note"]
    assert result["events"] == [] and result["next_sequence"] is None


def test_oversized_run_has_an_explicit_preview_limit(saved):
    from netzoo_agent_core.server import activity
    client, store, run = saved
    with (store.run_path(run) / "events.jsonl").open("r+b") as stream:
        stream.truncate(activity.MAX_RUN_BYTES + 1)
    response = client.get(f"/v1/history/earlier/activity/{run}", headers=AUTH)
    assert response.status_code == 413 and "64 MiB" in response.json()["detail"]
