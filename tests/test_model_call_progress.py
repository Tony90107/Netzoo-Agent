"""The live "now doing" line: each model call names what it reads, in the terminal as in the window."""

from netzoo_agent_core import presentation
from netzoo_agent_core.model_call_labels import role_label


def test_roles_read_as_words_and_unknown_roles_are_spelled_out():
    assert role_label("capability_check") == "checking what the methods can do"
    assert role_label("some_new_role") == "some new role"


def test_a_model_call_replaces_the_live_line_until_the_next_public_event():
    state = presentation.ProgressState.initial()
    presentation._PROGRESS_ACTIVITY = None
    assert presentation._apply_public_progress_event(
        state, "model", "Model call", {"kind": "model_call", "label": "checking the stated facts"})
    assert presentation._render_progress_state(state).endswith("Checking the stated facts…")
    state.activate("match", "Comparing against registered workflows")
    assert presentation._render_progress_state(state).endswith("Checking the stated facts…")
    presentation._apply_public_progress_event(state, "router", "x", {"kind": "registry_activity", "status": "started"})
    assert presentation._render_progress_state(state).endswith("Matching registered workflows…")
    presentation._PROGRESS_ACTIVITY = None
