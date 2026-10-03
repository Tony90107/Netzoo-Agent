"""Sessions as experiments: names, notes, tags, the models they ran under, and where outputs came from."""
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
    set_details,
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
    assert normalize_tags([" brca ", "BRCA", "乳癌 pilot", "", "bad<tag>", "x" * 60]) == [
        "brca", "乳癌 pilot", "x" * 48]
    assert len(normalize_tags([f"t{i}" for i in range(30)])) == 12


def test_a_field_tag_holds_one_value_under_a_lower_case_key():
    assert normalize_tags(["Dataset : batch-2", "hypothesis:DNA damage", "pilot", "dataset:batch-3",
                           "time:10:30", ":orphan", "empty:", "細胞株:MCF7"]) == [
        "dataset:batch-3", "hypothesis:DNA damage", "pilot", "細胞株:MCF7"]
    # A new value replaces the old one even when the list is full.
    full = [f"t{i}" for i in range(11)] + ["dataset:a"]
    assert normalize_tags([*full, "dataset:b"])[-1] == "dataset:b"


def test_a_name_and_notes_round_trip_are_searched_and_compared(store):
    client, write, sessions = store
    write("n1", title="We collected another batch of patient data", at=1)
    write("n2", title="We collected another batch of patient data", at=2)
    body = client.post("/v1/history/n1/details", json={"name": "  Batch 2:  DNA damage ",
                                                        "notes": "Mutations first.\r\nThen rewiring.\x07"},
                       headers=AUTH).json()
    assert body == {"session_id": "n1", "name": "Batch 2: DNA damage", "notes": "Mutations first.\nThen rewiring."}
    # Leaving a field out keeps it; "" clears it.
    assert client.post("/v1/history/n1/details", json={"notes": "Mutations first."}, headers=AUTH).json()["name"] == "Batch 2: DNA damage"
    rows = client.get("/v1/history", headers=AUTH).json()["sessions"]
    assert [(row["session_id"], row["name"], row["notes_preview"]) for row in rows] == [
        ("n2", "", ""), ("n1", "Batch 2: DNA damage", "Mutations first.")]
    assert rows[1]["title"] == "We collected another batch of patient data"  # the request stays the title
    for needle in ("dna damage", "mutations first"):
        found = client.get("/v1/history", params={"query": needle}, headers=AUTH).json()["sessions"]
        assert [row["session_id"] for row in found] == ["n1"]
    transcript = client.get("/v1/history/n1", headers=AUTH).json()
    assert transcript["name"] == "Batch 2: DNA damage" and transcript["notes"] == "Mutations first."
    compared = client.get("/v1/compare", params={"ids": "n1,n2"}, headers=AUTH).json()["sessions"]
    assert [(row["name"], row["notes"]) for row in compared] == [("Batch 2: DNA damage", "Mutations first."), ("", "")]
    details = client.get("/v1/history/n1/details", headers=AUTH).json()
    assert details == {"session_id": "n1", "name": "Batch 2: DNA damage", "notes": "Mutations first.",
                       "tags": [], "models": {}}
    assert client.post("/v1/history/n1/details", json={"name": ""}, headers=AUTH).json()["name"] == ""
    # Names and notes live beside the checkpoint, never in it.
    assert "notes" not in json.loads((sessions / "n1.json").read_text())


def test_details_of_an_unknown_session_are_refused(store):
    client, _, _ = store
    assert client.post("/v1/history/nosuch/details", json={"name": "x"}, headers=AUTH).status_code == 404
    assert client.post("/v1/history/n1/details", json={"name": "x"}).status_code == 401
    assert client.post("/v1/history/n1/details", json={"title": "x"}, headers=AUTH).status_code == 422


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


def test_a_named_or_annotated_session_is_kept_like_a_tagged_one(tmp_path, monkeypatch):
    import time as _time

    from netzoo_agent_core import session as session_module

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(session_module, "SESSION_ROOT", sessions)
    monkeypatch.setattr(session_module, "TOOL_LOG_ROOT", tmp_path / "logs")
    old = _time.time() - 40 * 86_400
    for name in ("cccc3333", "dddd4444", "eeee5555"):
        path = sessions / f"{name}.json"
        path.write_text(json.dumps({"session_id": name, "plan": {"status": "respond_only"}, "messages": []}))
        os.utime(path, (old, old))
    set_details("cccc3333", name="Batch 2", sessions_root=sessions)
    set_details("dddd4444", notes="Keep: the PANDA baseline", sessions_root=sessions)
    removed = session_module.cleanup_runtime_storage(retention_days=30, hard_retention_days=180)
    assert removed["sessions"] == 1
    assert [p.stem for p in sorted(sessions.glob("*.json"))] == ["cccc3333", "dddd4444"]


