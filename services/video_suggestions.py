import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or os.getenv("Youtube_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEARCH_URL = "https://youtube.googleapis.com/youtube/v3/search"
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY)


def normalize_topic(topic: str) -> str:
    topic = topic.strip()
    mapping = {
        "math": "Mathematics",
        "mathematics": "Mathematics",
        "science": "Science",
        "history": "History",
        "english": "English",
        "language": "English",
    }
    return mapping.get(topic.lower(), topic)


def build_search_query(grade: int, topic: str) -> str:
    topic = normalize_topic(topic)
    return f"Grade {grade} {topic} lesson for kids English"


def generate_video_summary_and_quiz(grade: int, topic: str, title: str, url: str, max_questions: int = 4) -> dict:
    if not OPENAI_API_KEY:
        return {
            "summary": (
                f"Topic: {topic}. This video teaches the main idea in three simple sentences, includes a real-life example, and explains the parts of {topic}."
            ),
            "quiz": []
        }

    prompt = f"""
You are an expert elementary school teacher using CRAFT prompt engineering.
Create a child-friendly summary and a 4-question quiz for a YouTube lesson.

Requirements:
- Start the summary with the topic name.
- Write three simple sentences about the topic.
- Provide one real-life example.
- Include a short "Parts of {topic}" section.
- Use the video title to make the summary accurate.

Return ONLY valid JSON with exactly these keys:
{{
  "summary": "...",
  "quiz": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer": "..."
    }},
    {{...}},
    {{...}},
    {{...}}
  ]
}}
Do not include any extra text, markdown, or commentary.

Video title: {title}
Topic: {topic}
Grade: {grade}
Video link: {url}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert elementary school teacher using CRAFT prompt engineering."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        output = response.choices[0].message.content or "{}"
        result = json.loads(output)

        if "summary" not in result or "quiz" not in result:
            raise ValueError("Incomplete AI response")

        return {
            "summary": result.get("summary", ""),
            "quiz": result.get("quiz", [])
        }
    except Exception:
        return {
            "summary": (
                f"Topic: {topic}. This video teaches the main idea in three simple sentences, includes a real-life example, and explains the parts of {topic}."
            ),
            "quiz": []
        }


def search_youtube_videos(query: str, max_results: int = 24) -> list[dict]:
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YouTube API key is not configured in environment variables")

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "safeSearch": "strict",
        "relevanceLanguage": "en",
        "videoEmbeddable": "true",
        "videoDuration": "medium",
        "videoCategoryId": "27",
        "key": YOUTUBE_API_KEY,
    }

    request_url = f"{SEARCH_URL}?{urlencode(params)}"
    request = Request(request_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except HTTPError as e:
        raise RuntimeError(f"YouTube API error: {e.code}")
    except URLError as e:
        raise RuntimeError(f"YouTube request failed: {e.reason}")

    videos = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id or snippet.get("liveBroadcastContent") != "none":
            continue

        title = snippet.get("title", "")
        if "shorts" in title.lower():
            continue

        videos.append({
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": title,
            "description": snippet.get("description", ""),
        })

    return videos


def get_video_suggestions(grade: int, topic: str, limit: int = 2) -> dict:
    if grade < 3 or grade > 8:
        raise ValueError("Grade must be between 3 and 8")

    topic = topic.strip()
    if not topic:
        raise ValueError("Topic is required")

    query = build_search_query(grade, topic)
    videos = search_youtube_videos(query, max_results=24)

    if len(videos) < limit:
        fallback_query = f"{topic} lesson for grade {grade} kids English"
        videos += search_youtube_videos(fallback_query, max_results=24)

    seen = set()
    selected = []
    for video in videos:
        if video["video_id"] in seen:
            continue
        seen.add(video["video_id"])
        selected.append(video)
        if len(selected) >= limit:
            break

    enriched_videos = []
    for video in selected:
        content = generate_video_summary_and_quiz(grade, topic, video["title"], video["url"])
        enriched_videos.append({
            "url": video["url"],
            "summary": content["summary"],
            "quiz": content["quiz"],
        })

    return {
        "grade": grade,
        "topic": topic,
        "count": len(enriched_videos),
        "videos": enriched_videos,
    }
