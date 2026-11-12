"""Output tags: auto tags from the run record and a person's own tags never contradict each other."""

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core import output_tags  # noqa: E402
from netzoo_agent_core.output_tags import ReservedTag, record_auto_tags, set_user_tags, tags_for  # noqa: E402
from netzoo_agent_core.server.app import create_app  # noqa: E402

AUTH = {"Authorization": "Bearer tags-token"}
FILE = "outputs/sessions/s1/toy-panda.tsv"


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(output_tags, "PROJECT_ROOT", tmp_path)
    folder = tmp_path / "outputs" / "sessions" / "s1"
    folder.mkdir(parents=True)
    (folder / "toy-panda.tsv").write_text("tf\tgene\tforce\n", encoding="utf-8")
    return tmp_path


def _written(path="/work/" + FILE, tags=("method:PANDA", "result:network", "scale:cohort")):
    return {"path": path, "written": True, "tags": list(tags)}


def test_a_run_records_auto_tags_only_for_files_it_wrote(project):
    planned = {"path": "outputs/sessions/s1/planned.tsv", "written": False, "tags": ["method:PANDA"]}
    missing = _written(path="outputs/sessions/s1/gone.tsv")
    outside = _written(path="data/official-toy/ToyExpressionData.txt")
    assert record_auto_tags([_written(), planned, missing, outside], session_id="s1", run_id="r1") == 1
    assert tags_for([FILE]) == {FILE: {"auto": ["method:PANDA", "result:network", "scale:cohort"], "user": []}}


def test_a_user_tag_may_not_use_a_reserved_key(project):
    record_auto_tags([_written()])
    for typed in ("method:OTTER", "Method : panda", "scale:per-sample", "mode:real", "result:anything"):
        with pytest.raises(ReservedTag, match="is set by NetZoo from the run record"):
            set_user_tags(FILE, ["baseline", typed])
    assert tags_for([FILE])[FILE]["user"] == []


def test_user_tags_sit_beside_auto_tags_and_survive_a_rewrite_of_the_file(project):
    record_auto_tags([_written()])
    saved = set_user_tags(FILE, ["baseline", "dataset:pasilla", "PANDA"])
    assert saved == {"path": FILE, "auto": ["method:PANDA", "result:network", "scale:cohort"],
                     "user": ["baseline", "dataset:pasilla", "PANDA"]}
    # A later run writes the same file with another method: its record replaces the auto tags, the person's stay.
    record_auto_tags([_written(tags=("method:OTTER", "result:network", "scale:cohort", "mode:synthetic test"))])
    assert tags_for([FILE])[FILE] == {"auto": ["method:OTTER", "result:network", "scale:cohort", "mode:synthetic test"],
                                      "user": ["baseline", "dataset:pasilla", "PANDA"]}


def test_a_file_without_a_run_record_can_still_get_user_tags(project):
    assert set_user_tags(FILE, ["for-paper"]) == {"path": FILE, "auto": [], "user": ["for-paper"]}


def test_only_existing_files_under_outputs_take_tags(project):
    with pytest.raises(ValueError, match="under outputs/"):
        set_user_tags("data/official-toy/ToyExpressionData.txt", ["x"])
    with pytest.raises(ValueError, match="under outputs/"):
        set_user_tags("outputs/../data/x.tsv", ["x"])
    with pytest.raises(FileNotFoundError):
        set_user_tags("outputs/sessions/s1/nothing.tsv", ["x"])


def test_the_api_reads_saves_and_refuses_with_the_reason(project):
    record_auto_tags([_written()])
    with TestClient(create_app(token="tags-token")) as client:
        assert client.get("/v1/outputs/tags", params={"path": FILE}, headers=AUTH).json() == {
            "path": FILE, "auto": ["method:PANDA", "result:network", "scale:cohort"], "user": []}
        saved = client.post("/v1/outputs/tags", json={"path": FILE, "tags": ["baseline"]}, headers=AUTH)
        assert saved.status_code == 200 and saved.json()["user"] == ["baseline"]
        refused = client.post("/v1/outputs/tags", json={"path": FILE, "tags": ["method:OTTER"]}, headers=AUTH)
        assert refused.status_code == 400 and "method: is set by NetZoo" in refused.json()["detail"]
        missing = client.post("/v1/outputs/tags", json={"path": "outputs/none.tsv", "tags": ["x"]}, headers=AUTH)
        assert missing.status_code == 404
        assert client.get("/v1/outputs/tags", params={"path": FILE}).status_code == 401


def test_the_respond_record_tags_a_written_file_even_without_a_session_id_in_state(project):
    # The graph state keeps only AgentState keys, so session_id never reaches the respond node (live round, 11-12).
    from netzoo_agent_core.cli.bootstrap import load_project_policy
    from netzoo_agent_core.framework_compat import HumanMessage
    from netzoo_agent_core.operation_summary import record_operation_summary

    state = {"messages": [HumanMessage(content="Run PANDA")], "run_id": "r1",
             "decision": {"action": "run_panda", "core": {"kind": "DO", "workflows": ["PANDA"]}},
             "plan": {"workflow": "PANDA", "status": "ready", "steps": [{"action": "run_panda", "purpose": "Run."}],
                      "evidence": [{"field": "output_file", "value": FILE, "status": "defaulted"}]},
             "tool_results": [{"action": "run_panda", "status": "success", "artifacts": ["/work/" + FILE]}],
             "evaluation": {"status": "completed"}}
    recorded = []
    record_operation_summary(lambda kind, payload: recorded.append(kind), state, {}, load_project_policy())
    assert recorded == ["operation.summary"]
    assert tags_for([FILE])[FILE]["auto"] == ["method:PANDA", "result:network", "scale:cohort"]
