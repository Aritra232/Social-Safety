from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from services.ai_moderator import check_text
from services.image_check import check_image
from services.video_check import check_video
from services.pii_check import check_pii

app = FastAPI()

@app.post("/check-content")
async def check_content(
    caption: str = Form(...),
    image: UploadFile = File(None),
    video: UploadFile = File(None)
):
    if image is None and video is None:
        raise HTTPException(status_code=400, detail="Provide image or video to check")

    image_bytes = await image.read() if image is not None else None
    video_bytes = await video.read() if video is not None else None

    # 🔹 TEXT CHECK
    text_result = check_text(caption)
    if not text_result["safe"]:
        return text_result

    # 🔹 IMAGE CHECK (Gemini)
    if image_bytes is not None:
        image_result = check_image(image_bytes)
        if not image_result["safe"]:
            return image_result

    # 🔹 VIDEO CHECK
    if video_bytes is not None:
        video_result = check_video(video_bytes)
        if not video_result["safe"]:
            return video_result

    # 🔹 PII CHECK
    pii_result = check_pii(caption)
    if not pii_result["safe"]:
        return pii_result

    return {"safe": True}