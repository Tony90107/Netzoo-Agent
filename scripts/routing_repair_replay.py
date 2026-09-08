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
# The failure that actually dominates the live record: 112 of 131 recorded first
# attempts omit a current input the harness's own witnesses already located, and
# 31 of them have no other defect at all. The other two suites reconstruct
# cross-field and schema failures, so without this one a repair-replay round
# never samples the class where a one-field repair should matter most.
MISSING_INPUT_ISSUES = {
    "original-q1": ["missing_current_input:mutation_matrix"],
    "original-q2": ["missing_current_input:mutation_matrix"],
    "original-q3": ["missing_current_input:mutation_matrix",
                    "terminal_goal_conflict:sample_cluster_assignment"],
}
# The class that dominates the loss once the citation failures are fixed: 126 of
# 165 `missing_evidence` occurrences over two rounds name a role dimension
# (entity_type 61, target_type 33, regulator_type 32), and the role is exactly
# what separates the expected capability from its compatible neighbours. These
# four prompts are the ones whose declared discriminator IS a role, two of them
# stating an input and two stating none, so the reconstructed first pass differs
# from the corpus answer in one respect only: the roles it writes into the
# outcome have no matching evidence entry.
ROLE_EVIDENCE_ISSUES = {
    "mirna-current-goal": ["missing_evidence:regulator_type=mirna",
                           "missing_evidence:target_type=gene"],
    "sparse-expression-not-mutation": ["missing_evidence:regulator_type=tf",
                                       "missing_evidence:target_type=gene"],
    "terse-mirna-per-sample": ["missing_evidence:regulator_type=mirna",
                               "missing_evidence:target_type=gene"],
    "mirna-misspelled-no-inputs": ["missing_evidence:regulator_type=mirna",
                                   "missing_evidence:target_type=gene"],
}

REPLAY_SUITES = {
    "cross-field": OBSERVED_ISSUES,
    "missing-required": MISSING_REQUIRED_ISSUES,
    "missing-input": MISSING_INPUT_ISSUES,
    "role-evidence": ROLE_EVIDENCE_ISSUES,
}


def suite_cases(suite: str) -> frozenset[str]:
    """The prompts a suite reconstructs a first pass for.

    Each suite owns its own set: the role-evidence class does not occur in the
    three mutation prompts at all, since SAMBAR has no regulator or target.
    """
    if suite not in REPLAY_SUITES:
        raise ValueError("Unknown repair replay suite")
    return frozenset(REPLAY_SUITES[suite])


def reconstructed_proposal(case_id: str, suite: str = "cross-field") -> dict:
    if suite not in REPLAY_SUITES:
        raise ValueError("Unknown repair replay suite")
    if suite == "missing-required":
        return _missing_required_proposal(case_id)
    if suite == "missing-input":
        return _missing_input_proposal(case_id)
    if suite == "role-evidence":
        return _role_evidence_proposal(case_id)
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


#: Everything the corpus expects, minus the role evidence. Kept beside the suite
#: rather than derived from the corpus file: a replay that read the answer key
#: would be handing the reviewer the answer.
_ROLE_EVIDENCE_OUTCOMES = {
    "mirna-current-goal": dict(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=["mirna"], target_types=["gene"],
    ),
    "sparse-expression-not-mutation": dict(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=["tf"], target_types=["gene"],
    ),
    "terse-mirna-per-sample": dict(
        operation="infer", input_artifacts=[],
        artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=["mirna"], target_types=["gene"],
    ),
    "mirna-misspelled-no-inputs": dict(
        operation="infer", input_artifacts=[],
        artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=["mirna"], target_types=["gene"],
    ),
}


def _role_evidence_proposal(case_id: str) -> dict:
    """A first pass whose only defect is role evidence it never wrote.

    The outcome states the roles; the evidence list covers every other dimension
    the validator asks for. So the run fails on `missing_evidence` for the roles
    and nothing else, and a repair has to add exactly those entries.
    """
    outcome = dict(_ROLE_EVIDENCE_OUTCOMES[case_id])
    values = [
        ("operation", outcome["operation"]),
        ("artifact_type", outcome["artifact_type"]),
        ("granularity", outcome["granularity"]),
    ]
    return dict(
        request_mode="guidance",
        semantic_goal="Infer the regulatory network the request describes",
        outcome_hypotheses=[dict(outcome=outcome, confidence=0.9, evidence=[
            dict(dimension=dimension, value=value, source="inferred",
                 rationale="Proposed interpretation of the requested result.")
            for dimension, value in values
        ])],
    )


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


def _missing_input_proposal(case_id: str) -> dict:
    """Reconstruct a schema-valid first pass whose only defect is an omitted input.

    Everything else is the outcome the corpus expects, so a repair needs to touch
    exactly one field. Q3 additionally keeps the terminal-goal conflict it shows
    live, where the requested result is stated as a network rather than cluster
    labels. No expected answer reaches the reviewer: it sees only this proposal,
    the original request and the deterministic issue codes.
    """
    proposal = reconstructed_proposal(case_id)
    proposal.pop("assumptions", None)
    item = proposal["outcome_hypotheses"][0]
    artifact = "regulatory_network" if case_id == "original-q3" else "sample_cluster_assignment"
    item["outcome"].update(
        operation="analyze", input_artifacts=[], artifact_type=artifact,
        entity_types=["sample"], granularity="aggregate",
        regulator_types=[], target_types=[],
    )
    if case_id == "original-q3":
        item["outcome"].update(
            operation="infer", entity_types=["tf", "gene"],
            regulator_types=["tf"], target_types=["gene"], granularity="sample_specific",
        )
    values = [
        ("operation", item["outcome"]["operation"]),
        ("artifact_type", artifact),
        ("granularity", item["outcome"]["granularity"]),
        *(("regulator_type", role) for role in item["outcome"]["regulator_types"]),
        *(("target_type", role) for role in item["outcome"]["target_types"]),
    ]
    item["evidence"] = [
        dict(dimension=dimension, value=value, source="inferred",
             rationale="Proposed interpretation of the requested result.")
        for dimension, value in values
    ]
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
