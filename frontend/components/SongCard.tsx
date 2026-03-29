"use client";

import { motion } from "framer-motion";
import { Disc3, Share2, ListPlus, Heart, Play } from "lucide-react";
import Image from "next/image";

interface SongCardProps {
  title: string;
  artist: string;
  album: string;
  albumArt?: string | null;
  youtubeUrl?: string | null;
  onShare?: () => void;
  onSave?: () => void;
  saved?: boolean;
}

export default function SongCard({
  title,
  artist,
  album,
  albumArt,
  youtubeUrl,
  onShare,
  onSave,
  saved,
}: SongCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="w-full rounded-3xl overflow-hidden border border-white/8 bg-[#0d0d0d]"
      style={{ boxShadow: "0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04)" }}
    >
      <div className="flex flex-col sm:flex-row">
        {/* â”€â”€ Album Art â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <div className="relative w-full sm:w-52 h-52 flex-shrink-0 bg-[#111]">
          {albumArt ? (
            <Image
              src={albumArt}
              alt={`${album} cover`}
              fill
              className="object-cover"
              sizes="208px"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Disc3
                className="w-20 h-20 text-white/10 animate-spin"
                style={{ animationDuration: "10s" }}
              />
            </div>
          )}
          {/* Vignette */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[#0d0d0d]/60 hidden sm:block" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/30 sm:hidden" />

          {/* HD AUDIO badge */}
          <span className="absolute bottom-3 left-3 text-[10px] font-black uppercase tracking-widest bg-brand-green text-black px-2.5 py-1 rounded-full">
            HD AUDIO
          </span>
        </div>

        {/* â”€â”€ Song Info â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <div className="flex flex-col justify-between flex-1 p-5 sm:p-6 gap-4 min-w-0">
          {/* Labels + title */}
          <div className="min-w-0">
            <p className="text-[11px] font-black uppercase tracking-[0.25em] text-brand-green mb-2">
              Now Identified
            </p>
            <h2 className="text-2xl sm:text-3xl font-black leading-tight truncate mb-1 text-white">
              {title}
            </h2>
            <p className="text-white/50 text-sm truncate">{artist}</p>
            {album && album !== "Unknown" && (
              <p className="text-white/25 text-xs truncate mt-0.5">{album}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2.5">
            {/* Primary CTA */}
            {youtubeUrl ? (
              <a
                href={youtubeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 bg-brand-green hover:bg-brand-green-light text-black font-bold text-sm rounded-2xl transition-colors active:scale-95"
              >
                <Play className="w-4 h-4 fill-black" />
                Watch on YouTube
              </a>
            ) : (
              <div className="w-full py-3 bg-white/5 border border-white/8 text-white/30 text-sm rounded-2xl text-center">
                YouTube link loading...
              </div>
            )}

            {/* Secondary actions */}
            <div className="flex gap-2">
              <button
                onClick={onShare}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-2xl text-sm font-medium text-white/70 hover:text-white transition-all"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <button
                onClick={onSave}
                disabled={saved}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 border rounded-2xl text-sm font-medium transition-all ${
                  saved
                    ? "bg-brand-green/10 border-brand-green/30 text-brand-green"
                    : "bg-white/5 hover:bg-white/10 border-white/10 hover:border-white/20 text-white/70 hover:text-white"
                }`}
              >
                {saved ? (
                  <Heart className="w-4 h-4 fill-brand-green text-brand-green" />
                ) : (
                  <ListPlus className="w-4 h-4" />
                )}
                {saved ? "Saved" : "+ Playlist"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
