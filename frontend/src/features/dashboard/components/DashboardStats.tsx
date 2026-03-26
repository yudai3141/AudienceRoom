import { Card } from "@/components/ui";

type DashboardStatsProps = {
  totalSessions: number;
  completedSessions: number;
  averageScore: number | null;
};

export function DashboardStats({
  totalSessions,
  completedSessions,
  averageScore,
}: DashboardStatsProps) {
  const stats = [
    {
      label: "練習回数",
      value: totalSessions,
      unit: "回",
    },
    {
      label: "完了",
      value: completedSessions,
      unit: "回",
    },
    {
      label: "平均スコア",
      value: averageScore !== null ? averageScore.toFixed(1) : "-",
      unit: averageScore !== null ? "点" : "",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {stats.map((stat) => (
        <Card key={stat.label} className="text-center">
          <p className="text-sm font-medium text-slate-500">{stat.label}</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">
            {stat.value}
            <span className="ml-1 text-lg font-normal text-slate-500">
              {stat.unit}
            </span>
          </p>
        </Card>
      ))}
    </div>
  );
}
