import asyncio
from services.mal_service import MALService
from services.ai_service import AIService

async def test():
    ai = AIService()
    mal = MALService()
    
    prompt = "Cari anime romantis yang karakter utamanya tidak peka, tapi ending-nya tidak menggantung."
    parse = ai._smart_fallback_parse(prompt, "anime")
    print("Parsed Keywords:", parse.keywords)
    print("Target Tropes:", parse.target_tropes)
    
    candidates = await mal.fetch_candidates(
        keywords=parse.keywords,
        target_tropes=parse.target_tropes,
        type_str="anime",
        limit=10
    )
    print(f"\nTotal Candidates Fetched: {len(candidates)}")
    print("\nTop Returned Anime Candidates:")
    for idx, c in enumerate(candidates[:10], 1):
        t = c['title'].encode('ascii', 'ignore').decode('ascii')
        genres = ", ".join(c.get('genres', []))
        print(f" {idx}. [{c.get('match_score')}% Match] {t} (Genres: {genres}) | Score: {c.get('score')}")

if __name__ == "__main__":
    asyncio.run(test())
