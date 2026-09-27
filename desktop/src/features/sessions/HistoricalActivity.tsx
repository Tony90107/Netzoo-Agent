import { useEffect, useState } from "react";
import type { DaemonConfig } from "../../transport/daemon";
import type { TraceEvent } from "../../transport/protocol";
import { readEvents, readRuns, type SavedRuns } from "../../transport/activity";
import { Timeline } from "../timeline/Timeline";
import { fullTime, dateLabel, clockLabel } from "../timeline/time";
import { useTimeZone } from "../timeline/timeZone";

export function HistoricalActivity({ config, sessionId, onOpenOutput }: { config: DaemonConfig; sessionId: string; onOpenOutput?: (path: string) => void }) {
  const { zone } = useTimeZone();
  const [listing, setListing] = useState<SavedRuns | null>(null);
  const [runId, setRunId] = useState("");
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [listingBusy, setListingBusy] = useState(false);
  const [incomplete, setIncomplete] = useState(false);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setListingBusy(true); setError("");
    readRuns(config, sessionId, offset, controller.signal).then((page) => {
      if (controller.signal.aborted) return;
      setListing((old) => ({ ...page, runs: offset ? [...(old?.runs ?? []), ...page.runs] : page.runs }));
      setRunId((old) => offset ? old : page.runs.some((run) => run.run_id === old) ? old : page.runs[0]?.run_id ?? "");
    }).catch((problem) => { if (!controller.signal.aborted) setError(String(problem)); })
      .finally(() => { if (!controller.signal.aborted) setListingBusy(false); });
    return () => controller.abort();
  }, [config, sessionId, offset, revision]);

  useEffect(() => {
    const controller = new AbortController();
    setEvents([]); setNote(""); setIncomplete(false); setLoading(!!runId);
    if (runId) void (async () => {
      let after = 0; let version = ""; const all: TraceEvent[] = [];
      try {
        while (!controller.signal.aborted) {
          const page = await readEvents(config, sessionId, runId, after, version, controller.signal);
          if (controller.signal.aborted) return;
          all.push(...page.events); version = page.version;
          setEvents([...all]); setIncomplete(page.incomplete); setNote(page.note);
          if (page.next_sequence === null) break;
          if (page.next_sequence <= after) throw new Error("The event cursor did not advance. Reload this run.");
          after = page.next_sequence;
        }
      } catch (problem) {
        if (!controller.signal.aborted) { setError(String(problem)); setIncomplete(true); }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    })();
    return () => controller.abort();
  }, [config, sessionId, runId, revision]);

  const selected = listing?.runs.find((run) => run.run_id === runId);
  return <div className="historical-activity">
    <div className="history__controls">
      <details className="history__about"><summary>About saved Activity</summary><p className="set__note">Saved execution activity · read-only snapshot. Reading history does not resume the agent.</p></details>
      <div className="history__selection"><label>Saved run<select aria-label="Saved run" value={runId} title={selected ? fullTime(selected.created_at, zone) : undefined} disabled={!listing?.runs.length} onChange={(event) => { setError(""); setRunId(event.target.value); }}>
        {listing?.runs.map((run) => <option key={run.run_id} value={run.run_id}>{dateLabel(run.created_at, zone)} {clockLabel(run.created_at, zone).slice(0, 8)} · {run.status} · {run.run_id.slice(0, 8)}</option>)}
      </select></label><button type="button" className="btn btn--quiet btn--small" disabled={loading || listingBusy} onClick={() => { setOffset(0); setRevision((value) => value + 1); }}>Reload</button></div>
      {listing?.has_more ? <button type="button" className="btn btn--quiet btn--small" disabled={listingBusy} onClick={() => setOffset(listing.runs.length)}>Load older runs</button> : null}
      {selected ? <p className="log__clock">{selected.status} · {selected.run_id.slice(0, 8)} · {selected.event_count} saved events · {zone}</p> : null}
      {listing?.unavailable_metadata ? <p className="set__note">Some saved run metadata is unavailable. Those records could not be assigned to a session.</p> : null}
      {selected && !selected.sealed ? <p className="tl__incomplete">This run has no sealed end record ({selected.status}). The saved snapshot may be unfinished.</p> : null}
      {note ? <p role="status" className="tl__incomplete">{note}</p> : null}
      {error ? <p className="fv__error" role="alert">{error}</p> : null}
      {listingBusy ? <p role="status">Reading saved runs…</p> : null}
      {loading ? <p role="status">Reading execution events… {events.length} loaded. Results and exports are incomplete until loading finishes.</p> : null}
    </div>
    {!listingBusy && listing?.runs.length === 0 ? <div className="pane__empty">No saved Activity is available for this session. Older sessions may only have a conversation checkpoint, or their traces may have expired.</div> : runId ?
      <Timeline key={runId} trace={events} entries={[]} sessionId={sessionId} busy={false} incomplete={incomplete || loading || selected?.sealed === false} initialTab="results" onOpenOutput={onOpenOutput} /> : null}
  </div>;
}
