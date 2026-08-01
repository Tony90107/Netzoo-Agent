import os
import re
import signal
import sys
import time
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as agent  # noqa: E402


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class CommandProcessTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "process groups require POSIX")
    def test_timeout_terminates_descendant_process(self):
        previous_execute = agent.EXECUTE_TOOLS
        previous_timeout = agent.TOOL_TIMEOUT_SECONDS
        agent.EXECUTE_TOOLS = True
        agent.TOOL_TIMEOUT_SECONDS = 0.2
        child_pid = None
        try:
            output = agent._run_command(
                [
                    sys.executable,
                    "-c",
                    (
                        "import subprocess,sys,time; "
                        "p=subprocess.Popen([sys.executable,'-c',"
                        "'import time; time.sleep(30)']); "
                        "print(p.pid, flush=True); time.sleep(30)"
                    ),
                ]
            )
            match = re.search(r"STDOUT before timeout:\n(\d+)", output)
            self.assertIsNotNone(match, output)
            child_pid = int(match.group(1))
            deadline = time.monotonic() + 1.0
            while process_exists(child_pid) and time.monotonic() < deadline:
                time.sleep(0.02)

            self.assertFalse(process_exists(child_pid), output)
        finally:
            agent.EXECUTE_TOOLS = previous_execute
            agent.TOOL_TIMEOUT_SECONDS = previous_timeout
            if child_pid is not None and process_exists(child_pid):
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


if __name__ == "__main__":
    unittest.main()
