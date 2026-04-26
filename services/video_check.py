import tempfile
import os
import cv2
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from .image_check import check_image

VIDEO_EXTENSIONS = {"mp4", "mov", "mkv", "webm", "avi", "flv", "mpeg", "mpg"}


def extract_frames_from_video(video_bytes, max_frames=5):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    cap = None
    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0:
            fps = 25.0

        if total_frames <= 0:
            total_frames = 1

        # Sample roughly one frame every 2 seconds (up to max_frames) for speed.
        step = max(1, int(fps * 2))
        sampled = list(range(0, total_frames, step))
        if not sampled:
            sampled = [0]

        if len(sampled) > max_frames:
            interval = len(sampled) / float(max_frames)
            sampled = [sampled[int(i * interval)] for i in range(max_frames)]

        positions = []
        for p in sampled:
            positions.append(min(total_frames - 1, p))

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
        if cap is not None:
            cap.release()
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def check_video(video_bytes, max_frames=5, frame_timeout_sec=8):
    if not video_bytes or len(video_bytes) < 1000:
        return {"safe": False}

    frames = extract_frames_from_video(video_bytes, max_frames=max_frames)
    if not frames:
        return {"safe": False}

    # Process frame-by-frame and return immediately on first unsafe frame.
    with ThreadPoolExecutor(max_workers=1) as executor:
        for frame in frames:
            future = executor.submit(check_image, frame, True)
            try:
                result = future.result(timeout=frame_timeout_sec)
            except TimeoutError:
                return {"safe": False}
            except Exception:
                return {"safe": False}

            if not result.get("safe", False):
                return {"safe": False}

    return {"safe": True}
