from google import genai
from config.settings import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

print("Modelos disponibles para tu API Key:")
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(f"- {model.name}")