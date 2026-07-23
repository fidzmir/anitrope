import asyncio
from services.mal_service import MALService
from services.ai_service import AIService

async def test():
    ai = AIService()
    mal = MALService()
    
    prompt = "anime action balas dendam dengan latar belakang viking"
    parse = ai._smart_fallback_parse(prompt, "anime")
    print("Parsed Keywords:", parse.keywords)
    print("Target Tropes:", parse.target_tropes)
    
    candidates = await mal.fetch_candidates(
        keywords=parse.keywords,
        type_str="anime",
        limit=25
    )
    print(f"Total Candidates Fetched: {len(candidates)}")
    print("\nTop Candidates Fetched:")
    for c in candidates[:10]:
        t = c['title'].encode('ascii', 'ignore').decode('ascii')
        score = c.get('score') or c.get('anilist_score') or 'N/A'
        print(f"- {t} | Score: {score} | Source: {c.get('source')}")

if __name__ == "__main__":
    asyncio.run(test())
