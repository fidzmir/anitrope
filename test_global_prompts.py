import asyncio
from services.mal_service import MALService
from services.ai_service import AIService

TEST_PROMPTS = [
    ("anime action balas dendam dengan latar belakang viking", "anime", "Vinland Saga"),
    ("anime tentang kompetisi memasak dan koki berbakat", "anime", "Shokugeki no Souma / Food Wars"),
    ("anime detektif zaman victoria inggris di abad 19", "anime", "Black Butler / Moriarty / Gosick"),
    ("anime polisi cyborg dengan teknologi masa depan cyberpunk", "anime", "Ghost in the Shell / Cyberpunk"),
    ("manga tentang pertarungan judi dan permainan pikiran", "manga", "Kaiji / Kakegurui / Liar Game")
]

async def run_tests():
    ai = AIService()
    mal = MALService()
    
    print("=========================================================================")
    print("TESTING GLOBAL DYNAMIC CONCEPT EXTRACTOR & HYBRID SEMANTIC SCORER")
    print("=========================================================================\n")
    
    for prompt, media_type, expected in TEST_PROMPTS:
        parse = ai._smart_fallback_parse(prompt, media_type)
        print(f"PROMPT: '{prompt}' [{media_type.upper()}]")
        print(f"Extracted Keywords: {parse.keywords}")
        print(f"Target Tropes: {parse.target_tropes}")
        
        results = await mal.fetch_candidates(
            keywords=parse.keywords,
            target_tropes=parse.target_tropes,
            type_str=media_type,
            limit=5
        )
        
        print(f"Expected Title Reference: {expected}")
        print("Top 3 Returned Results:")
        for idx, item in enumerate(results[:3], 1):
            t = item['title'].encode('ascii', 'ignore').decode('ascii')
            score = item.get('score') or item.get('anilist_score') or 'N/A'
            print(f"  {idx}. [{item.get('match_score', 85)}% Match] {t} (Rating: {score})")
        print("-" * 75 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
