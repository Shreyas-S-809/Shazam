"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Music2, Waves } from "lucide-react";
import { toast } from "sonner";

import AudioRecorder from "@/components/AudioRecorder";
import WaveVisualizer from "@/components/WaveVisualizer";
import { recognizeSong } from "@/lib/api";

type AppState = "idle" | "recording" | "processing" | "uploading";

export default function HomePage() {
  const router = useRouter();
  const [state, setState] = useState<AppState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);

  const handleRecordingComplete = useCallback(
    async (blob: Blob) => {
      setAudioBlob(blob);
      setState("processing");
      toast.info("Analyzing audio...");

      try {
        const result = await recognizeSong(blob, "mic");
        if (!result.success && result.error) {
          toast.error(result.error);
          setState("idle");
          return;
        }
        sessionStorage.setItem("recognition_result", JSON.stringify(result));
        router.push("/result");
      } catch (err: unknown) {
        console.error("Recognition error:", err);
        const axiosErr = err as { response?: { data?: Record<string, string> }; message?: string };
        const msg =
          axiosErr?.response?.data?.detail ??
          axiosErr?.response?.data?.error ??
          axiosErr?.message ??
          "Audio unclear. Try increasing volume or recording longer.";
        toast.error(msg);
        setState("idle");
      }
    },
    [router]
  );

  const handleCancelRecording = useCallback(() => {
    setState("idle");
    setAudioBlob(null);
    setAudioStream(null);
  }, []);

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setState("uploading");
      toast.info("Uploading & analyzing...");

      try {
        const result = await recognizeSong(file);
        if (!result.success && result.error) {
          toast.error(result.error);
          setState("idle");
          return;
        }
        sessionStorage.setItem("recognition_result", JSON.stringify(result));
        router.push("/result");
      } catch (err: unknown) {
        console.error("Upload error:", err);
        const axiosErr = err as { response?: { data?: Record<string, string> }; message?: string };
        const msg =
          axiosErr?.response?.data?.detail ??
          axiosErr?.response?.data?.error ??
          axiosErr?.message ??
          "Failed to process audio file. Please try again.";
        toast.error(msg);
        setState("idle");
      } finally {
        // Reset file input so the same file can be re-uploaded
        e.target.value = "";
      }
    },
    [router]
  );

  const micDisabled = state === "uploading" || state === "processing";
  const uploadDisabled = state === "recording" || state === "processing" || state === "uploading";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12 bg-mesh">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-3 mb-3">
          <div className="w-11 h-11 rounded-2xl bg-brand-green/15 border border-brand-green/20 flex items-center justify-center">
            <Music2 className="w-5 h-5 text-brand-green" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight">
            Song<span className="text-brand-green">Shazam</span>
          </h1>
        </div>
        <p className="text-white/40 text-base max-w-xs mx-auto leading-relaxed">
          Play a song near your mic â€” we&apos;ll identify it instantly
        </p>
      </motion.div>

      {/* Wave Visualizer */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-full max-w-xl mb-10"
      >
        <WaveVisualizer isActive={state === "recording"} stream={audioStream} />
      </motion.div>

      {/* Main Action Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="flex flex-col items-center gap-6 w-full max-w-xs"
      >
        {/* Mic button â€” fades when upload is active */}
        <div
          className={`transition-all duration-400 ${
            micDisabled ? "opacity-25 pointer-events-none" : "opacity-100"
          }`}
        >
          <AudioRecorder
            isRecording={state === "recording"}
            onStart={() => setState("recording")}
            onStop={handleRecordingComplete}
            onCancel={handleCancelRecording}
            onStreamReady={setAudioStream}
          />
        </div>

        {/* State Label */}
        <AnimatePresence mode="wait">
          <motion.div
            key={state}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="h-6 flex items-center"
          >
            {state === "idle" && (
              <p className="text-white/30 text-xs font-medium tracking-wide">
                Tap the mic to start
              </p>
            )}
            {(state === "processing" || state === "uploading") && (
              <span className="text-brand-green flex items-center gap-2 text-xs font-medium">
                <Waves className="w-3.5 h-3.5 animate-pulse" />
                Identifying song...
              </span>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Divider */}
        <div className="flex items-center gap-3 w-full">
          <div className="flex-1 h-px bg-white/8" />
          <span className="text-white/20 text-xs uppercase tracking-widest">or</span>
          <div className="flex-1 h-px bg-white/8" />
        </div>

        {/* Upload button â€” fades when recording is active */}
        <label
          className={`w-full flex items-center justify-center gap-2.5 px-5 py-3 rounded-2xl border transition-all duration-400 ${
            uploadDisabled
              ? "opacity-25 pointer-events-none cursor-not-allowed border-white/5 bg-white/3"
              : "cursor-pointer border-white/10 bg-white/5 hover:bg-white/8 hover:border-white/20 active:scale-95"
          }`}
        >
          <Upload className="w-4 h-4 text-white/50" />
          <span className="text-white/60 text-sm font-medium">Upload audio file</span>
          <input
            type="file"
            accept="audio/*,.mp3,.wav,.m4a,.ogg,.webm,.flac,.aac,.wma"
            className="hidden"
            onChange={handleFileUpload}
            disabled={uploadDisabled}
          />
        </label>
      </motion.div>
    </div>
  );
}
