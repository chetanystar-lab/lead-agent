import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Read API key and Model name from .env
api_key = os.getenv("GEMINI_API_KEY")
raw_model = os.getenv("MODEL", "gemini-3.5-flash-lite")
model_name = raw_model.strip().lower().replace(" ", "-") if raw_model else "gemini-3.5-flash-lite"

# Initialize Gemini client
client = genai.Client(api_key=api_key) if api_key else genai.Client()

# One simple call to test the Gemini connection
response = client.models.generate_content(
    model=model_name,
    contents="Say hello in one short sentence.",
)

print(response.text)
