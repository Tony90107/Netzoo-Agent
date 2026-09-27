import { useSyncExternalStore } from "react";

const KEY = "netzoo.display.time-zone";
const CHANGE = "netzoo-time-zone-change";
let memory: string | null = null;

export function validTimeZone(zone: string): boolean {
  try { new Intl.DateTimeFormat("en", { timeZone: zone }).format(); return true; }
  catch { return false; }
}

function preference(): string {
  let choice = memory;
  if (choice === null) {
    try { choice = localStorage.getItem(KEY); } catch { /* Use system time when storage is unavailable. */ }
  }
  return choice && validTimeZone(choice) ? choice : "system";
}

function subscribe(listener: () => void) {
  const stored = (event: StorageEvent) => { if (event.key === KEY || event.key === null) { memory = null; listener(); } };
  window.addEventListener(CHANGE, listener);
  window.addEventListener("storage", stored);
  return () => { window.removeEventListener(CHANGE, listener); window.removeEventListener("storage", stored); };
}

export function setTimeZone(choice: string): boolean {
  if (choice !== "system" && !validTimeZone(choice)) return false;
  memory = choice;
  let saved = true;
  try { localStorage.setItem(KEY, choice); } catch { saved = false; }
  window.dispatchEvent(new Event(CHANGE));
  return saved;
}

export function useTimeZone() {
  const choice = useSyncExternalStore(subscribe, preference, () => "system");
  return { choice, zone: choice === "system" ? Intl.DateTimeFormat().resolvedOptions().timeZone : choice };
}

/** Common country/city pairs; other IANA zones remain selectable below them. */
export const COUNTRY_ZONES: [string, string[]][] = [
  ["Taiwan", ["Asia/Taipei"]], ["Japan", ["Asia/Tokyo"]], ["South Korea", ["Asia/Seoul"]],
  ["China", ["Asia/Shanghai", "Asia/Urumqi"]], ["Hong Kong", ["Asia/Hong_Kong"]],
  ["Singapore", ["Asia/Singapore"]], ["India", ["Asia/Kolkata"]],
  ["Australia", ["Australia/Sydney", "Australia/Brisbane", "Australia/Adelaide", "Australia/Darwin", "Australia/Perth"]],
  ["New Zealand", ["Pacific/Auckland", "Pacific/Chatham"]],
  ["United States", ["America/New_York", "America/Chicago", "America/Denver", "America/Phoenix", "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu"]],
  ["Canada", ["America/Toronto", "America/Halifax", "America/St_Johns", "America/Winnipeg", "America/Edmonton", "America/Vancouver"]],
  ["Mexico", ["America/Mexico_City", "America/Tijuana", "America/Cancun"]],
  ["Brazil", ["America/Sao_Paulo", "America/Manaus", "America/Rio_Branco"]],
  ["United Kingdom", ["Europe/London"]], ["France", ["Europe/Paris"]], ["Germany", ["Europe/Berlin"]],
  ["Spain", ["Europe/Madrid", "Atlantic/Canary"]], ["South Africa", ["Africa/Johannesburg"]],
  ["United Arab Emirates", ["Asia/Dubai"]],
];

export function otherTimeZones(): string[] {
  const api = Intl as typeof Intl & { supportedValuesOf?: (key: string) => string[] };
  const common = new Set(COUNTRY_ZONES.flatMap(([, zones]) => zones));
  return ["UTC", ...(api.supportedValuesOf?.("timeZone") ?? [])].filter((zone) => !common.has(zone));
}
