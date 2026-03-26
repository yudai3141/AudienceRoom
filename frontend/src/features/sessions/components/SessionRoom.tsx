"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useRouter } from "next/navigation";
import { Button, Card, Spinner } from "@/components/ui";
import { useMediaDevices } from "../hooks/useMediaDevices";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { useConversation, type Message } from "../hooks/useConversation";
import { useSessionDetail } from "../hooks/useSessionDetail";
import { useUpdateSessionStatus } from "../hooks/useUpdateSessionStatus";
import { useGenerateFeedback } from "../hooks/useGenerateFeedback";

type SessionRoomProps = {
  sessionId: number;
};

type ConversationPhase = "waiting" | "active" | "ending" | "ended";

type FeedbackSummary = {
  overallScore: number | null;
  summaryTitle: string;
  shortComment: string | null;
};

function VideoIcon({ enabled }: { enabled: boolean }) {
  if (enabled) {
    return (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
        />
      </svg>
    );
  }
  return (
    <svg
      className="h-6 w-6"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
      />
    </svg>
  );
}

function MicIcon({ enabled }: { enabled: boolean }) {
  if (enabled) {
    return (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        />
      </svg>
    );
  }
  return (
    <svg
      className="h-6 w-6"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
      />
    </svg>
  );
}

function PermissionRequest({
  onRequest,
  loading,
}: {
  onRequest: () => void;
  loading: boolean;
}) {
  return (
    <div className="flex flex-1 items-center justify-center">
      <Card className="max-w-md">
        <div className="p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100">
            <svg
              className="h-8 w-8 text-indigo-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-semibold text-slate-900">
            カメラとマイクを使用します
          </h2>
          <p className="mb-6 text-sm text-slate-500">
            練習を開始するには、カメラとマイクへのアクセスを許可してください。
          </p>
          <Button onClick={onRequest} loading={loading} className="w-full">
            アクセスを許可する
          </Button>
        </div>
      </Card>
    </div>
  );
}

function PermissionDenied() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <Card className="max-w-md">
        <div className="p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-semibold text-slate-900">
            アクセスが拒否されました
          </h2>
          <p className="mb-6 text-sm text-slate-500">
            カメラとマイクへのアクセスが拒否されました。
            ブラウザの設定からアクセスを許可してください。
          </p>
        </div>
      </Card>
    </div>
  );
}

function VideoPreview({
  stream,
  videoEnabled,
}: {
  stream: MediaStream;
  videoEnabled: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-slate-900">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`h-full w-full object-cover ${videoEnabled ? "" : "hidden"}`}
      />
      {!videoEnabled && (
        <div className="flex h-full w-full items-center justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-slate-700">
            <svg
              className="h-10 w-10 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
        </div>
      )}
      <div className="absolute bottom-2 left-2 rounded bg-black/50 px-2 py-1 text-xs text-white">
        あなた
      </div>
    </div>
  );
}

function ControlBar({
  videoEnabled,
  audioEnabled,
  isEnding,
  onToggleVideo,
  onToggleAudio,
  onLeave,
}: {
  videoEnabled: boolean;
  audioEnabled: boolean;
  isEnding: boolean;
  onToggleVideo: () => void;
  onToggleAudio: () => void;
  onLeave: () => void;
}) {
  return (
    <div className="flex items-center justify-center gap-4 rounded-lg bg-slate-800 px-6 py-4">
      <button
        onClick={onToggleAudio}
        disabled={isEnding}
        className={`flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
          audioEnabled
            ? "bg-slate-700 text-white hover:bg-slate-600"
            : "bg-red-500 text-white hover:bg-red-600"
        } ${isEnding ? "cursor-not-allowed opacity-50" : ""}`}
        title={audioEnabled ? "マイクをオフにする" : "マイクをオンにする"}
      >
        <MicIcon enabled={audioEnabled} />
      </button>

      <button
        onClick={onToggleVideo}
        disabled={isEnding}
        className={`flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
          videoEnabled
            ? "bg-slate-700 text-white hover:bg-slate-600"
            : "bg-red-500 text-white hover:bg-red-600"
        } ${isEnding ? "cursor-not-allowed opacity-50" : ""}`}
        title={videoEnabled ? "カメラをオフにする" : "カメラをオンにする"}
      >
        <VideoIcon enabled={videoEnabled} />
      </button>

      <button
        onClick={onLeave}
        disabled={isEnding}
        className={`flex h-12 items-center justify-center gap-2 rounded-full bg-red-500 px-4 text-white transition-colors hover:bg-red-600 ${
          isEnding ? "cursor-not-allowed opacity-50" : ""
        }`}
        title="退出する"
      >
        {isEnding ? (
          <>
            <Spinner size="sm" />
            <span className="text-sm">終了中...</span>
          </>
        ) : (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
        )}
      </button>
    </div>
  );
}

