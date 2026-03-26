import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useConversation } from "@/features/sessions/hooks/useConversation";

const mockPost = vi.fn();

vi.mock("@/lib/api/client", () => ({
  api: {
    POST: (...args: unknown[]) => mockPost(...args),
  },
}));

describe("useConversation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with empty state", () => {
    const { result } = renderHook(() =>
      useConversation({ sessionId: 1 }),
    );

    expect(result.current.messages).toEqual([]);
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should send message and receive response", async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        text: "AI応答です",
        audio_base64: null,
        speaker_id: 3,
        participant_id: 1,
      },
      error: null,
    });

    const { result } = renderHook(() =>
      useConversation({ sessionId: 1, generateAudio: false }),
    );

    await act(async () => {
      await result.current.sendMessage("テストメッセージ");
    });

    expect(mockPost).toHaveBeenCalledWith("/conversation/message", {
      body: {
        session_id: 1,
        message: "テストメッセージ",
        generate_audio: false,
      },
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("テストメッセージ");
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("AI応答です");
  });

  it("should start conversation and receive opening message", async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        text: "こんにちは、面接を始めましょう",
        audio_base64: null,
        speaker_id: 3,
        participant_id: 1,
      },
      error: null,
    });

    const { result } = renderHook(() =>
      useConversation({ sessionId: 1, generateAudio: false }),
    );

    await act(async () => {
      await result.current.startConversation();
    });

    expect(mockPost).toHaveBeenCalledWith("/conversation/start", {
      body: {
        session_id: 1,
        generate_audio: false,
      },
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    expect(result.current.messages[0].role).toBe("assistant");
    expect(result.current.messages[0].content).toBe(
      "こんにちは、面接を始めましょう",
    );
  });

  it("should handle API errors", async () => {
    mockPost.mockResolvedValueOnce({
      data: null,
      error: { detail: "エラー" },
    });

    const { result } = renderHook(() =>
      useConversation({ sessionId: 1 }),
    );

    await act(async () => {
      await result.current.sendMessage("テスト");
    });

    await waitFor(() => {
      expect(result.current.error).toBe("メッセージの送信に失敗しました");
    });
  });

  it("should not send empty messages", async () => {
    const { result } = renderHook(() =>
      useConversation({ sessionId: 1 }),
    );

    await act(async () => {
      await result.current.sendMessage("");
    });

    expect(mockPost).not.toHaveBeenCalled();
  });

  it("should clear messages", async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        text: "応答",
        audio_base64: null,
        speaker_id: 3,
        participant_id: 1,
      },
      error: null,
    });

    const { result } = renderHook(() =>
      useConversation({ sessionId: 1, generateAudio: false }),
    );

    await act(async () => {
      await result.current.sendMessage("テスト");
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toEqual([]);
  });

  it("should call onAiResponse callback when receiving response", async () => {
    const onAiResponse = vi.fn();

    mockPost.mockResolvedValueOnce({
      data: {
        text: "AI応答",
        audio_base64: null,
        speaker_id: 3,
        participant_id: 1,
      },
      error: null,
    });

    const { result } = renderHook(() =>
      useConversation({
        sessionId: 1,
        generateAudio: false,
        onAiResponse,
      }),
    );

    await act(async () => {
      await result.current.sendMessage("テスト");
    });

    await waitFor(() => {
      expect(onAiResponse).toHaveBeenCalled();
    });

    expect(onAiResponse).toHaveBeenCalledWith(
      expect.objectContaining({
        role: "assistant",
        content: "AI応答",
      }),
    );
  });
});
