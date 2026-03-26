"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api/client";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  participantId?: number | null;
  timestamp: Date;
};

type ConversationState = {
  messages: Message[];
  isProcessing: boolean;
  isSpeaking: boolean;
  error: string | null;
};

type UseConversationOptions = {
  sessionId: number;
  generateAudio?: boolean;
  onAiResponse?: (message: Message) => void;
};

export function useConversation(options: UseConversationOptions) {
  const { sessionId, generateAudio = true, onAiResponse } = options;

  const [state, setState] = useState<ConversationState>({
    messages: [],
    isProcessing: false,
    isSpeaking: false,
    error: null,
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messageIdRef = useRef(0);

  const generateMessageId = useCallback(() => {
    messageIdRef.current += 1;
    return `msg-${Date.now()}-${messageIdRef.current}`;
  }, []);

  const playAudio = useCallback((base64Audio: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }

        const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
        audioRef.current = audio;

        setState((prev) => ({ ...prev, isSpeaking: true }));

        audio.onended = () => {
          setState((prev) => ({ ...prev, isSpeaking: false }));
          resolve();
        };

        audio.onerror = () => {
          setState((prev) => ({ ...prev, isSpeaking: false }));
          reject(new Error("音声の再生に失敗しました"));
        };

        audio.play().catch(reject);
      } catch (error) {
        setState((prev) => ({ ...prev, isSpeaking: false }));
        reject(error);
      }
    });
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setState((prev) => ({ ...prev, isSpeaking: false }));
    }
  }, []);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) return;

      const userMessage: Message = {
        id: generateMessageId(),
        role: "user",
        content: message,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isProcessing: true,
        error: null,
      }));

      try {
        const { data, error } = await api.POST("/conversation/message", {
          body: {
            session_id: sessionId,
            message,
            generate_audio: generateAudio,
          },
        });

        if (error) {
          throw new Error("メッセージの送信に失敗しました");
        }

        const aiMessage: Message = {
          id: generateMessageId(),
          role: "assistant",
          content: data.text,
          participantId: data.participant_id,
          timestamp: new Date(),
        };

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, aiMessage],
          isProcessing: false,
        }));

        onAiResponse?.(aiMessage);

        if (data.audio_base64) {
          await playAudio(data.audio_base64);
        }
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error:
            error instanceof Error ? error.message : "エラーが発生しました",
        }));
      }
    },
    [sessionId, generateAudio, generateMessageId, playAudio, onAiResponse],
  );

  const startConversation = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      isProcessing: true,
      error: null,
    }));

    try {
      const { data, error } = await api.POST("/conversation/start", {
        body: {
          session_id: sessionId,
          generate_audio: generateAudio,
        },
      });

      if (error) {
        throw new Error("会話の開始に失敗しました");
      }

      const aiMessage: Message = {
        id: generateMessageId(),
        role: "assistant",
        content: data.text,
        participantId: data.participant_id,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [aiMessage],
        isProcessing: false,
      }));

      onAiResponse?.(aiMessage);

      if (data.audio_base64) {
        await playAudio(data.audio_base64);
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: error instanceof Error ? error.message : "エラーが発生しました",
      }));
    }
  }, [sessionId, generateAudio, generateMessageId, playAudio, onAiResponse]);

  const clearMessages = useCallback(() => {
    setState((prev) => ({
      ...prev,
      messages: [],
      error: null,
    }));
  }, []);

  return {
    ...state,
    sendMessage,
    startConversation,
    clearMessages,
    stopAudio,
    playAudio,
  };
}
