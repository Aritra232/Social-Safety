from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    models = client.models.list()
    print("Available Gemini models for your API key:")
    print("=" * 50)

    for model in models:
        print(f"Model: {model.name}")
        print(f"Description: {model.description}")
        print("-" * 30)

except Exception as e:
    print(f"Error: {e}")