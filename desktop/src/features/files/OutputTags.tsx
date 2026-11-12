/**
 * Tags on one output file.
 *
 * Auto tags (`method:`, `result:`, `scale:`, `mode:`) come from the record of the run that wrote the file and
 * cannot be edited; user tags are a person's own labels and fields. The daemon refuses a user tag that reuses a
 * reserved key, so the two kinds never contradict each other.
 */
import { useEffect, useState } from "react";

import type { DaemonConfig } from "../../transport/daemon";
import { readOutputTags, saveOutputTags, type OutputTags } from "../../transport/files";
import { TagEditor, TagLabel } from "../sessions/TagEditor";

export const AUTO_TAG_HELP = "Set by NetZoo from the run that wrote this file (method, result kind, scale, mode). "
  + "Replaced when a later run writes the file again; it cannot be edited.";

export function AutoTagChips({ tags, onPick }: { tags: string[]; onPick?: (tag: string) => void }) {
  if (!tags.length) return null;
  return <span className="tags">{tags.map((tag) => onPick ? (
    <button key={tag} type="button" className="tag tag--auto tag--link" title={`${AUTO_TAG_HELP}\nShow outputs tagged “${tag}”`}
      onClick={(event) => { event.stopPropagation(); onPick(tag); }}><TagLabel tag={tag} /></button>
  ) : <span key={tag} className="tag tag--auto" title={AUTO_TAG_HELP}><TagLabel tag={tag} /></span>)}</span>;
}

export function UserTagChips({ tags, onPick }: { tags: string[]; onPick?: (tag: string) => void }) {
  if (!tags.length) return null;
  return <span className="tags">{tags.map((tag) => onPick ? (
    <button key={tag} type="button" className="tag tag--link" title={`Your tag. Show outputs tagged “${tag}”`}
      onClick={(event) => { event.stopPropagation(); onPick(tag); }}><TagLabel tag={tag} /></button>
  ) : <span key={tag} className="tag" title="Your tag"><TagLabel tag={tag} /></span>)}</span>;
}

/** Every tag of a file, auto first: what filters match against. */
export function allTags(tags?: OutputTags): string[] {
  return [...(tags?.auto ?? []), ...(tags?.user ?? [])];
}

/** A file's auto tags, read-only, and an editor for the user's own. */
export function OutputTagEditor({ config, path }: { config: DaemonConfig; path: string }) {
  const [tags, setTags] = useState<OutputTags | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setTags(null); setError("");
    readOutputTags(config, path, controller.signal).then((body) => { if (!controller.signal.aborted) setTags(body); })
      .catch((problem) => { if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : String(problem)); });
    return () => controller.abort();
  }, [config, path]);
  if (error) return <div className="otags otags--error" role="alert">Tags unavailable: {error}</div>;
  if (!tags) return null;
  return <div className="otags" aria-label="Output tags">
    <span className="otags__label">Tags</span>
    <AutoTagChips tags={tags.auto} />
    <TagEditor config={config} sessionId="" tags={tags.user} onSaved={(user) => setTags((current) => current && { ...current, user })} target={{
      key: path,
      save: async (next) => (await saveOutputTags(config, path, next)).user,
      label: "Add a tag to this output file",
      placeholder: "Add your tag, e.g. baseline or dataset:pasilla",
      help: "Your own labels for this file: a label such as baseline, or a field such as dataset:pasilla. "
        + "method:, result:, scale: and mode: are set by NetZoo from the run record and cannot be typed. "
        + "Filter outputs by any tag in Outputs. The agent never reads them.",
    }} />
  </div>;
}