class _FakeSupervisor:
    """Only what session creation touches: which workers are live, create, close."""

    def __init__(self, live=()):
        self.live = {item["session_id"]: item for item in live}
        self.created, self.closed = [], []

    async def start(self):
        return None

    async def shutdown(self):
        return None

    def list_sessions(self):
        return list(self.live.values())

    async def create(self, session_id, request):
        self.created.append((session_id, request))

    async def close(self, session_id):
        self.closed.append(session_id)
        self.live.pop(session_id, None)


def _client_with(supervisor, tmp_path, monkeypatch):
    sessions = tmp_path / "sessions"
    sessions.mkdir(exist_ok=True)
    monkeypatch.setattr(history, "SESSION_ROOT", sessions)
    (sessions / "s1.json").write_text(json.dumps({"session_id": "s1", "plan": {"status": "needs_input"}, "messages": []}))
    set_tags("s1", ["dataset:batch-2"], sessions_root=sessions)
    return TestClient(create_app(token="sessions-token", supervisor=supervisor)), sessions


def test_resuming_continues_the_saved_session_under_its_own_id(tmp_path, monkeypatch):
    supervisor = _FakeSupervisor()
    client, _ = _client_with(supervisor, tmp_path, monkeypatch)
    with client:
        body = client.post("/v1/sessions", json={"resume": "s1"}, headers=AUTH).json()
        assert body["session_id"] == "s1"
        assert supervisor.created == [("s1", {"resume": "s1"})]
        # "latest" is resolved by the worker, so it still gets a fresh id.
        fresh = client.post("/v1/sessions", json={"resume": "latest"}, headers=AUTH).json()["session_id"]
        assert fresh != "latest" and len(fresh) == 8


def test_resuming_a_live_session_attaches_to_it_and_a_stopped_one_is_replaced(tmp_path, monkeypatch):
    supervisor = _FakeSupervisor([{"session_id": "s1", "alive": True, "stopped": False}])
    client, _ = _client_with(supervisor, tmp_path, monkeypatch)
    with client:
        body = client.post("/v1/sessions", json={"resume": "s1"}, headers=AUTH).json()
        assert body == {"session_id": "s1", "tags": ["dataset:batch-2"], "attached": True}
        assert supervisor.created == [] and supervisor.closed == []
        supervisor.live["s1"]["stopped"] = True
        assert client.post("/v1/sessions", json={"resume": "s1"}, headers=AUTH).json()["session_id"] == "s1"
        assert supervisor.closed == ["s1"] and [item[0] for item in supervisor.created] == ["s1"]


def test_a_new_session_can_be_named_when_it_starts(tmp_path, monkeypatch):
    supervisor = _FakeSupervisor()
    client, sessions = _client_with(supervisor, tmp_path, monkeypatch)
    with client:
        body = client.post("/v1/sessions", json={"name": " Batch 2 ", "tags": ["pilot"]}, headers=AUTH).json()
        assert body["name"] == "Batch 2" and body["tags"] == ["pilot"]
        assert "name" not in supervisor.created[0][1]  # the worker never sees it
        assert load_meta(body["session_id"], sessions_root=sessions)["name"] == "Batch 2"


def test_outputs_are_one_entry_per_session_newest_first(tmp_path, monkeypatch):
    from netzoo_agent_core.server import files

    project, sessions = tmp_path / "project", tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(files, "PROJECT_ROOT", project)
    monkeypatch.setattr(history, "SESSION_ROOT", sessions)

    def put(relative, at):
        path = project / "outputs" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
        os.utime(path, (at, at))

    def save(name, workflow, artifact, at):
        path = sessions / f"{name}.json"
        artifacts = artifact if isinstance(artifact, list) else [artifact]
        path.write_text(json.dumps({
            "session_id": name, "messages": [{"role": "user", "content": f"run {workflow}"}],
            "plan": {"workflow": workflow, "status": "ready"}, "evaluation": {"status": "completed"},
            "tool_results": [{"action": f"run_{workflow.lower()}", "status": "success",
                              "artifacts": [f"/work/{item}" for item in artifacts]}],
        }))
        os.utime(path, (at, at))

    put("sessions/s1/panda.tsv", 10)
    save("s1", "PANDA", "outputs/sessions/s1/panda.tsv", 10)
    for name, at in (("otter.tsv", 30), ("manifest.json", 30), ("otter-execution-x_TW.md", 31)):
        put(f"sessions/s2/{name}", at)
    # A recorded manifest is the run's record, not a result.
    save("s2", "OTTER", ["outputs/sessions/s2/otter.tsv", "outputs/sessions/s2/manifest.json"], 31)
    set_details("s2", name="Batch 2: OTTER", sessions_root=sessions)
    # Two old sessions wrote the same shared file; the one on disk is the newer one's.
    put("demo/puma.tsv", 20)
    save("old1", "PUMA", "outputs/demo/puma.tsv", 15)
    save("old2", "PUMA", "outputs/demo/puma.tsv", 20)
    put("sessions/expired/cobra.tsv", 5)  # its checkpoint is gone
    put("stray.txt", 1)

    body = history.outputs_by_session()
    assert [entry["session_id"] for entry in body["sessions"]] == ["s2", "old2", "s1", "expired"]
    newest = body["sessions"][0]
    assert newest["name"] == "Batch 2: OTTER" and newest["folder"] == "outputs/sessions/s2"
    assert [(item["name"], item["result"], item["role"]) for item in newest["files"]] == [
        ("otter.tsv", True, "result"), ("manifest.json", False, "manifest"), ("otter-execution-x_TW.md", False, "report")]
    assert newest["added_at"] == 31
    assert [item["path"] for item in body["sessions"][2]["files"]] == ["outputs/sessions/s1/panda.tsv"]
    assert body["sessions"][3]["saved"] is False and body["sessions"][3]["title"] == ""
    assert body["other_files"] == 1  # stray.txt
    with TestClient(create_app(token="sessions-token", supervisor=_FakeSupervisor())) as client:
        assert client.get("/v1/outputs/sessions", headers=AUTH).json() == body
        assert client.get("/v1/outputs/sessions").status_code == 401


