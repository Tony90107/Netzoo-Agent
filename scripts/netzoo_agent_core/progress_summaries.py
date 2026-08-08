"""Public, fact-grounded progress summaries for the interactive timeline."""

from __future__ import annotations

def render_progress_summary(kind: str, facts: dict[str, str]) -> str | None:
    """Describe verified work without disclosing private reasoning."""
    if kind == "concept" and facts.get("source"):
        return (
            "This only needs an explanation, so I do not need to inspect files "
            "or run tools. I am using the registered workflow specification as "
            "the answer source."
        )
    return None


__all__ = ["render_progress_summary"]
