"use client";

import Link from "next/link";
import { Card, Badge, Button, Spinner } from "@/components/ui";
import { useSessionDetail } from "../hooks/useSessionDetail";

type FeedbackDisplayProps = {
  sessionId: number;
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
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

function ScoreDisplay({ score }: { score: number | null }) {
  if (score === null) return null;

  const stars = Math.round(score / 20);
  const percentage = score;

  return (
    <div className="text-center">
      <div className="text-4xl text-amber-500">
        {"★".repeat(stars)}
        {"☆".repeat(5 - stars)}
      </div>
      <div className="mt-2 text-2xl font-bold text-slate-900">{percentage}点</div>
    </div>
  );
}

function PointsList({
  title,
  points,
  variant,
}: {
  title: string;
  points: unknown;
  variant: "positive" | "improvement";
}) {
  const pointsArray = Array.isArray(points) ? points : [];

  if (pointsArray.length === 0) return null;

  return (
    <Card>
      <div className="p-6">
        <h3
          className={`mb-4 flex items-center gap-2 text-lg font-semibold ${
            variant === "positive" ? "text-green-700" : "text-amber-700"
          }`}
        >
          {variant === "positive" ? (
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          ) : (
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          )}
          {title}
        </h3>
        <ul className="space-y-3">
          {pointsArray.map((point, index) => (
            <li key={index} className="flex items-start gap-3">
              <span
                className={`mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-xs font-medium ${
                  variant === "positive"
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700"
                }`}
              >
                {index + 1}
              </span>
              <span className="text-slate-700">{String(point)}</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

function MetricsDisplay({
  metrics,
}: {
  metrics: { metric_key: string; metric_value: string; metric_label: string | null; metric_unit: string | null }[];
}) {
  if (metrics.length === 0) return null;

  return (
    <Card>
      <div className="p-6">
        <h3 className="mb-4 text-lg font-semibold text-slate-900">詳細スコア</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          {metrics.map((metric) => (
            <div
              key={metric.metric_key}
              className="rounded-lg bg-slate-50 p-4"
            >
              <div className="text-sm text-slate-500">
                {metric.metric_label || metric.metric_key}
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900">
                {metric.metric_value}
                {metric.metric_unit && (
                  <span className="ml-1 text-sm font-normal text-slate-500">
                    {metric.metric_unit}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

export function FeedbackDisplay({ sessionId }: FeedbackDisplayProps) {
  const { data: session, isLoading, error } = useSessionDetail(sessionId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        フィードバックの読み込みに失敗しました
      </div>
    );
  }

  const { feedback } = session;

  return (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Badge>{getModeLabel(session.mode)}</Badge>
                {session.status === "completed" && (
                  <Badge variant="success">完了</Badge>
                )}
              </div>
              {session.theme && (
                <p className="mt-2 text-lg font-medium text-slate-900">
                  {session.theme}
                </p>
              )}
              <p className="mt-1 text-sm text-slate-500">
                {formatDate(session.created_at)}
              </p>
            </div>
            <ScoreDisplay score={session.overall_score} />
          </div>
        </div>
      </Card>

      {feedback ? (
        <>
          <Card>
            <div className="p-6 text-center">
              <h2 className="text-xl font-bold text-slate-900">
                {feedback.summary_title}
              </h2>
              {feedback.short_comment && (
                <p className="mt-2 text-slate-600">{feedback.short_comment}</p>
              )}
            </div>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <PointsList
              title="良かった点"
              points={feedback.positive_points}
              variant="positive"
            />
            <PointsList
              title="改善点"
              points={feedback.improvement_points}
              variant="improvement"
            />
          </div>

          <MetricsDisplay metrics={feedback.metrics} />

          {feedback.closing_message && (
            <Card>
              <div className="p-6">
                <h3 className="mb-2 text-lg font-semibold text-slate-900">
                  最後に
                </h3>
                <p className="text-slate-700">{feedback.closing_message}</p>
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <div className="px-6 py-12 text-center">
            <p className="text-slate-500">
              {session.status === "completed"
                ? "フィードバックはまだ生成されていません"
                : "セッション完了後にフィードバックが表示されます"}
            </p>
          </div>
        </Card>
      )}

      <div className="flex justify-center gap-4">
        <Link href="/sessions">
          <Button variant="outline">履歴に戻る</Button>
        </Link>
        <Link href="/sessions/new">
          <Button>新しい練習を始める</Button>
        </Link>
      </div>
    </div>
  );
}
