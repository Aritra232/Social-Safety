import os
from dotenv import load_dotenv
import json
import time
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _extract_json(text):
    text = text.strip()
    import re

    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def check_emoji(text):
    """
    Check if text contains adult/suggestive emojis using Gemini AI
    """
    if not text:
        return {"safe": True}

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            prompt = f"""
You are a strict child-safety AI moderator specializing in emoji analysis.

Analyze the following text for adult/inappropriate emoji usage:

Text: "{text}"

Consider:
- Individual emojis that represent adult themes (sexual organs, explicit acts, etc.)
- Emoji combinations that create suggestive shapes or meanings
- Cultural context and hidden meanings
- Repeated emojis that might indicate emphasis on adult themes

Return ONLY a valid JSON object with this exact format:
{{
  "safe": true/false
}}

Examples:
- Safe: "Hello 😀" → {{"safe": true}}
- Unsafe: "🍆💦😏" → {{"safe": false}}
- Unsafe: "👉👌" → {{"safe": false}}

Be extremely strict - when in doubt, mark as unsafe for child protection.
Return only the JSON, no other text.
"""

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a strict child-safety AI moderator specializing in emoji analysis."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )

            output = response.choices[0].message.content or "{}"
            result = _extract_json(output)

            # Ensure the expected key exists
            if "safe" not in result:
                result["safe"] = False

            return result

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Emoji check quota exceeded, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("Emoji check AI quota exceeded, failing...")
                    return {"safe": False}
            else:
                print(f"Emoji check error: {e}")
                return {"safe": False}

    return {"safe": False}