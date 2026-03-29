import logging
import os

import requests

logger = logging.getLogger(__name__)


def search_youtube(song: str, artist: str) -> str | None:

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY environment variable is not set")

    clean_song = song.split("(")[0].strip()
    query = f"{clean_song} {artist} official music video"

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": 3,
        "type": "video",
    }

    response = requests.get(url, params=params)
    data = response.json()

    # --- DEBUG: log the actual API response status and body ---
    logger.info("YouTube API status=%s query=%r", response.status_code, query)
    if "error" in data:
        logger.error("YouTube API error: %s", data["error"])
        raise RuntimeError(
            f"YouTube API error {data['error'].get('code')}: "
            f"{data['error'].get('message', 'unknown')}"
        )

    items = data.get("items", [])

    for item in items:
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    return None