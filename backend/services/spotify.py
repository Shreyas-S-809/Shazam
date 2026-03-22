"""Spotify search + recommendation service.

Uses Spotipy (Spotify Web API wrapper) to:
  - search_spotify(): Find a track's URL, preview, album art.
  - get_recommendations(): Return 5 similar tracks using Spotify's
    recommendations API seeded by the recognised track.

Falls back gracefully if credentials are not configured.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

_RECOMMENDATION_LIMIT = 5


def _get_client():
    """Return an authenticated Spotipy client, or None if credentials are missing."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.info("Spotify credentials not configured — skipping")
        return None

    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
    )


def search_spotify(song: str, artist: str) -> dict | None:
    """Search Spotify for a track and return its metadata.

    Returns dict with keys: url, track_id, preview_url, album_art
    or None if not found / credentials missing.
    """
    sp = _get_client()
    if sp is None:
        return None

    try:
        query = f"track:{song} artist:{artist}"
        results = sp.search(q=query, type="track", limit=1)

        items = results.get("tracks", {}).get("items", [])
        if not items:
            return None

        track = items[0]
        album_images = track.get("album", {}).get("images", [])

        return {
            "url": track["external_urls"].get("spotify"),
            "track_id": track["id"],
            "preview_url": track.get("preview_url"),
            "album_art": album_images[0]["url"] if album_images else None,
        }
    except Exception as exc:
        logger.warning("Spotify search failed: %s", exc)
        return None


def get_recommendations(song: str, artist: str) -> list[dict]:
    """Return up to 5 similar tracks from Spotify's recommendations API.

    Steps:
      1. Search for the seed track by title + artist.
      2. Use the track's artist IDs + track ID as recommendation seeds.
      3. Infer market from the artist's metadata for region-aware results.
      4. Return a list of dicts with keys: title, artist, confidence.

    Returns an empty list on any failure.
    """
    sp = _get_client()
    if sp is None:
        return []

    try:
        # Step 1: find the seed track
        query = f"track:{song} artist:{artist}"
        search_res = sp.search(q=query, type="track", limit=1)
        items = search_res.get("tracks", {}).get("items", [])
        if not items:
            logger.info("Seed track not found on Spotify: %s – %s", song, artist)
            return []

        seed_track = items[0]
        seed_track_id = seed_track["id"]
        seed_artist_ids = [a["id"] for a in seed_track.get("artists", [])[:2]]

        # Step 2: infer market from artist info
        market = _infer_market(sp, seed_artist_ids)

        # Step 3: get recommendations
        rec_kwargs: dict = {
            "seed_tracks": [seed_track_id],
            "seed_artists": seed_artist_ids[:1],
            "limit": _RECOMMENDATION_LIMIT,
        }
        if market:
            rec_kwargs["market"] = market

        recs = sp.recommendations(**rec_kwargs)

        # Step 4: build result list
        results: list[dict] = []
        tracks = recs.get("tracks", [])
        for i, trk in enumerate(tracks):
            # Confidence: top result = 0.96, decreasing by 0.04
            confidence = round(0.96 - i * 0.04, 2)
            artists = ", ".join(a["name"] for a in trk.get("artists", []))
            results.append({
                "title": trk.get("name", "Unknown"),
                "artist": artists or "Unknown",
                "confidence": max(confidence, 0.60),
            })

        logger.info("Spotify recommendations for '%s – %s': %d results",
                     song, artist, len(results))
        return results

    except Exception as exc:
        logger.warning("Spotify recommendations failed: %s", exc)
        return []


def _infer_market(sp, artist_ids: list[str]) -> str | None:
    """Best-effort market inference from artist metadata.

    Checks the first seed artist's genres for regional indicators.
    Returns an ISO 3166-1 alpha-2 code ('IN', 'US', etc.) or None.
    """
    if not artist_ids:
        return None

    try:
        artist_info = sp.artist(artist_ids[0])
        genres = [g.lower() for g in artist_info.get("genres", [])]

        # Simple genre→market mapping for common regional music
        genre_market = {
            "bollywood": "IN",
            "desi pop": "IN",
            "filmi": "IN",
            "indian": "IN",
            "punjabi": "IN",
            "tollywood": "IN",
            "k-pop": "KR",
            "j-pop": "JP",
            "latin": "MX",
            "reggaeton": "MX",
        }
        for keyword, market in genre_market.items():
            if any(keyword in g for g in genres):
                return market
    except Exception:
        pass

    return None
