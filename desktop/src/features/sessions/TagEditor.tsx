/**
 * Tags on a session: short labels a person uses to find and group experiments.
 *
 * A tag is a label (`pilot`) or a field (`dataset:batch-2`). A field holds one
 * value per session, so Compare can line the same field up across sessions.
 * Saved beside the checkpoint by the daemon, which trims, de-duplicates and
 * bounds them; the editor shows what the daemon kept, not what was typed.
 */
import { KeyboardEvent, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { saveTags } from "../../transport/files";

/** `{key, value}` of a field tag (`dataset:batch-2`); null for a plain label. */
export function tagField(tag: string): { key: string; value: string } | null {
  const at = tag.indexOf(":");
  return at > 0 ? { key: tag.slice(0, at), value: tag.slice(at + 1) } : null;
}

/** A tag as shown: a field's key is set apart from its value. */
export function TagLabel({ tag }: { tag: string }) {
  const field = tagField(tag);
  return field ? <><span className="tag__key">{field.key}:</span>{field.value}</> : <>{tag}</>;
}

export function TagChips({ tags, onPick }: { tags: string[]; onPick?: (tag: string) => void }) {
  if (!tags.length) return null;
  return (
    <span className="tags">
      {tags.map((tag) => onPick ? (
        <button key={tag} type="button" className="tag tag--link" title={`Show sessions tagged “${tag}”`}
          onClick={(event) => { event.stopPropagation(); onPick(tag); }}><TagLabel tag={tag} /></button>
      ) : <span key={tag} className="tag"><TagLabel tag={tag} /></span>)}
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
  const [current, setCurrent] = useState(tags ?? []);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { setCurrent(tags ?? []); }, [sessionId, (tags ?? []).join("\u0000")]);

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
          <TagLabel tag={tag} />
          <button type="button" className="tag__remove" aria-label={`Remove tag ${tag}`}
            onClick={() => void save(current.filter((item) => item !== tag))}>×</button>
        </span>
      ))}
      <input
        className="tagedit__input"
        value={draft}
        maxLength={48}
        placeholder={current.length ? "Add tag" : "Add a tag, e.g. pilot or dataset:batch-2"}
        aria-label="Add a tag to this session"
        title={"Your own labels for finding and comparing sessions: a label such as pilot, or a field such as "
          + "dataset:batch-2 or hypothesis:dna-damage. A field holds one value per session, and Compare lines "
          + "fields up side by side. Filter by tags in Sessions; tagged sessions are kept from routine cleanup. "
          + "The agent never reads them."}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={add}
      />
      {error ? <span className="tagedit__error" role="alert">{error}</span> : null}
    </div>
  );
}
