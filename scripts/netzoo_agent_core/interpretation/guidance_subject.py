"""Keep explanatory intent separate from the scientific subject being explained."""

from ..contracts.repair_scope import Issue, OUTCOME_FIELDS
from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from pydantic import BaseModel, ConfigDict, Field
from workflow_registry import ArtifactType, Granularity
from ..contracts.outcomes import OutcomeEvidence


class GuidanceCurrentInput(BaseModel):
    """An input adjudicated by the review, subject to normal evidence checks."""

    model_config = ConfigDict(extra="forbid")
    artifact_type: ArtifactType
    text_span: str = Field(min_length=1, max_length=240)
    rationale: str = Field(min_length=1, max_length=240)


class GuidanceSubjectReview(BaseModel):
    """The two subject dimensions an empty explanation omitted, with support."""

    model_config = ConfigDict(extra="forbid")
    artifact_type: ArtifactType = Field(description=(
        "Scientific object under discussion, even in a philosophy-only question. "
        "In the NetZoo regulatory-network context, a noisy binding-site/motif prior "
        "from another species is a regulatory_network subject. It is not unknown "
        "merely because the user asks how to quantify uncertainty rather than to run it."
    ))
    granularity: Granularity = Field(description=(
        "Scale of the object discussed. A partition of one existing network is aggregate. "
        "Separately inferred patient networks are sample_specific; unstated scale is unknown."
    ))
    artifact_rationale: str = Field(min_length=1, max_length=240)
    granularity_rationale: str = Field(min_length=1, max_length=240)
    current_inputs: list[GuidanceCurrentInput] = Field(default_factory=list, max_length=4, description=(
        "Only inputs the user has NOW, with exact original-language quotes. "
        "Do not add historical, hypothetical, proposed, negated or output artifacts. "
        "Use [] if no current inputs are stated."
    ))


def restore_guidance_subject(proposal, review: GuidanceSubjectReview):
    """Copy model-reviewed dimensions; neither tools nor biology are guessed."""
    if review.artifact_type == "unknown":
        return proposal
    hypothesis = proposal.outcome_hypotheses[0]
    outcome = hypothesis.outcome.model_copy(update={
        "artifact_type": review.artifact_type, "granularity": review.granularity,
        "input_artifacts": list(dict.fromkeys([
            *hypothesis.outcome.input_artifacts,
            *(item.artifact_type for item in review.current_inputs),
        ])),
        "unresolved_dimensions": [field for field in hypothesis.outcome.unresolved_dimensions
                                  if field not in {"artifact_type", "granularity"}],
    })
    evidence = [item for item in hypothesis.evidence
                if item.dimension not in {"artifact_type", "granularity"}]
    evidence.extend([
        OutcomeEvidence(dimension="artifact_type", value=review.artifact_type,
                        source="inferred", rationale=review.artifact_rationale),
        OutcomeEvidence(dimension="granularity", value=review.granularity,
                        source="inferred", rationale=review.granularity_rationale),
    ])
    existing_inputs = {item.value for item in evidence if item.dimension == "input_artifact"}
    evidence.extend(OutcomeEvidence(
        dimension="input_artifact", value=item.artifact_type, source="explicit",
        text_span=item.text_span, rationale=item.rationale,
    ) for item in review.current_inputs if item.artifact_type not in existing_inputs)
    return proposal.model_copy(update={"outcome_hypotheses": [hypothesis.model_copy(
        update={"outcome": outcome, "evidence": evidence},
    )]})


SCIENTIFIC_GUIDANCE_INSTRUCTIONS = """
Scientific how/why/philosophy questions are guidance. Classify their scientific
subject, not the prose answer: binding-site (結合位點) predictions and motif priors,
even noisy or borrowed across species, concern regulatory_network, not covariance;
each patient's regulatory wiring is regulatory_network/sample_specific;
grouping a two-mode network is community_assignment/aggregate.
Preserve the subject without tool names or execution. Operation may be explain;
do not erase artifact_type. Probabilistic is a preference, not co-expression biology.
Keep supported inputs/roles/tags. Only no-subject definitions use unknown/not_applicable.
""".strip()


