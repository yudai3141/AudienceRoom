"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { coverageNodeStyle, layoutPositions } from "../lib/graphLayout";
import type { TopicEdge, TopicNode } from "../hooks/useTopicDetail";

const CONTRADICTS = "contradicts";

export function TopicGraphFlow({
  nodes,
  edges,
}: {
  nodes: TopicNode[];
  edges: TopicEdge[];
}) {
  const { rfNodes, rfEdges } = useMemo(() => {
    const positions = layoutPositions(nodes);
    const flowNodes: Node[] = nodes.map((n) => ({
      id: String(n.id),
      position: positions.get(n.id) ?? { x: 0, y: 0 },
      data: { label: n.label },
      style: {
        ...coverageNodeStyle(n.coverage),
        borderRadius: 8,
        padding: 8,
        fontSize: 12,
        width: 180,
      },
    }));

    const flowEdges: Edge[] = edges.map((e) => {
      const isContradiction = e.relation_type === CONTRADICTS;
      return {
        id: String(e.id),
        source: String(e.source_node_id),
        target: String(e.target_node_id),
        label: e.relation_type,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: isContradiction ? { stroke: "#dc2626" } : undefined,
        labelStyle: isContradiction ? { fill: "#dc2626" } : undefined,
      };
    });

    return { rfNodes: flowNodes, rfEdges: flowEdges };
  }, [nodes, edges]);

  if (nodes.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">
        まだ論点がありません。このトピックで練習すると育っていきます。
      </p>
    );
  }

  return (
    <div className="h-[420px] w-full overflow-hidden rounded-lg border border-slate-200">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        fitView
        nodesDraggable
        minZoom={0.2}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
