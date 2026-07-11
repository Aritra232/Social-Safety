import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    models = client.models.list()
    print("Available OpenAI models for your API key:")
    print("=" * 50)

    for model in models:
        print(f"Model: {model.id}")
        print("-" * 30)

except Exception as e:
    print(f"Error: {e}")