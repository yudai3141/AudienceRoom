import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionRoom } from "@/features/sessions/components/SessionRoom";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const mockStream = {
  getTracks: () => [
    { stop: vi.fn(), enabled: true, kind: "video" },
    { stop: vi.fn(), enabled: true, kind: "audio" },
  ],
  getVideoTracks: () => [{ enabled: true, stop: vi.fn() }],
  getAudioTracks: () => [{ enabled: true, stop: vi.fn() }],
};

const mockGetUserMedia = vi.fn();

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

describe("SessionRoom", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(global.navigator, "mediaDevices", {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      writable: true,
    });
  });

  it("renders permission request screen initially", () => {
    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    expect(
      screen.getByText("カメラとマイクを使用します"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "アクセスを許可する" }),
    ).toBeInTheDocument();
  });

  it("requests permissions when button is clicked", async () => {
    const user = userEvent.setup();
    mockGetUserMedia.mockResolvedValue(mockStream);

    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    const permissionButton = screen.getByRole("button", {
      name: "アクセスを許可する",
    });
    await user.click(permissionButton);

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      video: true,
      audio: true,
    });
  });

  it("shows denied screen when permission is denied", async () => {
    const user = userEvent.setup();
    mockGetUserMedia.mockRejectedValue({ name: "NotAllowedError" });

    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    const permissionButton = screen.getByRole("button", {
      name: "アクセスを許可する",
    });
    await user.click(permissionButton);

    await waitFor(() => {
      expect(
        screen.getByText("アクセスが拒否されました"),
      ).toBeInTheDocument();
    });
  });

  it("shows video room after permission granted", async () => {
    const user = userEvent.setup();
    mockGetUserMedia.mockResolvedValue(mockStream);

    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    const permissionButton = screen.getByRole("button", {
      name: "アクセスを許可する",
    });
    await user.click(permissionButton);

    await waitFor(() => {
      expect(screen.getByText("あなた")).toBeInTheDocument();
      expect(screen.getByText("面接官 A")).toBeInTheDocument();
      expect(screen.getByText("面接官 B")).toBeInTheDocument();
    });
  });

  it("shows control bar with camera, mic, and leave buttons", async () => {
    const user = userEvent.setup();
    mockGetUserMedia.mockResolvedValue(mockStream);

    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    const permissionButton = screen.getByRole("button", {
      name: "アクセスを許可する",
    });
    await user.click(permissionButton);

    await waitFor(() => {
      expect(
        screen.getByTitle("カメラをオフにする"),
      ).toBeInTheDocument();
      expect(
        screen.getByTitle("マイクをオフにする"),
      ).toBeInTheDocument();
      expect(screen.getByTitle("退出する")).toBeInTheDocument();
    });
  });

  it("navigates to sessions list when leave button clicked", async () => {
    const user = userEvent.setup();
    mockGetUserMedia.mockResolvedValue(mockStream);

    render(<SessionRoom sessionId={1} />, { wrapper: createWrapper() });

    const permissionButton = screen.getByRole("button", {
      name: "アクセスを許可する",
    });
    await user.click(permissionButton);

    await waitFor(() => {
      expect(screen.getByTitle("退出する")).toBeInTheDocument();
    });

    const leaveButton = screen.getByTitle("退出する");
    await user.click(leaveButton);

    expect(mockPush).toHaveBeenCalledWith("/sessions");
  });
});
