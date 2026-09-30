"""Sessions as experiments: tags, the models they ran under, and where outputs came from."""
import json
import os
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core.server import history  # noqa: E402
from netzoo_agent_core.server.app import create_app  # noqa: E402
from netzoo_agent_core.session_meta import (  # noqa: E402
    load_meta,
    normalize_tags,
    remember_turn,
    set_tags,
)

AUTH = {"Authorization": "Bearer sessions-token"}


@pytest.fixture
def store(tmp_path, monkeypatch):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(history, "SESSION_ROOT", sessions)

    def write(name, *, title="Request", workflow="PANDA", results=None, messages=None, at=1, decision=None):
        path = sessions / f"{name}.json"
        path.write_text(json.dumps({
            "session_id": name,
            "messages": messages or [{"role": "user", "content": title}],
            "plan": {"workflow": workflow, "status": "ready", "decision": decision or {}},
            "evaluation": {"status": "completed"}, "tool_results": results or [],
        }))
        os.utime(path, (at, at))

    with TestClient(create_app(token="sessions-token")) as client:
        yield client, write, sessions


def test_tags_are_trimmed_deduplicated_bounded_and_may_be_any_language():
    assert normalize_tags([" brca ", "BRCA", "乳癌 pilot", "", "bad<tag>", "x" * 50]) == [
        "brca", "乳癌 pilot", "x" * 32]
    assert len(normalize_tags([f"t{i}" for i in range(30)])) == 12


def test_tags_round_trip_filter_the_history_and_are_counted(store):
    client, write, sessions = store
    write("a1", title="PANDA pilot", at=1)
    write("b2", title="PUMA trial", at=2)
    response = client.post("/v1/history/a1/tags", json={"tags": ["pilot", "brca"]}, headers=AUTH)
    assert response.status_code == 200 and response.json()["tags"] == ["pilot", "brca"]
    set_tags("b2", ["brca"], sessions_root=sessions)
    rows = client.get("/v1/history", params={"tag": "PILOT"}, headers=AUTH).json()["sessions"]
    assert [row["session_id"] for row in rows] == ["a1"] and rows[0]["tags"] == ["pilot", "brca"]
    # Free-text search also finds a tag.
    assert [r["session_id"] for r in client.get("/v1/history", params={"query": "brca"}, headers=AUTH).json()["sessions"]] == ["b2", "a1"]
    assert client.get("/v1/tags", headers=AUTH).json()["tags"] == [{"tag": "brca", "count": 2}, {"tag": "pilot", "count": 1}]
    # Tags live beside the checkpoint, never in it.
    assert "tags" not in json.loads((sessions / "a1.json").read_text())


def test_tagging_an_unknown_session_is_refused(store):
    client, _, _ = store
    assert client.post("/v1/history/nosuch/tags", json={"tags": ["x"]}, headers=AUTH).status_code == 404
    assert client.post("/v1/history/a1/tags", json={"tags": ["x"]}).status_code == 401


def test_a_sessions_outputs_link_back_to_it(store):
    client, write, _ = store
    run = {"action": "run_panda", "status": "success", "artifacts": ["/work/outputs/demo/panda.tsv"]}
    write("old1", results=[run], at=1)
    write("old2", results=[run], at=2)
    write("new3", results=[{**run, "artifacts": ["/work/outputs/sessions/new3/panda.tsv"]}], at=3)
    write("preview", results=[{**run, "status": "dry_run", "artifacts": ["/work/outputs/demo/x.tsv"]}], at=4)
    shared = client.get("/v1/outputs/provenance", params={"path": "outputs/demo/panda.tsv"}, headers=AUTH).json()
    assert [row["session_id"] for row in shared["sessions"]] == ["old2", "old1"]
    owned = client.get("/v1/outputs/provenance", params={"path": "outputs/sessions/new3/panda.tsv"}, headers=AUTH).json()
    assert owned["sessions"][0]["session_id"] == "new3" and owned["sessions"][0]["owns_folder"]
    none = client.get("/v1/outputs/provenance", params={"path": "outputs/demo/x.tsv"}, headers=AUTH).json()
    assert none["sessions"] == []  # a dry run wrote nothing
    row = client.get("/v1/history", params={"query": "new3"}, headers=AUTH).json()["sessions"][0]
    assert row["outputs"] == ["outputs/sessions/new3/panda.tsv"] and row["output_count"] == 1


