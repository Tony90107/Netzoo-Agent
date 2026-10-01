import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { ErrorBoundary } from "./ErrorBoundary";

afterEach(cleanup);

function Broken(): never {
  throw new Error("tags is undefined");
}

it("shows what failed and a way back instead of a blank window", () => {
  const quiet = vi.spyOn(console, "error").mockImplementation(() => undefined);
  render(<ErrorBoundary><Broken /></ErrorBoundary>);
  expect(screen.getByRole("alert").textContent).toContain("This view stopped working");
  expect(screen.getByText("tags is undefined")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Reload the window" })).toBeTruthy();
  quiet.mockRestore();
});
