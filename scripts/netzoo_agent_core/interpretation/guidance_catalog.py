"""Small scientific capability catalog for unresolved conceptual guidance."""

from ..routing.clarification_planner import algorithmic_assumptions_for
from .method_philosophy import method_philosophies_for


def compact_guidance_catalog(context: dict) -> dict:
    """Retain scientific premises and boundaries without execution configuration.

    No catalog entry is certified as compatible until the subject is resolved.
    Controls, file paths and pipeline compositions are unnecessary for this
    comparison, and sending them drowns out the actual scientific question.
    """
    workflows = []
    philosophies = {}
    for item in context["workflows"]:
        capability = item["output_capability"]
        tags = capability["selection_tags"]
        for tag in tags:
            if notes := method_philosophies_for([tag]):
                philosophies[tag] = notes[0]
        workflows.append({
            key: item[key] for key in (
                "action", "workflow", "description", "required_inputs",
                "required_input_groups",
            ) if key in item
        } | {
            "method_premises": algorithmic_assumptions_for(tags),
            "output_capability": {
                key: capability[key] for key in (
                    "artifact_type", "granularities", "entity_types", "regulator_types",
                    "target_types", "selection_tags", "input_artifacts",
                    "produced_artifacts",
                ) if key in capability
            },
        })
    return context | {
        "workflows": workflows, "compositions": [], "handoffs": [],
        "selection_constraints": {
            "catalog_status": "conditional; subject unresolved",
            "method_philosophies": philosophies,
        },
    }
