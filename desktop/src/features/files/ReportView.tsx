/**
 * A run report as a reader wants it: what happened at a glance, then the
 * details, each section folded so a long input check does not bury the result.
 *
 * Execution reports are written by `execution_log.py` in one fixed shape
 * ("# NetZoo execution summary", then "## " sections); any other Markdown is
 * shown as a plain document. Everything is rendered by the same Markdown
 * component as the agent's replies, so no raw HTML reaches the WebView.
 */
import { Markdown } from "../conversation/Markdown";
import { clockLabel, dateLabel } from "../timeline/time";
import { useTimeZone } from "../timeline/timeZone";

type Section = { heading: string; body: string };
export type ParsedReport = { title: string; sections: Section[] };

/** The report's sections, or null when the text is not an execution report. */
export function parseReport(text: string): ParsedReport | null {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const first = lines.findIndex((line) => line.trim() !== "");
  if (first < 0 || !/^#\s+NetZoo execution summary\s*$/i.test(lines[first])) return null;
  const sections: Section[] = [];
  for (const line of lines.slice(first + 1)) {
    const heading = line.match(/^##\s+(.+?)\s*$/);
    if (heading) sections.push({ heading: heading[1], body: "" });
    else if (sections.length) sections[sections.length - 1].body += `${line}\n`;
  }
  return { title: lines[first].replace(/^#\s+/, "").trim(), sections: sections.map((item) => ({ ...item, body: item.body.trim() })) };
}

/** `- Key: value` bullets, backticks dropped. */
function facts(body: string): [string, string][] {
  return body.split("\n").flatMap((line) => {
    const match = line.match(/^-\s+([^:]+):\s*(.+)$/);
    return match ? [[match[1].trim(), match[2].replace(/`/g, "").trim()] as [string, string]] : [];
  });
}

/** `- Path: …` entries with their indented Exists and Size lines. */
function outputs(body: string): { path: string; size: string; exists: boolean }[] {
  const found: { path: string; size: string; exists: boolean }[] = [];
  for (const line of body.split("\n")) {
    const path = line.match(/^-\s+Path:\s*`?([^`]+?)`?\s*$/);
    const current = found[found.length - 1];
    if (path) found.push({ path: path[1], size: "", exists: true });
    else if (current && /^\s+-\s+Size:/.test(line)) current.size = line.replace(/^\s+-\s+Size:\s*/, "").replace(/`/g, "").replace(/\s*\(.*\)$/, "");
    else if (current && /^\s+-\s+Exists:/.test(line)) current.exists = /yes/.test(line);
  }
  return found;
}

const STATUS: Record<string, [string, string]> = {
  success: ["Succeeded", "ok"], completed: ["Succeeded", "ok"], failed: ["Failed", "bad"], error: ["Failed", "bad"],
  dry_run: ["Preview only", "muted"], skipped: ["Skipped", "muted"],
};
// Sections the card above already says; long ones are folded too.
const SUMMARIZED = new Set(["summary", "result", "output artifacts", "conclusion"]);
const LONG = 30;

export function ReportView({ text, onOpenFile }: { text: string; onOpenFile?: (path: string) => void }) {
  const { zone } = useTimeZone();
  const report = parseReport(text);
  if (!report) return <Markdown className="report report__doc">{text}</Markdown>;
  const section = (name: string) => report.sections.find((item) => item.heading.toLowerCase() === name);
  const summary = facts(section("summary")?.body ?? "");
  const value = (key: string) => summary.find(([name]) => name === key)?.[1] ?? "";
  const workflow = value("Workflow").replace(/_/g, "-");
  const [statusLabel, statusKind] = STATUS[value("Status").toLowerCase()] ?? [value("Status"), "muted"];
  const when = (stamp: string) => (/\d{4}-\d{2}-\d{2}T/.test(stamp) ? `${dateLabel(stamp, zone)} ${clockLabel(stamp, zone).slice(0, 8)}` : stamp);
  const times = summary.filter(([name]) => name !== "Workflow" && name !== "Status")
    .map(([name, item]) => [name.replace(/\s*\(.*\)$/, ""), when(item)] as [string, string]);
  const conclusion = section("conclusion")?.body ?? "";
  const files = outputs(section("output artifacts")?.body ?? "");
  const warnings = (section("warnings")?.body ?? "").split("\n").filter((line) => /^-\s+/.test(line)).length;

  return (
    <div className="report">
      <section className="report__glance" aria-label="At a glance">
        <div className="report__headline">
          <span className="report__workflow">{workflow ? `${workflow} run` : report.title}</span>
          {statusLabel ? <span className={`report__status report__status--${statusKind}`}>{statusLabel}</span> : null}
        </div>
        {times.length ? (
          <dl className="report__facts">
            {times.map(([name, item]) => <div key={name}><dt>{name}</dt><dd>{item}</dd></div>)}
          </dl>
        ) : null}
        {conclusion ? <Markdown className="report__conclusion">{conclusion}</Markdown> : null}
        {files.length ? (
          <div className="report__outputs">
            <span className="report__label">Outputs</span>
            {files.map((file) => (
              <button key={file.path} type="button" className="report__file" title={file.path}
                disabled={!onOpenFile || !file.exists} onClick={() => onOpenFile?.(file.path)}>
                {file.path.split("/").pop()}{file.size ? <span> · {file.size}</span> : null}{file.exists ? null : <span> · missing</span>}
              </button>
            ))}
          </div>
        ) : null}
        {warnings ? <div className="report__warn">{warnings} warning{warnings === 1 ? "" : "s"}, listed under Warnings below</div> : null}
      </section>
      {report.sections.map((item) => {
        const lines = item.body ? item.body.split("\n").length : 0;
        const open = !SUMMARIZED.has(item.heading.toLowerCase()) && lines <= LONG;
        return (
          <details key={item.heading} className="report__section" open={open}>
            <summary>
              {item.heading}
              {lines > LONG ? <span className="report__count">{lines} lines</span> : null}
            </summary>
            {item.body ? <Markdown className="report__body">{item.body}</Markdown> : <p className="report__empty">Nothing recorded.</p>}
          </details>
        );
      })}
    </div>
  );
}
