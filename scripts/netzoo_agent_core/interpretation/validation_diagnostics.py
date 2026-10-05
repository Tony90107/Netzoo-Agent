"""Shared failure taxonomy for validation and bounded semantic repair.

These diagnostics explain existing issues; they never grant repair authority,
accept an invalid result, or establish scientific truth.
"""


def validation_diagnostic(issue: str) -> dict[str, str]:
    code = str(issue)
    if ".ungrounded_evidence:" in code:
        category = "invalid_reference"
        action = "repair_citation"
    elif ".missing_evidence:" in code:
        category = "missing_evidence"
        action = "supply_support"
    elif ".undecided_granularity" in code:
        category = "request_underspecified"
        action = "preserve_uncertainty"
    elif code == "missing_hypotheses" or ".missing_current_input:" in code:
        category = "outcome_omission"
        action = "restore_request_fact"
    elif ".conflicting_evidence:" in code or "_conflict:" in code:
        category = "value_conflict"
        action = "resolve_against_request"
    else:
        category = "semantic_constraint"
        action = "repair_within_scope"
    return {"issue": code, "category": category, "action": action}