def test_a_transcript_carries_recorded_brief_replies_models_and_tags(store, monkeypatch):
    from netzoo_agent_core import session as session_module

    client, write, sessions = store
    monkeypatch.setattr(session_module, "SESSION_ROOT", sessions)
    reply = "Several registered methods fit this result."
    write("c3", messages=[{"role": "user", "content": "which method?"}, {"role": "assistant", "content": reply}])
    card = {"kind": "method_choice", "headline": "3 registered methods can build it.", "points": [],
            "choices": None, "unavailable": [], "next_steps": [], "ran_nothing": True}
    remember_turn("c3", models={"response": "openai/gpt-4o-mini"}, content=reply, card=card,
                  output_dir="outputs/sessions/c3", sessions_root=sessions)
    assert (sessions.parent / "session_meta" / "c3.json").exists()
    body = client.get("/v1/history/c3", headers=AUTH).json()
    assert body["messages"][1]["card"]["headline"] == "3 registered methods can build it."
    assert "card" not in body["messages"][0]
    assert body["models"] == {"response": "openai/gpt-4o-mini"}
    assert body["output_dir"] == "outputs/sessions/c3"


def test_compare_lists_what_each_session_ran_on_what(store):
    client, write, sessions = store
    write("p1", workflow="PANDA", decision={"expression_file": "data/a/expr.tsv", "motif_file": "data/a/motif.tsv"},
          results=[{"action": "run_panda", "status": "success", "artifacts": ["/work/outputs/sessions/p1/panda.tsv"]}])
    write("o2", workflow="OTTER", decision={"expression_file": "data/a/expr.tsv"})
    set_tags("p1", ["baseline"], sessions_root=sessions)
    rows = client.get("/v1/compare", params={"ids": "p1,o2,missing"}, headers=AUTH).json()["sessions"]
    assert [row["workflow"] for row in rows] == ["PANDA", "OTTER"]
    assert rows[0]["inputs"] == {"expression_file": "data/a/expr.tsv", "motif_file": "data/a/motif.tsv"}
    assert rows[0]["outputs"] == ["outputs/sessions/p1/panda.tsv"] and rows[0]["tags"] == ["baseline"]
    assert client.get("/v1/compare", params={"ids": "../etc"}, headers=AUTH).status_code == 400


def test_models_are_recorded_once_and_a_different_resume_is_noted(tmp_path):
    root = tmp_path / "sessions"
    remember_turn("m1", models={"response": "openai/gpt-4o-mini"}, sessions_root=root)
    remember_turn("m1", models={"response": "openai/gpt-4o"}, sessions_root=root)
    meta = load_meta("m1", sessions_root=root)
    assert meta["models"] == {"response": "openai/gpt-4o-mini"}
    assert meta["resumed_with_models"] == {"response": "openai/gpt-4o"}
    remember_turn("nothing", sessions_root=root)  # adds nothing, writes nothing
    assert not (tmp_path / "session_meta" / "nothing.json").exists()


def test_a_tagged_session_outlives_routine_retention_and_its_sidecar_goes_with_it(tmp_path, monkeypatch):
    import time as _time

    from netzoo_agent_core import session as session_module

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(session_module, "SESSION_ROOT", sessions)
    monkeypatch.setattr(session_module, "TOOL_LOG_ROOT", tmp_path / "logs")
    old = _time.time() - 40 * 86_400
    for name in ("aaaa1111", "bbbb2222"):
        path = sessions / f"{name}.json"
        path.write_text(json.dumps({"session_id": name, "plan": {"status": "respond_only"}, "messages": []}))
        os.utime(path, (old, old))
    set_tags("aaaa1111", ["keep"], sessions_root=sessions)
    remember_turn("bbbb2222", models={"response": "openai/gpt-4o-mini"}, sessions_root=sessions)
    removed = session_module.cleanup_runtime_storage(retention_days=30, hard_retention_days=180)
    assert removed["sessions"] == 1
    assert (sessions / "aaaa1111.json").exists() and not (sessions / "bbbb2222.json").exists()
    assert not (tmp_path / "session_meta" / "bbbb2222.json").exists()
    assert session_module.delete_session("aaaa1111")
    assert not (tmp_path / "session_meta" / "aaaa1111.json").exists()
