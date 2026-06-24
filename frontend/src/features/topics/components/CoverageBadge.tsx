import { Badge } from "@/components/ui";

const COVERAGE_MAP: Record<
  string,
  { variant: "success" | "warning" | "default"; label: string }
> = {
  covered: { variant: "success", label: "話せる" },
  weak: { variant: "warning", label: "弱い" },
  gap: { variant: "default", label: "未説明" },
};

export function CoverageBadge({ coverage }: { coverage: string }) {
  const m = COVERAGE_MAP[coverage] ?? { variant: "default" as const, label: coverage };
  return <Badge variant={m.variant}>{m.label}</Badge>;
}
