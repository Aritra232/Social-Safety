import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    models = genai.list_models()
    print("Available Gemini models for your API key:")
    print("=" * 50)

    for model in models:
        print(f"Model: {model.name}")
        print(f"Description: {model.description}")
        print(f"Supported generation methods: {model.supported_generation_methods}")
        print("-" * 30)

except Exception as e:
    print(f"Error: {e}")