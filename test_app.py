import asyncio
import logging
from services.mal_service import MALService
from services.ai_service import AIService
from main import app
from fastapi.testclient import TestClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_app")

async def test_mal_service():
    logger.info("--- Testing MALService (Jikan API v4) ---")
    mal = MALService()
    
    # Test top anime
    top_anime = await mal.get_top_items(type_str="anime", limit=3)
    assert len(top_anime) > 0, "Top anime should return items"
    logger.info(f"Top Anime fetched: {[item['title'] for item in top_anime]}")

    # Test candidate search with trope keywords
    candidates = await mal.fetch_candidates(keywords=["merchant", "isekai"], type_str="manga", limit=3)
    assert len(candidates) > 0, "Candidates search should return items"
    logger.info(f"Candidates fetched for ['merchant', 'isekai']: {[c['title'] for c in candidates]}")
    logger.info("MALService test PASSED.")

async def test_ai_service():
    logger.info("--- Testing AIService (2-Step Strategy) ---")
    ai = AIService()

    # Step 1: Parse prompt
    prompt = "Cari anime romantis yang karakter utamanya tidak peka, tapi ending-nya tidak menggantung."
    parsed = await ai.parse_query(prompt, default_media_type="anime")
    logger.info(f"Parsed result -> Keywords: {parsed.keywords}, Target Tropes: {parsed.target_tropes}")
    assert parsed.keywords, "Parsed keywords should not be empty"

    # Step 3: Rerank mock candidates
    mock_candidates = [
        {
            "mal_id": 1,
            "title": "Toradora!",
            "genres": ["Romance", "Comedy"],
            "synopsis": "Takasu Ryuuji is a gentle high school student with a scary face..."
        }
    ]
    evals = await ai.rerank_and_explain(prompt, parsed.target_tropes, parsed.exclude_tropes, mock_candidates)
    assert 1 in evals, "Evaluation result should contain mal_id 1"
    logger.info(f"Rerank explanation: {evals[1].why_it_matches} (Score: {evals[1].match_score})")
    logger.info("AIService test PASSED.")

def test_fastapi_endpoints():
    logger.info("--- Testing FastAPI Endpoints ---")
    client = TestClient(app)

    # Test /api/health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    logger.info(f"/api/health response: {res_health.json()}")

    # Test /api/tropes
    res_tropes = client.get("/api/tropes")
    assert res_tropes.status_code == 200
    assert len(res_tropes.json()) > 0
    logger.info(f"/api/tropes response count: {len(res_tropes.json())}")

    # Test /api/featured
    res_featured = client.get("/api/featured?media_type=anime")
    assert res_featured.status_code == 200
    assert len(res_featured.json()["items"]) > 0
    logger.info(f"/api/featured count: {len(res_featured.json()['items'])}")

    logger.info("FastAPI Endpoints test PASSED.")

if __name__ == "__main__":
    asyncio.run(test_mal_service())
    asyncio.run(test_ai_service())
    test_fastapi_endpoints()
    logger.info("🎉 ALL UNIT TESTS PASSED SUCCESSFULLY!")
