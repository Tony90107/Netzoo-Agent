/**
 * Complete contract objects for tests.
 *
 * Built in one place so that a field added to a contract fails here once,
 * rather than in every test that happened to construct a plan by hand. The
 * generated types make that failure a compile error.
 */
import type {
  NextTurnPrompt,
  ReplyCard,
  ReplyOption,
  ViewPayload,
  WorkflowPlan,
} from "../transport/protocol";

export function makePlan(overrides: Partial<WorkflowPlan> = {}): WorkflowPlan {
  return {
    workflow: "LIONESS-PUMA",
    objective: "run it",
    decision: {},
    evidence: [],
    input_bundle_options: [],
    steps: [],
    missing_inputs: [],
    status: "needs_input",
    question: null,
    workflow_handoff: null,
    preference_proposals: [],
    memory_notes: [],
    policy_hash: null,
    policy_notes: [],
    recovery_action: null,
    recovery_error_code: null,
    recovery_step_index: null,
    recovery_attempt: 0,
    ...overrides,
  };
}

export function makeNextTurnPrompt(
  overrides: Partial<NextTurnPrompt> = {},
): NextTurnPrompt {
  return {
    kind: "initial",
    question: "",
    allow_workflow_continuation: true,
    continuation_action: null,
    expected_field: null,
    required_fields: [],
    alternative_action: null,
    alternative_granularity: null,
    ...overrides,
  };
}

export function makeView(overrides: Partial<ViewPayload> = {}): ViewPayload {
  return {
    prompt_kind: "main",
    text: "",
    menu_enabled: true,
    mode: "Planning",
    plan: null,
    plan_hash: null,
    next_prompt: null,
    target_field: null,
    choosing_bundle: false,
    preflight_correction: false,
    card: null,
    ...overrides,
  };
}

export function makeOption(overrides: Partial<ReplyOption> = {}): ReplyOption {
  return {
    key: "run_panda",
    label: "PANDA",
    description: "",
    answer: "Use PANDA",
    recommended: false,
    badge: "",
    available: true,
    reason: "",
    action: "run_panda",
    granularity: null,
    resolution: "confirm_workflow",
    paths: [],
    ...overrides,
  };
}

export function makeCard(overrides: Partial<ReplyCard> = {}): ReplyCard {
  return {
    kind: "method_choice",
    headline: "",
    points: [],
    choices: null,
    unavailable: [],
    next_steps: [],
    ran_nothing: true,
    ...overrides,
  };
}
