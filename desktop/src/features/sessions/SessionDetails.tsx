/**
 * A session's name and notes: what a person calls an experiment, and what
 * they want to remember about it (why it ran, on which data, what it showed).
 *
 * Saved beside the checkpoint by the daemon, which trims and bounds them; the
 * editors show what the daemon kept, not what was typed. The agent never
 * reads either, so neither can change what it does.
 */
import { KeyboardEvent, useEffect, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { saveDetails } from "../../transport/files";

export const MAX_NAME = 80;
export const MAX_NOTES = 4000;

function message(problem: unknown): string {
  return problem instanceof Error ? problem.message : String(problem);
}

/** The name, edited in place: Enter or leaving the field saves, Escape cancels. */
export function SessionName({
  config,
  sessionId,
  name,
  placeholder = "Name this session",
  onSaved,
}: {
  config: DaemonConfig;
  sessionId: string;
  name: string;
  placeholder?: string;
  onSaved?: (name: string) => void;
}) {
  const [current, setCurrent] = useState(name);
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  // Enter unmounts the field, and a blur can follow; one save is enough.
  const saving = useRef(false);
  const editing = draft !== null;

  useEffect(() => { setCurrent(name); setDraft(null); }, [sessionId, name]);
  useEffect(() => { if (editing) input.current?.select(); }, [editing]);

  const save = async (value: string) => {
    if (saving.current) return;
    saving.current = true;
    setDraft(null);
    try {
      if (value.trim() === current) return;
      const saved = await saveDetails(config, sessionId, { name: value });
      setCurrent(saved.name);
      setError(null);
      onSaved?.(saved.name);
    } catch (problem) {
      setError(message(problem));
    } finally {
      saving.current = false;
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing) return;
    if (event.key === "Enter") { event.preventDefault(); void save(event.currentTarget.value); }
    else if (event.key === "Escape") { event.preventDefault(); setDraft(null); }
  };

  if (editing) {
    return (
      <input
        ref={input}
        className="sname__input"
        value={draft}
        maxLength={MAX_NAME}
        placeholder={placeholder}
        aria-label="Session name"
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={(event) => void save(event.currentTarget.value)}
      />
    );
  }
  return (
    <span className="sname">
      <button
        type="button"
        className={`sname__text${current ? "" : " is-empty"}`}
        title={current ? "Rename this session" : "Give this session a name you will recognise"}
        onClick={() => setDraft(current)}
      >
        {current || placeholder}
      </button>
      {error ? <span className="tagedit__error" role="alert">{error}</span> : null}
    </span>
  );
}

/** Notes on the experiment; Save or ⌘/Ctrl-Enter stores them. */
export function NotesEditor({
  config,
  sessionId,
  notes,
  autoFocus = false,
  onSaved,
}: {
  config: DaemonConfig;
  sessionId: string;
  notes: string;
  autoFocus?: boolean;
  onSaved?: (notes: string) => void;
}) {
  const [saved, setSaved] = useState(notes);
  const [draft, setDraft] = useState(notes);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = useState("");

  useEffect(() => { setSaved(notes); setDraft(notes); setStatus("idle"); }, [sessionId, notes]);

  const dirty = draft !== saved;
  const save = async () => {
    if (!dirty || status === "saving") return;
    setStatus("saving");
    try {
      const result = await saveDetails(config, sessionId, { notes: draft });
      setSaved(result.notes);
      setDraft(result.notes);
      setStatus("saved");
      onSaved?.(result.notes);
    } catch (problem) {
      setError(message(problem));
      setStatus("error");
    }
  };

  const note = status === "saving" ? "Saving…"
    : status === "saved" && !dirty ? "Saved"
    : status === "error" ? error
    : dirty ? "Unsaved · ⌘Enter saves"
    : "";
  return (
    <div className="notes">
      <textarea
        className="notes__text"
        rows={4}
        value={draft}
        maxLength={MAX_NOTES}
        autoFocus={autoFocus}
        aria-label="Session notes"
        placeholder="Why you ran it, which data version, what you concluded…"
        onChange={(event) => { setDraft(event.target.value); if (status !== "saving") setStatus("idle"); }}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); void save(); }
        }}
      />
      <div className="notes__actions">
        <span className={`notes__status${status === "error" ? " is-error" : ""}`} role={status === "error" ? "alert" : undefined}>{note}</span>
        <button className="btn btn--quiet btn--small" type="button" disabled={!dirty || status === "saving"} onClick={() => setDraft(saved)}>
          Revert
        </button>
        <button className="btn btn--primary btn--small" type="button" disabled={!dirty || status === "saving"} onClick={() => void save()}>
          Save notes
        </button>
      </div>
    </div>
  );
}

/** The current session's notes, opened from the header. */
export function NotesButton({
  config,
  sessionId,
  notes,
  onSaved,
}: {
  config: DaemonConfig;
  sessionId: string;
  notes: string;
  onSaved?: (notes: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const node = dialog.current;
    if (open && node && !node.open && typeof node.showModal === "function") node.showModal();
  }, [open]);

  return (
    <>
      <button
        type="button"
        className={`sname__notes${notes ? " has-notes" : ""}`}
        title={notes || "Write down what this experiment is for"}
        onClick={() => setOpen(true)}
      >
        {notes ? "Notes" : "Add notes"}
      </button>
      {open ? (
        <dialog ref={dialog} className="nsd" aria-label="Session notes"
          onCancel={(event) => { event.preventDefault(); setOpen(false); }}>
          <h2 className="nsd__title">Notes</h2>
          <p className="nsd__note">What this experiment is for and what you found. Compare shows them side by side; the agent never reads them.</p>
          <NotesEditor config={config} sessionId={sessionId} notes={notes} onSaved={onSaved} autoFocus />
          <div className="nsd__actions">
            <button className="btn" type="button" onClick={() => setOpen(false)}>Close</button>
          </div>
        </dialog>
      ) : null}
    </>
  );
}
