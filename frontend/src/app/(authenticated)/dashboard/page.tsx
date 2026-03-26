"use client";

import Link from "next/link";
import { useDashboard } from "@/features/dashboard/hooks/useDashboard";
import { DashboardStats } from "@/features/dashboard/components/DashboardStats";
import { RecentSessions } from "@/features/dashboard/components/RecentSessions";
import { WelcomeCard } from "@/features/dashboard/components/WelcomeCard";
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

  if (error || !data) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            ダッシュボード
          </h1>
        </div>
        <WelcomeCard />
      </div>
    );
  }

  const isNewUser = data.total_sessions === 0;

  if (isNewUser) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            ダッシュボード
          </h1>
        </div>
        <WelcomeCard />
      </div>
    );
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
