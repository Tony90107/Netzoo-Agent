/**
 * How a saved user turn reads to the person who wrote it.
 *
 * A checkpoint stores the task the agent ran, and for an answer to a
 * follow-up that is the machine's own form: the previous goal restated, a
 * confirmed-outcome marker, a workflow continuation. Those are correct for
 * the agent and unreadable in a transcript, so the transcript shows what the
 * person actually said or chose, and keeps the stored text for the tooltip.
 */

const WORKFLOW_NAMES: Record<string, string> = {
  run_panda: "PANDA",
  run_puma: "PUMA",
  run_lioness_panda: "LIONESS-PANDA",
  run_lioness_puma: "LIONESS-PUMA",
  run_lioness_coexpression: "LIONESS-COEXPRESSION",
  run_condor: "CONDOR",
  run_cobra: "COBRA",
  run_sambar: "SAMBAR",
  run_dragon: "DRAGON",
  run_otter: "OTTER",
  run_giraffe: "GIRAFFE",
  run_bonobo: "BONOBO",
  download_string: "STRING download",
};

export type UserTurn = { text: string; kind: "said" | "chose" | "continued" | "follow_up" };

function workflow(action: string): string {
  return WORKFLOW_NAMES[action] ?? action.replace(/^run_/, "").toUpperCase();
}

export function userTurn(stored: string): UserTurn {
  const confirmed = stored.match(/^CONFIRMED_OUTCOME_ACTION=([a-z_]+)\./);
  if (confirmed) return { text: `Chose ${workflow(confirmed[1])}`, kind: "chose" };
  const followUp = stored.match(/^Previous NetZoo goal:[\s\S]*?\nUser follow-up:\s*([\s\S]+)$/);
  if (followUp) return { text: followUp[1].trim(), kind: "follow_up" };
  const continued = stored.match(/PREVIOUS_ACTION=([a-z_]+)\./);
  if (continued) {
    const reply = stored.match(/\nUser reply:\s*([\s\S]+)$/);
    return {
      text: reply ? reply[1].trim() : `Continue ${workflow(continued[1])} with the selected inputs`,
      kind: "continued",
    };
  }
  return { text: stored, kind: "said" };
}
