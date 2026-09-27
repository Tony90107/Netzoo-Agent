"""Routing and capability decision contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import ActionName, ArtifactType, IntentType, PreferenceKey, RecommendedAction

from .outcomes import (
    RUNNABLE_CAPABILITY_COUNT,
    AdvisoryRecommendation,
    CapabilityMatchStatus,
    MatchBasis,
    OutcomeHypothesis,
    RejectedMethod,
    RequestedOutcome,
)

class PreferenceProposal(BaseModel):
    key: PreferenceKey
    value: str
    reason: str


class IntentDecision(BaseModel):
    """LLM-owned answer/execute choice with no workflow-selection authority."""

    mode: Literal["answer", "execute"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=300)


class RouterDecision(BaseModel):
    """LLM-owned semantic routing proposal, bounded by the action allowlist."""

    action: ActionName
    selected_action: ActionName | None = Field(
        default=None,
        description="Selected action; action remains as the migration-compatible alias.",
    )
    candidate_actions: list[ActionName] = Field(default_factory=list, max_length=6)
    in_scope: bool = True
    intent_type: IntentType = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=600)
    semantic_goal: str | None = Field(default=None, max_length=240)
    clarification_question: str | None = Field(default=None, max_length=300)
    outcome_hypotheses: list[OutcomeHypothesis] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Bounded interpretations of the scientific result. Preserve competing "
            "interpretations instead of erasing known evidence. An empty list "
            "triggers one workflow-independent semantic interpretation call."
        )
    )

    @property
    def requested_outcome(self) -> RequestedOutcome | None:
        """Compatibility view until all consumers read outcome hypotheses directly."""
        if len(self.outcome_hypotheses) != 1:
            return None
        return self.outcome_hypotheses[0].outcome

class TaskDecision(BaseModel):
    """A capability-aware routing decision for the allow-listed NetZoo agent."""

    action: ActionName
    in_scope: bool = Field(
        description="True only when the requested operation is supported by this agent."
    )
    should_execute: bool = Field(
        description="True only when a tool call is necessary to fulfil the request now."
    )
    intent_type: IntentType = Field(
        default="unknown",
        description=(
            "High-level user intent. answer_question means explain concepts, "
            "formats, inputs, or usage without running local tools."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    candidate_actions: list[ActionName] = Field(default_factory=list, max_length=6)
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list,
        description=(
            "Code-owned exact match or fallback candidate sequence, distinguished by "
            "capability_match_status. Router output must not populate this field."
        ),
    )
    requested_outcome: RequestedOutcome | None = None
    guidance_input_artifacts: list[ArtifactType] = Field(
        default_factory=list, max_length=4,
        description="Candidate-compatible lexical input clues; not a validated current-input classification, user goal or execution authority.",
    )
    outcome_hypotheses: list[OutcomeHypothesis] = Field(
        default_factory=list, max_length=3
    )
    capability_match_status: CapabilityMatchStatus | None = None
    match_basis: MatchBasis = "semantic"
    rejected_methods: list[RejectedMethod] = Field(default_factory=list)
    # Exact matches can be either a runnable scientific capability or a direct
    # retrieval action such as ``web_search``/``query_context7``.  Keep this
    # field aligned with the registry's ActionName contract; the narrower
    # RecommendedAction type is reserved for workflow recommendations and
    # compositions.
    matched_actions: list[ActionName] = Field(default_factory=list)
    # Same bound as CapabilityMatch, from the same registry-derived source.
    # `assembly` copies the match straight into this field, so a cap of its own
    # only decides how many candidates it takes to abort the run.
    hypothesis_actions: list[RecommendedAction] = Field(
        default_factory=list, max_length=RUNNABLE_CAPABILITY_COUNT
    )
    alternative_actions: list[RecommendedAction] = Field(default_factory=list)
    mismatch_dimensions: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    # Advisory only (Log 139): a preferred candidate among tied workflows,
    # backed by quoted experimental conditions. It never changes action,
    # should_execute, capability_match_status or matched_actions.
    # Omitted from dumps while unset, so every existing serialized decision is
    # byte-identical to before this field existed.
    advisory_recommendation: AdvisoryRecommendation | None = Field(
        default=None, exclude_if=lambda value: value is None,
    )
    # Folders whose file contents routing read to advise among tied
    # workflows (Log 154); lets every reply say so truthfully. Omitted from
    # dumps while empty.
    inspected_directories: list[str] = Field(
        default_factory=list, exclude_if=lambda value: not value,
    )
    # Files in those folders that validated by content for an input role,
    # as `role=path`, reported without being used (Log 188). Omitted from
    # dumps while empty.
    discovered_inputs: list[str] = Field(
        default_factory=list, exclude_if=lambda value: not value,
    )
    missing_inputs: list[str] = Field(default_factory=list)
    expression_file: str | None = None
    design_file: str | None = None
    motif_file: str | None = None
    ppi_file: str | None = None
    mirna_file: str | None = None
    coexpression_file: str | None = None
    taxon: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        description=(
            "Requested organism or taxon for gene validation, such as "
            "Homo sapiens or Mus musculus; leave unset when the user did not specify one."
        ),
    )
    output_file: str | None = None
    lioness_output: str | None = None
    network_file: str | None = None
    mutation_file: str | None = None
    exon_size_file: str | None = None
    cancer_gene_file: str | None = None
    pathway_file: str | None = None
    omics_layer_1: str | None = None
    omics_layer_2: str | None = None
    output_dir: str | None = None
    prefix: str | None = None
    norm_patient: bool = True
    kmin: int = Field(default=2, ge=2)
    kmax: int = Field(default=4, ge=2)
    gmt_msigdb: bool = True
    subset_cancer_genes: bool = True
    distance: str = Field(default="binomial", min_length=1, max_length=80)
    linkage: str = Field(default="complete", min_length=1, max_length=80)
    cluster: bool = True
    with_header: bool = False
    # BONOBO's API-specific output and sample-selection controls are kept
    # separate from the shared DRAGON/OTTER output_format field.
    bonobo_output_format: Literal[".h5", ".hdf", ".txt", ".csv"] = ".h5"
    sample_names: list[str] = Field(default_factory=list)
    sparsify: bool = False
    bonobo_confidence: float = Field(default=0.05, gt=0.0, lt=1.0)
    save_pvals: bool = False
    keep_in_memory: bool = False
    delta: float | None = Field(default=None, gt=0.0, le=1.0)
    log_transformed: bool | None = None
    centered: bool | None = None
    genes_axis: Literal["auto", "rows", "columns"] = "auto"
    output_format: Literal["matrix", "edge_list"] = "matrix"
    computing: Literal["cpu", "gpu"] = "cpu"
    precision: Literal["single", "double"] = "double"
    lam: float = Field(default=0.035, ge=0.0, le=1.0)
    gamma: float = Field(default=0.335, ge=0.0)
    iterations: int = Field(default=60, ge=1)
    eta: float = Field(default=0.00001, gt=0.0)
    bexp: float = Field(default=1.0, gt=0.0)
    lambda1: float | None = Field(default=None, ge=0.0, le=1.0)
    lambda2: float | None = Field(default=None, ge=0.0, le=1.0)
    library_name: str | None = None
    library_id: str | None = None
    docs_query: str | None = None
    web_query: str | None = None
    preference_updates: list[PreferenceProposal] = Field(default_factory=list)

__all__ = ['IntentDecision', 'PreferenceProposal', 'RouterDecision', 'TaskDecision']
