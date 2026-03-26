import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DashboardStats } from "@/features/dashboard/components/DashboardStats";

describe("DashboardStats", () => {
  it("renders all stats correctly", () => {
    render(
      <DashboardStats
        totalSessions={10}
        completedSessions={8}
        averageScore={75.5}
      />,
    );

    expect(screen.getByText("練習回数")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();

    expect(screen.getByText("完了")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();

    expect(screen.getByText("平均スコア")).toBeInTheDocument();
    expect(screen.getByText("75.5")).toBeInTheDocument();
  });

  it("renders dash when average score is null", () => {
    render(
      <DashboardStats
        totalSessions={5}
        completedSessions={3}
        averageScore={null}
      />,
    );

    expect(screen.getByText("平均スコア")).toBeInTheDocument();
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders zero values correctly", () => {
    render(
      <DashboardStats
        totalSessions={0}
        completedSessions={0}
        averageScore={null}
      />,
    );

    const zeros = screen.getAllByText("0");
    expect(zeros).toHaveLength(2);
  });
});
