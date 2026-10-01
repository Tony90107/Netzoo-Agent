/**
 * Generated from the Pydantic contracts. Do not edit.
 *
 * Regenerate with `python scripts/generate_ui_types.py`;
 * `tests/test_ui_contract_sync.py` fails if this file is stale.
 */

/** Everything a client needs to render the current question. */
export type ViewPayload = {
  prompt_kind: "main" | "clarification" | "input_confirmation" | "preference_confirmation" | "execution_confirmation";
  text: string;
  menu_enabled: boolean;
  mode: "Planning" | "Execute" | "Test";
  plan: WorkflowPlan | null;
  plan_hash: string | null;
  next_prompt: NextTurnPrompt | null;
  target_field: string | null;
  choosing_bundle: boolean;
  preflight_correction: boolean;
  card: ReplyCard | null;
};

export type WorkflowPlan = {
  workflow: string;
  objective: string;
  decision: Record<string, unknown>;
  evidence: InputEvidence[];
  input_bundle_options: InputBundleOption[];
  steps: WorkflowStep[];
  missing_inputs: string[];
  status: "ready" | "needs_input" | "needs_confirmation" | "respond_only";
  question: string | null;
  workflow_handoff: WorkflowHandoff | null;
  preference_proposals: PreferenceProposal[];
  memory_notes: string[];
  policy_hash: string | null;
  policy_notes: string[];
  recovery_action: string | null;
  recovery_error_code: string | null;
  recovery_step_index: number | null;
  recovery_attempt: number;
};

/** Where a workflow input came from and why it is (or is not) usable. */
export type InputEvidence = {
  field: string;
  status: "provided" | "selected" | "discovered" | "derived" | "demo_bundle" | "defaulted" | "missing";
  value: string | null;
  reason: string;
  candidates: string[];
  candidate_bundle_ids: string[];
  bundle_id: string | null;
  derived_from: string | null;
};

/** One complete coherent input bundle offered as an atomic selection. */
export type InputBundleOption = {
  bundle_id: string;
  directory: string;
  inputs: Record<string, string>;
};

export type WorkflowStep = {
  action: string;
  purpose: string;
  arguments: Record<string, unknown>;
};

export type PreferenceProposal = {
  key: "default_output_dir" | "allow_demo_autofill" | "reuse_last_inputs" | "preferred_workflow";
  value: string;
  reason: string;
};

/** Outcome-aware CLI prompt plus optional workflow continuation context. */
export type NextTurnPrompt = {
  kind: "initial" | "recommended_workflow" | "dry_run" | "completed" | "failed" | "plan_rejected" | "unsupported" | "retrieval" | "clarify_outcome" | "alternative_outcome";
  question: string;
  allow_workflow_continuation: boolean;
  continuation_action: string | null;
  expected_field: string | null;
  required_fields: string[];
  alternative_action: "inspect_inputs" | "inspect_condor_inputs" | "format_expression" | "convert_expression" | "run_panda" | "run_puma" | "run_lioness_panda" | "run_lioness_puma" | "run_lioness_coexpression" | "run_condor" | "run_cobra" | "run_sambar" | "run_dragon" | "run_lioness_dragon" | "run_otter" | "run_giraffe" | "run_bonobo" | null;
  alternative_granularity: "aggregate" | "sample_specific" | "not_applicable" | "unknown" | null;
};

/** Per-task token telemetry with explicit estimated/actual provenance. */
export type LLMUsage = {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  calls: LLMCallUsage[];
  budget_tokens: number;
  budget_exhausted: boolean;
};

/** One immutable event in a per-run append-only hash chain. */
export type TraceEvent = {
  schema_version: 1;
  event_id: string;
  run_id: string;
  sequence: number;
  event_type: string;
  occurred_at: string;
  recorded_at: string;
  node: string;
  parent_event_id: string | null;
  visibility: "shareable" | "restricted" | "local_only";
  payload: Record<string, unknown>;
  previous_hash: string;
  event_hash: string;
};

/** Key points of one reply, plus its choices and next steps. */
export type ReplyCard = {
  kind: "method_choice" | "clarification" | "reading_choice" | "hypothesis_choice" | "capability_gap" | "workflow_guidance" | "composition" | "plan_ready" | "run_completed" | "run_failed" | "unresolved" | "general";
  headline: string;
  points: string[];
  choices: ReplyChoices | null;
  unavailable: ReplyOption[];
  next_steps: ReplyOption[];
  ran_nothing: boolean;
};