def test_a_title_is_the_first_request_never_a_stored_marker(store):
    from netzoo_agent_core.session_meta import readable_request

    assert readable_request("if i want sample-specific miRNA networks, what do I need?") == (
        "if i want sample-specific miRNA networks, what do I need?")
    assert readable_request("Previous NetZoo goal: Build a PANDA network\nUser follow-up: use OTTER") == "Build a PANDA network"
    for marker in ("PREVIOUS_ACTION=run_lioness_puma. Continue the recommended LIONESS-PUMA workflow.",
                   "CONFIRMED_OUTCOME_ACTION=run_otter. The user chose OTTER.", "/doctor", "new", "2", "1, 3", ""):
        assert readable_request(marker) == ""
    client, write, sessions = store
    # A long session whose checkpoint kept only the newest turns.
    write("t1", workflow="LIONESS-PUMA", messages=[
        {"role": "user", "content": "PREVIOUS_ACTION=run_lioness_puma. Continue the recommended LIONESS-PUMA workflow."},
        {"role": "assistant", "content": "Choose one complete input bundle."},
        {"role": "user", "content": "which tools give sample-specific miRNA networks?"}])
    write("t2", workflow="LIONESS-PUMA", messages=[
        {"role": "user", "content": "PREVIOUS_ACTION=run_lioness_puma. Continue with the selected inputs."}])
    titles = {row["session_id"]: row["title"] for row in client.get("/v1/history", headers=AUTH).json()["sessions"]}
    assert titles["t1"] == "which tools give sample-specific miRNA networks?"
    assert titles["t2"] == "Continue LIONESS-PUMA"
    # Once recorded, the first request outlives the checkpoint's compaction.
    remember_turn("t2", request="/doctor", sessions_root=sessions)
    remember_turn("t2", request="build per-sample miRNA networks for my cohort", sessions_root=sessions)
    remember_turn("t2", request="a later question", sessions_root=sessions)
    assert load_meta("t2", sessions_root=sessions)["first_request"] == "build per-sample miRNA networks for my cohort"
    assert client.get("/v1/history/t2", headers=AUTH).json()["title"] == "build per-sample miRNA networks for my cohort"



def test_a_session_another_process_already_pruned_is_skipped(tmp_path, monkeypatch):
    # TEST_PROMPTS r6 (2026-10-04): five CLI processes started together after
    # the date changed, and three crashed on FileNotFoundError while pruning.
    import time as _time

    from netzoo_agent_core import session as session_module

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr(session_module, "SESSION_ROOT", sessions)
    monkeypatch.setattr(session_module, "TOOL_LOG_ROOT", tmp_path / "logs")
    ancient = _time.time() - 400 * 86_400
    for name in ("ffff6666", "gggg7777"):
        path = sessions / f"{name}.json"
        path.write_text(json.dumps({"session_id": name, "plan": {"status": "respond_only"}, "messages": []}))
        os.utime(path, (ancient, ancient))
    real_scandir = os.scandir

    def raced(root):
        entries = list(real_scandir(root))
        (sessions / "ffff6666.json").unlink()  # the other process got there first
        return iter(entries)

    monkeypatch.setattr(session_module.os, "scandir", raced)
    removed = session_module.cleanup_runtime_storage(retention_days=30, hard_retention_days=180)
    assert removed["sessions"] == 1 and not list(sessions.glob("*.json"))
