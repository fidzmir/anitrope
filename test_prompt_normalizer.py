import asyncio
from services.ai_service import AIService

TEST_PROMPTS = [
    # 1. Typo in Indonesian prompt
    "anime dnegan kesedihan yang berturut turut tapi ending nya good",
    # 2. Slang & abbreviations
    "anime mc nya op banget ga ada obat",
    # 3. Specific phrase
    "anime adik kaka kekuatan alkimia",
    # 4. Pirate King prompt
    "anime bajak laut mau jadi raja bajak laut",
    # 5. Death Note prompt
    "anime tentang dewa kematian dan buku catatan misterius",
    # 6. Typo in Orphanage
    "anime mc pante asuhan ga punya skill",
    # 7. English typo & slang
    "anime with op mc that is actually a demon king in disguis",
    # 8. Spanish query
    "anime de romance en la escuela con un protagonista frio",
    # 9. Japanese Romaji query
    "isekai mecha anime de saikou no protagonist",
]

async def test_all_prompts():
    ai = AIService()
    print("=== TESTING PROMPT PARSER & NORMALIZER ===\n")
    for prompt in TEST_PROMPTS:
        res = await ai.parse_query(prompt, "anime")
        print(f"INPUT : '{prompt}'")
        print(f"PARSED: Keywords = {res.keywords} | Tropes = {res.target_tropes[:3]}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_prompts())
