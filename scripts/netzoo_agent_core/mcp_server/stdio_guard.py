"""Keep the protocol's stdout to itself.

Over stdio, every byte on file descriptor 1 is read by the client as JSON-RPC.
One stray ``print`` from an imported module, or one line from a worker process
before it has redirected its own output, breaks the connection. Rather than
trust everything this process loads to stay silent, the real stdout is set
aside for the protocol and descriptor 1 is pointed at stderr. Whatever is
printed after that, by this process or a child, ends up in the client's log.
"""

from __future__ import annotations

import os
import sys

__all__ = ["protect_stdout"]


def protect_stdout() -> int:
    """Return a descriptor for the real stdout and send everything else to stderr.

    Call it before importing anything that might print.
    """
    sys.stdout.flush()
    protocol = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    return protocol
