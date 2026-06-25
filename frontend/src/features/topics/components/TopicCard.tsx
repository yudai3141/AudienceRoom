import Link from "next/link";
import { Card } from "@/components/ui";
import type { Topic } from "@/features/sessions/hooks/useTopics";

export function TopicCard({ topic }: { topic: Topic }) {
  const completeness = topic.completeness_score ?? 0;

  return (
    <Link href={`/topics/${topic.id}`} className="block">
      <Card className="transition-colors hover:border-indigo-300">
        <div className="p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-900">
              {topic.title}
            </h3>
            <span className="text-sm font-medium text-slate-500">
              {topic.completeness_score != null
                ? `${completeness}%`
                : "未評価"}
            </span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all"
              style={{ width: `${completeness}%` }}
            />
          </div>

          {topic.current_summary && (
            <p className="line-clamp-2 text-sm text-slate-600">
              {topic.current_summary}
            </p>
          )}
        </div>
      </Card>
    </Link>
  );
}
