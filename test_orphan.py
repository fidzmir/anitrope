import asyncio
from services.mal_service import MALService
from services.ai_service import AIService

async def test_orphan_search():
    ai = AIService()
    mal = MALService()
    prompt = 'anime yang mc nya anak asuh dari panti asuhan dan tidak mempunyai skill tetapi menjadi kuat'
    parsed = await ai.parse_query(prompt, 'anime')
    print('Parsed Keywords:', parsed.keywords)
    candidates = await mal.fetch_candidates(parsed.keywords, 'anime', limit=8)
    print('\nTop Candidates:')
    for c in candidates:
        tags_str = ", ".join(c.get('tags', [])[:3])
        print(f"- {c['title']} (Score Rank: {c.get('score_rank')}, Tags: {tags_str})")

if __name__ == "__main__":
    asyncio.run(test_orphan_search())
