"""What each model call is for, in words a person can follow while it runs.

Every model call passes through the budget preflight with a `role` (which part of the request it
reads). The live "now doing" line in the terminal and the window's step list both name the call by
this table, so the two never describe the same call differently. The label says what the call
reads, never what it concluded: the conclusion is the code's, recorded in its own events.
"""

from __future__ import annotations

__all__ = ["ROLE_LABELS", "role_label"]

ROLE_LABELS: dict[str, str] = {
    "semantic_interpreter": "reading the request",
    "semantic_reviewer": "reviewing that reading",
    "semantic_discriminator": "telling the readings apart",
    "semantic_sibling_repair": "repairing the reading",
    "intent_router": "classifying the request",
    "router": "routing the request",
    "router_repair": "repairing the route",
    "goal_read": "reading the goal",
    "study_purpose": "reading the study purpose",
    "capability_check": "checking what the methods can do",
    "capability_second_opinion": "getting a second opinion on that check",
    "capability_reread": "re-reading that check",
    "capability_condition_check": "checking the stated conditions",
    "fact_check": "checking the stated facts",
    "data_facts": "reading facts about the data",
    "hypothesis_bases": "reading what each reading rests on",
    "request_concerns": "reading stated concerns",
    "selection_conditions": "reading stated preferences",
    "follow_up": "reading the follow-up",
    "normalization_need": "checking whether normalization is needed",
    "input_content_mapper": "matching file contents to inputs",
    "settings_read": "reading the requested settings",
    "jev_settings_values": "reading the setting values",
    "general_background": "writing general background",
    "response": "writing the reply",
}


def role_label(role: str) -> str:
    """The table's words for a role, or the role itself spelled out."""
    return ROLE_LABELS.get(role, str(role or "model call").replace("_", " "))
