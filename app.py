import os
import sys

# Fix for missing VC++ Redistributable DLLs on Windows
if os.name == 'nt':
    # Try to find the Scripts directory in the venv
    possible_scripts = [
        os.path.join(os.path.dirname(__file__), 'venv', 'Scripts'),
        os.path.join(sys.prefix, 'Scripts'),
    ]
    for scripts_path in possible_scripts:
        if os.path.exists(scripts_path):
            try:
                os.add_dll_directory(scripts_path)
            except (AttributeError, OSError):
                pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from services.ai_moderator import check_text
from services.image_check import check_image
from services.video_check import check_video
from services.pii_check import check_pii
from services.emoji_check import check_emoji
from services.video_suggestions import get_video_suggestions

app = FastAPI()

@app.post("/check-content")
async def check_content(
    caption: str = Form(None),
    image: UploadFile = File(None),
    video: UploadFile = File(None)
):
    if caption is None and image is None and video is None:
        raise HTTPException(status_code=400, detail="Provide at least a caption, image, or video to check")

    image_bytes = await image.read() if image is not None else None
    video_bytes = await video.read() if video is not None else None

    # 🔹 TEXT CHECK (only if caption provided)
    language_and_tone = True
    content_appropriateness = True
    kindness = True
    personal_info_safe = True
    emoji_safe = True

    if caption:
        text_result = check_text(caption)
        language_and_tone = text_result.get("language_and_tone", False)
        content_appropriateness = text_result.get("content_appropriateness", False)
        kindness = text_result.get("kindness", False)

        # 🔹 PII CHECK (only if caption provided)
        pii_result = check_pii(caption)
        personal_info_safe = pii_result["safe"]

        # 🔹 EMOJI CHECK (only if caption provided)
        emoji_result = check_emoji(caption)
        emoji_safe = emoji_result["safe"]

    # 🔹 IMAGE / VIDEO CHECK → "photos" field
    photos_safe = True
    if image_bytes is not None:
        image_result = check_image(image_bytes)
        if not image_result["safe"]:
            photos_safe = False

    if video_bytes is not None:
        video_result = check_video(video_bytes)
        if not video_result["safe"]:
            photos_safe = False

    overall = all([
        language_and_tone,
        content_appropriateness,
        photos_safe,
        personal_info_safe,
        kindness,
        emoji_safe
    ])

    return {
        "language_and_tone": language_and_tone,
        "content_appropriateness": content_appropriateness,
        "photos": photos_safe,
        "personal_information": personal_info_safe,
        "kindness": kindness,
        "overall": overall
    }


@app.get("/video-suggestions")
async def video_suggestions(
    grade: int = Query(..., ge=3, le=8),
    topic: str = Query(..., min_length=1),
    limit: int = Query(2, ge=1, le=12)
):
    """Return kid-friendly English YouTube videos for a grade and topic."""
    try:
        result = await run_in_threadpool(get_video_suggestions, grade, topic, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Video suggestion lookup failed")

    return result