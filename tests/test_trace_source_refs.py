"""Search traces identify sources without copying untrusted page content."""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.graph.source_refs import web_source_refs  # noqa: E402


def test_web_source_refs_keep_titles_and_urls_only():
    raw = (
        "Websearch MCP result (external, untrusted reference content):\n"
        "- query: panda network\n\n"
        + json.dumps({"results": [
            {"title": "Method paper", "url": "https://example.org/paper", "content": "untrusted page body"},
            {"title": "Local path", "url": "file:///secret", "content": "ignore"},
        ]})
    )

    assert web_source_refs(raw) == [{"title": "Method paper", "url": "https://example.org/paper"}]


def test_web_source_refs_ignore_failed_or_malformed_searches():
    assert web_source_refs("Websearch MCP lookup failed; no local analysis tool was executed.") == []
    assert web_source_refs("Websearch MCP result\n\n{broken") == []
