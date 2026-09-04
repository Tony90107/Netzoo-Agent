"""Bounded reviewer diagnostics, never a shortcut around semantic validation."""
from collections.abc import Mapping
import json
import re

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS, artifact_field_constraints


def proposal_data(proposal):
    return proposal.model_dump() if hasattr(proposal, "model_dump") else proposal


def semantic_payload(result):
    """Keep invalid function arguments for review, transiently and without logging."""
    if not isinstance(result, dict) or "parsed" not in result:
        return result, None
    raw = result.get("raw")
    if result.get("parsed") is not None:
        return result["parsed"], raw
    calls = getattr(raw, "tool_calls", None) or []
    if len(calls) == 1 and isinstance(calls[0].get("args"), Mapping):
        return calls[0]["args"], raw
    error = result.get("parsing_error")
    if isinstance(error, BaseException):
        raise error
    raise ValueError("Semantic structured output could not be decoded")


def repair_feedback(proposal, issues: tuple[str, ...]) -> list[dict]:
    """Describe actual/expected fields and the evidence changes a repair requires."""
    data = proposal_data(proposal)
    hypotheses = data.get("outcome_hypotheses", []) if isinstance(data, Mapping) else []
    feedback = []
    for issue in issues[:12]:
        match = re.search(r"hypothesis\[(\d+)\]", issue)
        index = int(match[1]) if match else 0
        item = hypotheses[index] if isinstance(hypotheses, list) and index < len(hypotheses) else {}
        outcome = item.get("outcome", {}) if isinstance(item, Mapping) else {}
        artifact = outcome.get("artifact_type") if isinstance(outcome, Mapping) else None
        fields = artifact_field_constraints(artifact) if isinstance(artifact, str) and artifact in ARTIFACT_SEMANTICS else {}
        expected = {"field_constraints": fields}
        if "schema_validation" in issue:
            expected["shape"] = (
                "Review root: request_mode, semantic_goal, outcome_hypothesis only. "
                "Metadata belongs in outcome_hypothesis.confidence, outcome_hypothesis.evidence, "
                "outcome_hypothesis.assumptions; outcome fields in outcome_hypothesis.outcome."
            )
        if "evidence" in issue:
            pair = re.search(r"evidence:([a-z_]+)=(.+)$", issue)
            if pair:
                expected["evidence_pair"] = {"dimension": pair[1], "value": pair[2]}
            expected["evidence"] = (
                "Supply evidence for the named dimension=value, consistent with the corrected outcome. "
                "Explicit evidence must quote the original request; inferred evidence needs a scientific rationale. "
                "Remove evidence for removed fields. Do not invent quotes or relabel an invalid quote as inference."
            )
        if "roles" in issue:
            expected["roles"] = "Non-regulatory outputs have empty role lists and no unresolved regulator/target fields."
        feedback.append({"issue": issue, "actual": outcome, "expected": expected})
    return feedback


def repair_message(proposal, issues: tuple[str, ...]) -> str:
    return json.dumps({"repair_feedback": repair_feedback(proposal, issues)}, ensure_ascii=False)
