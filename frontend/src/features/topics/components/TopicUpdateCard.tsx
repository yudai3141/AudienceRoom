import Link from "next/link";
import { Card } from "@/components/ui";
import { coverageLabel } from "./CoverageBadge";
import type { TopicUpdateResult } from "@/features/sessions/hooks/useUpdateTopicMemory";

export function TopicUpdateCard({ result }: { result: TopicUpdateResult }) {
  if (result.skipped) return null;

  const hasChanges =
    result.coverage_changes.length > 0 ||
    result.created_node_labels.length > 0;

  return (
    <Card>
      <div className="space-y-4 p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          トピックが育ちました
        </h3>

        {result.completeness_after != null && (
          <p className="text-sm text-slate-600">
            完成度{" "}
            {result.completeness_before != null && (
              <span className="text-slate-400">
                {result.completeness_before}% →{" "}
              </span>
            )}
            <span className="font-semibold text-indigo-600">
              {result.completeness_after}%
            </span>
          </p>
        )}

        {hasChanges ? (
          <ul className="space-y-1 text-sm">
            {result.coverage_changes.map((c) => (
              <li key={`cov-${c.label}`} className="text-slate-700">
                <span className="font-medium">{c.label}</span>:{" "}
                <span className="text-slate-400">
                  {coverageLabel(c.before)}
                </span>{" "}
                → <span className="text-green-700">{coverageLabel(c.after)}</span>
              </li>
            ))}
            {result.created_node_labels.map((label) => (
              <li key={`new-${label}`} className="text-slate-700">
                ＋ 新しい論点「{label}」
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">
            今回は大きな更新はありませんでした。
          </p>
        )}

        {result.topic_id != null && (
          <Link
            href={`/topics/${result.topic_id}`}
            className="inline-block text-sm font-medium text-indigo-600"
          >
            トピック詳細を見る →
          </Link>
        )}
      </div>
    </Card>
  );
}
