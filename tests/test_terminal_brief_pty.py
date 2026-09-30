"""Acceptance in a real PTY: brief replies, an arrow-key menu, and /details."""
import os
import sys
from pathlib import Path

import pytest

pexpect = pytest.importorskip("pexpect")

CHILD = """
import tempfile
from pathlib import Path
from types import SimpleNamespace
from netzoo_agent_core import session as session_module
session_module.SESSION_ROOT = Path(tempfile.mkdtemp())
from netzoo_agent_core.runtime import configure_runtime
configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False, TRACE_ENABLED=False,
                  PRESENTATION_MODE="state_machine", TRANSIENT_TRACE=False)
from test_reply_card_choices import POLICY, _tie_result
from test_cli_lifecycle import _fake_cli_runtime
from netzoo_agent_core.cli import conversation
results = [_tie_result(), _tie_result()]
runtime = _fake_cli_runtime(invoke_error=AssertionError("replaced below"))
runtime.project_policy = POLICY
runtime.input_func = input
def record(app, invocation):
    print("TASK=" + repr(invocation["messages"][-1].content[:60]), flush=True)
    return results.pop(0)
runtime.invoke_graph_turn_func = record
code = conversation.run_conversation(SimpleNamespace(task=None, keep_session=False, full_replies=False), runtime)
print("EXIT=" + str(code), flush=True)
"""


def test_brief_reply_arrow_menu_and_details_in_a_real_terminal():
    root = Path(__file__).parents[1]
    env = {**os.environ, "TERM": "xterm-256color", "PROMPT_TOOLKIT_NO_CPR": "1", "NO_COLOR": "1",
           "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
           "PYTHONPATH": os.pathsep.join([str(root / "scripts"), str(root / "tests")])}
    child = pexpect.spawn(sys.executable, ["-c", CHILD], cwd=str(root), env=env,
                          dimensions=(40, 120), encoding="utf-8", timeout=20)
    try:
        child.expect("What would you like to accomplish with NetZoo")
        child.send("one TF-gene network for the cohort\r")
        child.expect("TASK='one TF-gene network for the cohort'")
        # The brief form comes first; the full text is behind /details.
        child.expect("3 registered methods can build a cohort-level TF-gene regulatory network")
        child.expect("Full explanation: /details")
        child.expect("1\\) PANDA")
        child.expect("2\\) OTTER")
        child.send("\x1b[B")          # down arrow: highlight OTTER
        child.send("\r")
        child.expect("TASK='CONFIRMED_OUTCOME_ACTION=run_otter")
        child.expect("Full explanation: /details")
        child.send("/details\r")
        child.expect("OTTER")
        child.send("exit\r")
        child.expect("EXIT=0")
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)
