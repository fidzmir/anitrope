import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

async def test_comparison():
    if not api_key:
        print("GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    prompt_text = "Cari anime romantis yang cowoknya gak peka tapi endingnya gak gantung"

    # Option A: User's Proposed Tropedia System Prompt (Unstructured/Pure Text)
    tropedia_prompt = """
    Kamu adalah AI Pakar Anime yang memiliki pengetahuan seluas ensiklopedia Tropedia (tropedia.fandom.com) dan TVTropes.
    Tugas utamamu adalah mendeteksi trope/klise cerita dari bahasa santai pengguna, lalu memetakannya ke kategori trope standar Tropedia (contoh: Dense Protagonist, Business Isekai, Tsundere, Truck-kun, Satisfying Ending).
    Selalu analisa kueri pengguna berdasarkan logika Tropedia ini.
    """

    print("=========================================================================")
    print("TESTING OPTION A: User Tropedia Persona Prompt (Raw Output)")
    print("=========================================================================")
    try:
        res_a = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=tropedia_prompt,
                temperature=0.1
            )
        )
        print("Response Option A:\n", res_a.text)
    except Exception as e:
        print("Option A Error:", e)

    # Option B: Integrated Tropedia Persona + Structured JSON (Our Hybrid System)
    print("\n=========================================================================")
    print("TESTING OPTION B: Integrated Tropedia Persona + Structured JSON Schema")
    print("=========================================================================")
    structured_system = """
    You are an elite Anime/Manga AI Expert with deep knowledge of TVTropes and Tropedia (tropedia.fandom.com).
    Your task is to analyze the user's casual prompt and map it to canonical Tropedia / TVTropes concepts (e.g., 'Dense Protagonist', 'Satisfying Ending', 'Romance').
    Output strictly as JSON containing:
    - media_type: 'anime' or 'manga'
    - keywords: 1-4 English search terms for MyAnimeList API
    - target_tropes: list of canonical TVTropes concepts
    """
    try:
        res_b = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"User Prompt: '{prompt_text}'",
            config=types.GenerateContentConfig(
                system_instruction=structured_system,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        print("Response Option B (JSON):\n", res_b.text)
    except Exception as e:
        print("Option B Error:", e)

if __name__ == "__main__":
    asyncio.run(test_comparison())
