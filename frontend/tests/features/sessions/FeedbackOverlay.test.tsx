import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

type ConversationPhase = "waiting" | "active" | "ending" | "ended";

type FeedbackSummary = {
  overallScore: number | null;
  summaryTitle: string;
  shortComment: string | null;
};

function FeedbackOverlay({
  phase,
  feedback,
  onViewDetails,
}: {
  phase: ConversationPhase;
  feedback: FeedbackSummary | null;
  onViewDetails: () => void;
}) {
  if (phase !== "ending" && phase !== "ended") {
    return null;
  }

  const stars = feedback?.overallScore
    ? Math.round(feedback.overallScore / 20)
    : 0;

  return (
    <div
      data-testid="feedback-overlay"
      className="absolute inset-0 z-50 flex items-center justify-center bg-black/80"
    >
      <div className="mx-4 max-w-md rounded-xl border bg-white p-6">
        <div className="p-8 text-center">
          {phase === "ending" ? (
            <>
              <div data-testid="spinner" className="mx-auto mb-4">
                Loading...
              </div>
              <h2 className="mb-2 text-xl font-semibold text-slate-900">
                フィードバックを生成中...
              </h2>
              <p className="text-sm text-slate-500">
                AIがあなたのパフォーマンスを分析しています
              </p>
            </>
          ) : feedback ? (
            <>
              <div className="mb-4 text-4xl text-amber-500">
                {"★".repeat(stars)}
                {"☆".repeat(5 - stars)}
              </div>
              {feedback.overallScore !== null && (
                <div className="mb-2 text-3xl font-bold text-slate-900">
                  {feedback.overallScore}点
                </div>
              )}
              <h2 className="mb-2 text-xl font-semibold text-slate-900">
                {feedback.summaryTitle}
              </h2>
              {feedback.shortComment && (
                <p className="mb-6 text-sm text-slate-600">
                  {feedback.shortComment}
                </p>
              )}
              <button
                onClick={onViewDetails}
                className="w-full rounded bg-indigo-600 px-4 py-2 text-white"
              >
                詳しい結果を見る
              </button>
            </>
          ) : (
            <>
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <span>✓</span>
              </div>
              <h2 className="mb-2 text-xl font-semibold text-slate-900">
                お疲れ様でした！
              </h2>
              <p className="mb-6 text-sm text-slate-500">練習が完了しました</p>
              <button
                onClick={onViewDetails}
                className="w-full rounded bg-indigo-600 px-4 py-2 text-white"
              >
                結果を見る
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

describe("FeedbackOverlay", () => {
  it("returns null when phase is waiting", () => {
    const { container } = render(
      <FeedbackOverlay
        phase="waiting"
        feedback={null}
        onViewDetails={vi.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("returns null when phase is active", () => {
    const { container } = render(
      <FeedbackOverlay
        phase="active"
        feedback={null}
        onViewDetails={vi.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows loading state when phase is ending", () => {
    render(
      <FeedbackOverlay
        phase="ending"
        feedback={null}
        onViewDetails={vi.fn()}
      />,
    );

    expect(screen.getByTestId("feedback-overlay")).toBeInTheDocument();
    expect(screen.getByText("フィードバックを生成中...")).toBeInTheDocument();
    expect(
      screen.getByText("AIがあなたのパフォーマンスを分析しています"),
    ).toBeInTheDocument();
  });

  it("shows feedback summary when phase is ended with feedback", () => {
    const feedback: FeedbackSummary = {
      overallScore: 80,
      summaryTitle: "素晴らしいパフォーマンス",
      shortComment: "よく頑張りました",
    };

    render(
      <FeedbackOverlay
        phase="ended"
        feedback={feedback}
        onViewDetails={vi.fn()}
      />,
    );

    expect(screen.getByTestId("feedback-overlay")).toBeInTheDocument();
    expect(screen.getByText("80点")).toBeInTheDocument();
    expect(screen.getByText("素晴らしいパフォーマンス")).toBeInTheDocument();
    expect(screen.getByText("よく頑張りました")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "詳しい結果を見る" }),
    ).toBeInTheDocument();
  });

  it("shows completion message when phase is ended without feedback", () => {
    render(
      <FeedbackOverlay phase="ended" feedback={null} onViewDetails={vi.fn()} />,
    );

    expect(screen.getByTestId("feedback-overlay")).toBeInTheDocument();
    expect(screen.getByText("お疲れ様でした！")).toBeInTheDocument();
    expect(screen.getByText("練習が完了しました")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "結果を見る" }),
    ).toBeInTheDocument();
  });

  it("calls onViewDetails when button is clicked", async () => {
    const user = userEvent.setup();
    const mockOnViewDetails = vi.fn();

    render(
      <FeedbackOverlay
        phase="ended"
        feedback={null}
        onViewDetails={mockOnViewDetails}
      />,
    );

    await user.click(screen.getByRole("button", { name: "結果を見る" }));
    expect(mockOnViewDetails).toHaveBeenCalledTimes(1);
  });

  it("displays correct star rating based on score", () => {
    const feedback: FeedbackSummary = {
      overallScore: 60,
      summaryTitle: "良い調子",
      shortComment: null,
    };

    render(
      <FeedbackOverlay
        phase="ended"
        feedback={feedback}
        onViewDetails={vi.fn()}
      />,
    );

    const starsContainer = screen.getByText(/★/);
    expect(starsContainer.textContent).toBe("★★★☆☆");
  });

  it("has correct overlay styling", () => {
    render(
      <FeedbackOverlay
        phase="ending"
        feedback={null}
        onViewDetails={vi.fn()}
      />,
    );

    const overlay = screen.getByTestId("feedback-overlay");
    expect(overlay).toHaveClass("absolute");
    expect(overlay).toHaveClass("inset-0");
    expect(overlay).toHaveClass("z-50");
    expect(overlay).toHaveClass("bg-black/80");
  });
});
