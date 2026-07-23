import asyncio
from services.anilist_service import AniListService

async def test_anilist():
    service = AniListService()
    results = await service.fetch_candidates(['comedy', 'action'], 'anime', limit=10)
    print(f"AniList candidates count: {len(results)}")
    for r in results[:5]:
        print(f"- {r['title']} | Score: {r['anilist_score']} | URL: {r['anilist_url']} | Tags: {r[:3] if isinstance(r, list) else r.get('tags', [])[:3]}")

if __name__ == "__main__":
    asyncio.run(test_anilist())
