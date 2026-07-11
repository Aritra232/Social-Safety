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


def check_text(text):
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            prompt = f"""
You are a strict child-safety AI moderator. Analyze the following text for appropriateness.

Text: "{text}"

Evaluate each category and return ONLY a valid JSON object with these exact keys and boolean values:
{{
  "language_and_tone": true/false,
  "content_appropriateness": true/false,
  "kindness": true/false
}}

Examples:
- Safe text "Hello, how are you?": {{"language_and_tone": true, "content_appropriateness": true, "kindness": true}}
- Unsafe text "You are stupid and ugly": {{"language_and_tone": false, "content_appropriateness": true, "kindness": false}}

Do not include any other text, explanations, or formatting. Return only the JSON.
"""

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a strict child-safety AI moderator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )

            output = response.choices[0].message.content or "{}"
            result = _extract_json(output)

            # Ensure all expected keys exist
            for key in ["language_and_tone", "content_appropriateness", "kindness"]:
                if key not in result:
                    result[key] = False

            return result

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Quota exceeded, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("AI quota exceeded, failing...")
                    return {
                        "language_and_tone": False,
                        "content_appropriateness": False,
                        "kindness": False
                    }
            else:
                return {
                    "language_and_tone": False,
                    "content_appropriateness": False,
                    "kindness": False
                }

    return {
        "language_and_tone": False,
        "content_appropriateness": False,
        "kindness": False
    }