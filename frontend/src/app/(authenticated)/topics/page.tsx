"use client";

import { Spinner } from "@/components/ui";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { useTopics } from "@/features/sessions/hooks/useTopics";
import { TopicCard } from "@/features/topics/components/TopicCard";

export default function TopicsPage() {
  const { data: user } = useCurrentUser();
  const { data: topics, isLoading } = useTopics(user?.id);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          トピック
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          面接で話すエピソードごとに、話せる内容が育っていきます。
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : !topics || topics.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 px-4 py-12 text-center text-sm text-slate-500">
          まだトピックがありません。練習を始めるときにトピックを作成できます。
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {topics.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      )}
    </div>
  );
}
