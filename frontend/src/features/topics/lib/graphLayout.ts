import type { TopicNode } from "../hooks/useTopicDetail";

/** node_type を左→右の列に並べる際の優先順。未知の型は右端に回す。 */
const TYPE_ORDER = [
  "theme",
  "problem",
  "method",
  "contribution",
  "result",
  "learning",
  "strength",
  "weakness",
  "episode",
  "other",
];

const COL_WIDTH = 220;
const ROW_HEIGHT = 90;

function typeKey(node: TopicNode): string {
  return node.node_type ?? "other";
}

function typeRank(type: string): number {
  const i = TYPE_ORDER.indexOf(type);
  return i === -1 ? TYPE_ORDER.length : i;
}

/**
 * ノードを node_type ごとの列に配置し、列内で縦に積む決定論的レイアウト。
 * 小さなトピックグラフ向けの簡易自動配置（React Flow に渡す x/y を返す）。
 */
export function layoutPositions(
  nodes: TopicNode[],
): Map<number, { x: number; y: number }> {
  const types = [...new Set(nodes.map(typeKey))].sort(
    (a, b) => typeRank(a) - typeRank(b) || a.localeCompare(b),
  );
  const colOf = new Map(types.map((t, i) => [t, i]));
  const rowCounter = new Map<string, number>();
  const positions = new Map<number, { x: number; y: number }>();

  for (const node of nodes) {
    const t = typeKey(node);
    const col = colOf.get(t) ?? 0;
    const row = rowCounter.get(t) ?? 0;
    rowCounter.set(t, row + 1);
    positions.set(node.id, { x: col * COL_WIDTH, y: row * ROW_HEIGHT });
  }

  return positions;
}

/** coverage に応じたノードの見た目。 */
export function coverageNodeStyle(coverage: string): React.CSSProperties {
  switch (coverage) {
    case "covered":
      return { border: "2px solid #16a34a", background: "#f0fdf4", color: "#14532d" };
    case "weak":
      return { border: "2px solid #d97706", background: "#fffbeb", color: "#78350f" };
    default: // gap
      return {
        border: "2px dashed #94a3b8",
        background: "#f8fafc",
        color: "#475569",
      };
  }
}
