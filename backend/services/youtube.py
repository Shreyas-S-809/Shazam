import os
import requests


def search_youtube(song, artist):

    api_key = os.environ["YOUTUBE_API_KEY"]

    clean_song = song.split("(")[0].strip()
    query = f"{clean_song} {artist} official music video"

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": 3,
        "type": "video"
    }

    response = requests.get(url, params=params)
    data = response.json()

    items = data.get("items", [])

    for item in items:
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    return None