"""Wave animation & base64 image generation utilities.

Generates base64-encoded PNG images for:
  - Waveform visualization (amplitude over time)
  - Mel-spectrogram heatmap

These are returned to the Next.js frontend for direct rendering
via <img src="data:image/png;base64,..." />.
"""

import base64
import io

import librosa
import librosa.display
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Use non-interactive backend (no GUI needed on server)
matplotlib.use("Agg")


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_waveform_base64(audio_file: str) -> str:
    """Generate a stylized waveform image and return as base64 PNG.

    The waveform uses a gradient-like green color scheme inspired by
    Spotify's visual language for a modern look.
    """
    y, sr = librosa.load(audio_file, sr=22050)

    fig, ax = plt.subplots(figsize=(8, 2.5))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    # Time axis
    t = np.linspace(0, len(y) / sr, num=len(y))

    # Plot waveform with gradient-like effect
    ax.fill_between(t, y, alpha=0.6, color="#1DB954")
    ax.fill_between(t, -np.abs(y), alpha=0.3, color="#1ed760")
    ax.plot(t, y, color="#1DB954", linewidth=0.4, alpha=0.8)

    ax.set_xlim(0, len(y) / sr)
    ax.set_ylim(-1, 1)
    ax.axis("off")

    return _fig_to_base64(fig)


def generate_spectrogram_base64(audio_file: str) -> str:
    """Generate a mel-spectrogram heatmap and return as base64 PNG.

    Uses the same librosa logic from the original audio_processing.py
    but outputs to base64 instead of returning a figure object.
    """
    y, sr = librosa.load(audio_file)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(figsize=(8, 3))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    librosa.display.specshow(
        S_db,
        sr=sr,
        ax=ax,
        cmap="magma",
        x_axis="time",
        y_axis="mel",
    )
    ax.set_title("Spectrogram", color="white", fontsize=12, pad=8)
    ax.tick_params(colors="white", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

    return _fig_to_base64(fig)
