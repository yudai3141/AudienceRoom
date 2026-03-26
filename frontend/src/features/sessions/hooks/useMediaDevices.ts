"use client";

import { useState, useEffect, useCallback, useRef } from "react";

type MediaDevicesState = {
  stream: MediaStream | null;
  videoEnabled: boolean;
  audioEnabled: boolean;
  permissionStatus: "prompt" | "granted" | "denied" | "error";
  error: string | null;
};

export function useMediaDevices() {
  const [state, setState] = useState<MediaDevicesState>({
    stream: null,
    videoEnabled: true,
    audioEnabled: true,
    permissionStatus: "prompt",
    error: null,
  });

  const streamRef = useRef<MediaStream | null>(null);

  const requestPermissions = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      streamRef.current = stream;

      setState({
        stream,
        videoEnabled: true,
        audioEnabled: true,
        permissionStatus: "granted",
        error: null,
      });

      return stream;
    } catch (err) {
      const error = err as Error;
      let permissionStatus: MediaDevicesState["permissionStatus"] = "error";
      let errorMessage = "メディアデバイスへのアクセスに失敗しました";

      if (error.name === "NotAllowedError") {
        permissionStatus = "denied";
        errorMessage = "カメラ・マイクへのアクセスが拒否されました";
      } else if (error.name === "NotFoundError") {
        errorMessage = "カメラまたはマイクが見つかりません";
      }

      setState((prev) => ({
        ...prev,
        permissionStatus,
        error: errorMessage,
      }));

      return null;
    }
  }, []);

  const toggleVideo = useCallback(() => {
    const stream = streamRef.current;
    if (!stream) return;

    setState((prev) => {
      const newEnabled = !prev.videoEnabled;
      const videoTracks = stream.getVideoTracks();
      videoTracks.forEach((track) => {
        track.enabled = newEnabled;
      });
      return { ...prev, videoEnabled: newEnabled };
    });
  }, []);

  const toggleAudio = useCallback(() => {
    const stream = streamRef.current;
    if (!stream) return;

    setState((prev) => {
      const newEnabled = !prev.audioEnabled;
      const audioTracks = stream.getAudioTracks();
      audioTracks.forEach((track) => {
        track.enabled = newEnabled;
      });
      return { ...prev, audioEnabled: newEnabled };
    });
  }, []);

  const stopStream = useCallback(() => {
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setState((prev) => ({
        ...prev,
        stream: null,
        permissionStatus: "prompt",
      }));
    }
  }, []);

  useEffect(() => {
    return () => {
      const stream = streamRef.current;
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return {
    ...state,
    requestPermissions,
    toggleVideo,
    toggleAudio,
    stopStream,
  };
}
