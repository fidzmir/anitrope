import asyncio
from services.ai_service import AIService
from services.mal_service import MALService

async def test():
    ai = AIService()
    mal = MALService()
    
    prompt = "anime dnegan kesedihan yang berturut turut tapi ending nya good"
    parse_res = await ai.parse_query(prompt, "anime")
    print("Parsed Keywords:", parse_res.keywords)
    print("Target Tropes:", parse_res.target_tropes)

    candidates = await mal.fetch_candidates(parse_res.keywords, "anime", limit=10)
    print("\nCandidates Returned Count:", len(candidates))
    for c in candidates[:10]:
        print(f"- {c['title']} | Score Rank: {c.get('score_rank')} | Genres: {c.get('genres')} | Tags: {c.get('tags', [])[:3]}")

if __name__ == "__main__":
    asyncio.run(test())
