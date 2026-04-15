"use client";

import { useCallback, useRef, useState } from "react";
import { readSSEStream } from "@/lib/api/sse";
import { baseUrl } from "@/lib/api/client";
import { getFirebaseAuth } from "@/lib/firebase";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  participantId?: number | null;
  timestamp: Date;
};

type StreamingConversationState = {
  messages: Message[];
  isStreaming: boolean;
  isSpeaking: boolean;
  speakingParticipantId: number | null;
  error: string | null;
};

type UseStreamingConversationOptions = {
  sessionId: number;
  generateAudio?: boolean;
  onAiResponse?: (message: Message) => void;
};

type AudioQueueItem = {
  audio: string;
  sequence: number;
  participantId?: number | null;
};

export function useStreamingConversation(
  options: UseStreamingConversationOptions
) {
  const { sessionId, generateAudio = true, onAiResponse } = options;

  const [state, setState] = useState<StreamingConversationState>({
    messages: [],
    isStreaming: false,
    isSpeaking: false,
    speakingParticipantId: null,
    error: null,
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messageIdRef = useRef(0);
  const audioQueueRef = useRef<AudioQueueItem[]>([]);
  const nextSequenceRef = useRef(1);
  const isPlayingRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const generateMessageId = useCallback(() => {
    messageIdRef.current += 1;
    return `msg-${Date.now()}-${messageIdRef.current}`;
  }, []);

  const playAudio = useCallback(
    (
      base64Audio: string,
      participantId?: number | null
    ): Promise<void> => {
      return new Promise((resolve, reject) => {
        try {
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
          }

          const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
          audioRef.current = audio;

          setState((prev) => ({
            ...prev,
            isSpeaking: true,
            speakingParticipantId: participantId ?? null,
          }));

          audio.onended = () => {
            setState((prev) => ({
              ...prev,
              isSpeaking: false,
              speakingParticipantId: null,
            }));
            resolve();
          };

          audio.onerror = () => {
            setState((prev) => ({
              ...prev,
              isSpeaking: false,
              speakingParticipantId: null,
            }));
            reject(new Error("音声の再生に失敗しました"));
          };

          audio.play().catch(reject);
        } catch (error) {
          setState((prev) => ({
            ...prev,
            isSpeaking: false,
            speakingParticipantId: null,
          }));
          reject(error);
        }
      });
    },
    []
  );

  const playNextAudio = useCallback(async () => {
    if (isPlayingRef.current) return;

    const nextAudio = audioQueueRef.current.find(
      (item) => item.sequence === nextSequenceRef.current
    );

    if (nextAudio) {
      isPlayingRef.current = true;
      try {
        await playAudio(nextAudio.audio, nextAudio.participantId);
        nextSequenceRef.current++;
        audioQueueRef.current = audioQueueRef.current.filter(
          (item) => item.sequence !== nextAudio.sequence
        );
      } catch (error) {
        console.error("音声再生エラー:", error);
      } finally {
        isPlayingRef.current = false;
        // 次の音声があれば再帰的に再生
        if (audioQueueRef.current.length > 0) {
          playNextAudio();
        }
      }
    }
  }, [playAudio]);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setState((prev) => ({
        ...prev,
        isSpeaking: false,
        speakingParticipantId: null,
      }));
    }
    audioQueueRef.current = [];
    nextSequenceRef.current = 1;
    isPlayingRef.current = false;
  }, []);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) return;

      // 既存のストリーミングをキャンセル
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const userMessage: Message = {
        id: generateMessageId(),
        role: "user",
        content: message,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isStreaming: true,
        error: null,
      }));

      // オーディオキューをリセット
      stopAudio();
      nextSequenceRef.current = 1;

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        // Firebase トークンを取得
        const auth = getFirebaseAuth();
        const token = await auth?.currentUser?.getIdToken();

        const response = await fetch(`${baseUrl}/conversation/message/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({
            session_id: sessionId,
            message,
            generate_audio: generateAudio,
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("メッセージの送信に失敗しました");
        }

        const aiMessageId = generateMessageId();
        let fullText = "";
        let participantId: number | null = null;

        for await (const sseEvent of readSSEStream(response)) {
          if (controller.signal.aborted) break;

          // Discriminated Union により型が自動的に絞り込まれる
          if (sseEvent.event === "metadata") {
            participantId = sseEvent.data.participant_id ?? null;
          } else if (sseEvent.event === "text_chunk") {
            fullText += sseEvent.data.text;

            // メッセージを更新（既存メッセージがあれば更新、なければ追加）
            setState((prev) => {
              const existingIndex = prev.messages.findIndex(
                (m) => m.id === aiMessageId
              );
              const aiMessage: Message = {
                id: aiMessageId,
                role: "assistant",
                content: fullText,
                participantId,
                timestamp: new Date(),
              };

              if (existingIndex >= 0) {
                const newMessages = [...prev.messages];
                newMessages[existingIndex] = aiMessage;
                return { ...prev, messages: newMessages };
              } else {
                return {
                  ...prev,
                  messages: [...prev.messages, aiMessage],
                };
              }
            });
          } else if (sseEvent.event === "audio_chunk") {
            // オーディオキューに追加（型が自動的に絞り込まれる）
            audioQueueRef.current.push({
              audio: sseEvent.data.audio_base64,
              sequence: sseEvent.data.sequence,
              participantId,
            });
            // 再生開始
            playNextAudio();
          } else if (sseEvent.event === "complete") {
            setState((prev) => ({ ...prev, isStreaming: false }));

            // 最終メッセージを取得してコールバック実行
            const finalMessage: Message = {
              id: aiMessageId,
              role: "assistant",
              content: fullText,
              participantId,
              timestamp: new Date(),
            };
            onAiResponse?.(finalMessage);
          } else if (sseEvent.event === "error") {
            throw new Error(sseEvent.data.message || "エラーが発生しました");
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          // キャンセルされた場合は無視
          return;
        }

        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error:
            error instanceof Error ? error.message : "エラーが発生しました",
        }));
      } finally {
        abortControllerRef.current = null;
      }
    },
    [
      sessionId,
      generateAudio,
      generateMessageId,
      playNextAudio,
      stopAudio,
      onAiResponse,
    ]
  );

  const startConversation = useCallback(async () => {
    // 既存のストリーミングをキャンセル
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setState((prev) => ({
      ...prev,
      isStreaming: true,
      error: null,
    }));

    // オーディオキューをリセット
    stopAudio();
    nextSequenceRef.current = 1;

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // Firebase トークンを取得
      const auth = getFirebaseAuth();
      const token = await auth?.currentUser?.getIdToken();

      const response = await fetch(`${baseUrl}/conversation/start/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          session_id: sessionId,
          generate_audio: generateAudio,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error("会話の開始に失敗しました");
      }

      const aiMessageId = generateMessageId();
      let fullText = "";
      let participantId: number | null = null;

      for await (const sseEvent of readSSEStream(response)) {
        if (controller.signal.aborted) break;

        // Discriminated Union により型が自動的に絞り込まれる
        if (sseEvent.event === "metadata") {
          participantId = sseEvent.data.participant_id ?? null;
        } else if (sseEvent.event === "text_chunk") {
          fullText += sseEvent.data.text;

          setState((prev) => {
            const existingIndex = prev.messages.findIndex(
              (m) => m.id === aiMessageId
            );
            const aiMessage: Message = {
              id: aiMessageId,
              role: "assistant",
              content: fullText,
              participantId,
              timestamp: new Date(),
            };

            if (existingIndex >= 0) {
              const newMessages = [...prev.messages];
              newMessages[existingIndex] = aiMessage;
              return { ...prev, messages: newMessages };
            } else {
              return {
                ...prev,
                messages: [aiMessage],
              };
            }
          });
        } else if (sseEvent.event === "audio_chunk") {
          // 型が自動的に絞り込まれる
          audioQueueRef.current.push({
            audio: sseEvent.data.audio_base64,
            sequence: sseEvent.data.sequence,
            participantId,
          });
          playNextAudio();
        } else if (sseEvent.event === "complete") {
          setState((prev) => ({ ...prev, isStreaming: false }));

          const finalMessage: Message = {
            id: aiMessageId,
            role: "assistant",
            content: fullText,
            participantId,
            timestamp: new Date(),
          };
          onAiResponse?.(finalMessage);
        } else if (sseEvent.event === "error") {
          throw new Error(sseEvent.data.message || "エラーが発生しました");
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }

      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : "エラーが発生しました",
      }));
    } finally {
      abortControllerRef.current = null;
    }
  }, [
    sessionId,
    generateAudio,
    generateMessageId,
    playNextAudio,
    stopAudio,
    onAiResponse,
  ]);

  const clearMessages = useCallback(() => {
    setState((prev) => ({
      ...prev,
      messages: [],
      error: null,
    }));
  }, []);

  return {
    ...state,
    isProcessing: state.isStreaming, // 後方互換性のためのエイリアス
    sendMessage,
    startConversation,
    clearMessages,
    stopAudio,
    playAudio,
  };
}
