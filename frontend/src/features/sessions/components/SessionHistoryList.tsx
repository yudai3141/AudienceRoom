"use client";

import Link from "next/link";
import { Card, Badge, Spinner } from "@/components/ui";
import { useSessions, type SessionListItem } from "../hooks/useSessions";

function formatDate(dateString: string | null): string {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getModeLabel(mode: string): string {
  switch (mode) {
    case "interview":
      return "面接練習";
    case "presentation":
      return "プレゼン練習";
    default:
      return mode;
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "completed":
      return <Badge variant="success">完了</Badge>;
    case "in_progress":
      return <Badge variant="warning">進行中</Badge>;
    case "cancelled":
      return <Badge variant="default">キャンセル</Badge>;
    default:
      return <Badge variant="default">{status}</Badge>;
  }
}

function getScoreStars(score: number | null): string {
  if (score === null) return "-";
  const stars = Math.round(score / 20);
  return "★".repeat(stars) + "☆".repeat(5 - stars);
}

function SessionCard({ session }: { session: SessionListItem }) {
  return (
    <Link href={`/sessions/${session.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <div className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-900">
                  {getModeLabel(session.mode)}
                </span>
                {getStatusBadge(session.status)}
              </div>
              {session.theme && (
                <p className="text-sm text-slate-600">{session.theme}</p>
              )}
            </div>
            <div className="text-right">
              <div className="text-lg text-amber-500">
                {getScoreStars(session.overall_score)}
              </div>
              {session.has_feedback && (
                <span className="text-xs text-indigo-600">
                  フィードバックあり
                </span>
              )}
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-500">
            {formatDate(session.started_at || session.created_at)}
          </div>
        </div>
      </Card>
    </Link>
  );
}

export function SessionHistoryList() {
  const { data, isLoading, error } = useSessions();

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
        履歴の読み込みに失敗しました
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <Card>
        <div className="px-6 py-12 text-center">
          <p className="text-slate-500">まだ練習履歴がありません</p>
          <Link
            href="/sessions/new"
            className="mt-4 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500"
          >
            最初の練習を始める →
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-slate-500">
        全 {data.total} 件中 {data.items.length} 件を表示
      </div>
      <div className="space-y-3">
        {data.items.map((session) => (
          <SessionCard key={session.id} session={session} />
        ))}
      </div>
    </div>
  );
}
