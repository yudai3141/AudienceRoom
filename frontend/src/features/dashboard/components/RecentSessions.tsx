import Link from "next/link";
import { Card, Badge } from "@/components/ui";
import type { SessionListItem } from "../hooks/useDashboard";

type RecentSessionsProps = {
  sessions: SessionListItem[];
};

const modeLabels: Record<string, string> = {
  presentation: "プレゼン",
  interview: "面接",
  free_conversation: "自由会話",
};

const statusVariants: Record<string, "default" | "success" | "warning" | "info"> = {
  waiting: "default",
  active: "info",
  completed: "success",
  cancelled: "warning",
  error: "warning",
};

function formatDate(dateString: string | null): string {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleDateString("ja-JP", {
    month: "numeric",
    day: "numeric",
  });
}

function renderScore(score: number | null): string {
  if (score === null) return "-";
  const stars = Math.round(score / 20);
  return "★".repeat(stars) + "☆".repeat(5 - stars);
}

export function RecentSessions({ sessions }: RecentSessionsProps) {
  if (sessions.length === 0) {
    return (
      <Card className="text-center">
        <p className="text-slate-500">まだ練習履歴がありません</p>
        <Link
          href="/sessions/new"
          className="mt-2 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          最初の練習を始める
        </Link>
      </Card>
    );
  }

  return (
    <Card padding="none">
      <div className="divide-y divide-slate-100">
        {sessions.map((session) => (
          <Link
            key={session.id}
            href={`/sessions/${session.id}`}
            className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-slate-50"
          >
            <div className="flex items-center gap-4">
              <div>
                <p className="font-medium text-slate-900">
                  {modeLabels[session.mode] ?? session.mode}
                </p>
                <p className="text-sm text-slate-500">
                  {session.theme ?? "テーマなし"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-amber-500">{renderScore(session.overall_score)}</p>
                <p className="text-sm text-slate-500">
                  {formatDate(session.started_at ?? session.created_at)}
                </p>
              </div>
              <Badge variant={statusVariants[session.status] ?? "default"}>
                {session.has_feedback ? "FB済" : session.status}
              </Badge>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}
