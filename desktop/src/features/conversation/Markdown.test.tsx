import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { Markdown } from "./Markdown";

afterEach(cleanup);
it("renders headings, GFM tables and safe links while leaving executable markup inert", () => {
  render(<Markdown>{"## Results\n\n| gene | score |\n| --- | --- |\n| AHR | 1 |\n\n[Documentation](https://netzoopy.readthedocs.io)\n\n<script>window.injected = true</script>\n\n[Unsafe](javascript:alert(1))"}</Markdown>);
  expect(screen.getByRole("heading", { name: "Results" })).toBeTruthy();
  expect(screen.getByRole("table")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Documentation" }).getAttribute("rel")).toBe("noopener noreferrer");
  expect(document.querySelector("script")).toBeNull();
  expect(screen.queryByRole("link", { name: "Unsafe" })).toBeNull();
});

it("keeps a written line break without printing blank lines between blocks", () => {
  const { container } = render(<Markdown>{"Result: a network.\nEach input on its own:\n- From expression\n- From mutations"}</Markdown>);
  expect(container.querySelectorAll("br").length).toBe(1);
  expect(container.querySelectorAll("li").length).toBe(2);
  expect(getComputedStyle(container.firstElementChild as Element).whiteSpace).not.toBe("pre-wrap");
});