def guidance_subject_review_issues(interpretation) -> tuple[Issue, ...]:
    """License one semantic review of an empty guidance subject, without guessing it.

    A schema-valid absence is not evidence that a scientific question has no
    subject. The model must check that claim once; ordinary definitions may be
    confirmed unchanged. No keyword selects an artifact or workflow here.
    """
    if interpretation.request_mode != "guidance":
        return ()
    return tuple(
        Issue(
            f"hypothesis[{index}].unresolved_guidance_subject:recheck the original "
            "question for its scientific subject, intended result, inputs, topology, "
            "granularity and mathematical assumptions; retain no-outcome only if "
            "none is identifiable",
            OUTCOME_FIELDS,
        )
        for index, hypothesis in enumerate(interpretation.outcome_hypotheses)
        if hypothesis.outcome.artifact_type == "unknown"
        and hypothesis.outcome.operation != "unknown"
    )


def subject_review_prompt(schema_name: str) -> str:
    """A focused second reading, independent of method catalog and prior prose.

    A long general routing prompt can reinforce the draft's category error.
    This review owns the biological object, not tool selection or execution.
    """
    ontology = "\n".join(
        f"{name}: {rule.description}" for name, rule in ARTIFACT_SEMANTICS.items()
    )
    if schema_name == "GuidanceSubjectReview":
        return (
            "Identify the scientific SUBJECT of the user's question. Return only "
            "GuidanceSubjectReview: artifact_type, granularity, artifact_rationale, "
            "granularity_rationale, current_inputs. Rationales are short English sentences, <=240 characters. "
            "Retain explicitly current inputs with verbatim quotes; never add history or suggested inputs. "
            "This classifies what the question discusses, even if it only asks for an "
            "explanation; it never selects tools or authorizes analysis.\n"
            + SCIENTIFIC_GUIDANCE_INSTRUCTIONS + "\nScientific object vocabulary:\n" + ontology
            + "\nOne partition of an existing network is aggregate. Separately estimated "
            "patient networks are sample_specific. If the scale is unstated, use unknown. "
            "Only no identifiable scientific subject uses unknown/not_applicable."
        )
    return (
        f"Return only {schema_name}. Re-read the ORIGINAL scientific question. "
        "The draft may have mistaken asking for an explanation for having no scientific subject. "
        "Correct that error before considering method preferences. Do not preserve an unknown "
        "artifact just because no execution, file paths or explicit tool names were requested.\n"
        "For SemanticReview, root fields are request_mode, semantic_goal, outcome_hypothesis. "
        "outcome_hypothesis contains outcome, confidence, evidence, assumptions; scientific "
        "fields must be nested inside outcome. Write English except verbatim text_span quotes. "
        "Allowed entity_types: tf, mirna, gene, protein, metabolite, sample, pathway, "
        "omics_layer_1_feature, omics_layer_2_feature, unknown. Never use regulator or target "
        "as entity_type literals. Empty lists are valid for unstated entities. "
        "regulator_types and target_types apply only to regulatory-network artifacts; "
        "community_assignment has empty regulator_types/target_types/unresolved role fields.\n"
        + SCIENTIFIC_GUIDANCE_INSTRUCTIONS
        + "\nChoose the scientific object from this ontology:\n" + ontology
        + "\nRegulators, their binding sites and targets describe regulation; association "
        "among gene measurements describes co-expression. A probability preference does "
        "not change this distinction. Community detection on an existing network yields "
        "community_assignment, not a new inferred network.\n"
        "Repair the primary hypothesis and its dependent fields. Roles can stay empty "
        "when unstated. Granularity may be unknown if unstated; do not erase a known object. "
        "Add evidence for corrected fields: explicit needs verbatim original-language text_span; "
        "inferred needs an English scientific rationale, with no invented quote. "
        "Withdraw stale evidence. Keep request_mode=guidance for questions. "
        "Do not invent inputs, uncertainty outputs, biological roles, or workflow names."
    )
