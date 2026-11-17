import { expect, it } from "vitest";
import { sessionHeading } from "./SessionsPane";

it("prefers the person's name, then NetZoo's short title, then the request", () => {
  expect(sessionHeading({ name: "Mine", auto_title: "Run PANDA", title: "Run PANDA on data/x" })).toBe("Mine");
  expect(sessionHeading({ auto_title: "Run PANDA", title: "Run PANDA on data/x" })).toBe("Run PANDA");
  expect(sessionHeading({ title: "Run PANDA on data/x" })).toBe("Run PANDA on data/x");
  expect(sessionHeading({})).toBe("");
});
