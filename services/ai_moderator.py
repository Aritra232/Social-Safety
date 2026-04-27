import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import time


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Try models in order of expected quota limits (lite/flash models have higher free tier limits)
MODEL_OPTIONS = [
    # "models/gemini-2.5-flash-lite",  # Highest free tier limits
    # "models/gemini-2.0-flash-lite-001",
    # "models/gemini-flash-lite-latest",
    # "models/gemini-2.5-flash",  # Good balance
    # "models/gemini-2.0-flash-001",
    # "models/gemini-flash-latest",
    # "models/gemini-2.5-pro",  # Lower limits but more capable
    # "models/gemini-pro-latest"
    "models/gemini-2.5-flash"
]

model = None
for model_name in MODEL_OPTIONS:
    try:
        model = genai.GenerativeModel(model_name)
        # Test the model with a simple request
        test_response = model.generate_content("test")
        print(f"Using model: {model_name}")
        break
    except Exception as e:
        print(f"Model {model_name} failed: {e}")
        continue

if model is None:
    print("All Gemini models failed. Using fallback.")
    model = genai.GenerativeModel("models/gemini-1.0-pro")  # Fallback


def check_text(text):
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            prompt = f"""
You are a strict child-safety AI moderator.

Analyze this text and evaluate each category independently:
1. Language & Tone - Is the language appropriate and tone respectful? (no slurs, hate speech, aggressive language)
2. Content Appropriateness - Is the content suitable for children? (no violence, drugs, sexual references)
3. Kindness - Is the message kind and non-bullying? (no insults, threats, harassment)

Text: {text}

Return ONLY valid JSON with boolean values (true = safe, false = unsafe):
{{
  "language_and_tone": true/false,
  "content_appropriateness": true/false,
  "kindness": true/false
}}
"""

            response = model.generate_content(prompt)

            output = response.text.strip()

            # clean possible markdown
            output = output.replace("```json", "").replace("```", "").strip()

            result = json.loads(output)

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
                    print("AI quota exceeded, using toxicity backup...")
                    from .toxicity_backup import check_toxicity
                    return check_toxicity(text)
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