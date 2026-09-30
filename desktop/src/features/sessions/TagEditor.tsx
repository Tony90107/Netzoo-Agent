/**
 * Tags on a session: short labels a person uses to find and group experiments.
 *
 * Saved beside the checkpoint by the daemon, which trims, de-duplicates and
 * bounds them; the editor shows what the daemon kept, not what was typed.
 */
import { KeyboardEvent, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { saveTags } from "../../transport/files";

export function TagChips({ tags, onPick }: { tags: string[]; onPick?: (tag: string) => void }) {
  if (!tags.length) return null;
  return (
    <span className="tags">
      {tags.map((tag) => onPick ? (
        <button key={tag} type="button" className="tag tag--link" title={`Show sessions tagged “${tag}”`}
          onClick={(event) => { event.stopPropagation(); onPick(tag); }}>{tag}</button>
      ) : <span key={tag} className="tag">{tag}</span>)}
    </span>
  );
}

export function TagEditor({
  config,
  sessionId,
  tags,
  onSaved,
}: {
  config: DaemonConfig;
  sessionId: string;
  tags: string[];
  onSaved?: (tags: string[]) => void;
}) {
  const [current, setCurrent] = useState(tags);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { setCurrent(tags); }, [sessionId, tags.join("\u0000")]);

  const save = async (next: string[]) => {
    setSaving(true); setError(null);
    try {
      const saved = (await saveTags(config, sessionId, next)).tags;
      setCurrent(saved);
      onSaved?.(saved);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : String(problem));
    } finally {
      setSaving(false);
    }
  };

  const add = () => {
    const values = draft.split(",").map((value) => value.trim()).filter(Boolean);
    if (!values.length) return;
    setDraft("");
    void save([...current, ...values]);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if ((event.key === "Enter" || event.key === ",") && !event.nativeEvent.isComposing) {
      event.preventDefault();
      add();
    } else if (event.key === "Backspace" && !draft && current.length) {
      void save(current.slice(0, -1));
    }
  };

  return (
    <div className="tagedit" aria-busy={saving}>
      {current.map((tag) => (
        <span key={tag} className="tag">
          {tag}
          <button type="button" className="tag__remove" aria-label={`Remove tag ${tag}`}
            onClick={() => void save(current.filter((item) => item !== tag))}>×</button>
        </span>
      ))}
      <input
        className="tagedit__input"
        value={draft}
        maxLength={32}
        placeholder={current.length ? "Add tag" : "Add a tag, e.g. pilot"}
        aria-label="Add a tag to this session"
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={add}
      />
      {error ? <span className="tagedit__error" role="alert">{error}</span> : null}
    </div>
  );
}
