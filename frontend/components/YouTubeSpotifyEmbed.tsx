"use client";

import { motion } from "framer-motion";

interface YouTubeSpotifyEmbedProps {
  youtubeUrl?: string | null;
  spotifyUrl?: string | null;
}

function extractYouTubeId(url: string): string | null {
  const match = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/
  );
  return match?.[1] ?? null;
}

function extractSpotifyTrackId(url: string): string | null {
  const match = url.match(/spotify\.com\/track\/([a-zA-Z0-9]+)/);
  return match?.[1] ?? null;
}

export default function YouTubeSpotifyEmbed({
  youtubeUrl,
  spotifyUrl,
}: YouTubeSpotifyEmbedProps) {
  const ytId = youtubeUrl ? extractYouTubeId(youtubeUrl) : null;
  const spotifyTrackId = spotifyUrl ? extractSpotifyTrackId(spotifyUrl) : null;

  if (!ytId && !spotifyTrackId) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* YouTube Embed */}
      {ytId && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card"
        >
          <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wider">
            Music Video
          </h3>
          <div className="relative w-full aspect-video rounded-xl overflow-hidden">
            <iframe
              src={`https://www.youtube.com/embed/${ytId}?rel=0&modestbranding=1`}
              title="YouTube music video"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              className="absolute inset-0 w-full h-full"
            />
          </div>
        </motion.div>
      )}

      {/* Spotify Embed */}
      {spotifyTrackId && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card"
        >
          <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wider">
            Listen on Spotify
          </h3>
          <div className="rounded-xl overflow-hidden">
            <iframe
              src={`https://open.spotify.com/embed/track/${spotifyTrackId}?theme=0`}
              title="Spotify player"
              allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
              loading="lazy"
              className="w-full h-[352px] rounded-xl"
            />
          </div>
        </motion.div>
      )}
    </div>
  );
}
