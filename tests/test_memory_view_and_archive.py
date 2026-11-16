"""The desktop Memory view, and a transcript that stays whole when the context is compacted."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

from netzoo_agent_core import session as session_store  # noqa: E402
from netzoo_agent_core.contracts import PreferenceProposal  # noqa: E402
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore  # noqa: E402
from netzoo_agent_core.server import history, memory_view  # noqa: E402
from netzoo_agent_core.session import compact_conversation, save_session  # noqa: E402
from netzoo_agent_core.session_meta import archive_messages, delete_meta, read_archive  # noqa: E402


@pytest.fixture
def stores(tmp_path, monkeypatch):
    profiles = UserProfileStore(tmp_path / "profiles")
    episodes = EpisodeStore(tmp_path / "episodes")
    monkeypatch.setattr(memory_view, "_worker_memory",
                        lambda: SimpleNamespace(profile_id="default", profile_store=profiles, episode_store=episodes))
    return profiles, episodes


def test_a_confirmed_preference_is_listed_with_its_reason_and_can_be_forgotten(stores):
    profiles, _ = stores
    profiles.confirm("default", [
        PreferenceProposal(key="reuse_last_inputs", value="true", reason="You said: reuse last time's files."),
        PreferenceProposal(key="allow_demo_autofill", value="false", reason="You said: never use demo data."),
    ])
    view = memory_view.describe_memory()
    assert [item["key"] for item in view["preferences"]] == ["allow_demo_autofill", "reuse_last_inputs"]
    assert view["preferences"][1]["source"] == "You said: reuse last time's files."

    assert memory_view.forget_preference("reuse_last_inputs")
    assert not memory_view.forget_preference("reuse_last_inputs")
    assert [item["key"] for item in memory_view.describe_memory()["preferences"]] == ["allow_demo_autofill"]


def test_one_episode_can_be_forgotten_and_a_bad_id_touches_nothing(stores):
    _, episodes = stores
    root = episodes.profile_root("default")
    root.mkdir(parents=True)
    target = root / ("a" * 32 + ".json")
    target.write_text("{}")
    assert not memory_view.forget_episode("../" + "a" * 32)
    assert target.exists()
    assert memory_view.forget_episode("a" * 32)
    assert not target.exists()


def test_compacted_turns_are_archived_and_the_transcript_is_whole(tmp_path, monkeypatch):
    sessions = tmp_path / "sessions"
    monkeypatch.setattr(session_store, "SESSION_ROOT", sessions)
    monkeypatch.setattr(history, "SESSION_ROOT", sessions)
    turns = []
    for index in range(10):
        turns += [HumanMessage(content=f"question {index}"), AIMessage(content=f"answer {index}")]
    kept = compact_conversation(turns)
    assert len(kept) == 12
    archive_messages("long1", [{"role": "assistant" if m.type == "ai" else "user", "content": m.content}
                               for m in turns[: len(turns) - len(kept)]], sessions_root=sessions)
    save_session("long1", kept, {"plan": {"status": "completed", "workflow": "PANDA"}})

    transcript = history.read_transcript("long1")
    assert [m["content"] for m in transcript.messages] == [m.content for m in turns]
    assert transcript.truncated is False

    delete_meta("long1", sessions_root=sessions)
    assert read_archive("long1", sessions_root=sessions)["messages"] == []


def test_the_archive_is_bounded_and_then_says_it_is_incomplete(tmp_path, monkeypatch):
    from netzoo_agent_core import session_meta

    monkeypatch.setattr(session_meta, "MAX_ARCHIVED_MESSAGES", 3)
    archive_messages("b1", [{"role": "user", "content": str(i)} for i in range(5)], sessions_root=tmp_path)
    archive = read_archive("b1", sessions_root=tmp_path)
    assert [m["content"] for m in archive["messages"]] == ["2", "3", "4"]
    assert archive["dropped"] == 2


def test_the_machine_archives_what_it_compacts_and_says_so_once(tmp_path, monkeypatch):
    from netzoo_agent_core.engine.transcript_archive import archive_compacted

    monkeypatch.setattr(session_store, "SESSION_ROOT", tmp_path / "sessions")
    runtime = SimpleNamespace(session_models={"response": "m"})
    turns = [HumanMessage(content=f"q{i}") for i in range(14)]

    first = archive_compacted(runtime, "m1", turns, turns[2:])
    assert len(first) == 1 and "latest 12 messages" in first[0].text
    q14 = HumanMessage(content="q14")
    assert archive_compacted(runtime, "m1", turns[2:] + [q14], turns[3:] + [q14]) == []
    assert [m["content"] for m in read_archive("m1", sessions_root=session_store.SESSION_ROOT)["messages"]] == ["q0", "q1", "q2"]
    # Nothing dropped, nothing archived, nothing said; a hand-built runtime keeps no sidecar.
    assert archive_compacted(runtime, "m1", turns[:3], turns[:3]) == []
    assert archive_compacted(SimpleNamespace(), "m2", turns, turns[2:]) == []
