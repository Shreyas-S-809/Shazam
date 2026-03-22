from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


# ── Recognition ──────────────────────────────────────────────

class RecognitionResult(BaseModel):
    title: str = Field(..., example="Blinding Lights")
    artist: str = Field(..., example="The Weeknd")
    album: str = Field(default="Unknown", example="After Hours")


class RecognitionResponse(BaseModel):
    success: bool
    result: Optional[RecognitionResult] = None
    spectrogram_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded PNG spectrogram image",
    )
    waveform_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded PNG waveform image",
    )
    error: Optional[str] = None


# ── Links ────────────────────────────────────────────────────

class YouTubeLinkResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class SpotifyLinkResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    track_id: Optional[str] = None
    preview_url: Optional[str] = None
    album_art: Optional[str] = None
    error: Optional[str] = None


# ── Similar Songs ────────────────────────────────────────────

class SimilarSong(BaseModel):
    title: str
    artist: str
    similarity: float = Field(..., ge=0.0, le=1.0)


class SimilarSongsResponse(BaseModel):
    success: bool
    songs: List[SimilarSong] = Field(default_factory=list)
    error: Optional[str] = None


# ── Health ───────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
