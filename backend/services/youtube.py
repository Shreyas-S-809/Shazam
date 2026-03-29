import os
from urllib.parse import quote_plus

import requests


def _search_youtube_api(query: str) -> str | None:
    """Try the official YouTube Data API v3 (requires YOUTUBE_API_KEY)."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("[YouTube] YOUTUBE_API_KEY not set, skipping API search")
        return None

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": 3,
        "type": "video",
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    print(f"[YouTube API] status={response.status_code} query={query!r}")
    print(f"[YouTube API] response keys={list(data.keys())}")

    if "error" in data:
        print(f"[YouTube API] ERROR: {data['error']}")
        return None

    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    return None


def _search_youtube_scrape(query: str) -> str | None:
    """Fallback: scrape YouTube search results (no API key needed)."""
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        print(f"[YouTube Scrape] status={resp.status_code} query={query!r}")

        # YouTube embeds video IDs in the page HTML as "videoId":"XXXXXXXXXXX"
        import re
        match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        if match:
            video_id = match.group(1)
            print(f"[YouTube Scrape] Found video: {video_id}")
            return f"https://www.youtube.com/watch?v={video_id}"

        print("[YouTube Scrape] No videoId found in page HTML")
    except Exception as exc:
        print(f"[YouTube Scrape] Exception: {exc}")

    return None


def search_youtube(song: str, artist: str) -> str | None:
    clean_song = song.split("(")[0].strip()
    query = f"{clean_song} {artist} official music video"
    print(f"[YouTube] Searching: {query!r}")

    # 1. Try official API first
    url = _search_youtube_api(query)
    if url:
        return url

    # 2. Fallback to scraping YouTube search page
    print("[YouTube] API failed, trying scrape fallback...")
    url = _search_youtube_scrape(query)
    if url:
        return url

    print("[YouTube] All methods failed")
    return None