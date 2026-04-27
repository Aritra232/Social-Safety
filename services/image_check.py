import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import os
import io
import tempfile
import google.generativeai as genai
import opennsfw2 as n2
from dotenv import load_dotenv
from nudenet import NudeDetector
from PIL import Image
import pillow_heif

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Models
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
nude_detector = NudeDetector()

# Thresholds (strict for children)
NUDE_THRESHOLD = 0.25
NSFW_THRESHOLD = 0.30


def detect_and_convert_image(image_bytes):
    """
    Detect image format and convert to JPEG bytes for processing.
    Returns (converted_bytes, mime_type) tuple.
    """
    try:
        # Try to open as HEIC first
        try:
            heif_file = pillow_heif.open(io.BytesIO(image_bytes))
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode
            )
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to JPEG bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue(), "image/jpeg"

        except Exception:
            # Not HEIC, try regular PIL formats
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')

            # Convert to JPEG bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue(), "image/jpeg"

    except Exception as e:
        # If conversion fails, return original bytes with jpeg mime type
        # Gemini might still be able to handle it
        return image_bytes, "image/jpeg"


def nudity_check(image_bytes):
    """
    Detect explicit body parts using NudeNet.
    Returns:
        True  -> unsafe
        False -> safe
        None  -> uncertain
    """
    temp_path = None
    try:
        # Convert image to JPEG first
        converted_bytes, _ = detect_and_convert_image(image_bytes)
        image = Image.open(io.BytesIO(converted_bytes))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = tmp.name
            image.save(temp_path)

        detections = nude_detector.detect(temp_path)

        for item in detections:
            if item["score"] >= NUDE_THRESHOLD:
                return True

        return False

    except Exception:
        return None

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def opennsfw_check(image_bytes):
    """
    General NSFW probability using OpenNSFW2.
    Returns:
        score between 0 and 1
        None on error
    """
    temp_path = None
    try:
        # Convert image to JPEG first
        converted_bytes, _ = detect_and_convert_image(image_bytes)
        image = Image.open(io.BytesIO(converted_bytes)).convert("RGB")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = tmp.name
            image.save(temp_path)

        score = n2.predict_image(temp_path)
        return float(score)

    except Exception:
        return None

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def gemini_check(image_bytes):
    """
    Gemini contextual moderation.
    Returns:
        True  -> safe
        False -> unsafe
        None  -> uncertain
    """
    try:
        # Convert image and get proper mime type
        converted_bytes, mime_type = detect_and_convert_image(image_bytes)

        response = gemini_model.generate_content([
            {
                "mime_type": mime_type,
                "data": converted_bytes
            },
            """
You are a strict child safety AI moderator.

Check whether this image contains:
- nudity
- sexual content
- suggestive adult content
- unsafe violence for children

Respond ONLY with:
SAFE
or
UNSAFE
"""
        ])

        output = response.text.strip().lower()

        if "unsafe" in output:
            return False
        if "safe" in output:
            return True

        return None

    except Exception:
        return None


def check_image(image_bytes):
    """
    Final image moderation logic.
    Returns:
        {"safe": bool, "review": bool}
    """

    # 1. Explicit nudity check
    nude_result = nudity_check(image_bytes)

    if nude_result is True:
        return {"safe": False, "review": False}

    # 2. General NSFW score
    nsfw_score = opennsfw_check(image_bytes)

    if nsfw_score is not None:
        if nsfw_score >= NSFW_THRESHOLD:
            return {"safe": False, "review": False}

    # 3. Gemini context moderation
    gemini_result = gemini_check(image_bytes)

    if gemini_result is False:
        return {"safe": False, "review": False}

    if gemini_result is None:
        return {"safe": False, "review": True}

    return {"safe": True, "review": False}