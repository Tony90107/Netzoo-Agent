/** A single clock convention for activity: local date, 24-hour time and zone. */
const CLOCKS = new Map<string, Intl.DateTimeFormat>();
const DATES = new Map<string, Intl.DateTimeFormat>();
export function timestamp(value: string | undefined): number | null {
  if (!value || !/(?:Z|[+-]\d{2}:\d{2})$/i.test(value)) return null;
  const result = Date.parse(value);
  return Number.isFinite(result) ? result : null;
}

export function clockLabel(value: string | undefined, zone?: string): string {
  const at = timestamp(value);
  if (at === null) return "Time unavailable";
  const key = zone ?? "local";
  if (!CLOCKS.has(key)) CLOCKS.set(key, new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3, hourCycle: "h23", timeZone: zone,
  }));
  return CLOCKS.get(key)!.format(at);
}

export function dateLabel(value: string | undefined, zone?: string): string {
  const at = timestamp(value);
  if (at === null) return "Date unavailable";
  const key = zone ?? "local";
  if (!DATES.has(key)) DATES.set(key, new Intl.DateTimeFormat("en-GB", {
    year: "numeric", month: "short", day: "2-digit", timeZone: zone,
  }));
  return DATES.get(key)!.format(at);
}

export const TIME_ZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
export function fullTime(value: string | undefined, zone = TIME_ZONE): string {
  return `${dateLabel(value, zone)} ${clockLabel(value, zone)} · ${zone}`;
}

/** "just now", "5m ago", "3h ago", "2d ago", from epoch seconds. */
export function relativeTime(seconds: number, now = Date.now()): string {
  const elapsed = now / 1000 - seconds;
  if (elapsed < 60) return "just now";
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)}h ago`;
  return `${Math.floor(elapsed / 86400)}d ago`;
}

export function durationLabel(ms: number | null): string {
  if (ms === null || !Number.isFinite(ms) || ms < 0) return "Timing unavailable";
  if (ms < 1) return "<1 ms";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)} s`;
  return `${Math.floor(ms / 60000)} min ${Math.floor(ms % 60000 / 1000)} s`;
}
