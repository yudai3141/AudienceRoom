import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionSetupForm } from "@/features/sessions/components/SessionSetupForm";

const mockReplace = vi.fn();
const mockBack = vi.fn();
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    back: mockBack,
    push: mockPush,
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

const mockAiCharacters = [
  {
    id: 1,
    code: "interviewer_1",
    name: "田中面接官",
    role: "interviewer",
    strictness: "medium",
    personality: "friendly",
    voice_style: "calm",
    description: "経験豊富な面接官",
    is_active: true,
  },
];

vi.mock("@/features/auth/hooks/useCurrentUser", () => ({
  useCurrentUser: () => ({
    data: mockCurrentUser,
    isLoading: false,
  }),
}));

vi.mock("@/features/sessions/hooks/useAiCharacters", () => ({
  useAiCharacters: () => ({
    data: mockAiCharacters,
    isLoading: false,
  }),
}));

const mockMutateAsync = vi.fn();

vi.mock("@/features/sessions/hooks/useCreateSession", () => ({
  useCreateSession: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
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

describe("SessionSetupForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form with all sections", () => {
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    expect(screen.getByText("練習モード")).toBeInTheDocument();
    expect(screen.getByText("面接練習")).toBeInTheDocument();
    expect(screen.getByText("プレゼン練習")).toBeInTheDocument();
    expect(screen.getByText("参加者数")).toBeInTheDocument();
    expect(screen.getByText("練習テーマ（任意）")).toBeInTheDocument();
    expect(screen.getByText("練習の目標（任意）")).toBeInTheDocument();
    expect(screen.getByText("不安な点・苦手な点（任意）")).toBeInTheDocument();
    expect(screen.getByText("フィードバックを受け取る")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "練習を開始" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "キャンセル" }),
    ).toBeInTheDocument();
  });

  it("selects interview mode by default", () => {
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const interviewRadio = screen.getByRole("radio", { name: /面接練習/i });
    expect(interviewRadio).toBeChecked();
  });

  it("can switch to presentation mode", async () => {
    const user = userEvent.setup();
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const presentationRadio = screen.getByRole("radio", {
      name: /プレゼン練習/i,
    });
    await user.click(presentationRadio);

    expect(presentationRadio).toBeChecked();
  });

  it("can select participant count", async () => {
    const user = userEvent.setup();
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const twoPersonRadio = screen.getByRole("radio", { name: "2人" });
    await user.click(twoPersonRadio);

    expect(twoPersonRadio).toBeChecked();
  });

  it("submits form and navigates to session page", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue({ id: 123 });

    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const themeInput = screen.getByPlaceholderText("テーマを入力...");
    await user.type(themeInput, "エンジニア職の最終面接");

    const submitButton = screen.getByRole("button", { name: "練習を開始" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        user_id: 1,
        mode: "interview",
        participant_count: 1,
        feedback_enabled: true,
        theme: "エンジニア職の最終面接",
        user_goal: null,
        user_concerns: null,
      });
      expect(mockPush).toHaveBeenCalledWith("/sessions/123");
    });
  });

  it("can cancel and go back", async () => {
    const user = userEvent.setup();
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const cancelButton = screen.getByRole("button", { name: "キャンセル" });
    await user.click(cancelButton);

    expect(mockBack).toHaveBeenCalled();
  });

  it("shows error on submission failure", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockRejectedValue(new Error("Failed"));

    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const submitButton = screen.getByRole("button", { name: "練習を開始" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("セッションの作成に失敗しました"),
      ).toBeInTheDocument();
    });
  });

  it("displays available AI characters count", () => {
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    expect(
      screen.getByText("使用可能なAIキャラクター: 1人"),
    ).toBeInTheDocument();
  });

  it("can toggle feedback enabled", async () => {
    const user = userEvent.setup();
    render(<SessionSetupForm />, { wrapper: createWrapper() });

    const feedbackCheckbox = screen.getByRole("checkbox", {
      name: /フィードバックを受け取る/i,
    });
    expect(feedbackCheckbox).toBeChecked();

    await user.click(feedbackCheckbox);
    expect(feedbackCheckbox).not.toBeChecked();
  });
});
