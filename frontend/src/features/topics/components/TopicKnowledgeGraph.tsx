"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, {
  type ForceGraphMethods,
} from "react-force-graph-2d";
import { coverageColor } from "../lib/graphLayout";
import type { TopicEdge, TopicNode } from "../hooks/useTopicDetail";

const CONTRADICTS = "contradicts";

type GraphNode = {
  id: number;
  label: string;
  node_type: string | null;
  coverage: string;
};
type GraphLink = {
  source: number;
  target: number;
  relation_type: string;
};

export function TopicKnowledgeGraph({
  nodes,
  edges,
}: {
  nodes: TopicNode[];
  edges: TopicEdge[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<ForceGraphMethods<GraphNode, GraphLink> | undefined>(
    undefined,
  );
  const [width, setWidth] = useState(600);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setWidth(el.clientWidth);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const data = useMemo(
    () => ({
      nodes: nodes.map((n) => ({
        id: n.id,
        label: n.label,
        node_type: n.node_type,
        coverage: n.coverage,
      })),
      links: edges.map((e) => ({
        source: e.source_node_id,
        target: e.target_node_id,
        relation_type: e.relation_type,
      })),
    }),
    [nodes, edges],
  );

  if (nodes.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">
        まだ論点がありません。このトピックで練習すると育っていきます。
      </p>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-[460px] w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-50"
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        width={width}
        height={460}
        cooldownTicks={120}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 60)}
        nodeRelSize={6}
        nodeColor={(n) => coverageColor((n as GraphNode).coverage)}
        nodeLabel={(n) => (n as GraphNode).node_type ?? ""}
        linkColor={(l) =>
          (l as GraphLink).relation_type === CONTRADICTS ? "#dc2626" : "#cbd5e1"
        }
        linkWidth={(l) =>
          (l as GraphLink).relation_type === CONTRADICTS ? 2 : 1
        }
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkLabel={(l) => (l as GraphLink).relation_type}
        nodeCanvasObjectMode={() => "after"}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const n = node as GraphNode & { x?: number; y?: number };
          if (n.x == null || n.y == null) return;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillStyle = "#0f172a";
          ctx.fillText(n.label, n.x, n.y + 8);
        }}
      />
    </div>
  );
}
