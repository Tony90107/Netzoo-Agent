"""Acceptance against an interactive PTY and an ANSI terminal screen, not strings."""
import os
import sys
import time
from pathlib import Path

import pytest

pexpect = pytest.importorskip("pexpect")
pyte = pytest.importorskip("pyte")

CHILD = """
from test_routing_evaluation import FixtureProvider, run
from netzoo_agent_core.cli.terminal_input import _read_menu_line
row = run(FixtureProvider(first=ValueError('offline')))["results"][0]
print(row["progress"], flush=True)
print(row["answer"], flush=True)
answer = _read_menu_line(row["next_step_text"] + "\\n> ", "/execute")
print("SUBMITTED=" + repr(answer), flush=True)
"""


def _compact(text):
    return "".join(text.split())


def _read_frame(child, stream, screen):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            stream.feed(child.read_nonblocking(65536, timeout=.15))
        except pexpect.TIMEOUT:
            if any(line.startswith("> ") for line in screen.display):
                return _compact("".join(screen.display))
    pytest.fail("Interactive prompt did not render within 10 seconds")


@pytest.mark.parametrize("width", [40, 60, 90])
def test_fallback_next_step_is_complete_on_narrow_terminal_and_after_resize(width):
    root = Path(__file__).parents[1]
    env = {**os.environ, "TERM": "xterm-256color", "PROMPT_TOOLKIT_NO_CPR": "1",
           "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
           "PYTHONPATH": os.pathsep.join([str(root / "scripts"), str(root / "tests")])}
    child = pexpect.spawn(sys.executable, ["-c", CHILD], cwd=str(root), env=env,
                          dimensions=(30, width), encoding="utf-8", timeout=10)
    screen = pyte.Screen(width, 30)
    stream = pyte.Stream(screen)
    try:
        frame = _read_frame(child, stream, screen)
        for expected in (
            "Next step", "intended deliverable and inputs.",
            "this candidate is not ready to start.",
            "Enter/back: start a new task | exit: close",
        ):
            assert _compact(expected) in frame, screen.display
        # Resize an already active prompt; redraw must not lose the end of the warning.
        screen.resize(columns=32, lines=30)
        child.setwinsize(30, 32)
        child.send("/e")
        frame = _read_frame(child, stream, screen)
        assert _compact("intended deliverable and inputs.") in frame, screen.display
        assert _compact("this candidate is not ready to start.") in frame, screen.display
        assert _compact("Enter/back: start a new task | exit: close") in frame
        child.send("\x7f\x7fexit\r")
        child.expect("SUBMITTED='exit'")
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)
