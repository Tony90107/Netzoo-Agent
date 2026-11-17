"""The sidebar's short session title: written once from the first request, never from the reply."""

from netzoo_agent_core import session_title
from netzoo_agent_core.session_meta import load_meta, remember_turn, set_details
from netzoo_agent_core.session_title import clean_title, ensure_auto_title, start_auto_title


def test_clean_title_strips_decoration_and_rejects_unusable_answers():
    assert clean_title('Title: "Build per-patient networks."\nextra') == "Build per-patient networks"
    assert clean_title("**Compare two tissues**") == "Compare two tissues"
    assert clean_title("") == ""
    assert clean_title("word " * 12) == ""
    assert clean_title("x" * 61) == ""


def test_title_is_written_once_from_the_first_request(tmp_path):
    remember_turn("s1", request="Run PANDA on data/official-toy and save outputs/panda.tsv", sessions_root=tmp_path)
    seen = []

    def ask(request, model):
        seen.append((request, model))
        return "Run PANDA on toy data", 42

    assert ensure_auto_title("s1", "openai/gpt-4o-mini", sessions_root=tmp_path, ask=ask) == "Run PANDA on toy data"
    assert seen == [("Run PANDA on data/official-toy and save outputs/panda.tsv", "openai/gpt-4o-mini")]
    meta = load_meta("s1", sessions_root=tmp_path)
    assert meta["auto_title"] == "Run PANDA on toy data"
    assert meta["auto_title_tokens"] == 42
    assert "tokens_total" not in meta  # the session's own count is never replaced by the title's
    # A second turn reuses it without another call.
    assert ensure_auto_title("s1", "openai/gpt-4o-mini", sessions_root=tmp_path, ask=lambda *_: 1 / 0) == "Run PANDA on toy data"


def test_no_request_or_a_failed_call_writes_nothing_and_keeps_the_name(tmp_path):
    assert ensure_auto_title("empty", "m", sessions_root=tmp_path, ask=lambda *_: ("Title", 1)) == ""
    remember_turn("s2", request="Compare heart and lung regulation", sessions_root=tmp_path)
    set_details("s2", name="My experiment", sessions_root=tmp_path)

    def broken(*_):
        raise TimeoutError("provider down")

    assert ensure_auto_title("s2", "m", sessions_root=tmp_path, ask=broken) == ""
    meta = load_meta("s2", sessions_root=tmp_path)
    assert "auto_title" not in meta and meta["name"] == "My experiment"


def test_background_start_is_off_under_the_switch(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_AUTO_TITLE", "off")
    called = []
    monkeypatch.setattr(session_title, "ensure_auto_title", lambda *a, **k: called.append(a) or "x")
    start_auto_title("s3", "m", sessions_root=tmp_path)
    assert called == []
