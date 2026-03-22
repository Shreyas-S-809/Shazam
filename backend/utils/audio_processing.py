"""Audio processing utilities.

Provides:
  - convert_to_clean_wav(): Mic-optimised pipeline — silence trim, volume boost,
    strict format normalisation. Use this for microphone recordings.
  - convert_to_wav(): General-purpose conversion for file uploads.
  - get_audio_duration(): Return the duration in seconds of an audio file.
  - generate_spectrogram(): Legacy matplotlib spectrogram (kept for backward compat).
"""

import logging
import os
import tempfile

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

# ── Shared constants ──────────────────────────────────────

TARGET_SAMPLE_RATE = 44100
TARGET_CHANNELS = 1        # mono
TARGET_SAMPLE_WIDTH = 2    # 16-bit PCM
MAX_DURATION_MS = 15_000   # ACRCloud sample window
MIN_DURATION_MS = 7_000    # reject samples shorter than this after silence trim
VOLUME_BOOST_DB = 10       # dB boost applied to mic recordings


# ── Silence trimmer ───────────────────────────────────────

def _trim_silence(audio: AudioSegment) -> AudioSegment:
    """Remove leading/trailing silence.

    Finds the first and last non-silent range (≥ 500 ms,
    silence threshold −40 dBFS) and slices the audio to
    that span.  Returns the original segment unchanged if
    no voiced content is detected.
    """
    ranges = detect_nonsilent(audio, min_silence_len=500, silence_thresh=-40)
    if not ranges:
        logger.warning("No non-silent regions detected — returning original audio")
        return audio
    start_ms, end_ms = ranges[0][0], ranges[-1][1]
    trimmed = audio[start_ms:end_ms]
    logger.info("Silence trim: %d ms → %d ms (removed %d ms)",
                len(audio), len(trimmed), len(audio) - len(trimmed))
    return trimmed


# ── Mic-optimised conversion ──────────────────────────────

def convert_to_clean_wav(input_path: str) -> str:
    """Convert a microphone recording to ACRCloud-ready WAV.

    Pipeline:
      1. ffmpeg auto-detect decode (handles webm/opus, ogg, m4a, …)
      2. Mono · 44 100 Hz · 16-bit PCM normalisation
      3. Silence trimming (removes dead air at start/end)
      4. +10 dB volume boost (mic recordings are typically low-level)
      5. Hard trim to 15 s (ACRCloud optimal window)
      6. Reject if < 7 s of voiced content remains

    Returns the path to a new temporary WAV file.
    The caller is responsible for deleting it when done.

    Raises ``ValueError`` on decode failure or clip too short.
    """
    logger.info("MIC pipeline: decoding %s", os.path.basename(input_path))
    try:
        audio = AudioSegment.from_file(input_path)
    except CouldntDecodeError as exc:
        raise ValueError(f"Audio decoding failed: {os.path.basename(input_path)}") from exc
    except Exception as exc:
        raise ValueError(f"Audio decoding failed: {os.path.basename(input_path)}") from exc

    # Normalise format first so silence detection works at target sample rate
    audio = (
        audio
        .set_channels(TARGET_CHANNELS)
        .set_frame_rate(TARGET_SAMPLE_RATE)
        .set_sample_width(TARGET_SAMPLE_WIDTH)
    )

    logger.info("Audio duration before trim: %d ms | max amplitude: %d",
                len(audio), audio.max)

    # Remove silence
    audio = _trim_silence(audio)

    # Boost gain — mic input is often 6–20 dB below line level
    audio = audio + VOLUME_BOOST_DB

    # Trim to ACRCloud optimal window
    if len(audio) > MAX_DURATION_MS:
        audio = audio[:MAX_DURATION_MS]
        logger.info("Trimmed to %d ms", MAX_DURATION_MS)

    logger.info("Audio duration after processing: %d ms | max amplitude: %d",
                len(audio), audio.max)

    if len(audio) < MIN_DURATION_MS:
        raise ValueError(
            f"Audio too short after silence removal ({len(audio) / 1000:.1f}s). "
            f"Please record at least {MIN_DURATION_MS // 1000} seconds of audio."
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(tmp.name, format="wav")
    tmp.close()

    logger.info("Mic WAV ready → %s (%d bytes)", tmp.name, os.path.getsize(tmp.name))
    return tmp.name


# ── General-purpose conversion (file uploads) ────────────

def convert_to_wav(input_path: str) -> str:
    """Convert *any* ffmpeg-supported audio file to a normalised WAV.

    Lets ffmpeg probe the actual byte stream to determine the codec —
    never trusts MIME types or file extensions.

    Returns the path to a new temporary WAV file.  The caller is
    responsible for deleting it when done.

    Raises ``ValueError`` if pydub / ffmpeg cannot decode the input.
    """
    logger.info("Converting %s → WAV (PCM 16-bit, mono, %d Hz)",
                os.path.basename(input_path), TARGET_SAMPLE_RATE)
    try:
        # No format= hint — let ffmpeg auto-detect from the byte stream
        audio = AudioSegment.from_file(input_path)
    except CouldntDecodeError as exc:
        logger.warning("pydub decode failed for %s: %s", input_path, exc)
        raise ValueError(
            f"Audio decoding failed: {os.path.basename(input_path)}"
        ) from exc
    except Exception as exc:
        logger.error("Unexpected decode error for %s: %s", input_path, exc)
        raise ValueError(
            f"Audio decoding failed: {os.path.basename(input_path)}"
        ) from exc

    audio = (
        audio
        .set_frame_rate(TARGET_SAMPLE_RATE)
        .set_channels(TARGET_CHANNELS)
        .set_sample_width(TARGET_SAMPLE_WIDTH)
    )

    # Trim to MAX_DURATION_MS to keep the sample small for ACRCloud
    if len(audio) > MAX_DURATION_MS:
        audio = audio[:MAX_DURATION_MS]
        logger.info("Trimmed audio to %d ms", MAX_DURATION_MS)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(tmp.name, format="wav")
    tmp.close()

    logger.info("Conversion complete → %s (%d bytes)",
                tmp.name, os.path.getsize(tmp.name))
    return tmp.name


def get_audio_duration(path: str) -> float:
    """Return the duration of an audio file in seconds."""
    try:
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0
    except Exception:
        return 0.0


# ── Legacy spectrogram (kept for backward compat) ────────

def generate_spectrogram(audio_file):
    y, sr = librosa.load(audio_file)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(figsize=(6, 3))
    librosa.display.specshow(S_db, sr=sr, ax=ax)
    ax.set_title("Spectrogram")
    plt.tight_layout()

    return fig
