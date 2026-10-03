"""Bounded reviewer diagnostics, never a shortcut around semantic validation."""
from collections.abc import Mapping
import json
import re

from ..contracts.artifact_semantics import (
    ARTIFACT_SEMANTICS,
    artifact_field_constraints,
    artifacts_supporting_regulatory_roles,
)
from ..contracts.outcomes import SemanticInterpretation
from .request_integrity import regulatory_role_mentions


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
    # Type-check every raw provider value before indexing it, so a malformed
    # tool call stays a reported decoding failure rather than a TypeError.
    if len(calls) == 1 and isinstance(calls[0], Mapping) and isinstance(calls[0].get("args"), Mapping):
        return calls[0]["args"], raw
    error = result.get("parsing_error")
    if isinstance(error, BaseException):
        raise error
    raise ValueError("Semantic structured output could not be decoded")


def repair_feedback(proposal, issues: tuple[str, ...], user_task: str = "") -> list[dict]:
    """Describe actual/expected fields and the evidence changes a repair requires."""
    data = proposal_data(proposal)
    hypotheses = data.get("outcome_hypotheses", []) if isinstance(data, Mapping) else []
    # Constraints must describe the outcome the review should return. Deriving
    # them from the artifact validation has just rejected pins that artifact with
    # a const, contradicting the correction requested in the same message.
    role_mentions = regulatory_role_mentions(user_task)
    role_facts = [
        {"regulator_type": item.regulator_type, "target_type": item.target_type,
         "text_span": item.text_span}
        for item in role_mentions
    ]
    role_artifacts = artifacts_supporting_regulatory_roles(
        (item.regulator_type, item.target_type) for item in role_mentions
    )
    role_artifact = next(iter(role_artifacts)) if len(role_artifacts) == 1 else None
    corrections: dict[int, set[str]] = {}
    for issue in issues:
        if "terminal_goal_conflict:" in issue:
            value = issue.rsplit(":", 1)[-1]
        elif "stated_roles_conflict:" in issue:
            value = role_artifact
        else:
            continue
        match = re.search(r"(?:hypothesis\[|outcome_hypotheses\.)(\d+)", issue)
        if value is not None and match:
            corrections.setdefault(int(match[1]), set()).add(value)
    corrected = {
        index: next(iter(values))
        for index, values in corrections.items()
        if len(values) == 1
    }
    feedback = []
    for issue in issues[:12]:
        location = issue.split(":", 2)[1].split(".") if issue.startswith("schema_validation:") else []
        match = re.search(r"(?:hypothesis\[|outcome_hypotheses\.)(\d+)", issue)
        index = int(match[1]) if match else 0
        item = hypotheses[index] if isinstance(hypotheses, list) and index < len(hypotheses) else {}
        outcome = item.get("outcome", {}) if isinstance(item, Mapping) else {}
        repairable_fields = set(getattr(issue, "fields", ()))
        if not repairable_fields and any(marker in issue for marker in (
            "stated_roles_conflict:", "artifact_entity:",
            "artifact_granularity:", "artifact_roles:",
        )):
            repairable_fields.add("artifact_type")
        artifact = corrected.get(index) or (
            outcome.get("artifact_type")
            if isinstance(outcome, Mapping) and "artifact_type" not in repairable_fields
            else None
        )
        fields = (
            artifact_field_constraints(artifact)
            if isinstance(artifact, str) and artifact in ARTIFACT_SEMANTICS
            and artifact != "unknown"
            else {}
        )
        # An unresolved artifact has nothing to constrain toward; saying so is
        # better than asking the review to keep the value under repair.
        expected = {
            "field_constraints": fields,
            "field_constraints_note": (
                "JSON Schema constraints for fields of outcome; not values to copy "
                "into a list. input_artifacts holds plain artifact_type literals."
            ),
        } if fields else {}
        if "stated_roles_conflict:" in issue and index in corrected:
            expected.update(
                required_value={"field": "artifact_type", "value": corrected[index]},
                request_facts={"roles": role_facts[:4]},
            )
        if "terminal_goal_conflict:" in issue:
            expected.update(
                action="restore_terminal_goal",
                review_path="outcome_hypothesis.outcome.artifact_type",
                artifact_type=issue.rsplit(":", 1)[-1],
                instruction=(
                    "Preserve the user's terminal scientific result and update dependent fields and evidence. "
                    "A distance matrix or network proposed as a means to reach that result is an "
                    "intermediate step, not the requested result, and does not belong in this outcome; "
                    "the final answer lists related registry artifacts on its own. Never substitute a "
                    "tool's default output. Do not add assumptions to record that relationship: an "
                    "assumption marks an unconfirmed interpretation of the request itself."
                ),
            )
        if "artifact_granularity:" in issue or "artifact_entity:" in issue:
            field = "granularity" if "artifact_granularity:" in issue else "entity_types"
            rule = ARTIFACT_SEMANTICS.get(artifact) if isinstance(artifact, str) else None
            allowed = getattr(rule, "granularities" if field == "granularity" else "entities", None) if rule else None
            expected.update(
                action="align_with_artifact_ontology",
                review_path=f"outcome_hypothesis.outcome.{field}",
                instruction=(
                    f"The chosen artifact_type restricts {field}. Correct {field} to a value "
                    "that artifact allows, or change artifact_type if the requested result was "
                    "misidentified; do not keep a combination the ontology forbids. Update or "
                    "remove the evidence for the field you change."
                ),
            )
            if allowed is not None:
                expected["allowed_values"] = sorted(allowed | {"unknown"})
        if "inconsistent_not_applicable_outcome" in issue:
            expected.update(
                action="replace_not_applicable_outcome",
                review_path="outcome_hypothesis.outcome",
                instruction=(
                    "This request does describe a scientific result, so it cannot use the "
                    "canonical empty outcome. granularity=not_applicable with "
                    "artifact_type=unknown is reserved for a request with no scientific "
                    "result at all. Asking for guidance, for a tool recommendation, or for "
                    "a plan is still a request about a scientific result: interpret the "
                    "result itself and set operation, artifact_type and granularity from "
                    "the user's stated goal, with matching evidence."
                ),
            )
            if isinstance(user_task, str) and re.search(
                r"(?:omics|transcriptomics|metabolomics|methylation|mRNA|miRNA|多體學|組學|轉錄組|代謝組|甲基化)",
                user_task,
                re.IGNORECASE,
            ) and re.search(
                r"(?:precision|partial[- ]?correlation|conditional[- ]?depend|逆共變異|偏相關|條件依賴|聯合建模|joint|two[- ]layer)",
                user_task,
                re.IGNORECASE,
            ):
                expected["multi_omic_recovery_rule"] = (
                    "For paired continuous omics layers requesting one joint precision, "
                    "partial-correlation, or conditional-dependency network, recover "
                    "artifact_type=multi_omic_network, operation=infer, and "
                    "granularity=aggregate unless the request explicitly asks for a "
                    "separately inferred network per sample. Use feature entities, not "
                    "regulator/target roles; a no-motif or no-sequence-prior statement "
                    "is a negative constraint, not an input artifact."
                )
        if "missing_current_input:" in issue or "noncurrent_input:" in issue:
            artifact_literal = issue.rsplit(":", 1)[-1]
            expected.update(
                action="restore_current_input" if "missing_current_input:" in issue else "remove_noncurrent_input",
                review_path="outcome_hypothesis.outcome.input_artifacts",
                input_artifact=artifact_literal,
                # The named value is already a canonical literal. Repeating its
                # ontology meaning and the closed vocabulary keeps the reviewer
                # from answering with an invented near-miss name.
                input_artifact_definition=(
                    ARTIFACT_SEMANTICS[artifact_literal].description
                    if artifact_literal in ARTIFACT_SEMANTICS else ""
                ),
                permitted_input_artifacts=sorted(ARTIFACT_SEMANTICS),
                input_artifacts_item_type="string",
                instruction=(
                    "Reconcile current inputs with the original request and request_facts. "
                    "Use the exact input_artifact literal named here; it is already a canonical "
                    "ontology value, so do not rename, translate or substitute a similar term. "
                    "Historical data, hypothetical inputs and proposed outputs are not current inputs. "
                    "A proposed method does not erase an explicitly supplied current dataset. "
                    "Return a complete review with matching input_artifact evidence quoting the request; "
                    "remove evidence for removed inputs. Never infer inputs from method names."
                ),
            )
            # A restored input without its evidence pair fails validation again on
            # the last attempt. The span is the user's own wording, already located
            # by the same witnesses that raised this issue, so naming it is not
            # fabrication; the reviewer still writes its own rationale.
            span = _current_span(user_task, artifact_literal) if "missing_current_input:" in issue else None
            if span is not None:
                expected["required_evidence"] = {
                    "dimension": "input_artifact",
                    "value": artifact_literal,
                    "source": "explicit",
                    "text_span": span,
                }
        if "schema_validation" in issue:
            expected.update(_schema_repair(location, issue.rsplit(":", 1)[-1]))
            field = location[-1] if location else None
            if fields and field in fields and "field_schema" in expected:
                # Include the selected artifact's tighter constraint, not only
                # the broad ontology enum. Validation still runs after review.
                expected["field_schema"].update(fields[field])
            expected["shape"] = (
                "Review root: request_mode, semantic_goal, outcome_hypothesis only. "
                "Metadata belongs in outcome_hypothesis.confidence, outcome_hypothesis.evidence, "
                "outcome_hypothesis.assumptions; outcome fields in outcome_hypothesis.outcome."
            )
        # Log 325: a schema-failed first pass handed to the patch as a draft.
        if "schema_missing:confidence" in issue:
            expected.update(
                action="write_missing_field",
                review_path="confidence",
                instruction=(
                    "The first pass gave this hypothesis no confidence; the draft shows null. "
                    "Write this hypothesis's confidence (0 to 1) in the patch."
                ),
            )
        if "schema_invalid_value:artifact_type=" in issue:
            written = issue.split("=", 1)[1]
            expected.update(
                action="replace_invalid_value",
                review_path="outcome.artifact_type",
                written_value=written,
                allowed_values=sorted(ARTIFACT_SEMANTICS),
                instruction=(
                    f"The first pass wrote {written!r} as artifact_type, which is not an artifact_type; "
                    "the draft shows unknown. Set artifact_type to the requested result, or leave unknown, "
                    "with matching evidence. A value that names another dimension belongs in that field."
                ),
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
        if "artifact_roles:" in issue and not (
            isinstance(artifact, str) and artifact in {
                "regulatory_network",
                "regulatory_network_and_tf_activity",
                "signed_regulatory_effect_network",
            }
        ):
            expected["roles"] = "Non-regulatory outputs have empty role lists and no unresolved regulator/target fields."
        feedback.append({"issue": issue, "location": location, "actual": outcome, "expected": expected})
    return feedback


def _current_span(user_task: str, artifact: str) -> str | None:
    """Return the request's own wording for one current input, if it has any."""
    from .request_integrity import input_mentions

    return next(
        (
            item.text_span
            for item in input_mentions(user_task)
            if item.artifact == artifact and item.status == "current"
        ),
        None,
    )


def _schema_repair(location: list[str], error_type: str) -> dict:
    """Resolve Pydantic error paths against the canonical contract, never tool defaults."""
    schema = SemanticInterpretation.model_json_schema()
    node = schema
    parent = schema
    for segment in location:
        while "$ref" in node:
            node = schema["$defs"][node["$ref"].rsplit("/", 1)[-1]]
        parent = node
        node = node.get("items", {}) if segment.isdigit() else node.get("properties", {}).get(segment, {})
    review_location = list(location)
    if len(location) >= 2 and location[0] == "outcome_hypotheses" and location[1].isdigit():
        review_location = ["outcome_hypothesis", *location[2:]]
    return {
        "review_path": ".".join(review_location),
        "action": "add_required_field" if error_type == "missing" else "correct_field",
        "required_fields": parent.get("required", []),
        "field_schema": node,
        "instruction": (
            "Return a complete replacement SemanticReview, not a patch or a copied incomplete proposal. "
            "Supply the named field using its schema and the original request, independently adjudicating "
            "the primary goal when there are multiple hypotheses. Never use a candidate tool's default "
            "output or operation to fill a missing field. For genuinely unresolved meaning use an allowed "
            "unknown value and unresolved_dimensions, not omission. Add or update matching evidence for "
            "each repaired scientific dimension; preserve grounded fields."
        ),
    }


def repair_message(proposal, issues: tuple[str, ...], user_task: str = "") -> str:
    from dataclasses import asdict
    from .request_integrity import input_mentions

    return json.dumps({
        "repair_feedback": repair_feedback(proposal, issues, user_task),
        "request_facts": [asdict(item) for item in input_mentions(user_task)][:24],
    }, ensure_ascii=False)
