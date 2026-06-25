import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TopicGraphView } from "@/features/topics/components/TopicGraphView";

const nodes = [
  { id: 1, node_type: "method", label: "評価方法", detail: "15%改善", coverage: "covered", sort_order: 1 },
  { id: 2, node_type: "weakness", label: "企業での活かし方", detail: null, coverage: "gap", sort_order: 2 },
];

const edges = [
  { id: 10, source_node_id: 1, target_node_id: 2, relation_type: "contradicts" },
];

describe("TopicGraphView", () => {
  it("renders nodes with coverage labels", () => {
    render(<TopicGraphView nodes={nodes} edges={[]} />);
    expect(screen.getByText("評価方法")).toBeInTheDocument();
    expect(screen.getByText("話せる")).toBeInTheDocument(); // covered
    expect(screen.getByText("未説明")).toBeInTheDocument(); // gap
  });

  it("highlights contradiction edges", () => {
    render(<TopicGraphView nodes={nodes} edges={edges} />);
    expect(screen.getByText(/contradicts/)).toBeInTheDocument();
  });

  it("shows empty message when no nodes", () => {
    render(<TopicGraphView nodes={[]} edges={[]} />);
    expect(
      screen.getByText(/まだ論点がありません/),
    ).toBeInTheDocument();
  });
});
