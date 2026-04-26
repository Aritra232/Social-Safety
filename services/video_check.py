import tempfile
import os
import cv2
from .image_check import check_image

VIDEO_EXTENSIONS = {"mp4", "mov", "mkv", "webm", "avi", "flv", "mpeg", "mpg"}


def extract_frames_from_video(video_bytes, max_frames=3):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1

        positions = []
        if total_frames <= max_frames:
            positions = list(range(total_frames))
        else:
            interval = total_frames // max_frames
            positions = [min(total_frames - 1, i * interval) for i in range(max_frames)]

        frames = []
        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            success, frame = cap.read()
            if not success or frame is None:
                continue

            success, jpg = cv2.imencode(".jpg", frame)
            if not success:
                continue

            frames.append(jpg.tobytes())

        return frames
    finally:
        cap.release()
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def check_video(video_bytes):
    if not video_bytes or len(video_bytes) < 1000:
        return {"safe": False}

    frames = extract_frames_from_video(video_bytes)
    if not frames:
        return {"safe": False}

    for index, frame_bytes in enumerate(frames, start=1):
        result = check_image(frame_bytes)
        if not result["safe"]:
            return {
                "safe": False
            }

    return {"safe": True}
