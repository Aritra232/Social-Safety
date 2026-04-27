import tempfile
import os
import cv2
from .image_check import check_image


def extract_frames_from_video(video_bytes, max_frames=30):
    """
    Extract 1 frame per second, max 30 frames.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    frames = []
    cap = cv2.VideoCapture(tmp_path)

    try:
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0:
            fps = 25

        step = int(fps)

        positions = list(range(0, total_frames, step))[:max_frames]

        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            success, frame = cap.read()

            if not success:
                continue

            success, jpg = cv2.imencode(".jpg", frame)

            if success:
                frames.append(jpg.tobytes())

        return frames

    finally:
        cap.release()
        os.remove(tmp_path)


def check_video(video_bytes):
    """
    Video moderation:
    - unsafe if any frame unsafe
    - review if uncertain
    """
    frames = extract_frames_from_video(video_bytes, max_frames=30)

    if not frames:
        return {"safe": False, "review": True}

    review_needed = False

    for frame in frames:
        result = check_image(frame)

        if result["safe"] is False:
            if result["review"]:
                review_needed = True
            else:
                return {"safe": False, "review": False}

    if review_needed:
        return {"safe": False, "review": True}

    return {"safe": True, "review": False}