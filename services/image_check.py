import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import os
import io
import tempfile
from google import genai
from dotenv import load_dotenv
from PIL import Image
import pillow_heif

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model
gemini_model_name = "gemini-2.5-pro"


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


def check_image(image_bytes):
    """
    Main image check function using Gemini API.
    Returns {"safe": bool, "review": bool}
    """
    try:
        # Convert image and get proper mime type
        converted_bytes, mime_type = detect_and_convert_image(image_bytes)

        from google.genai import types
        part = types.Part.from_bytes(data=converted_bytes, mime_type=mime_type)

        config = types.GenerateContentConfig(
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
            ]
        )

        response = client.models.generate_content(
            model=gemini_model_name,
            contents=[
                part,
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
            ],
            config=config
        )

        output = response.text.strip().lower()

        if "unsafe" in output:
            return {"safe": False, "review": False}
        elif "safe" in output:
            return {"safe": True, "review": False}
        else:
            # Uncertain, err on side of caution
            return {"safe": False, "review": True}

    except Exception as e:
        print(f"Image check failed: {e}")
        return {"safe": False, "review": True}