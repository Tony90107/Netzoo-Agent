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
    if kind == "next_step":
        if facts.get("capability_match_status") == "unsupported":
            return (
                "The requested result does not exactly match a registered workflow. "
                "I will explain the capability gap without running an analysis."
            )
        if facts.get("capability_match_status") == "ambiguous":
            return (
                "The requested result is ambiguous, so I need one clarification "
                "before selecting a workflow."
            )
        if facts.get("action") == "no_tool" and facts.get("in_scope") == "true":
            return (
                "This is stable guidance, so I will answer from registered "
                "workflow information without running an analysis."
            )
        if facts.get("should_execute") == "true":
            return (
                "This goal needs an analysis workflow. I will prepare the "
                "matching registered workflow and validate its inputs."
            )
        if facts.get("in_scope") != "true":
            return "This request is outside the registered NetZoo capabilities."
        return "I will prepare the next safe step from the registered workflow policy."
    return None


__all__ = ["render_progress_summary"]
