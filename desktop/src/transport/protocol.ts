/**
 * The wire format.
 *
 * Everything the agent owns — plans, views, trace events, usage — is
 * generated from the Pydantic contracts and re-exported here, so there is one
 * definition of each and a test that fails when it drifts. What stays by hand
 * is only what the transport itself owns: the envelope, the small set of
 * things a client may say, and the message names.
 */
export type {
  InputBundleOption,
  InputEvidence,
  LLMUsage,
  NextTurnPrompt,
  PreferenceProposal,
  TraceEvent,
  ViewPayload,
  WorkflowPlan,
  WorkflowStep,
} from "../generated/contracts";

import type { ViewPayload } from "../generated/contracts";

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
export type PromptKind = ViewPayload["prompt_kind"];

/** What the window is allowed to say. Mirrors `ClientMessage` in protocol.py. */
export type ClientMessage =
  | { type: "answer"; text: string }
  | { type: "approve_execution"; plan_hash: string }
  | { type: "decline_execution" }
  | { type: "cancel" }
  | { type: "ping" };

/** What the daemon sends. Mirrors `ServerMessageType` in protocol.py. */
export type ServerMessageType =
  | "ready"
  | "view"
  | "message"
  | "notice"
  | "progress"
  | "trace"
  | "turn_started"
  | "turn_finished"
  | "usage"
  | "error"
  | "stopped"
  | "pong";
