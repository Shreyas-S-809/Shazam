"""Pydantic v2 schemas for Song Shazam Pro API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Recognition ──────────────────────────────────────────────

class RecognitionResult(BaseModel):
    title: str = Field(..., examples=["Blinding Lights"])
    artist: str = Field(..., examples=["The Weeknd"])
    album: str = Field(default="Unknown", examples=["After Hours"])


class RecognitionResponse(BaseModel):
    success: bool
    result: RecognitionResult | None = None
    spectrogram_base64: str | None = Field(
        default=None,
        description="Base64-encoded PNG spectrogram image",
    )
    waveform_base64: str | None = Field(
        default=None,
        description="Base64-encoded PNG waveform image",
    )
    error: str | None = None


# ── Links ────────────────────────────────────────────────────

class YouTubeLinkResponse(BaseModel):
    success: bool
    url: str | None = None
    error: str | None = None


class SpotifyLinkResponse(BaseModel):
    success: bool
    url: str | None = None
    track_id: str | None = None
    preview_url: str | None = None
    album_art: str | None = None
    error: str | None = None


# ── Similar Songs ────────────────────────────────────────────

class SimilarSong(BaseModel):
    title: str
    artist: str
    similarity: float = Field(..., ge=0.0, le=1.0)


class SimilarSongsResponse(BaseModel):
    success: bool
    songs: list[SimilarSong] = []
    error: str | None = None


# ── Health ───────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
