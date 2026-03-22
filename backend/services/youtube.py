"""YouTube search service.

Original logic preserved exactly from the Streamlit project.
Only change: st.secrets → os.environ for FastAPI compatibility.
"""

import os
import requests


def search_youtube(song, artist):

    api_key = os.environ["YOUTUBE_API_KEY"]
    query = f"{song} {artist} official song"

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": 1,
        "type": "video"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data and data["items"]:
        video_id = data["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"

    return None
