"use client";

import { motion } from "framer-motion";

interface SpectrogramProps {
  base64: string;
}

export default function Spectrogram({ base64 }: SpectrogramProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="relative overflow-hidden rounded-xl"
    >
      <img
        src={`data:image/png;base64,${base64}`}
        alt="Audio spectrogram visualization"
        className="w-full rounded-xl"
      />
      {/* Subtle gradient overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none rounded-xl" />
    </motion.div>
  );
}
