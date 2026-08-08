from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import runtime, settings  # noqa: E402
from netzoo_agent_core.cli.loop import run_cli  # noqa: E402


def test_presentation_mode_is_mutable(monkeypatch):
    monkeypatch.setattr(settings, "PRESENTATION_MODE", "compact")

    runtime.configure_runtime(PRESENTATION_MODE="timeline")

    assert settings.PRESENTATION_MODE == "timeline"


def test_run_cli_selects_timeline_without_transient_output(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "netzoo_agent_core.cli.loop.configure_runtime",
        lambda **values: captured.update(values),
    )
    monkeypatch.setattr(
        "netzoo_agent_core.cli.loop.handle_preflight_command",
        lambda _args: 0,
    )
    args = SimpleNamespace(
        execute=False,
        quiet=False,
        verbose=False,
        timeline=True,
        transient_trace=False,
        tool_timeout=30.0,
    )

    assert run_cli(args) == 0
    assert captured["PRESENTATION_MODE"] == "timeline"
    assert captured["TRANSIENT_TRACE"] is False
