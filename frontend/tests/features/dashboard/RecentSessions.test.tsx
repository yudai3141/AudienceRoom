import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RecentSessions } from "@/features/dashboard/components/RecentSessions";
import type { SessionListItem } from "@/features/dashboard/hooks/useDashboard";

const mockSessions: SessionListItem[] = [
  {
    id: 1,
    status: "completed",
    mode: "presentation",
    theme: "自己紹介プレゼン",
    overall_score: 80,
    has_feedback: true,
    started_at: "2026-03-25T10:00:00Z",
    ended_at: "2026-03-25T10:30:00Z",
    created_at: "2026-03-25T09:55:00Z",
  },
  {
    id: 2,
    status: "completed",
    mode: "interview",
    theme: null,
    overall_score: 60,
    has_feedback: false,
    started_at: "2026-03-24T14:00:00Z",
    ended_at: "2026-03-24T14:20:00Z",
    created_at: "2026-03-24T13:55:00Z",
  },
];

describe("RecentSessions", () => {
  it("renders empty state when no sessions", () => {
    render(<RecentSessions sessions={[]} />);

    expect(screen.getByText("まだ練習履歴がありません")).toBeInTheDocument();
    expect(screen.getByText("最初の練習を始める")).toBeInTheDocument();
  });

  it("renders session list correctly", () => {
    render(<RecentSessions sessions={mockSessions} />);

    expect(screen.getByText("プレゼン")).toBeInTheDocument();
    expect(screen.getByText("自己紹介プレゼン")).toBeInTheDocument();

    expect(screen.getByText("面接")).toBeInTheDocument();
    expect(screen.getByText("テーマなし")).toBeInTheDocument();
  });

  it("renders feedback badge for sessions with feedback", () => {
    render(<RecentSessions sessions={mockSessions} />);

    expect(screen.getByText("FB済")).toBeInTheDocument();
  });

  it("renders star scores correctly", () => {
    render(<RecentSessions sessions={mockSessions} />);

    expect(screen.getByText("★★★★☆")).toBeInTheDocument();
    expect(screen.getByText("★★★☆☆")).toBeInTheDocument();
  });

  it("links to session detail page", () => {
    render(<RecentSessions sessions={mockSessions} />);

    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/sessions/1");
    expect(links[1]).toHaveAttribute("href", "/sessions/2");
  });
});
