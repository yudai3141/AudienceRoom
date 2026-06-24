import { describe, expect, it } from "vitest";
import { classifyTopicSelection } from "../topicSelection";

describe("classifyTopicSelection", () => {
  it("returns none for empty/undefined selection", () => {
    expect(classifyTopicSelection("", undefined)).toEqual({ kind: "none" });
    expect(classifyTopicSelection(undefined, undefined)).toEqual({
      kind: "none",
    });
  });

  it("returns existing for a numeric selection", () => {
    expect(classifyTopicSelection("42", undefined)).toEqual({
      kind: "existing",
      id: 42,
    });
  });

  it("returns new with trimmed title", () => {
    expect(classifyTopicSelection("new", "  研究内容  ")).toEqual({
      kind: "new",
      title: "研究内容",
    });
  });

  it("returns error when new is chosen without a title", () => {
    const result = classifyTopicSelection("new", "   ");
    expect(result.kind).toBe("error");
  });
});
