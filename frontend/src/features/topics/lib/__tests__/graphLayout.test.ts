import { describe, it, expect } from "vitest";
import { coverageColor } from "../graphLayout";

describe("coverageColor", () => {
  it("maps coverage to distinct colors", () => {
    const covered = coverageColor("covered");
    const weak = coverageColor("weak");
    const gap = coverageColor("gap");
    expect(covered).not.toBe(weak);
    expect(weak).not.toBe(gap);
  });

  it("falls back to the gap color for unknown coverage", () => {
    expect(coverageColor("unknown")).toBe(coverageColor("gap"));
  });
});
