/**
 * A run report reads as a report: a card at a glance, folded details, links to its outputs.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { ReportView, parseReport } from "./ReportView";

afterEach(cleanup);

const inputs = Array.from({ length: 40 }, (_, index) => `- Note: check ${index}`).join("\n");
export const REPORT = `# NetZoo execution summary

## Summary

- Workflow: \`LIONESS_PUMA\`
- Status: \`success\`
- Started (Taiwan time): 2026-10-01T11:58:44.360+08:00
- Finished (Taiwan time): 2026-10-01T11:58:47.155+08:00
- Duration: \`2.79 seconds\`

## Executed command

\`\`\`bash
run-lioness puma -e data/case-5/expression.tsv -o outputs/sessions/s1/puma-aggregate.tsv
\`\`\`

## Inputs and validation

${inputs}

## Output artifacts

- Path: \`outputs/sessions/s1/puma-aggregate.tsv\`
  - Exists: \`yes\`
  - Size: \`306 bytes\`
  - Validation: \`passed\`
- Path: \`outputs/sessions/s1/gone.tsv\`
  - Exists: \`no\`
  - Validation: \`not found\`

## Warnings

- expression genes not recognized by the configured gene authority
- miRNA was read as whitespace-delimited text

## Conclusion

The workflow completed successfully and passed the available result checks.
`;

it("finds the sections of an execution report and nothing in other Markdown", () => {
  expect(parseReport(REPORT)?.sections.map((section) => section.heading)).toEqual([
    "Summary", "Executed command", "Inputs and validation", "Output artifacts", "Warnings", "Conclusion"]);
  expect(parseReport("# Notes\n\nSome text")).toBeNull();
});

it("leads with what happened, then folds what the card already says and what is long", () => {
  const onOpenFile = vi.fn();
  const { container } = render(<ReportView text={REPORT} onOpenFile={onOpenFile} />);
  const glance = within(container.querySelector(".report__glance") as HTMLElement);
  expect(glance.getByText("LIONESS-PUMA run")).toBeTruthy();
  expect(glance.getByText("Succeeded").className).toContain("report__status--ok");
  expect(glance.getByText("2.79 seconds")).toBeTruthy();
  expect(glance.getByText("Started").nextElementSibling?.textContent).toMatch(/^01 Oct 2026 \d\d:58:44$/);
  expect(glance.getByText("The workflow completed successfully and passed the available result checks.")).toBeTruthy();
  expect(glance.getByText("2 warnings, listed under Warnings below")).toBeTruthy();
  const open = Array.from(container.querySelectorAll("details")).map((item) => [item.querySelector("summary")?.textContent, item.open]);
  expect(open).toEqual([
    ["Summary", false], ["Executed command", true], ["Inputs and validation40 lines", false],
    ["Output artifacts", false], ["Warnings", true], ["Conclusion", false]]);
  // The command reads as code, not as a paragraph.
  expect(container.querySelector("pre code")?.textContent).toContain("run-lioness puma");
  fireEvent.click(screen.getByText("puma-aggregate.tsv"));
  expect(onOpenFile).toHaveBeenCalledWith("outputs/sessions/s1/puma-aggregate.tsv");
  expect((screen.getByText("gone.tsv").closest("button") as HTMLButtonElement).disabled).toBe(true);
});

it("shows any other Markdown as a plain document", () => {
  const { container } = render(<ReportView text={"# Notes\n\n- one\n- two"} />);
  expect(container.querySelector("h1")?.textContent).toBe("Notes");
  expect(container.querySelectorAll("li")).toHaveLength(2);
  expect(container.querySelector(".report__glance")).toBeNull();
});
