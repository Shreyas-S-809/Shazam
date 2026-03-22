"""Integration tests for API endpoints."""

import os
import struct
import wave
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables for all tests."""
    monkeypatch.setenv("ACR_HOST", "test.acrcloud.com")
    monkeypatch.setenv("ACR_KEY", "test_key")
    monkeypatch.setenv("ACR_SECRET", "test_secret")
    monkeypatch.setenv("YOUTUBE_API_KEY", "test_yt_key")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def _wav_bytes(duration_secs: float = 5.0) -> bytes:
    """Return raw bytes of a minimal valid WAV file."""
    buf = io.BytesIO()
    sample_rate = 44100
    n_samples = int(sample_rate * duration_secs)
    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_samples, *([0] * n_samples)))
    return buf.getvalue()


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestRecognizeEndpoint:
    @patch("app.routers.audio.identify_song")
    @patch("app.routers.audio.generate_spectrogram_base64")
    @patch("app.routers.audio.generate_waveform_base64")
    @patch("app.routers.audio.convert_to_wav")
    @patch("app.routers.audio.get_audio_duration", return_value=10.0)
    def test_recognize_wav_success(
        self, mock_dur, mock_conv, mock_wave, mock_spec, mock_identify, client, tmp_path
    ):
        """WAV upload → conversion → ACRCloud match → 200 success."""
        # convert_to_wav returns a temp file
        conv_path = str(tmp_path / "converted.wav")
        with open(conv_path, "wb") as f:
            f.write(_wav_bytes())
        mock_conv.return_value = conv_path

        mock_identify.return_value = {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
        }
        mock_spec.return_value = "spec_base64_data"
        mock_wave.return_value = "wave_base64_data"

        response = client.post(
            "/api/audio/recognize",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["title"] == "Blinding Lights"
        assert data["spectrogram_base64"] == "spec_base64_data"
        mock_conv.assert_called_once()

    @patch("app.routers.audio.identify_song")
    @patch("app.routers.audio.generate_spectrogram_base64")
    @patch("app.routers.audio.generate_waveform_base64")
    @patch("app.routers.audio.convert_to_wav")
    @patch("app.routers.audio.get_audio_duration", return_value=10.0)
    def test_recognize_mp3_success(
        self, mock_dur, mock_conv, mock_wave, mock_spec, mock_identify, client, tmp_path
    ):
        """MP3 upload should also work — conversion normalises it."""
        conv_path = str(tmp_path / "converted.wav")
        with open(conv_path, "wb") as f:
            f.write(_wav_bytes())
        mock_conv.return_value = conv_path

        mock_identify.return_value = {
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "album": "÷",
        }
        mock_spec.return_value = "x"
        mock_wave.return_value = "x"

        # Send bytes with .mp3 extension and mpeg content-type
        response = client.post(
            "/api/audio/recognize",
            files={"file": ("song.mp3", b"\xff\xfb\x90\x00" + b"\x00" * 500, "audio/mpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["artist"] == "Ed Sheeran"

    @patch("app.routers.audio.identify_song")
    @patch("app.routers.audio.generate_spectrogram_base64")
    @patch("app.routers.audio.generate_waveform_base64")
    @patch("app.routers.audio.convert_to_wav")
    @patch("app.routers.audio.get_audio_duration", return_value=10.0)
    def test_recognize_no_match(
        self, mock_dur, mock_conv, mock_wave, mock_spec, mock_identify, client, tmp_path
    ):
        conv_path = str(tmp_path / "converted.wav")
        with open(conv_path, "wb") as f:
            f.write(_wav_bytes())
        mock_conv.return_value = conv_path
        mock_identify.return_value = None
        mock_spec.return_value = "x"
        mock_wave.return_value = "x"

        response = client.post(
            "/api/audio/recognize",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not recognized" in data["error"].lower()

    @patch("app.routers.audio.convert_to_wav")
    def test_recognize_invalid_file(self, mock_conv, client):
        """Non-audio file → decode error → friendly error message."""
        mock_conv.side_effect = ValueError("Audio decoding failed: junk.txt")

        response = client.post(
            "/api/audio/recognize",
            files={"file": ("junk.txt", b"not audio at all", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Audio processing failed" in data["error"]

    def test_recognize_empty_file(self, client):
        """Empty upload should return 400."""
        response = client.post(
            "/api/audio/recognize",
            files={"file": ("empty.wav", b"", "audio/wav")},
        )
        assert response.status_code == 400

    @patch("app.routers.audio.convert_to_wav")
    @patch("app.routers.audio.get_audio_duration", return_value=1.5)
    def test_recognize_too_short(self, mock_dur, mock_conv, client, tmp_path):
        """Audio shorter than MIN_DURATION_SECS → error."""
        conv_path = str(tmp_path / "short.wav")
        with open(conv_path, "wb") as f:
            f.write(_wav_bytes(1.5))
        mock_conv.return_value = conv_path

        response = client.post(
            "/api/audio/recognize",
            files={"file": ("short.wav", _wav_bytes(1.5), "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "too short" in data["error"].lower()


class TestSimilarSongsEndpoint:
    @patch("app.routers.audio.get_recommendations")
    def test_similar_songs(self, mock_recs, client):
        mock_recs.return_value = [
            {"title": "Save Your Tears", "artist": "The Weeknd", "confidence": 0.96},
            {"title": "Starboy", "artist": "The Weeknd", "confidence": 0.92},
        ]
        response = client.get("/api/audio/similar?song=Blinding+Lights&artist=The+Weeknd")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["songs"]) == 2
        for song in data["songs"]:
            assert "title" in song
            assert "artist" in song
            assert 0.0 <= song["similarity"] <= 1.0

    @patch("app.routers.audio.get_recommendations")
    def test_similar_songs_no_results(self, mock_recs, client):
        mock_recs.return_value = []
        response = client.get("/api/audio/similar?song=Unknown+Song&artist=Nobody")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "no similar" in data["error"].lower() or "not be configured" in data["error"].lower()


class TestYouTubeLinkEndpoint:
    @patch("app.routers.links.search_youtube")
    def test_youtube_link(self, mock_search, client):
        mock_search.return_value = "https://www.youtube.com/watch?v=abc123"
        response = client.get("/api/links/youtube?song=Blinding+Lights&artist=The+Weeknd")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "youtube.com" in data["url"]


class TestSpotifyLinkEndpoint:
    @patch("app.routers.links.search_spotify")
    def test_spotify_link(self, mock_search, client):
        mock_search.return_value = {
            "url": "https://open.spotify.com/track/123",
            "track_id": "123",
            "preview_url": None,
            "album_art": "https://i.scdn.co/image/abc",
        }
        response = client.get("/api/links/spotify?song=Blinding+Lights&artist=The+Weeknd")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "spotify.com" in data["url"]
