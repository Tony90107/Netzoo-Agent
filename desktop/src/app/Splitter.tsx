/**
 * Draggable dividers, so a pane can be given the room its content needs.
 *
 * An evidence ledger, a timeline and a results tree do not want the same
 * share of the window, and which one matters changes while you work. Sizes
 * are remembered per divider so the layout you settle on survives a relaunch.
 *
 * Keyboard works too: a divider is a real control, and a layout that can only
 * be changed with a mouse is one some people cannot change.
 */
import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_PREFIX = "netzoo.layout.";
/** One arrow press moves a divider this many pixels. */
const KEY_STEP = 16;

function load(key: string, fallback: number): number {
  try {
    const stored = window.localStorage.getItem(STORAGE_PREFIX + key);
    const value = stored === null ? Number.NaN : Number(stored);
    return Number.isFinite(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

/** A remembered pane size, clamped to a range it can never leave. */
export function usePaneSize(
  key: string,
  initial: number,
  min: number,
  max: number,
): [number, (next: number) => void] {
  const clamp = useCallback(
    (value: number) => Math.min(max, Math.max(min, value)),
    [min, max],
  );
  const [size, setSize] = useState(() => clamp(load(key, initial)));

  const update = useCallback(
    (next: number) => {
      const clamped = clamp(next);
      setSize(clamped);
      try {
        window.localStorage.setItem(STORAGE_PREFIX + key, String(clamped));
      } catch {
        // A layout preference is not worth failing over; the session keeps
        // the size it has, it just will not be there next launch.
      }
    },
    [clamp, key],
  );

  return [size, update];
}

export function Splitter({
  orientation,
  onDelta,
  label,
}: {
  orientation: "vertical" | "horizontal";
  /** Positive is rightwards or downwards, in CSS pixels. */
  onDelta: (delta: number) => void;
  label: string;
}) {
  const [dragging, setDragging] = useState(false);
  const last = useRef(0);

  useEffect(() => {
    if (!dragging) return;
    const move = (event: PointerEvent) => {
      const position = orientation === "vertical" ? event.clientX : event.clientY;
      onDelta(position - last.current);
      last.current = position;
    };
    const stop = () => setDragging(false);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
    // A pointer that leaves the window must not leave the divider stuck to it.
    window.addEventListener("pointercancel", stop);
    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", stop);
    };
  }, [dragging, onDelta, orientation]);

  return (
    <div
      className={`splitter splitter--${orientation}${dragging ? " is-dragging" : ""}`}
      role="separator"
      aria-label={label}
      aria-orientation={orientation === "vertical" ? "vertical" : "horizontal"}
      tabIndex={0}
      onPointerDown={(event) => {
        last.current = orientation === "vertical" ? event.clientX : event.clientY;
        setDragging(true);
        event.preventDefault();
      }}
      onKeyDown={(event) => {
        const back = orientation === "vertical" ? "ArrowLeft" : "ArrowUp";
        const forward = orientation === "vertical" ? "ArrowRight" : "ArrowDown";
        if (event.key === back) onDelta(-KEY_STEP);
        else if (event.key === forward) onDelta(KEY_STEP);
        else return;
        event.preventDefault();
      }}
    />
  );
}
