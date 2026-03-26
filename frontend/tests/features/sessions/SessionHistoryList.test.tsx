import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionHistoryList } from "@/features/sessions/components/SessionHistoryList";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

const mockCurrentUser = {
  id: 1,
  firebase_uid: "test-uid",
  email: "test@example.com",
  display_name: "Test User",
  photo_url: null,
  onboarding_completed: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

vi.mock("@/features/auth/hooks/useCurrentUser", () => ({
  useCurrentUser: () => ({
    data: mockCurrentUser,
    isLoading: false,
  }),
}));

const mockSessionsData = {
  items: [
    {
      id: 1,
      status: "completed",
      mode: "interview",
      theme: "エンジニア面接",
      overall_score: 80,
      has_feedback: true,
      started_at: "2024-01-15T10:00:00Z",
      ended_at: "2024-01-15T10:30:00Z",
      created_at: "2024-01-15T09:55:00Z",
    },
    {
      id: 2,
      status: "in_progress",
      mode: "presentation",
      theme: null,
      overall_score: null,
      has_feedback: false,
      started_at: "2024-01-16T14:00:00Z",
      ended_at: null,
      created_at: "2024-01-16T13:55:00Z",
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
};

const mockUseSessions = vi.fn();

vi.mock("@/features/sessions/hooks/useSessions", () => ({
  useSessions: () => mockUseSessions(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("SessionHistoryList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    mockUseSessions.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseSessions.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Failed"),
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(
      screen.getByText("履歴の読み込みに失敗しました"),
    ).toBeInTheDocument();
  });

  it("renders empty state", () => {
    mockUseSessions.mockReturnValue({
      data: { items: [], total: 0, limit: 20, offset: 0 },
      isLoading: false,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(screen.getByText("まだ練習履歴がありません")).toBeInTheDocument();
    expect(screen.getByText("最初の練習を始める →")).toBeInTheDocument();
  });

  it("renders session list", () => {
    mockUseSessions.mockReturnValue({
      data: mockSessionsData,
      isLoading: false,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(screen.getByText("全 2 件中 2 件を表示")).toBeInTheDocument();
    expect(screen.getByText("面接練習")).toBeInTheDocument();
    expect(screen.getByText("プレゼン練習")).toBeInTheDocument();
    expect(screen.getByText("エンジニア面接")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
    expect(screen.getByText("進行中")).toBeInTheDocument();
  });

  it("displays feedback indicator for sessions with feedback", () => {
    mockUseSessions.mockReturnValue({
      data: mockSessionsData,
      isLoading: false,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(screen.getByText("フィードバックあり")).toBeInTheDocument();
  });

  it("displays score as stars", () => {
    mockUseSessions.mockReturnValue({
      data: mockSessionsData,
      isLoading: false,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    expect(screen.getByText("★★★★☆")).toBeInTheDocument();
  });

  it("links to session detail page", () => {
    mockUseSessions.mockReturnValue({
      data: mockSessionsData,
      isLoading: false,
      error: null,
    });

    render(<SessionHistoryList />, { wrapper: createWrapper() });

    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/sessions/1");
    expect(links[1]).toHaveAttribute("href", "/sessions/2");
  });
});
