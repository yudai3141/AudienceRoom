import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FeedbackDisplay } from "@/features/sessions/components/FeedbackDisplay";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const mockSessionWithFeedback = {
  id: 1,
  user_id: 1,
  status: "completed",
  mode: "interview",
  participant_count: 2,
  feedback_enabled: true,
  theme: "エンジニア面接",
  overall_score: 80,
  feedback_summary: "Good job!",
  started_at: "2024-01-15T10:00:00Z",
  ended_at: "2024-01-15T10:30:00Z",
  created_at: "2024-01-15T09:55:00Z",
  updated_at: "2024-01-15T10:35:00Z",
  participants: [],
  messages: [],
  feedback: {
    id: 1,
    summary_title: "素晴らしい練習でした！",
    short_comment: "自信を持って話せていました。",
    positive_points: ["論理的な説明ができた", "声が聞き取りやすかった"],
    improvement_points: ["もう少しゆっくり話すと良い", "具体例を増やすと良い"],
    closing_message: "この調子で頑張りましょう！",
    created_at: "2024-01-15T10:35:00Z",
    metrics: [
      {
        id: 1,
        feedback_id: 1,
        metric_key: "clarity",
        metric_value: "85",
        metric_label: "明瞭さ",
        metric_unit: "点",
        created_at: "2024-01-15T10:35:00Z",
      },
    ],
  },
};

const mockSessionWithoutFeedback = {
  ...mockSessionWithFeedback,
  feedback: null,
  overall_score: null,
};

const mockUseSessionDetail = vi.fn();

vi.mock("@/features/sessions/hooks/useSessionDetail", () => ({
  useSessionDetail: () => mockUseSessionDetail(),
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

describe("FeedbackDisplay", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    mockUseSessionDetail.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseSessionDetail.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Failed"),
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(
      screen.getByText("フィードバックの読み込みに失敗しました"),
    ).toBeInTheDocument();
  });

  it("renders session info with feedback", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("面接練習")).toBeInTheDocument();
    expect(screen.getByText("エンジニア面接")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
    expect(screen.getByText("80点")).toBeInTheDocument();
  });

  it("renders feedback summary", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("素晴らしい練習でした！")).toBeInTheDocument();
    expect(
      screen.getByText("自信を持って話せていました。"),
    ).toBeInTheDocument();
  });

  it("renders positive points", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("良かった点")).toBeInTheDocument();
    expect(screen.getByText("論理的な説明ができた")).toBeInTheDocument();
    expect(screen.getByText("声が聞き取りやすかった")).toBeInTheDocument();
  });

  it("renders improvement points", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("改善点")).toBeInTheDocument();
    expect(
      screen.getByText("もう少しゆっくり話すと良い"),
    ).toBeInTheDocument();
    expect(screen.getByText("具体例を増やすと良い")).toBeInTheDocument();
  });

  it("renders metrics", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("詳細スコア")).toBeInTheDocument();
    expect(screen.getByText("明瞭さ")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders closing message", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("最後に")).toBeInTheDocument();
    expect(
      screen.getByText("この調子で頑張りましょう！"),
    ).toBeInTheDocument();
  });

  it("renders empty state when no feedback", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithoutFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(
      screen.getByText("フィードバックはまだ生成されていません"),
    ).toBeInTheDocument();
  });

  it("renders navigation buttons", () => {
    mockUseSessionDetail.mockReturnValue({
      data: mockSessionWithFeedback,
      isLoading: false,
      error: null,
    });

    render(<FeedbackDisplay sessionId={1} />, { wrapper: createWrapper() });

    expect(screen.getByText("履歴に戻る")).toBeInTheDocument();
    expect(screen.getByText("新しい練習を始める")).toBeInTheDocument();
  });
});
