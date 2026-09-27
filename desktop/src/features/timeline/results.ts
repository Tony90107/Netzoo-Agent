import type { TraceEvent } from "../../transport/protocol";
import { actionLabel, buildRuns } from "./model";

const strings = (value: unknown): string[] => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && !!item.trim()) : [];
const text = (value: unknown) => typeof value === "string" ? value : "";

/** Advice is a display-only suggestion. It never relaxes the input or execution gates. */
export function repairSteps(errors: string[], hint?: unknown): string[] {
  const error = errors.join("\n").toLowerCase();
  const steps: string[] = [];
  if (/without a species|set taxon|taxon.*missing|species.*required/.test(error)) steps.push("Specify the organism (for example human / 9606) and inspect the inputs again before approving execution.");
  if (/not recognized.*gene authority|unknown gene|unrecognized.*gene/.test(error)) steps.push("Check the gene IDs against the selected organism. Use consistent, supported identifiers in every input. If these are intentionally synthetic fixtures, select Synthetic Test mode; keep that mode off for real analysis.");
  if (/filenotfound|no such file|file.*not found|missing.*file|path.*does not exist/.test(error)) steps.push("Check the input path and filename in the workspace. Select the existing file and rebuild the plan before retrying.");
  if (/docker|daemon.*not running|image.*not found|image.*missing|container.*unavailable/.test(error)) steps.push("Open Environment or run /doctor. Start Docker and resolve the missing NetZoo image shown by the environment check, then check again.");
  if (/modulenotfound|importerror|no module named|command not found|executable.*not found/.test(error)) steps.push("Check the missing dependency in Environment and the Method guide. Rebuild the configured NetZoo image with that dependency, then retry the checked plan.");
  if (/permission denied|permissionerror|read.only file|not writable/.test(error)) steps.push("Choose a writable output directory and check Docker's access to the workspace. Keep the original inputs unchanged.");
  if (/out of memory|memoryerror|cannot allocate memory|exit.*137/.test(error)) steps.push("Increase Docker's available memory or select a smaller validated dataset. Rebuild the plan before retrying.");
  if (/overlap|dimension|shape|identifier.*mismatch|incompatible.*identifier/.test(error)) steps.push("Inspect all inputs together. Check the matrix dimensions and shared gene / regulator identifiers, and select files from the same dataset bundle.");
  if (/delimiter|non.numeric|numeric.*required|invalid.*format|parse.*error|malformed|expected.*column/.test(error)) steps.push("Check the required columns, delimiter, headers and numeric values in the Method guide. Correct a copy of the input, then inspect it again.");
  if (/timeout|timed out|connection.*error|rate.limit|quota|429/.test(error)) steps.push("Check the named service's connection, quota and retry timing. Retry after it is available; a retry still requires the normal plan checks.");
  if (text(hint)) steps.push(`Recorded recovery hint: ${text(hint)}`);
  return [...new Set(steps.length ? steps : ["Expand the full error below and locate the failing tool or stage. Check its required inputs in the Method guide, correct the reported cause, then rebuild and review the plan before retrying."])];
}

export function outputPath(path: string): string | null {
  const normalized = path.replace(/^\/work\//, "");
  return normalized.startsWith("outputs/") && !normalized.split("/").some((part) => part === ".." || part === "." || !part) && !/[\\\x00-\x1f]/.test(normalized) ? normalized : null;
}

export function buildResults(events: TraceEvent[]) {
  return buildRuns(events).map((run) => {
    const group = events.filter((event) => event.run_id === run.id).sort((a, b) => a.sequence - b.sequence);
    const tools = group.filter((event) => event.event_type === "tool.completed").map((event) => {
      const p = event.payload;
      const errors = strings(p.errors);
      if (p.status === "failed" && !errors.length) errors.push(text(p.summary) || "The tool failed without a detailed error.");
      return { id: event.event_id, action: actionLabel(text(p.action) || event.node), status: text(p.status), summary: text(p.summary),
        errors, warnings: strings(p.warnings), artifacts: strings(p.artifacts), superseded: p.superseded === true,
        repairs: errors.length ? repairSteps(errors, p.recovery_hint) : [],
        metrics: Object.entries(p.metrics && typeof p.metrics === "object" ? p.metrics : {}).filter(([key, value]) => typeof value === "number" && /rows|samples|genes|edges|regulators|values|validated_artifacts/.test(key)),
      };
    });
    const errors = group.filter((event) => event.event_type === "error.recorded" || event.event_type === "plan.rejected").map((event) => ({
      id: event.event_id, message: [text(event.payload.error_type), text(event.payload.message)].filter(Boolean).join(": ") || "An error was recorded without details.",
    }));
    for (const error of errors) {
      const original = group.find((event) => event.event_id === error.id)!;
      if (original.event_type === "plan.rejected") error.message = text(original.payload.summary) || "The plan was rejected. Review its required inputs and validation findings before execution.";
    }
    const terminal = group.filter((event) => event.event_type === "run.finished").at(-1);
    const usage = terminal?.payload.token_usage;
    const tokens = usage && typeof usage === "object" && "total_tokens" in usage && typeof usage.total_tokens === "number" ? usage.total_tokens : null;
    const analysis = tools.filter((tool) => !tool.superseded && tool.action !== "Inspect input data");
    const outcome = run.status === "Failed" ? "Execution failed" : analysis.length && analysis.every((tool) => tool.status === "dry_run") ? "Command preview · analysis was not executed" : run.status === "Completed" ? analysis.length ? "Workflow completed" : tools.length ? "Input inspection completed" : "Conversation completed · no workflow executed" : run.status;
    const outputs = new Set(tools.filter((tool) => tool.status === "success" && !tool.superseded).flatMap((tool) => tool.artifacts)).size;
    const plannedOutputs = new Set(tools.filter((tool) => tool.status === "dry_run" && !tool.superseded).flatMap((tool) => tool.artifacts)).size;
    const warnings = new Set(tools.flatMap((tool) => tool.warnings)).size;
    return { ...run, tools, errors, tokens, outcome, outputs, plannedOutputs, warnings };
  });
}
