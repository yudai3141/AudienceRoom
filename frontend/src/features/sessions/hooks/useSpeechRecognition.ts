"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type SpeechRecognitionState = {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
};

type UseSpeechRecognitionOptions = {
  language?: string;
  continuous?: boolean;
};

type SpeechRecognitionEvent = {
  results: SpeechRecognitionResultList;
  resultIndex: number;
};

type SpeechRecognitionErrorEvent = {
  error: string;
  message?: string;
};

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

function checkSpeechRecognitionSupport(): boolean {
  if (typeof window === "undefined") return false;
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const { language = "ja-JP", continuous = false } = options;

  const isSupported = useMemo(() => checkSpeechRecognitionSupport(), []);

  const [state, setState] = useState<SpeechRecognitionState>({
    isListening: false,
    transcript: "",
    interimTranscript: "",
    error: null,
  });

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptRef = useRef("");
  const interimTranscriptRef = useRef("");
  // ボタンを押している間 true — onend で自動再開するかの判定に使う
  const isHoldingRef = useRef(false);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = continuous;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onstart = () => {
      setState((prev) => ({
        ...prev,
        isListening: true,
        error: null,
      }));
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      setState((prev) => {
        const newTranscript = prev.transcript + finalTranscript;
        transcriptRef.current = newTranscript;
        interimTranscriptRef.current = interimTranscript;
        return {
          ...prev,
          transcript: newTranscript,
          interimTranscript,
        };
      });
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // no-speech はボタン押下中の無音なので、holding 中はエラー扱いしない
      if (event.error === "no-speech" && isHoldingRef.current) {
        return;
      }
      // aborted は stopListening 時に発生するため無視
      if (event.error === "aborted") {
        return;
      }

      const errorMessages: Record<string, string> = {
        "no-speech": "音声が検出されませんでした",
        "audio-capture": "マイクにアクセスできません",
        "not-allowed": "マイクの使用が許可されていません",
        network: "ネットワークエラーが発生しました",
      };

      const errorMessage =
        errorMessages[event.error] || `エラー: ${event.error}`;

      setState((prev) => ({
        ...prev,
        error: errorMessage,
        isListening: false,
      }));
    };

    recognition.onend = () => {
      // ボタンをまだ押している場合は自動再開（ブラウザ側VADによる終了対策）
      if (isHoldingRef.current) {
        try {
          recognition.start();
        } catch {
          // start() 失敗時はリスニング状態を解除
          setState((prev) => ({ ...prev, isListening: false }));
        }
        return;
      }
      setState((prev) => ({ ...prev, isListening: false }));
    };

    recognitionRef.current = recognition;

    return () => {
      isHoldingRef.current = false;
      recognition.abort();
    };
  }, [language, continuous]);

  const startListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    isHoldingRef.current = true;
    transcriptRef.current = "";
    interimTranscriptRef.current = "";
    setState((prev) => ({
      ...prev,
      transcript: "",
      interimTranscript: "",
      error: null,
    }));

    try {
      recognition.start();
    } catch {
      isHoldingRef.current = false;
      setState((prev) => ({
        ...prev,
        error: "音声認識を開始できませんでした",
      }));
    }
  }, []);

  const stopListening = useCallback((): string => {
    isHoldingRef.current = false;

    const recognition = recognitionRef.current;
    if (!recognition) return "";

    try {
      recognition.stop();
    } catch {
      // 既に停止済みの場合のエラーを無視
    }

    // final 確定済み + まだ interim に残っているテキストを合わせて返す
    return transcriptRef.current + interimTranscriptRef.current;
  }, []);

  const resetTranscript = useCallback(() => {
    transcriptRef.current = "";
    interimTranscriptRef.current = "";
    setState((prev) => ({
      ...prev,
      transcript: "",
      interimTranscript: "",
    }));
  }, []);

  return {
    ...state,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  };
}
