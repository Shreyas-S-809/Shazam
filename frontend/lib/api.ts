import axios from "axios";

// In dev, Next.js rewrites /api/* → http://localhost:8000/api/* (see next.config.mjs).
// This means we use relative URLs ("") so all requests go through the same origin,
// completely avoiding CORS issues between the browser and the FastAPI backend.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s — audio processing can be slow
});

// ── Recognition ─────────────────────────────────────────

export interface RecognitionResult {
  success: boolean;
  result?: {
    title: string;
    artist: string;
    album: string;
  };
  spectrogram_base64?: string;
  waveform_base64?: string;
  error?: string;
}

export async function recognizeSong(
  audioFile: Blob | File,
  source: "mic" | "upload" = "upload"
): Promise<RecognitionResult> {
  const formData = new FormData();
  // Preserve the real filename/extension so the backend saves with the correct suffix.
  // IMPORTANT: do NOT set Content-Type manually — axios auto-sets
  // 'multipart/form-data; boundary=...' for FormData. Overriding it drops the
  // boundary and causes FastAPI to return 400 "Missing boundary in multipart."
  const filename =
    audioFile instanceof File ? audioFile.name : "recording.webm";
  formData.append("file", audioFile, filename);

  const { data } = await api.post<RecognitionResult>(
    `/api/audio/recognize?source=${encodeURIComponent(source)}`,
    formData
    // No Content-Type override — axios handles it correctly with FormData
  );
  return data;
}

// ── YouTube ─────────────────────────────────────────────

export interface YouTubeLinkResult {
  success: boolean;
  url?: string;
  error?: string;
}

export async function getYouTubeLink(
  song: string,
  artist: string
): Promise<YouTubeLinkResult> {
  const { data } = await api.get<YouTubeLinkResult>("/api/links/youtube", {
    params: { song, artist },
  });
  return data;
}

// ── Spotify ─────────────────────────────────────────────

export interface SpotifyLinkResult {
  success: boolean;
  url?: string;
  track_id?: string;
  preview_url?: string;
  album_art?: string;
  error?: string;
}

export async function getSpotifyLink(
  song: string,
  artist: string
): Promise<SpotifyLinkResult> {
  const { data } = await api.get<SpotifyLinkResult>("/api/links/spotify", {
    params: { song, artist },
  });
  return data;
}

// ── Similar Songs ───────────────────────────────────────

export interface SimilarSong {
  title: string;
  artist: string;
  similarity: number;
}

export interface SimilarSongsResult {
  success: boolean;
  songs: SimilarSong[];
  error?: string;
}

export async function getSimilarSongs(
  song: string,
  artist: string
): Promise<SimilarSongsResult> {
  const { data } = await api.get<SimilarSongsResult>("/api/audio/similar", {
    params: { song, artist },
  });
  return data;
}
