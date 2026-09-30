/**
 * What has been asked before, and a way back into it.
 *
 * The list is read from the same checkpoints the terminal writes, so a
 * session started in one can be resumed in the other. Only a session the
 * agent paused mid-question can be resumed; the rest are history, and the
 * pane says which is which rather than offering a button that would fail.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { SessionSummary, TagCount, listSessions, listTags, type SessionFilter } from "../../transport/files";
import { TagChips, tagField } from "./TagEditor";

import { useTimeZone } from "../timeline/timeZone";
import { fullTime, relativeTime as when } from "../timeline/time";

const STATUS_LABELS: Record<string, string> = {
  needs_input: "Needs input", needs_confirmation: "Needs approval", completed: "Completed",
  failed: "Failed", dry_run: "Preview only", ready: "Plan ready", respond_only: "Conversation", unknown: "Unknown",
};

/** Labels first, then one group per field, so `dataset:` values sit together. */
function TagOptions({ tags }: { tags: TagCount[] }) {
  const labels = tags.filter((item) => !tagField(item.tag));
  const fields = new Map<string, TagCount[]>();
  for (const item of tags) {
    const field = tagField(item.tag);
    if (field) fields.set(field.key, [...(fields.get(field.key) ?? []), item]);
  }
  if (fields.size === 0) return <>{labels.map((item) => <option key={item.tag} value={item.tag}>{item.tag} ({item.count})</option>)}</>;
  return (
    <>
      {labels.length ? <optgroup label="Labels">
        {labels.map((item) => <option key={item.tag} value={item.tag}>{item.tag} ({item.count})</option>)}
      </optgroup> : null}
      {[...fields].map(([key, items]) => (
        <optgroup key={key} label={key}>
          {items.map((item) => <option key={item.tag} value={item.tag}>{key}: {tagField(item.tag)!.value} ({item.count})</option>)}
        </optgroup>
      ))}
    </>
  );
}

function shortModel(models?: Record<string, string>): string {
  const name = models?.response || models?.router || "";
  return name.split("/").pop() ?? "";
}

