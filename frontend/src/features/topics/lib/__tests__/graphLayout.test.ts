import { describe, it, expect } from "vitest";
import { layoutPositions } from "../graphLayout";

const node = (id: number, node_type: string | null) => ({
  id,
  node_type,
  label: `n${id}`,
  detail: null,
  coverage: "gap",
  sort_order: 0,
});

describe("layoutPositions", () => {
  it("places different node_types in different columns", () => {
    const nodes = [node(1, "theme"), node(2, "method")];
    const pos = layoutPositions(nodes);
    expect(pos.get(1)!.x).toBeLessThan(pos.get(2)!.x); // theme は method より左
  });

  it("stacks same-type nodes in rows within a column", () => {
    const nodes = [node(1, "weakness"), node(2, "weakness")];
    const pos = layoutPositions(nodes);
    expect(pos.get(1)!.x).toBe(pos.get(2)!.x); // 同じ列
    expect(pos.get(1)!.y).not.toBe(pos.get(2)!.y); // 別の行
  });

  it("handles null node_type", () => {
    const pos = layoutPositions([node(1, null)]);
    expect(pos.get(1)).toBeDefined();
  });
});