/** A registry-validated producer-to-consumer workflow boundary. */
export type WorkflowHandoff = {
  producer_action: "inspect_inputs" | "inspect_condor_inputs" | "format_expression" | "convert_expression" | "run_panda" | "run_puma" | "run_lioness_panda" | "run_lioness_puma" | "run_lioness_coexpression" | "run_condor" | "run_cobra" | "run_sambar" | "run_dragon" | "run_lioness_dragon" | "run_otter" | "run_giraffe" | "run_bonobo";
  producer_workflow: string;
  source_artifact_type: "measurement_dataset" | "expression_matrix" | "tf_activity_matrix" | "regulatory_network_and_tf_activity" | "signed_regulatory_effect_network" | "regulatory_network" | "coexpression_network" | "pvalue_matrix" | "mutation_matrix" | "pathway_mutation_matrix" | "gene_mutation_scores" | "sample_distance_matrix" | "sample_cluster_assignment" | "community_assignment" | "validation_report" | "multi_omic_network" | "unknown";
  source_granularity: "aggregate" | "sample_specific" | "not_applicable" | "unknown";
  produced_artifacts: ("measurement_dataset" | "expression_matrix" | "tf_activity_matrix" | "regulatory_network_and_tf_activity" | "signed_regulatory_effect_network" | "regulatory_network" | "coexpression_network" | "pvalue_matrix" | "mutation_matrix" | "pathway_mutation_matrix" | "gene_mutation_scores" | "sample_distance_matrix" | "sample_cluster_assignment" | "community_assignment" | "validation_report" | "multi_omic_network" | "unknown")[];
  source_artifact_paths: string[];
  artifact_paths: Record<string, string[]>;
  sample_ids: string[];
  gene_ids: string[];
  consumer_action: "inspect_inputs" | "inspect_condor_inputs" | "format_expression" | "convert_expression" | "run_panda" | "run_puma" | "run_lioness_panda" | "run_lioness_puma" | "run_lioness_coexpression" | "run_condor" | "run_cobra" | "run_sambar" | "run_dragon" | "run_lioness_dragon" | "run_otter" | "run_giraffe" | "run_bonobo" | null;
  consumer_workflow: string | null;
  consumer_input_field: string | null;
  required_prior_inputs: string[];
  status: "not_requested" | "validated" | "blocked_no_consumer" | "blocked_incompatible";
  reason: string;
};

/** Token, timing, and cost provenance for one provider call. */
export type LLMCallUsage = {
  call_id: string;
  role: string;
  model: string;
  provider_request_id: string | null;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  total_tokens: number;
  usage_provenance: "actual" | "estimated" | "unavailable";
  cost_provenance: "actual" | "estimated" | "unavailable";
  cost_micro_usd: number | null;
  price_snapshot: PriceSnapshot | null;
  duration_ms: number;
  status: "success" | "failed" | "blocked";
};

/** A question with ordered answers, the best-supported first. */
export type ReplyChoices = {
  header: string;
  question: string;
  options: ReplyOption[];
  allow_other: boolean;
  ordering: string;
};

/** One thing the user can pick, or a related thing this agent cannot do. */
export type ReplyOption = {
  key: string;
  label: string;
  description: string;
  answer: string;
  recommended: boolean;
  badge: "" | "Recommended" | "Best match";
  available: boolean;
  reason: string;
  action: "inspect_inputs" | "inspect_condor_inputs" | "format_expression" | "convert_expression" | "run_panda" | "run_puma" | "run_lioness_panda" | "run_lioness_puma" | "run_lioness_coexpression" | "run_condor" | "run_cobra" | "run_sambar" | "run_dragon" | "run_lioness_dragon" | "run_otter" | "run_giraffe" | "run_bonobo" | null;
  granularity: "aggregate" | "sample_specific" | null;
  resolution: "confirm_workflow" | "plan_workflow" | "follow_up" | "command" | "open_outputs" | "none";
  paths: string[];
};

/** Immutable model rates used for one historical cost estimate. */
export type PriceSnapshot = {
  snapshot_id: string;
  model: string;
  provenance: "estimated" | "unavailable";
  effective_at: string;
  input_micro_usd_per_million: number | null;
  output_micro_usd_per_million: number | null;
};
