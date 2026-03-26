"use client";

import Link from "next/link";
import { useDashboard } from "@/features/dashboard/hooks/useDashboard";
import { DashboardStats } from "@/features/dashboard/components/DashboardStats";
import { RecentSessions } from "@/features/dashboard/components/RecentSessions";
import { Button, Spinner } from "@/components/ui";

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        ダッシュボードの読み込みに失敗しました
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            ダッシュボード
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            練習の記録と成長を確認しましょう
          </p>
        </div>
        <Link href="/sessions/new">
          <Button>今日の練習を始める</Button>
        </Link>
      </div>

      <DashboardStats
        totalSessions={data.total_sessions}
        completedSessions={data.completed_sessions}
        averageScore={data.average_score}
      />

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          最近の練習
        </h2>
        <RecentSessions sessions={data.recent_sessions} />
      </div>

      {data.recent_sessions.length > 0 && (
        <div className="text-center">
          <Link
            href="/sessions"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
          >
            すべての履歴を見る →
          </Link>
        </div>
      )}
    </div>
  );
}