function ParticipantPlaceholder({
  name,
  isSpeaking,
}: {
  name: string;
  isSpeaking?: boolean;
}) {
  return (
    <div
      className={`relative aspect-video overflow-hidden rounded-lg bg-slate-800 ${isSpeaking ? "ring-2 ring-green-500" : ""}`}
    >
      <div className="flex h-full w-full items-center justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-700">
          <svg
            className="h-8 w-8 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      </div>
      <div className="absolute bottom-2 left-2 rounded bg-black/50 px-2 py-1 text-xs text-white">
        {name}
      </div>
      {isSpeaking && (
        <div className="absolute right-2 top-2 flex items-center gap-1 rounded bg-green-500 px-2 py-1 text-xs text-white">
          <span className="h-2 w-2 animate-pulse rounded-full bg-white" />
          発話中
        </div>
      )}
    </div>
  );
}

function ConversationLog({ messages }: { messages: Message[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        会話が開始されるのを待っています...
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="h-full space-y-3 overflow-y-auto p-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2 ${
              msg.role === "user"
                ? "bg-indigo-600 text-white"
                : "bg-slate-700 text-white"
            }`}
          >
            <p className="text-sm">{msg.content}</p>
            <p className="mt-1 text-xs opacity-70">
              {msg.timestamp.toLocaleTimeString("ja-JP", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function TranscriptDisplay({
  transcript,
  interimTranscript,
  isListening,
}: {
  transcript: string;
  interimTranscript: string;
  isListening: boolean;
}) {
  if (!isListening && !transcript && !interimTranscript) {
    return null;
  }

  return (
    <div className="rounded-lg bg-slate-800 px-4 py-3">
      <div className="flex items-center gap-2">
        {isListening && (
          <span className="h-3 w-3 animate-pulse rounded-full bg-red-500" />
        )}
        <span className="text-xs text-slate-400">
          {isListening ? "音声認識中..." : "認識完了"}
        </span>
      </div>
      <p className="mt-1 text-sm text-white">
        {transcript}
        <span className="text-slate-400">{interimTranscript}</span>
      </p>
    </div>
  );
}

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
      <Card className="mx-4 max-w-md">
        <div className="p-8 text-center">
          {phase === "ending" ? (
            <>
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center">
                <Spinner size="lg" />
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
              <Button onClick={onViewDetails} className="w-full">
                詳しい結果を見る
              </Button>
            </>
          ) : (
            <>
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <svg
                  className="h-8 w-8 text-green-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="mb-2 text-xl font-semibold text-slate-900">
                お疲れ様でした！
              </h2>
              <p className="mb-6 text-sm text-slate-500">
                練習が完了しました
              </p>
              <Button onClick={onViewDetails} className="w-full">
                結果を見る
              </Button>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}

function getModeLabel(mode: string): string {
  switch (mode) {
    case "interview":
      return "面接練習";
    case "presentation":
      return "プレゼン練習";
    default:
      return mode;
  }
}

function getRoleLabel(mode: string): string {
  switch (mode) {
    case "interview":
      return "面接官";
    case "presentation":
      return "聴衆";
    default:
      return "参加者";
  }
}

function SessionInfo({
  mode,
  theme,
  participantCount,
}: {
  mode: string;
  theme: string | null;
  participantCount: number;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg bg-slate-800 px-4 py-2 text-sm text-white">
      <span className="rounded bg-indigo-600 px-2 py-1 text-xs font-medium">
        {getModeLabel(mode)}
      </span>
      {theme && (
        <span className="truncate text-slate-300" title={theme}>
          {theme}
        </span>
      )}
      <span className="text-slate-400">
        {getRoleLabel(mode)} {participantCount}人
      </span>
    </div>
  );
}

export function SessionRoom({ sessionId }: SessionRoomProps) {
  const router = useRouter();
  const [requestingPermission, setRequestingPermission] = useState(false);
  const [phase, setPhase] = useState<ConversationPhase>("waiting");
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary | null>(
    null,
  );
  const conversationStartedRef = useRef(false);

  const {
    data: sessionDetail,
    isLoading: sessionLoading,
  } = useSessionDetail(sessionId);

  const updateStatus = useUpdateSessionStatus();
  const generateFeedback = useGenerateFeedback();

  const {
    stream,
    videoEnabled,
    audioEnabled,
    permissionStatus,
    error: mediaError,
    requestPermissions,
    toggleVideo,
    toggleAudio,
    stopStream,
  } = useMediaDevices();

  const {
    messages,
    isProcessing,
    isSpeaking,
    error: conversationError,
    sendMessage,
    startConversation,
    stopAudio,
  } = useConversation({
    sessionId,
    generateAudio: true,
  });

  const handleSpeechResult = useCallback(
    (transcript: string) => {
      if (phase === "active" && !isProcessing && !isSpeaking) {
        sendMessage(transcript);
      }
    },
    [phase, isProcessing, isSpeaking, sendMessage],
  );

  const handleSpeechEnd = useCallback(() => {
    // 無音検知後の処理（必要に応じて）
  }, []);

  const {
    isListening,
    isSupported: isSpeechSupported,
    transcript,
    interimTranscript,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition({
    language: "ja-JP",
    continuous: false,
    onResult: handleSpeechResult,
    onEnd: handleSpeechEnd,
  });

  const handleRequestPermissions = async () => {
    setRequestingPermission(true);
    await requestPermissions();
    setRequestingPermission(false);
  };

  const handleStartConversation = useCallback(async () => {
    if (conversationStartedRef.current) return;
    conversationStartedRef.current = true;
    setPhase("active");
    await startConversation();
  }, [startConversation]);

  const handleStartSpeaking = useCallback(() => {
    if (!isProcessing && !isSpeaking && phase === "active") {
      resetTranscript();
      startListening();
    }
  }, [isProcessing, isSpeaking, phase, resetTranscript, startListening]);

  const handleStopSpeaking = useCallback(() => {
    stopListening();
  }, [stopListening]);

  const handleLeave = useCallback(async () => {
    if (phase === "ending" || phase === "ended") return;
    
    flushSync(() => {
      setPhase("ending");
    });

    stopStream();
    stopAudio();
    stopListening();

    try {
      await updateStatus.mutateAsync({
        sessionId,
        status: "completed",
      });

      if (sessionDetail?.feedback_enabled) {
        const result = await generateFeedback.mutateAsync(sessionId);
        setFeedbackSummary({
          overallScore: result.overall_score,
          summaryTitle: result.summary_title,
          shortComment: result.short_comment,
        });
      }
    } catch {
      // エラーが発生しても終了画面を表示
    }

    setPhase("ended");
  }, [
    phase,
    stopStream,
    stopAudio,
    stopListening,
    updateStatus,
    generateFeedback,
    sessionId,
    sessionDetail,
  ]);

  const handleViewDetails = useCallback(() => {
    router.push(`/sessions/${sessionId}/result`);
  }, [router, sessionId]);

  useEffect(() => {
    if (stream && phase === "waiting" && !conversationStartedRef.current) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- AI会話開始は外部システムとの同期
      handleStartConversation();
    }
  }, [stream, phase, handleStartConversation]);

  const error = mediaError || conversationError || speechError;
  const isEndingOrEnded = phase === "ending" || phase === "ended";

  if (isEndingOrEnded) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-900">
        <FeedbackOverlay
          phase={phase}
          feedback={feedbackSummary}
          onViewDetails={handleViewDetails}
        />
      </div>
    );
  }

  if (sessionLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (permissionStatus === "prompt") {
    return (
      <PermissionRequest
        onRequest={handleRequestPermissions}
        loading={requestingPermission}
      />
    );
  }

  if (permissionStatus === "denied" || permissionStatus === "error") {
    return <PermissionDenied />;
  }

  if (!stream) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  const participants = sessionDetail?.participants ?? [];
  const participantCount = sessionDetail?.participant_count ?? 1;
  const roleLabel = sessionDetail ? getRoleLabel(sessionDetail.mode) : "参加者";

  const displayParticipantCount =
    participants.length > 0 ? participants.length : participantCount;

  const participantElements =
    participants.length > 0
      ? participants.map((participant, index) => (
          <ParticipantPlaceholder
            key={participant.id}
            name={participant.display_name}
            isSpeaking={isSpeaking && index === 0}
          />
        ))
      : Array.from({ length: participantCount }, (_, index) => (
          <ParticipantPlaceholder
            key={`placeholder-${index}`}
            name={`${roleLabel}${participantCount > 1 ? ` ${index + 1}` : ""}`}
            isSpeaking={isSpeaking && index === 0}
          />
        ));

  return (
    <div className="relative flex h-full flex-col">
      {sessionDetail && (
        <div className="px-4 pt-4">
          <SessionInfo
            mode={sessionDetail.mode}
            theme={sessionDetail.theme}
            participantCount={sessionDetail.participant_count}
          />
        </div>
      )}

      <div className="flex flex-1 gap-4 p-4">
        <div className="flex flex-1 flex-col gap-4">
          {displayParticipantCount === 1 ? (
            <div className="grid flex-1 gap-4 md:grid-cols-2">
              <VideoPreview stream={stream} videoEnabled={videoEnabled} />
              {participantElements}
            </div>
          ) : (
            <div className="grid flex-1 grid-cols-2 gap-4">
              <VideoPreview stream={stream} videoEnabled={videoEnabled} />
              {participantElements}
            </div>
          )}

          <TranscriptDisplay
            transcript={transcript}
            interimTranscript={interimTranscript}
            isListening={isListening}
          />
        </div>

        <div className="hidden w-80 flex-col rounded-lg bg-slate-900 lg:flex">
          <div className="border-b border-slate-700 px-4 py-3">
            <h3 className="text-sm font-medium text-white">会話ログ</h3>
          </div>
          <div className="flex-1 overflow-hidden">
            <ConversationLog messages={messages} />
          </div>
        </div>
      </div>

      {error && (
        <div className="mx-4 mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!isSpeechSupported && (
        <div className="mx-4 mb-4 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-700">
          お使いのブラウザは音声認識をサポートしていません。Chrome
          の使用をお勧めします。
        </div>
      )}

      <div className="flex items-center justify-center gap-4 pb-6">
        <ControlBar
          videoEnabled={videoEnabled}
          audioEnabled={audioEnabled}
          isEnding={false}
          onToggleVideo={toggleVideo}
          onToggleAudio={toggleAudio}
          onLeave={handleLeave}
        />

        {isSpeechSupported && phase === "active" && (
          <button
            onMouseDown={handleStartSpeaking}
            onMouseUp={handleStopSpeaking}
            onTouchStart={handleStartSpeaking}
            onTouchEnd={handleStopSpeaking}
            disabled={isProcessing || isSpeaking}
            className={`flex h-14 items-center gap-2 rounded-full px-6 text-white transition-colors ${
              isListening
                ? "bg-red-500"
                : isProcessing || isSpeaking
                  ? "cursor-not-allowed bg-slate-600"
                  : "bg-green-600 hover:bg-green-700"
            }`}
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
            <span className="text-sm font-medium">
              {isListening
                ? "話しています..."
                : isProcessing
                  ? "処理中..."
                  : isSpeaking
                    ? "AI応答中..."
                    : "押して話す"}
            </span>
          </button>
        )}
      </div>
    </div>
  );
}
