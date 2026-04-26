from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from services.ai_moderator import check_text
from services.image_check import check_image
from services.video_check import check_video
from services.pii_check import check_pii

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

    if caption:
        text_result = check_text(caption)
        language_and_tone = text_result.get("language_and_tone", False)
        content_appropriateness = text_result.get("content_appropriateness", False)
        kindness = text_result.get("kindness", False)

        # 🔹 PII CHECK (only if caption provided)
        pii_result = check_pii(caption)
        personal_info_safe = pii_result["safe"]

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
        kindness
    ])

    return {
        "language_and_tone": language_and_tone,
        "content_appropriateness": content_appropriateness,
        "photos": photos_safe,
        "personal_information": personal_info_safe,
        "kindness": kindness,
        "overall": overall
    }