export function SessionsPane({
  config,
  currentId,
  selectedId,
  onResume,
  onOpen,
  onCompare,
  refreshToken,
  changeToken = 0,
}: {
  config: DaemonConfig;
  currentId: string | null;
  selectedId: string | null;
  onResume: (sessionId: string) => void;
  onOpen: (sessionId: string) => void;
  onCompare?: (sessionIds: string[]) => void;
  refreshToken?: boolean;
  /** Changes when a session's name, notes or tags were edited elsewhere in the window. */
  changeToken?: number;
}) {
  const { zone } = useTimeZone();
  const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<SessionFilter>("all");
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [tag, setTag] = useState("");
  const [knownTags, setKnownTags] = useState<TagCount[]>([]);
  const [comparing, setComparing] = useState(false);
  const [picked, setPicked] = useState<string[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    // Tags are an aid to finding sessions; a daemon without them lists as before.
    void Promise.resolve()
      .then(() => listTags(config, controller.signal))
      .then((body) => { if (body?.tags && !controller.signal.aborted) setKnownTags(body.tags); })
      .catch(() => undefined);
    return () => controller.abort();
  }, [config, currentId, refreshToken, revision, changeToken]);

  // A fresh checkpoint can move to the top or change its saved state. Refresh
  // from the first page instead of appending an outdated later page.
  useEffect(() => { setOffset(0); }, [config, currentId, refreshToken, tag]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    const timer = window.setTimeout(() => {
      void listSessions(config, tag ? { query, status, offset, tag } : { query, status, offset }, controller.signal).then((page) => {
        if (controller.signal.aborted) return;
        setSessions((old) => offset ? [...(old ?? []).filter((item) => !page.sessions.some((next) => next.session_id === item.session_id)), ...page.sessions] : page.sessions);
        setNextOffset(page.next_offset);
      }).catch((problem) => {
        if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : String(problem));
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, query.trim() ? 200 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [config, currentId, query, status, offset, revision, refreshToken, tag, changeToken]);

  const togglePick = (sessionId: string) => setPicked((current) =>
    current.includes(sessionId) ? current.filter((id) => id !== sessionId) : [...current, sessionId].slice(-4));

  return (
    <section className="pane">
      <header className="pane__header">
        Sessions
        {onCompare ? (
          <button className="pane__action" type="button" aria-pressed={comparing}
            title="Pick two to four sessions to compare their workflows, inputs, models and outputs"
            onClick={() => { setComparing((value) => !value); setPicked([]); }}>
            {comparing ? "done" : "compare"}
          </button>
        ) : null}
        <button className="pane__action" type="button" disabled={loading} onClick={() => { setOffset(0); setRevision((value) => value + 1); }}>
          refresh
        </button>
      </header>
      <div className="sl__controls">
        <label>Search sessions<input type="search" maxLength={200} placeholder="Name, request, tag or notes" value={query} onChange={(event) => { setQuery(event.target.value); setOffset(0); }} /></label>
        <label>Latest saved state<select value={status} onChange={(event) => { setStatus(event.target.value as SessionFilter); setOffset(0); }}>
          <option value="all">All states</option><option value="needs_input">Needs input</option><option value="needs_confirmation">Needs approval</option>
          <option value="failed">Failed</option><option value="completed">Completed</option><option value="dry_run">Preview only</option>
        </select></label>
        {knownTags.length > 0 || tag ? (
          <label>Tag<select value={tag} onChange={(event) => setTag(event.target.value)}>
            <option value="">All tags</option>
            {tag && !knownTags.some((item) => item.tag === tag) ? <option value={tag}>{tag}</option> : null}
            <TagOptions tags={knownTags} />
          </select></label>
        ) : null}
      </div>
      {comparing ? (
        <div className="sl__compare">
          <span>{picked.length ? `${picked.length} selected` : "Pick sessions to compare"}</span>
          <button className="btn btn--primary btn--small" type="button" disabled={picked.length < 2}
            onClick={() => { onCompare?.(picked); setComparing(false); setPicked([]); }}>Compare</button>
        </div>
      ) : null}
      <div className="pane__scroll">
        {error ? <div className="fv__error" role="alert">{error}</div> : null}
        {(loading && offset === 0) || sessions === null ? (
          <div className="pane__empty" role="status">{error ? "History could not be loaded. Use refresh to try again." : "Reading history…"}</div>
        ) : sessions.length === 0 ? (
          <div className="pane__empty">{query || status !== "all" ? "No matching sessions. Try another search or clear the filters." : "No earlier sessions."}</div>
        ) : (
          <ul className="sl">
            {sessions.map((session) => (
              <li
                key={session.session_id}
                className={`sl__item${
                  session.session_id === currentId ? " is-current" : ""
                }${session.session_id === selectedId ? " is-selected" : ""}`}
              >
                {comparing ? (
                  <input type="checkbox" className="sl__pick" aria-label={`Compare ${session.name || session.title || session.session_id}`}
                    checked={picked.includes(session.session_id)} onChange={() => togglePick(session.session_id)} />
                ) : null}
                <button
                  className="sl__open"
                  type="button"
                  title="Read this session"
                  aria-current={session.session_id === selectedId ? "page" : undefined}
                  onClick={() => (comparing ? togglePick(session.session_id) : onOpen(session.session_id))}
                >
                  <span className="sl__title">
                    {session.name || session.title || "(no request recorded)"}
                  </span>
                  {session.name && session.title ? <span className="sl__request" title={session.title}>{session.title}</span> : null}
                  <span className="sl__meta">
                    <span>{session.workflow || "—"}</span>
                    <span title={fullTime(new Date(session.updated_at * 1000).toISOString(), zone)}>{when(session.updated_at)}</span>
                    {session.total_tokens > 0 ? (
                      <span>{session.total_tokens.toLocaleString()}t</span>
                    ) : null}
                    {session.output_count ? <span title={(session.outputs ?? []).join("\n")}>{session.output_count} out</span> : null}
                    {shortModel(session.models) ? <span title={Object.entries(session.models ?? {}).map(([role, name]) => `${role}: ${name}`).join("\n")}>{shortModel(session.models)}</span> : null}
                    {session.notes_preview ? <span className="sl__notes" title={session.notes_preview}>notes</span> : null}
                  </span>
                  <TagChips tags={session.tags ?? []} />
                </button>
                {session.resumable && session.session_id !== currentId ? (
                  <button
                    className="btn btn--quiet btn--small"
                    type="button"
                    title="Reopen this session where the agent left off"
                    onClick={() => onResume(session.session_id)}
                  >
                    Resume
                  </button>
                ) : (
                  <span className="sl__status">
                    {session.session_id === currentId ? "Current" : STATUS_LABELS[session.status] ?? session.status.replace(/_/g, " ")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
        {nextOffset !== null && !error && (!loading || offset > 0) ? <div className="sl__more"><button className="btn btn--quiet btn--small" disabled={loading} type="button" onClick={() => setOffset(nextOffset)}>{loading ? "Loading…" : "Load older sessions"}</button></div> : null}
      </div>
    </section>
  );
}
