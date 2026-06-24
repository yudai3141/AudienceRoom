import { Card } from "@/components/ui";
import { CoverageBadge } from "./CoverageBadge";
import type { TopicEdge, TopicNode } from "../hooks/useTopicDetail";

const CONTRADICTS = "contradicts";

export function TopicGraphView({
  nodes,
  edges,
}: {
  nodes: TopicNode[];
  edges: TopicEdge[];
}) {
  const idToLabel = new Map(nodes.map((n) => [n.id, n.label]));

  // node_type ごとにグループ化（未設定は「その他」）
  const groups = new Map<string, TopicNode[]>();
  for (const n of nodes) {
    const key = n.node_type ?? "その他";
    const arr = groups.get(key);
    if (arr) {
      arr.push(n);
    } else {
      groups.set(key, [n]);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="mb-3 text-sm font-semibold text-slate-900">論点</h3>
        {nodes.length === 0 ? (
          <p className="text-sm text-slate-500">
            まだ論点がありません。このトピックで練習すると育っていきます。
          </p>
        ) : (
          <div className="space-y-4">
            {[...groups.entries()].map(([type, items]) => (
              <div key={type}>
                <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                  {type}
                </p>
                <ul className="space-y-1">
                  {items.map((n) => (
                    <li
                      key={n.id}
                      className="flex items-start gap-2 rounded-md border border-slate-100 px-3 py-2"
                    >
                      <CoverageBadge coverage={n.coverage} />
                      <div>
                        <span className="text-sm font-medium text-slate-900">
                          {n.label}
                        </span>
                        {n.detail && (
                          <p className="text-xs text-slate-500">{n.detail}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </section>

      {edges.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-semibold text-slate-900">関係</h3>
          <ul className="space-y-1">
            {edges.map((e) => {
              const isContradiction = e.relation_type === CONTRADICTS;
              return (
                <li
                  key={e.id}
                  className={`rounded-md px-3 py-2 text-sm ${
                    isContradiction
                      ? "bg-red-50 text-red-700"
                      : "text-slate-600"
                  }`}
                >
                  {isContradiction && <span className="mr-1">⚡</span>}
                  {idToLabel.get(e.source_node_id) ?? "?"}
                  <span className="mx-1 text-slate-400">
                    --{e.relation_type}--&gt;
                  </span>
                  {idToLabel.get(e.target_node_id) ?? "?"}
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
