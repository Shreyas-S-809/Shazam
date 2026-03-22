"""Audio router — recognition, spectrogram, waveform, and similar songs."""

from __future__ import annotations

import logging
import os
import tempfile

from fastapi import APIRouter, File, Query, UploadFile, HTTPException

from app.models import (
    RecognitionResponse,
    RecognitionResult,
    SimilarSong,
    SimilarSongsResponse,
)
from services.recognition import identify_song
from services.spotify import get_recommendations
from utils.audio_processing import convert_to_clean_wav, convert_to_wav, get_audio_duration
from utils.wave_animation import generate_waveform_base64, generate_spectrogram_base64

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024  # bytes
MIN_DURATION_SECS = 3   # reject clips shorter than this (pre-conversion sanity check)
# Mic recordings use convert_to_clean_wav which enforces its own 7 s minimum


async def _save_upload(upload: UploadFile) -> str:
    """Save an UploadFile to a temporary path and return the path."""
    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_SIZE // 1024 // 1024} MB)",
        )

    # Use a generic suffix — ffmpeg will probe the actual bytes, not the extension
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".audio")
    tmp.write(contents)
    tmp.close()
    logger.info("Upload received: filename=%s, size=%d bytes, content_type=%s → %s",
                upload.filename, len(contents),
                upload.content_type, tmp.name)
    return tmp.name


def _safe_unlink(*paths: str) -> None:
    """Delete temp files, ignoring errors."""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.unlink(p)
        except OSError:
            pass


@router.post("/recognize", response_model=RecognitionResponse)
async def recognize_audio(
    file: UploadFile = File(...),
    source: str = Query(default="upload", description="'mic' for microphone, 'upload' for file"),
):
    """Upload an audio file and identify the song via ACRCloud.

    Pipeline:
      1. Save raw upload to a temp file.
      2. Convert to PCM WAV:
           - source=mic  → convert_to_clean_wav (silence trim, +10 dB boost, 7–15 s gate)
           - source=upload → convert_to_wav (generic, no volume adjustment)
      3. Validate duration ≥ MIN_DURATION_SECS.
      4. Send the WAV to ACRCloud for recognition.
      5. Generate optional spectrogram / waveform images.
      6. Clean up all temp files.
    """
    raw_path = await _save_upload(file)
    wav_path: str | None = None
    is_mic = source.lower() == "mic"
    try:
        # ── 1. Convert to normalised WAV ──────────────────
        try:
            if is_mic:
                logger.info("Using mic pipeline for %s", file.filename)
                wav_path = convert_to_clean_wav(raw_path)
            else:
                wav_path = convert_to_wav(raw_path)
        except ValueError as exc:
            logger.warning("Audio conversion failed for %s: %s",
                           file.filename, exc)
            return RecognitionResponse(
                success=False,
                error=f"Audio processing failed: {exc}",
            )

        # ── 2. Duration check ─────────────────────────────
        duration = get_audio_duration(wav_path)
        logger.info("Audio duration: %.1f s", duration)
        if duration < MIN_DURATION_SECS:
            return RecognitionResponse(
                success=False,
                error=f"Audio too short ({duration:.1f}s). "
                      f"Please provide at least {MIN_DURATION_SECS} seconds.",
            )

        # ── 3. ACRCloud recognition ───────────────────────
        result = identify_song(wav_path)

        # ── 4. Visualizations (best-effort) ───────────────
        spectrogram_b64: str | None = None
        waveform_b64: str | None = None
        try:
            spectrogram_b64 = generate_spectrogram_base64(wav_path)
            waveform_b64 = generate_waveform_base64(wav_path)
        except Exception as viz_err:
            logger.warning("Visualization generation failed: %s", viz_err)

        # ── 5. Return result ──────────────────────────────
        if result:
            logger.info("Recognition success: %s – %s",
                        result["title"], result["artist"])
            return RecognitionResponse(
                success=True,
                result=RecognitionResult(**result),
                spectrogram_base64=spectrogram_b64,
                waveform_base64=waveform_b64,
            )

        logger.info("No match found for upload %s", file.filename)
        if is_mic:
            return RecognitionResponse(
                success=False,
                error="Audio unclear. Try increasing volume or recording longer.",
            )
        return RecognitionResponse(success=False, error="Song not recognized")

    except Exception as exc:
        logger.exception("Unhandled error in /recognize")
        return RecognitionResponse(success=False, error=str(exc))
    finally:
        _safe_unlink(raw_path, wav_path)


@router.post("/spectrogram")
async def get_spectrogram(file: UploadFile = File(...)):
    """Upload audio and receive a base64-encoded spectrogram PNG."""
    raw_path = await _save_upload(file)
    wav_path: str | None = None
    try:
        wav_path = convert_to_wav(raw_path)
        b64 = generate_spectrogram_base64(wav_path)
        return {"success": True, "image_base64": b64}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        _safe_unlink(raw_path, wav_path)


@router.post("/waveform")
async def get_waveform(file: UploadFile = File(...)):
    """Upload audio and receive a base64-encoded waveform PNG."""
    raw_path = await _save_upload(file)
    wav_path: str | None = None
    try:
        wav_path = convert_to_wav(raw_path)
        b64 = generate_waveform_base64(wav_path)
        return {"success": True, "image_base64": b64}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        _safe_unlink(raw_path, wav_path)


@router.get("/similar", response_model=SimilarSongsResponse)
async def get_similar_songs(
    song: str = Query(..., min_length=1),
    artist: str = Query(..., min_length=1),
):
    """Return similar song recommendations via the Spotify recommendations API.

    Falls back with an error message if Spotify credentials are missing
    or the API returns no results.
    """
    try:
        recs = get_recommendations(song, artist)
    except Exception as exc:
        logger.warning("Recommendations failed for '%s – %s': %s",
                       song, artist, exc)
        return SimilarSongsResponse(
            success=False,
            error="Could not fetch recommendations. Please try again.",
        )

    if not recs:
        return SimilarSongsResponse(
            success=False,
            error="No similar songs found. Spotify credentials may not be configured.",
        )

    songs = [
        SimilarSong(
            title=r["title"],
            artist=r["artist"],
            similarity=r["confidence"],
        )
        for r in recs
    ]

    return SimilarSongsResponse(success=True, songs=songs)
