import { useState } from "react";
import { COUNTRY_ZONES, otherTimeZones, setTimeZone, useTimeZone, validTimeZone } from "../timeline/timeZone";
import { fullTime } from "../timeline/time";

export function TimeZoneSettings() {
  const { choice, zone } = useTimeZone();
  const [note, setNote] = useState("");
  const all = otherTimeZones();
  const known = new Set([...COUNTRY_ZONES.flatMap(([, zones]) => zones), ...all]);
  return <div className="set__group time-zone-settings">
    <h2 className="set__title">Display time</h2>
    <label htmlFor="display-time-zone">Time zone · country / city</label>
    <select id="display-time-zone" value={choice} onChange={(event) => setNote(setTimeZone(event.target.value) ? "Time zone saved on this device." : "Time zone changed for this window. Device storage is unavailable.")}>
      <option value="system">Follow system · {Intl.DateTimeFormat().resolvedOptions().timeZone}</option>
      {choice !== "system" && !known.has(choice) ? <option value={choice}>{choice}</option> : null}
      {COUNTRY_ZONES.map(([country, zones]) => <optgroup key={country} label={country}>{zones.filter(validTimeZone).map((value) => <option key={value} value={value}>{country} · {value.split("/").slice(1).join(" / ").replace(/_/g, " ")}</option>)}</optgroup>)}
      <optgroup label="Other regions / IANA time zones">{all.map((value) => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}</optgroup>
    </select>
    <p className="set__note">Countries may have several time zones. Choose the city nearest you. Daylight saving changes follow that zone automatically.</p>
    <p className="time-zone-preview">Preview · {fullTime(new Date().toISOString(), zone)}</p>
    <p className="set__note">Applies to Activity, logs and file times. Recorded timestamps remain in UTC.</p>
    {note ? <p role="status" className="log__feedback">{note}</p> : null}
  </div>;
}
