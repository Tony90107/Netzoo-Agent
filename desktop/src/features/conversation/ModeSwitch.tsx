/**
 * Mode is state, so it gets a control rather than a sentence.
 *
 * The terminal switches modes by typing `/planning` or `/test`, which is the
 * only affordance a terminal has. Here the switch keeps the
 * current mode visible between messages.
 *
 * The command still goes to the agent: `TEST_DATA_MODE` and `EXECUTE_TOOLS`
 * belong to the engine, and the window is not allowed to set them itself. Control actions
 * are recorded in the activity log, and the agent's explanation of synthetic
 * results stays in the thread.
 */
import { ViewPayload } from "../../transport/protocol";

type Mode = ViewPayload["mode"];

const OPTIONS: { mode: Mode; command: string; label: string; title: string }[] = [
  {
    mode: "Planning",
    command: "/planning",
    label: "Planning",
    title: "Strict validation. Workflows are previewed, never run without approval.",
  },
  {
    mode: "Test",
    command: "/test",
    label: "Synthetic test",
    title:
      "Unresolved gene labels are accepted as test-only identifiers. Results are for software testing, not biological evidence.",
  },
];

export function ModeSwitch({
  mode,
  disabled,
  onSelect,
}: {
  mode: Mode | undefined;
  disabled: boolean;
  onSelect: (command: string) => void;
}) {
  return (
    <div className="modeswitch" role="group" aria-label="Agent mode">
      {OPTIONS.map((option) => {
        const active = mode === option.mode;
        return (
          <button
            key={option.mode}
            type="button"
            className={`modeswitch__option${active ? " is-active" : ""}`}
            aria-pressed={active}
            title={option.title}
            disabled={disabled || active}
            onClick={() => onSelect(option.command)}
          >
            {option.label}
          </button>
        );
      })}
      {mode === "Execute" ? (
        // Execution authority is scoped to a single turn, so this is only ever
        // visible while that turn is in flight.
        <span className="modeswitch__executing">Executing</span>
      ) : null}
    </div>
  );
}
