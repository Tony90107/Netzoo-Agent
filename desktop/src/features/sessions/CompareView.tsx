/**
 * Sessions side by side: which workflow each ran, on which inputs, under
 * which model, and what it wrote.
 *
 * One session is one experiment, so comparing experiments is comparing
 * sessions. Everything shown is read from the saved checkpoints and their
 * sidecars; nothing is re-run and nothing is inferred.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { ComparedSession, compareSessions } from "../../transport/files";
import { useTimeZone } from "../timeline/timeZone";
import { fullTime } from "../timeline/time";
import { TagChips } from "./TagEditor";

const STATUS: Record<string, string> = {
  completed: "Completed", failed: "Failed", dry_run: "Preview only", needs_input: "Needs input",
  needs_confirmation: "Needs approval", respond_only: "Conversation",
};

function base(path: string): string {
  return path.split("/").pop() ?? path;
}

export function CompareView({
  config,
  sessionIds,
  onOpenSession,
  onOpenOutput,
  onClose,
}: {
  config: DaemonConfig;
  sessionIds: string[];
  onOpenSession: (sessionId: string) => void;
  onOpenOutput: (path: string) => void;
  onClose: () => void;
}) {
  const { zone } = useTimeZone();
  const [rows, setRows] = useState<ComparedSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setRows(null); setError(null);
    compareSessions(config, sessionIds, controller.signal)
      .then((body) => setRows(body.sessions))
      .catch((problem) => { if (!controller.signal.aborted) setError(String(problem)); });
    return () => controller.abort();
  }, [config, sessionIds.join(",")]);

  const inputFields = Array.from(new Set((rows ?? []).flatMap((row) => Object.keys(row.inputs))));
  const differs = (values: string[]) => new Set(values).size > 1;

  return (
    <section className="pane pane--wide">
      <header className="pane__header">
        Compare sessions
        <button className="pane__action" type="button" onClick={onClose}>close</button>
      </header>
      <div className="pane__scroll cmp">
        {error ? <div className="fv__error" role="alert">{error}</div> : null}
        {rows === null && !error ? <div className="pane__empty" role="status">Reading sessions…</div> : null}
        {rows && rows.length < 2 ? <div className="pane__empty">Pick at least two saved sessions to compare.</div> : null}
        {rows && rows.length >= 2 ? (
          <table className="cmp__table">
            <thead>
              <tr>
                <th scope="col" />
                {rows.map((row) => (
                  <th scope="col" key={row.session_id}>
                    <button type="button" className="cmp__open" onClick={() => onOpenSession(row.session_id)}
                      title="Open this session">{row.title || row.session_id}</button>
                    <code>{row.session_id}</code>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className={differs(rows.map((r) => r.workflow)) ? "is-diff" : ""}>
                <th scope="row">Workflow</th>
                {rows.map((row) => <td key={row.session_id}>{row.workflow || "—"}</td>)}
              </tr>
              <tr className={differs(rows.map((r) => r.status)) ? "is-diff" : ""}>
                <th scope="row">Result</th>
                {rows.map((row) => <td key={row.session_id}>{STATUS[row.status] ?? row.status}</td>)}
              </tr>
              <tr className={differs(rows.map((r) => JSON.stringify(r.models))) ? "is-diff" : ""}>
                <th scope="row">Model</th>
                {rows.map((row) => (
                  <td key={row.session_id}>{Object.entries(row.models).map(([role, name]) => (
                    <div key={role}><span className="cmp__role">{role}</span> {name}</div>
                  ))}{Object.keys(row.models).length ? null : "not recorded"}</td>
                ))}
              </tr>
              {inputFields.map((field) => (
                <tr key={field} className={differs(rows.map((r) => r.inputs[field] ?? "")) ? "is-diff" : ""}>
                  <th scope="row">{field.replace(/_file$/, "").replace(/_/g, " ")}</th>
                  {rows.map((row) => <td key={row.session_id} title={row.inputs[field] ?? ""}>{row.inputs[field] ? base(row.inputs[field]) : "—"}</td>)}
                </tr>
              ))}
              <tr>
                <th scope="row">Outputs</th>
                {rows.map((row) => (
                  <td key={row.session_id}>
                    {row.outputs.length === 0 ? "none written" : row.outputs.slice(0, 6).map((path) => (
                      <div key={path}><button type="button" className="cmp__file" title={path}
                        onClick={() => onOpenOutput(path)}>{base(path)}</button></div>
                    ))}
                    {row.outputs.length > 6 ? <div className="cmp__more">+{row.outputs.length - 6} more</div> : null}
                  </td>
                ))}
              </tr>
              <tr>
                <th scope="row">Tags</th>
                {rows.map((row) => <td key={row.session_id}><TagChips tags={row.tags} />{row.tags.length ? null : "—"}</td>)}
              </tr>
              <tr>
                <th scope="row">Tokens</th>
                {rows.map((row) => <td key={row.session_id}>{row.total_tokens.toLocaleString()}</td>)}
              </tr>
              <tr>
                <th scope="row">Updated</th>
                {rows.map((row) => <td key={row.session_id}>{fullTime(new Date(row.updated_at * 1000).toISOString(), zone)}</td>)}
              </tr>
            </tbody>
          </table>
        ) : null}
        {rows && rows.length >= 2 ? <p className="cmp__note">Rows that differ between the sessions are highlighted.</p> : null}
      </div>
    </section>
  );
}
