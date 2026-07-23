import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing API Key: {api_key[:15]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key
}

payload = {
    "contents": [
        {
            "parts": [
                {"text": "Hello! Reply with 'OK' if authentication is successful."}
            ]
        }
    ]
}

res = httpx.post(url, headers=headers, json=payload, timeout=10.0)
print(f"Status Code: {res.status_code}")
print(f"Response: {res.text[:300]}")
