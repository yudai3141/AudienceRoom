"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Spinner } from "@/components/ui";
import { useMediaDevices } from "../hooks/useMediaDevices";

type SessionRoomProps = {
  sessionId: number;
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
      {videoEnabled ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="h-full w-full object-cover"
        />
      ) : (
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
  onToggleVideo,
  onToggleAudio,
  onLeave,
}: {
  videoEnabled: boolean;
  audioEnabled: boolean;
  onToggleVideo: () => void;
  onToggleAudio: () => void;
  onLeave: () => void;
}) {
  return (
    <div className="flex items-center justify-center gap-4 rounded-lg bg-slate-800 px-6 py-4">
      <button
        onClick={onToggleAudio}
        className={`flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
          audioEnabled
            ? "bg-slate-700 text-white hover:bg-slate-600"
            : "bg-red-500 text-white hover:bg-red-600"
        }`}
        title={audioEnabled ? "マイクをオフにする" : "マイクをオンにする"}
      >
        <MicIcon enabled={audioEnabled} />
      </button>

      <button
        onClick={onToggleVideo}
        className={`flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
          videoEnabled
            ? "bg-slate-700 text-white hover:bg-slate-600"
            : "bg-red-500 text-white hover:bg-red-600"
        }`}
        title={videoEnabled ? "カメラをオフにする" : "カメラをオンにする"}
      >
        <VideoIcon enabled={videoEnabled} />
      </button>

      <button
        onClick={onLeave}
        className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500 text-white transition-colors hover:bg-red-600"
        title="退出する"
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
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
          />
        </svg>
      </button>
    </div>
  );
}

function ParticipantPlaceholder({ name }: { name: string }) {
  return (
    <div className="relative aspect-video overflow-hidden rounded-lg bg-slate-800">
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
    </div>
  );
}

export function SessionRoom({ sessionId: _sessionId }: SessionRoomProps) {
  const router = useRouter();
  const [requestingPermission, setRequestingPermission] = useState(false);

  const {
    stream,
    videoEnabled,
    audioEnabled,
    permissionStatus,
    error,
    requestPermissions,
    toggleVideo,
    toggleAudio,
    stopStream,
  } = useMediaDevices();

  const handleRequestPermissions = async () => {
    setRequestingPermission(true);
    await requestPermissions();
    setRequestingPermission(false);
  };

  const handleLeave = () => {
    stopStream();
    router.push("/sessions");
  };

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

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 p-4">
        <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-2 lg:grid-cols-3">
          <VideoPreview stream={stream} videoEnabled={videoEnabled} />
          <ParticipantPlaceholder name="面接官 A" />
          <ParticipantPlaceholder name="面接官 B" />
        </div>

        {error && (
          <div className="mx-auto mt-4 max-w-md rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
      </div>

      <div className="flex justify-center pb-6">
        <ControlBar
          videoEnabled={videoEnabled}
          audioEnabled={audioEnabled}
          onToggleVideo={toggleVideo}
          onToggleAudio={toggleAudio}
          onLeave={handleLeave}
        />
      </div>
    </div>
  );
}
