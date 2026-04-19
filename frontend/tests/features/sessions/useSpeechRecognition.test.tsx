import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSpeechRecognition } from "@/features/sessions/hooks/useSpeechRecognition";

function createMockSpeechRecognition() {
  return {
    continuous: false,
    interimResults: false,
    lang: "",
    start: vi.fn(),
    stop: vi.fn(),
    abort: vi.fn(),
    onresult: null as ((event: unknown) => void) | null,
    onerror: null as ((event: unknown) => void) | null,
    onend: null as (() => void) | null,
    onstart: null as (() => void) | null,
  };
}

let mockInstance: ReturnType<typeof createMockSpeechRecognition>;

class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = "";

  constructor() {
    mockInstance = createMockSpeechRecognition();
    this.start = mockInstance.start;
    this.stop = mockInstance.stop;
    this.abort = mockInstance.abort;
  }

  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: unknown) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  onstart: (() => void) | null = null;
}

describe("useSpeechRecognition", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockSpeechRecognition,
      writable: true,
      configurable: true,
    });
  });

  it("should initialize with supported state when SpeechRecognition is available", () => {
    const { result } = renderHook(() => useSpeechRecognition());

    expect(result.current.isSupported).toBe(true);
    expect(result.current.isListening).toBe(false);
    expect(result.current.transcript).toBe("");
  });

  it("should not be supported when SpeechRecognition is unavailable", () => {
    Object.defineProperty(window, "SpeechRecognition", {
      value: undefined,
      writable: true,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      value: undefined,
      writable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    expect(result.current.isSupported).toBe(false);
  });

  it("should start listening when startListening is called", () => {
    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
    });

    expect(mockInstance.start).toHaveBeenCalled();
  });

  it("should stop listening when stopListening is called", () => {
    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.stopListening();
    });

    expect(mockInstance.stop).toHaveBeenCalled();
  });

  it("should update isListening when recognition starts", () => {
    let capturedOnStart: (() => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onresult: ((event: unknown) => void) | null = null;
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;

      set onstart(fn: (() => void) | null) {
        capturedOnStart = fn;
      }

      get onstart() {
        return capturedOnStart;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnStart?.();
    });

    expect(result.current.isListening).toBe(true);
  });

  it("should buffer transcript and return it from stopListening", () => {
    let capturedOnStart: (() => void) | null = null;
    let capturedOnResult: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;

      set onstart(fn: (() => void) | null) {
        capturedOnStart = fn;
      }

      get onstart() {
        return capturedOnStart;
      }

      set onresult(fn: ((event: unknown) => void) | null) {
        capturedOnResult = fn;
      }

      get onresult() {
        return capturedOnResult;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnStart?.();
    });

    act(() => {
      capturedOnResult?.({
        resultIndex: 0,
        results: {
          length: 1,
          0: {
            isFinal: true,
            0: { transcript: "こんにちは" },
          },
        },
      });
    });

    expect(result.current.transcript).toBe("こんにちは");

    let returnedTranscript = "";
    act(() => {
      returnedTranscript = result.current.stopListening();
    });

    expect(returnedTranscript).toBe("こんにちは");
  });

  it("should update interimTranscript for non-final results", () => {
    let capturedOnStart: (() => void) | null = null;
    let capturedOnResult: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;

      set onstart(fn: (() => void) | null) {
        capturedOnStart = fn;
      }

      get onstart() {
        return capturedOnStart;
      }

      set onresult(fn: ((event: unknown) => void) | null) {
        capturedOnResult = fn;
      }

      get onresult() {
        return capturedOnResult;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnStart?.();
    });

    act(() => {
      capturedOnResult?.({
        resultIndex: 0,
        results: {
          length: 1,
          0: {
            isFinal: false,
            0: { transcript: "こんに" },
          },
        },
      });
    });

    expect(result.current.interimTranscript).toBe("こんに");
  });

  it("should handle errors when not holding", () => {
    let capturedOnError: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onresult: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      onstart: (() => void) | null = null;

      set onerror(fn: ((event: unknown) => void) | null) {
        capturedOnError = fn;
      }

      get onerror() {
        return capturedOnError;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    // stopListening で isHolding を false にしてからエラーを発火
    act(() => {
      result.current.startListening();
      result.current.stopListening();
      capturedOnError?.({ error: "no-speech" });
    });

    expect(result.current.error).toBe("音声が検出されませんでした");
    expect(result.current.isListening).toBe(false);
  });

  it("should suppress no-speech error while holding button", () => {
    let capturedOnError: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onresult: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      onstart: (() => void) | null = null;

      set onerror(fn: ((event: unknown) => void) | null) {
        capturedOnError = fn;
      }

      get onerror() {
        return capturedOnError;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnError?.({ error: "no-speech" });
    });

    // isHolding 中は no-speech をエラー扱いしない
    expect(result.current.error).toBeNull();
  });

  it("should auto-restart recognition on onend while holding", () => {
    let capturedOnEnd: (() => void) | null = null;
    const mockStart = vi.fn();

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = mockStart;
      stop = vi.fn();
      abort = vi.fn();
      onresult: ((event: unknown) => void) | null = null;
      onerror: ((event: unknown) => void) | null = null;
      onstart: (() => void) | null = null;

      set onend(fn: (() => void) | null) {
        capturedOnEnd = fn;
      }

      get onend() {
        return capturedOnEnd;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
    });

    expect(mockStart).toHaveBeenCalledTimes(1);

    // ブラウザVADによる onend — holding 中なので自動再開
    act(() => {
      capturedOnEnd?.();
    });

    expect(mockStart).toHaveBeenCalledTimes(2);
    // isListening は false にならない（再開するため）
  });

  it("should include interim transcript in stopListening return value", () => {
    let capturedOnStart: (() => void) | null = null;
    let capturedOnResult: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;

      set onstart(fn: (() => void) | null) {
        capturedOnStart = fn;
      }

      get onstart() {
        return capturedOnStart;
      }

      set onresult(fn: ((event: unknown) => void) | null) {
        capturedOnResult = fn;
      }

      get onresult() {
        return capturedOnResult;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnStart?.();
    });

    // final + interim が混在する状態
    act(() => {
      capturedOnResult?.({
        resultIndex: 0,
        results: {
          length: 2,
          0: { isFinal: true, 0: { transcript: "こんにちは" } },
          1: { isFinal: false, 0: { transcript: "世界" } },
        },
      });
    });

    let returnedTranscript = "";
    act(() => {
      returnedTranscript = result.current.stopListening();
    });

    // final("こんにちは") + interim("世界") の両方が含まれる
    expect(returnedTranscript).toBe("こんにちは世界");
  });

  it("should reset transcript when resetTranscript is called", () => {
    let capturedOnStart: (() => void) | null = null;
    let capturedOnResult: ((event: unknown) => void) | null = null;

    class MockRecognition {
      continuous = false;
      interimResults = false;
      lang = "";
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;

      set onstart(fn: (() => void) | null) {
        capturedOnStart = fn;
      }

      get onstart() {
        return capturedOnStart;
      }

      set onresult(fn: ((event: unknown) => void) | null) {
        capturedOnResult = fn;
      }

      get onresult() {
        return capturedOnResult;
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockRecognition,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.startListening();
      capturedOnStart?.();
      capturedOnResult?.({
        resultIndex: 0,
        results: {
          length: 1,
          0: {
            isFinal: true,
            0: { transcript: "テスト" },
          },
        },
      });
    });

    expect(result.current.transcript).toBe("テスト");

    act(() => {
      result.current.resetTranscript();
    });

    expect(result.current.transcript).toBe("");
  });
});
