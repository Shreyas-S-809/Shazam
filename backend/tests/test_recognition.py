"""Unit tests for recognition, youtube, and audio conversion."""

import os
import struct
import wave
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables for all tests."""
    monkeypatch.setenv("ACR_HOST", "test.acrcloud.com")
    monkeypatch.setenv("ACR_KEY", "test_key")
    monkeypatch.setenv("ACR_SECRET", "test_secret")
    monkeypatch.setenv("YOUTUBE_API_KEY", "test_yt_key")


def _make_wav(path: str, duration_secs: float = 5.0) -> str:
    """Create a minimal valid WAV file at *path*."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_secs)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_samples, *([0] * n_samples)))
    return str(path)


# ── ACRCloud recognition ────────────────────────────────


class TestIdentifySong:
    """Tests for services.recognition.identify_song."""

    @patch("services.recognition.requests.post")
    def test_successful_recognition(self, mock_post, tmp_path):
        """Should return title, artist, album when ACRCloud returns a match."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": {"code": 0, "msg": "Success"},
            "metadata": {
                "music": [
                    {
                        "title": "Blinding Lights",
                        "artists": [{"name": "The Weeknd"}],
                        "album": {"name": "After Hours"},
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        audio_file = _make_wav(tmp_path / "test.wav")

        from services.recognition import identify_song

        result = identify_song(audio_file)

        assert result is not None
        assert result["title"] == "Blinding Lights"
        assert result["artist"] == "The Weeknd"
        assert result["album"] == "After Hours"

    @patch("services.recognition.requests.post")
    def test_no_match(self, mock_post, tmp_path):
        """Should return None when ACRCloud returns no match."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": {"code": 1001, "msg": "No result"},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        audio_file = _make_wav(tmp_path / "test.wav")

        from services.recognition import identify_song

        result = identify_song(audio_file)
        assert result is None

    @patch("services.recognition.requests.post")
    def test_api_timeout(self, mock_post, tmp_path):
        """Should raise RuntimeError after retries are exhausted."""
        import requests as req
        mock_post.side_effect = req.Timeout("Connection timed out")

        audio_file = _make_wav(tmp_path / "test.wav")

        from services.recognition import identify_song

        with pytest.raises(RuntimeError, match="did not respond after"):
            identify_song(audio_file)

        # Verify it retried 3 times
        assert mock_post.call_count == 3

    def test_missing_credentials(self, monkeypatch, tmp_path):
        """Should raise RuntimeError when env vars are absent."""
        monkeypatch.delenv("ACR_HOST", raising=False)
        monkeypatch.delenv("ACR_KEY", raising=False)

        audio_file = _make_wav(tmp_path / "test.wav")

        from services.recognition import identify_song

        with pytest.raises(RuntimeError, match="Missing ACRCloud credentials"):
            identify_song(audio_file)


# ── YouTube search ───────────────────────────────────────


class TestSearchYouTube:
    """Tests for services.youtube.search_youtube."""

    @patch("services.youtube.requests.get")
    def test_successful_search(self, mock_get):
        """Should return a YouTube URL when a video is found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{"id": {"videoId": "abc123"}}]
        }
        mock_get.return_value = mock_response

        from services.youtube import search_youtube

        url = search_youtube("Blinding Lights", "The Weeknd")
        assert url == "https://www.youtube.com/watch?v=abc123"

    @patch("services.youtube.requests.get")
    def test_no_results(self, mock_get):
        """Should return None when YouTube returns empty items list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        # Reload module to pick up the patched requests.get
        import importlib
        import services.youtube as yt_mod
        importlib.reload(yt_mod)

        url = yt_mod.search_youtube("Unknown Song", "Unknown Artist")
        assert url is None


# ── Audio conversion ─────────────────────────────────────


class TestAudioConversion:
    """Tests for utils.audio_processing.convert_to_wav."""

    def test_wav_passthrough(self, tmp_path):
        """A valid WAV should convert without error."""
        src = _make_wav(tmp_path / "input.wav")

        from utils.audio_processing import convert_to_wav

        out = convert_to_wav(src)
        try:
            assert os.path.exists(out)
            assert out.endswith(".wav")
            # Verify it's a valid WAV
            with wave.open(out, "r") as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2
                assert wf.getframerate() == 44100
        finally:
            os.unlink(out)

    def test_invalid_file_raises(self, tmp_path):
        """A non-audio file should raise ValueError."""
        bad = tmp_path / "garbage.mp3"
        bad.write_bytes(b"this is not audio data at all")

        from utils.audio_processing import convert_to_wav

        with pytest.raises(ValueError, match="Audio decoding failed"):
            convert_to_wav(str(bad))

    def test_duration_check(self, tmp_path):
        """get_audio_duration should report correct length."""
        src = _make_wav(tmp_path / "five_sec.wav", duration_secs=5.0)

        from utils.audio_processing import get_audio_duration

        dur = get_audio_duration(src)
        assert 4.9 <= dur <= 5.1
