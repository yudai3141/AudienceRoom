"use client";

import { use } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Card, Spinner } from "@/components/ui";
import { useTopicDetail } from "@/features/topics/hooks/useTopicDetail";
import { TopicGraphView } from "@/features/topics/components/TopicGraphView";

// react-force-graph はクライアント専用（SSR 無効）で読み込む。
const TopicKnowledgeGraph = dynamic(
  () =>
    import("@/features/topics/components/TopicKnowledgeGraph").then(
      (m) => m.TopicKnowledgeGraph,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[460px] items-center justify-center">
        <Spinner size="lg" />
      </div>
    ),
  },
);

const WEAK_COVERAGES = ["weak", "gap"];

export default function TopicDetailPage({
  params,
}: {
  params: Promise<{ topicId: string }>;
}) {
  const { topicId } = use(params);
  const { data: topic, isLoading, error } = useTopicDetail(Number(topicId));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !topic) {
    return (
      <div className="space-y-4">
        <Link href="/topics" className="text-sm text-indigo-600">
          ← トピック一覧
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          トピックを取得できませんでした。
        </div>
      </div>
    );
  }

  const completeness = topic.completeness_score ?? 0;
  const weakCount = topic.nodes.filter((n) =>
    WEAK_COVERAGES.includes(n.coverage),
  ).length;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/topics" className="text-sm text-indigo-600">
          ← トピック一覧
        </Link>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
          {topic.title}
        </h1>
      </div>

      <Card>
        <div className="space-y-3 p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">完成度</span>
            <span className="text-sm font-medium text-slate-500">
              {topic.completeness_score != null ? `${completeness}%` : "未評価"}
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all"
              style={{ width: `${completeness}%` }}
            />
          </div>
          {topic.current_summary && (
            <p className="text-sm text-slate-600">{topic.current_summary}</p>
          )}
          <p className="text-xs text-slate-500">
            まだ弱い論点: {weakCount}個
          </p>
        </div>
      </Card>

      <Card>
        <div className="space-y-3 p-5">
          <h2 className="text-sm font-semibold text-slate-900">構造</h2>
          <TopicKnowledgeGraph nodes={topic.nodes} edges={topic.edges} />
          <div className="flex flex-wrap gap-3 text-xs text-slate-500">
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-green-500" />
              話せる
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />
              弱い
            </span>
            <span>
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-slate-400" />
              未説明
            </span>
            <span className="text-red-500">⚡ 赤い線 = 矛盾</span>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-5">
          <TopicGraphView nodes={topic.nodes} edges={topic.edges} />
        </div>
      </Card>
    </div>
  );
}
