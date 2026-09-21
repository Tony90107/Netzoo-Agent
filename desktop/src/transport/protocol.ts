/**
 * The wire format, mirrored from scripts/netzoo_agent_core/server/protocol.py.
 *
 * Hand-written for now. Section 7 of the architecture note generates these
 * from the Pydantic contracts with a drift check in CI; until that lands,
 * changing one side means changing the other, and the daemon's tests are
 * what catch a mismatch.
 */

export const PROTOCOL_VERSION = 1;
export const WS_TOKEN_SUBPROTOCOL = "netzoo.bearer";

export type Envelope<P = Record<string, unknown>> = {
  v: number;
  type: string;
  session_id: string;
  seq: number;
  payload: P;
};

/** Which question the agent is asking; decides the whole input area. */
export type PromptKind =
  | "main"
  | "clarification"
  | "input_confirmation"
  | "preference_confirmation"
  | "execution_confirmation";

export type InputEvidence = {
  field: string;
  status:
    | "provided"
    | "selected"
    | "discovered"
    | "derived"
    | "demo_bundle"
    | "defaulted"
    | "missing";
  value: string | null;
  reason: string;
  candidates: string[];
  candidate_bundle_ids: string[];
  bundle_id: string | null;
};

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
  memory_notes: string[];
  policy_notes: string[];
  recovery_action: string | null;
  recovery_attempt: number;
  preference_proposals: { key: string; value: string; reason: string }[];
};

export type NextTurnPrompt = {
  kind: string;
  question: string;
  expected_field: string | null;
  required_fields: string[];
};

export type ViewPayload = {
  prompt_kind: PromptKind;
  /** The exact string the terminal would print. Kept for parity and fallback. */
  text: string;
  menu_enabled: boolean;
  mode: "Planning" | "Execute" | "Test";
  plan: WorkflowPlan | null;
  plan_hash: string | null;
  next_prompt: NextTurnPrompt | null;
  /** The one input the clarification wizard is asking for right now. */
  target_field: string | null;
  /** True while the answer picks a whole input bundle rather than one field. */
  choosing_bundle: boolean;
  /** True when the plan failed validation; this mode accepts field=path. */
  preflight_correction: boolean;
};

export type TraceEvent = {
  event_id: string;
  run_id: string;
  sequence: number;
  event_type: string;
  occurred_at: string;
  node: string;
  payload: Record<string, unknown>;
};

export type UsagePayload = {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  budget_tokens: number;
};

export type ServerMessage =
  | { type: "ready"; payload: { session_id: string } }
  | { type: "view"; payload: ViewPayload }
  | { type: "message"; payload: { text: string } }
  | { type: "notice"; payload: { text: string } }
  | { type: "progress"; payload: { text: string } }
  | { type: "trace"; payload: TraceEvent }
  | { type: "turn_started"; payload: { task: string; execute_once: boolean } }
  | { type: "turn_finished"; payload: Record<string, never> }
  | { type: "usage"; payload: UsagePayload }
  | { type: "error"; payload: { error_type: string; message: string; expected_plan_hash?: string } }
  | { type: "stopped"; payload: { exit_code: number } }
  | { type: "pong"; payload: Record<string, never> };

export type ClientMessage =
  | { type: "answer"; text: string }
  | { type: "approve_execution"; plan_hash: string }
  | { type: "decline_execution" }
  | { type: "cancel" }
  | { type: "ping" };
