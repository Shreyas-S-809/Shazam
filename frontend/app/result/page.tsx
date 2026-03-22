"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Music2, ExternalLink, Mic, Search } from "lucide-react";
import { toast } from "sonner";

import SongCard from "@/components/SongCard";
import Spectrogram from "@/components/Spectrogram";
import YouTubeSpotifyEmbed from "@/components/YouTubeSpotifyEmbed";
import { getYouTubeLink, getSpotifyLink, getSimilarSongs } from "@/lib/api";

interface RecognitionData {
  success: boolean;
  result?: { title: string; artist: string; album: string };
  spectrogram_base64?: string;
  waveform_base64?: string;
  error?: string;
}

interface SimilarSong {
  title: string;
  artist: string;
  similarity: number;
}

type Tab = "overview" | "lyrics" | "similar";

export default function ResultPage() {
  const router = useRouter();
  const [data, setData] = useState<RecognitionData | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState<string | null>(null);
  const [spotifyUrl, setSpotifyUrl] = useState<string | null>(null);
  const [albumArt, setAlbumArt] = useState<string | null>(null);
  const [similarSongs, setSimilarSongs] = useState<SimilarSong[]>([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarError, setSimilarError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("recognition_result");
    if (!stored) {
      // Hard redirect — router.push can stall on cold navigations
      window.location.replace("/");
      return;
    }

    const parsed: RecognitionData = JSON.parse(stored);
    setData(parsed);

    if (parsed.success && parsed.result) {
      const { title, artist } = parsed.result;

      getYouTubeLink(title, artist).then((res) => {
        if (res.success && res.url) setYoutubeUrl(res.url);
      });

      getSpotifyLink(title, artist).then((res) => {
        if (res.success) {
          if (res.url) setSpotifyUrl(res.url);
          if (res.album_art) setAlbumArt(res.album_art);
        }
      });

      setSimilarLoading(true);
      getSimilarSongs(title, artist)
        .then((res) => {
          if (res.success && res.songs && res.songs.length > 0) {
            setSimilarSongs(res.songs);
          } else {
            setSimilarError(res.error || "No similar songs found.");
          }
        })
        .catch(() => setSimilarError("Could not load recommendations."))
        .finally(() => setSimilarLoading(false));
    }
  }, [router]);

  const handleSaveToPlaylist = () => {
    if (!data?.result) return;
    const existing = JSON.parse(localStorage.getItem("playlist") || "[]");
    const entry = { ...data.result, savedAt: new Date().toISOString() };
    const isDuplicate = existing.some(
      (s: { title: string; artist: string }) =>
        s.title === entry.title && s.artist === entry.artist
    );
    if (!isDuplicate) {
      existing.push(entry);
      localStorage.setItem("playlist", JSON.stringify(existing));
    }
    setSaved(true);
    toast.success("Added to your playlist!");
  };

  // Share opens YouTube link directly
  const handleShare = () => {
    if (youtubeUrl) {
      window.open(youtubeUrl, "_blank", "noopener noreferrer");
    } else {
      toast.info("YouTube link not available yet.");
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="wave-bar" />
        ))}
      </div>
    );
  }

  if (!data.success || !data.result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 gap-6 bg-mesh">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="glass-card text-center max-w-md"
        >
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <Music2 className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Song Not Recognized</h2>
          <p className="text-white/50 mb-6">
            {data.error || "We couldn't identify that audio. Try again with a clearer recording."}
          </p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-2.5 bg-brand-green text-black font-semibold rounded-xl hover:bg-brand-green-light transition-colors"
          >
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  const { title, artist, album } = data.result;

  return (
    <div className="min-h-screen pb-24 bg-mesh">
      <div className="max-w-5xl mx-auto py-8 px-4">
        {/* Top Bar — back only */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center mb-8"
        >
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 text-white/40 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">New Search</span>
          </button>
        </motion.div>

        {/* Song Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <SongCard
            title={title}
            artist={artist}
            album={album}
            albumArt={albumArt}
            youtubeUrl={youtubeUrl}
            onShare={handleShare}
            onSave={handleSaveToPlaylist}
            saved={saved}
          />
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8"
        >
          <div className="flex gap-1 p-1 bg-white/5 border border-white/8 rounded-2xl w-fit mb-6">
            {(["overview", "lyrics", "similar"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2 rounded-xl text-sm font-semibold transition-all capitalize ${
                  activeTab === tab
                    ? "bg-brand-green text-black"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                {tab === "similar" && similarLoading
                  ? "Similar…"
                  : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Overview */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {data.spectrogram_base64 && (
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass-card">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-4">Audio Spectrogram</h3>
                  <Spectrogram base64={data.spectrogram_base64} />
                </motion.div>
              )}
              {data.waveform_base64 && (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass-card">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-4">Waveform</h3>
                  <img src={`data:image/png;base64,${data.waveform_base64}`} alt="waveform" className="w-full rounded-xl" />
                </motion.div>
              )}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="lg:col-span-2"
              >
                <YouTubeSpotifyEmbed youtubeUrl={youtubeUrl} spotifyUrl={spotifyUrl} />
              </motion.div>
            </div>
          )}

          {/* Lyrics */}
          {activeTab === "lyrics" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card max-w-2xl">
              <div className="flex items-center gap-3 mb-5">
                <Search className="w-5 h-5 text-brand-green" />
                <h3 className="text-lg font-semibold">Lyrics</h3>
              </div>
              <p className="text-white/40 text-sm mb-4">
                Search for lyrics of &quot;{title}&quot; by {artist}:
              </p>
              <div className="flex flex-wrap gap-2">
                {[
                  { label: "Genius", href: `https://genius.com/search?q=${encodeURIComponent(`${title} ${artist}`)}` },
                  { label: "AZLyrics", href: `https://www.azlyrics.com/lyrics/${artist.toLowerCase().replace(/\s+/g, "")}/${title.toLowerCase().replace(/\s+/g, "")}.html` },
                  { label: "Google", href: `https://www.google.com/search?q=${encodeURIComponent(`${title} ${artist} lyrics`)}` },
                ].map(({ label, href }) => (
                  <a key={label} href={href} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/8 rounded-xl transition-all text-sm font-medium">
                    {label} <ExternalLink className="w-3 h-3 text-white/30" />
                  </a>
                ))}
              </div>
            </motion.div>
          )}

          {/* Similar Songs */}
          {activeTab === "similar" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3 max-w-2xl">
              <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                <Music2 className="w-5 h-5 text-brand-green" />
                Similar Songs
              </h3>

              {similarLoading && (
                <div className="glass-card py-10 flex flex-col items-center gap-3">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-brand-green animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                  <p className="text-white/35 text-sm">Finding similar songs…</p>
                </div>
              )}

              {!similarLoading && similarError && (
                <div className="glass-card py-8 text-center">
                  <p className="text-white/35 text-sm">{similarError}</p>
                </div>
              )}

              {!similarLoading && !similarError && similarSongs.map((song, i) => (
                <motion.div
                  key={`${song.title}-${song.artist}-${i}`}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="flex items-center justify-between px-4 py-3.5 rounded-2xl bg-white/3 border border-white/7 hover:bg-white/5 hover:border-white/12 transition-all"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <span className="text-white/20 text-xs font-mono w-5 flex-shrink-0">
                      {(i + 1).toString().padStart(2, "0")}
                    </span>
                    <div className="min-w-0">
                      <p className="font-semibold text-sm truncate">{song.title}</p>
                      <p className="text-white/40 text-xs truncate">{song.artist}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5 flex-shrink-0 ml-3">
                    <div className="w-16 h-1 rounded-full bg-white/8 overflow-hidden">
                      <div
                        className="h-full bg-brand-green rounded-full"
                        style={{ width: `${Math.round(song.similarity * 100)}%` }}
                      />
                    </div>
                    <span className="text-brand-green text-xs font-bold w-9 text-right">
                      {Math.round(song.similarity * 100)}%
                    </span>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Bottom status strip */}
      <div className="fixed bottom-0 inset-x-0 bg-black/85 backdrop-blur-md border-t border-white/5 px-5 py-3 flex items-center gap-4">
        <div className="w-8 h-8 rounded-full bg-brand-green flex items-center justify-center flex-shrink-0">
          <Mic className="w-3.5 h-3.5 text-black" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold text-white leading-tight">Fingerprint Matched</p>
          <p className="text-[10px] font-mono uppercase tracking-[0.18em] text-white/30 truncate">
            Acoustic Analysis Complete · ACRCloud
          </p>
        </div>
      </div>
    </div>
  );
}








