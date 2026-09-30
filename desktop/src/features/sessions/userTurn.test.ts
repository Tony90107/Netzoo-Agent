import { expect, it } from "vitest";
import { userTurn } from "./userTurn";

it("shows the option a person chose, not the confirmed-outcome marker", () => {
  expect(userTurn("CONFIRMED_OUTCOME_ACTION=run_bonobo. Explain the confirmed supported outcome and recommend its workflow. Do not execute it yet."))
    .toEqual({ text: "Chose BONOBO", kind: "chose" });
});

it("shows only the follow-up a person wrote, not the restated goal", () => {
  expect(userTurn("Previous NetZoo goal: build a network\nUser follow-up: Transcription factors only").text)
    .toBe("Transcription factors only");
});

it("shows a continuation's own reply, and leaves ordinary requests alone", () => {
  expect(userTurn("PREVIOUS_ACTION=run_puma. Continue the recommended PUMA workflow. The user accepted the previous capability recommendation.\nUser reply: Start planning PUMA").text)
    .toBe("Start planning PUMA");
  expect(userTurn("run PANDA on data/x").kind).toBe("said");
});
