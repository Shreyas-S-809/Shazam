"""Links router — YouTube and Spotify URL resolution."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models import SpotifyLinkResponse, YouTubeLinkResponse
from services.youtube import search_youtube
from services.spotify import search_spotify

router = APIRouter()


@router.get("/youtube", response_model=YouTubeLinkResponse)
async def get_youtube_link(
    song: str = Query(..., min_length=1),
    artist: str = Query(..., min_length=1),
):
    """Search YouTube for the official music video."""
    try:
        url = search_youtube(song, artist)
        if url:
            return YouTubeLinkResponse(success=True, url=url)
        return YouTubeLinkResponse(success=False, error="No YouTube result found")
    except Exception as exc:
        return YouTubeLinkResponse(success=False, error=str(exc))


@router.get("/spotify", response_model=SpotifyLinkResponse)
async def get_spotify_link(
    song: str = Query(..., min_length=1),
    artist: str = Query(..., min_length=1),
):
    """Search Spotify for the track."""
    try:
        result = search_spotify(song, artist)
        if result:
            return SpotifyLinkResponse(success=True, **result)
        return SpotifyLinkResponse(success=False, error="No Spotify result found")
    except Exception as exc:
        return SpotifyLinkResponse(success=False, error=str(exc))
