"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import { Mic, Square, X } from "lucide-react";

const RECOMMENDED_SECS = 10;

interface AudioRecorderProps {
  isRecording: boolean;
  onStart: () => void;
  onStop: (blob: Blob) => void;
  onCancel?: () => void;
  onStreamReady?: (stream: MediaStream | null) => void;
}

export default function AudioRecorder({
  isRecording,
  onStart,
  onStop,
  onCancel,
  onStreamReady,
}: AudioRecorderProps) {
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const analyser = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationId = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cancelledRef = useRef(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);

  const drawWaveform = useCallback(() => {
    if (!analyser.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const bufferLength = analyser.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationId.current = requestAnimationFrame(draw);
      analyser.current!.getByteFrequencyData(dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barCount = 60;
      const barWidth = canvas.width / barCount - 2;
      const centerY = canvas.height / 2;
      for (let i = 0; i < barCount; i++) {
        const dataIndex = Math.floor((i / barCount) * bufferLength);
        const value = dataArray[dataIndex] / 255;
        const barHeight = value * centerY * 0.9;
        const gradient = ctx.createLinearGradient(0, centerY - barHeight, 0, centerY + barHeight);
        gradient.addColorStop(0, "rgba(29, 185, 84, 0.8)");
        gradient.addColorStop(0.5, "rgba(30, 215, 96, 1)");
        gradient.addColorStop(1, "rgba(29, 185, 84, 0.8)");
        ctx.fillStyle = gradient;
        const x = i * (barWidth + 2);
        ctx.fillRect(x, centerY - barHeight, barWidth, barHeight);
        ctx.fillRect(x, centerY, barWidth, barHeight);
      }
    };
    draw();
  }, []);

  const cleanupTimers = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    cancelAnimationFrame(animationId.current);
  }, []);

  const stopRecording = useCallback(() => {
    cleanupTimers();
    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.stop();
    }
  }, [cleanupTimers]);

  const cancelRecording = useCallback(() => {
    cancelledRef.current = true;
    cleanupTimers();
    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.stop();
    }
  }, [cleanupTimers]);

  const startRecording = useCallback(async () => {
    cancelledRef.current = false;
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 44100 },
      });

      setStream(audioStream);
      onStreamReady?.(audioStream);

      const audioCtx = new AudioContext();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(audioStream);
      const analyserNode = audioCtx.createAnalyser();
      analyserNode.fftSize = 256;
      source.connect(analyserNode);
      analyser.current = analyserNode;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(audioStream, { mimeType, audioBitsPerSecond: 128000 });
      chunks.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.current.push(e.data); };

      recorder.onstop = () => {
        cleanupTimers();
        setRecordingSeconds(0);
        audioStream.getTracks().forEach((t) => t.stop());
        audioCtxRef.current?.close().catch(() => {});
        audioCtxRef.current = null;
        setStream(null);
        onStreamReady?.(null);

        if (!cancelledRef.current) {
          const blob = new Blob(chunks.current, { type: "audio/webm" });
          onStop(blob);
        } else {
          cancelledRef.current = false;
          onCancel?.();
        }
      };

      mediaRecorder.current = recorder;
      recorder.start();
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds((p) => p + 1), 1000);
      onStart();
      drawWaveform();
    } catch {
      // mic denied
    }
  }, [onStart, onStop, onCancel, onStreamReady, drawWaveform, stopRecording, cleanupTimers]);

  // Cleanup only on unmount — do NOT put timerRef-clearing logic in a
  // stream-dependent effect, or it will fire immediately when stream is set
  // and kill the interval before it ticks.
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      cancelAnimationFrame(animationId.current);
      stream?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close().catch(() => {});
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mm = String(Math.floor(recordingSeconds / 60)).padStart(2, "0");
  const ss = String(recordingSeconds % 60).padStart(2, "0");

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Hint */}
      {!isRecording && (
        <p className="text-xs text-white/30 text-center">
          Recommended: hold for {RECOMMENDED_SECS}s
        </p>
      )}

      {/* Live waveform canvas */}
      {isRecording && (
        <canvas
          ref={canvasRef}
          width={480}
          height={80}
          className="w-full max-w-xs rounded-xl opacity-80"
        />
      )}

      {/* Prominent timer */}
      {isRecording && (
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-2xl font-mono font-bold tabular-nums tracking-widest text-white">
            {mm}:{ss}
          </span>
        </div>
      )}

      {/* Record / stop button + Cancel (side-by-side) */}
      <div className="flex items-center gap-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
            isRecording
              ? "bg-red-600 recording-pulse scale-110"
              : "bg-brand-green glow-green hover:scale-105 active:scale-95"
          }`}
        >
          <div
            className={`absolute inset-0 rounded-full border-2 transition-colors ${
              isRecording ? "border-red-400/40" : "border-brand-green/30"
            }`}
            style={{ transform: "scale(1.3)" }}
          />
          {isRecording ? (
            <Square className="w-7 h-7 text-white fill-white" />
          ) : (
            <Mic className="w-8 h-8 text-black" />
          )}
        </button>

        {/* Cancel */}
        {isRecording && (
          <button
            onClick={cancelRecording}
            className="flex items-center gap-1.5 text-white/35 hover:text-white/70 text-xs font-medium transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
          >
            <X className="w-3.5 h-3.5" />
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
