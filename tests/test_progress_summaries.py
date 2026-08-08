from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.progress_summaries import render_progress_summary  # noqa: E402


def test_no_tool_summary_explains_source_and_safety():
    summary = render_progress_summary(
        "concept", {"source": "registered workflow specification"}
    )

    assert summary is not None
    assert "do not need to inspect files or run tools" in summary
    assert "registered workflow specification" in summary
