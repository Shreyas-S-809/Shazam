import logging
import os
import tempfile

import matplotlib.pyplot as plt
import numpy as np
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 44100
TARGET_CHANNELS = 1
TARGET_SAMPLE_WIDTH = 2
MAX_DURATION_MS = 15_000
MIN_DURATION_MS = 7_000
VOLUME_BOOST_DB = 10


def _trim_silence(audio: AudioSegment) -> AudioSegment:
    ranges = detect_nonsilent(audio, min_silence_len=500, silence_thresh=-40)
    if not ranges:
        logger.warning("No non-silent regions detected — returning original audio")
        return audio
    start_ms, end_ms = ranges[0][0], ranges[-1][1]
    trimmed = audio[start_ms:end_ms]
    logger.info("Silence trim: %d ms → %d ms (removed %d ms)",
                len(audio), len(trimmed), len(audio) - len(trimmed))
    return trimmed


def convert_to_clean_wav(input_path: str) -> str:
    logger.info("MIC pipeline: decoding %s", os.path.basename(input_path))
    try:
        audio = AudioSegment.from_file(input_path)
    except CouldntDecodeError as exc:
        raise ValueError(f"Audio decoding failed: {os.path.basename(input_path)}") from exc
    except Exception as exc:
        raise ValueError(f"Audio decoding failed: {os.path.basename(input_path)}") from exc

    audio = (
        audio
        .set_channels(TARGET_CHANNELS)
        .set_frame_rate(TARGET_SAMPLE_RATE)
        .set_sample_width(TARGET_SAMPLE_WIDTH)
    )

    logger.info("Audio duration before trim: %d ms | max amplitude: %d",
                len(audio), audio.max)

    audio = _trim_silence(audio)
    audio = audio + VOLUME_BOOST_DB

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


def convert_to_wav(input_path: str) -> str:
    logger.info("Converting %s → WAV (PCM 16-bit, mono, %d Hz)",
                os.path.basename(input_path), TARGET_SAMPLE_RATE)
    try:
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
    try:
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0
    except Exception:
        return 0.0


def generate_spectrogram(audio_file):
    audio = AudioSegment.from_file(audio_file)
    samples = np.array(audio.get_array_of_samples())

    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)

    sr = audio.frame_rate

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.specgram(samples, Fs=sr)
    ax.set_title("Spectrogram")
    plt.tight_layout()

    return fig
