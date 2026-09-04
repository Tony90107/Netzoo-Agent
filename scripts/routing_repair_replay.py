"""Reconstructed failures observed in the three public mutation prompts.

The old traces retain error codes, NOT raw proposals. These minimal proposals
exercise those error classes; they are not representations of captured model text.
No expected answer is sent to the reviewer.
"""
from copy import deepcopy

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation


OBSERVED_ISSUES = {
    "original-q1": ["artifact_granularity:sample_distance_matrix", "artifact_roles:sample_distance_matrix"],
    "original-q2": ["artifact_granularity:sample_cluster_assignment", "missing_evidence:operation=analyze"],
    "original-q3": ["schema_validation:assumptions:extra_forbidden", "artifact_roles:multi_omic_network"],
}

MISSING_REQUIRED_ISSUES = {
    "original-q1": ["schema_validation:outcome_hypotheses.0.outcome.operation:missing"],
    "original-q2": ["schema_validation:outcome_hypotheses.0.outcome.operation:missing",
                    "schema_validation:outcome_hypotheses.0.outcome.granularity:missing"],
    "original-q3": ["schema_validation:outcome_hypotheses.0.outcome.operation:missing",
                    "schema_validation:outcome_hypotheses.1.outcome.operation:missing"],
}
REPLAY_SUITES = {"cross-field": OBSERVED_ISSUES, "missing-required": MISSING_REQUIRED_ISSUES}


def reconstructed_proposal(case_id: str, suite: str = "cross-field") -> dict:
    if suite not in REPLAY_SUITES:
        raise ValueError("Unknown repair replay suite")
    if suite == "missing-required":
        return _missing_required_proposal(case_id)
    artifact = {"original-q1": "sample_distance_matrix", "original-q2": "sample_cluster_assignment",
                "original-q3": "multi_omic_network"}[case_id]
    outcome = dict(operation="analyze", input_artifacts=["mutation_matrix"], artifact_type=artifact,
                   entity_types=["sample"], granularity="sample_specific")
    if case_id != "original-q2":
        outcome["target_types"] = ["gene"]
    values = [("operation", "analyze"), ("input_artifact", "mutation_matrix"),
              ("artifact_type", artifact), ("entity_type", "sample"), ("granularity", "sample_specific")]
    if case_id == "original-q2":
        values = values[1:]
    if case_id != "original-q2":
        values.append(("target_type", "gene"))
    proposal = dict(request_mode="guidance", semantic_goal="Compare cancer patients from mutation profiles",
                    outcome_hypotheses=[dict(outcome=outcome, confidence=.9, evidence=[
                        dict(dimension=dimension, value=value, source="inferred",
                             rationale="Proposed interpretation of mutation-based patient comparison.")
                        for dimension, value in values
                    ])])
    if case_id == "original-q3":
        proposal["assumptions"] = ["Previously used expression analysis methods may apply to the new data."]
    return proposal


def _missing_required_proposal(case_id: str) -> dict:
    """Reconstruct field omissions, not the earlier missing-evidence failure."""
    issues = MISSING_REQUIRED_ISSUES[case_id]
    proposal = reconstructed_proposal(case_id)
    proposal.pop("assumptions", None)
    item = proposal["outcome_hypotheses"][0]
    item["outcome"].update(granularity="aggregate", target_types=[])
    item["evidence"] = [dict(dimension=dimension, value=value, source="inferred",
                            rationale="Proposed interpretation of mutation-based patient comparison.")
                        for dimension, value in (
                            ("operation", "analyze"), ("input_artifact", "mutation_matrix"),
                            ("artifact_type", item["outcome"]["artifact_type"]),
                            ("entity_type", "sample"), ("granularity", "aggregate"),
                        )]
    if case_id == "original-q3":
        proposal["outcome_hypotheses"].append(deepcopy(item))
    for issue in issues:
        path = issue.split(":")[1].split(".")
        proposal["outcome_hypotheses"][int(path[1])]["outcome"].pop(path[-1])
    return proposal


class RepairReplayProvider:
    """Inject only the failed first pass; delegate review and intent normally."""
    repair_replay = True

    def __init__(self, provider, suite: str = "cross-field"):
        if suite not in REPLAY_SUITES:
            raise ValueError("Unknown repair replay suite")
        self.provider = provider
        self.suite = suite
        self.case_id = None

    def with_structured_output(self, schema, **kwargs):
        if schema is not SemanticInterpretation:
            return self.provider.with_structured_output(schema, **kwargs)
        replay = self

        class Adapter:
            def invoke(self, _messages):
                return deepcopy(reconstructed_proposal(replay.case_id, replay.suite))

        return Adapter()
