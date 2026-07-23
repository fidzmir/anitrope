import asyncio
import logging
import sys

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService
from services.mal_service import MALService

logging.basicConfig(level=logging.INFO)

async def test_hiding_power_user_query():
    ai = AIService()
    mal = MALService()

    prompt = "Cari anime fantasi dengan MC super kuat tapi sengaja menyembunyikan kekuatannya dari teman-temannya."

    print("\n==========================================================================================")
    print(f"USER FEEDBACK QUERY TEST: '{prompt}'")
    print("==========================================================================================\n")

    parse_res = await ai.parse_query(prompt, default_media_type="anime")
    print(f" -> Extracted Tags: {parse_res.anilist_tags}")
    print(f" -> Extracted Genres: {parse_res.genres}")
    print(f" -> Clean Search KW: '{parse_res.clean_keyword}'")

    candidates = await mal.fetch_candidates(
        keywords=parse_res.keywords,
        type_str="anime",
        limit=15,
        anilist_tags=parse_res.anilist_tags,
        genres=parse_res.genres,
        target_tropes=parse_res.target_tropes,
        clean_keyword=parse_res.clean_keyword
    )
    print(f" -> Candidates Fetched: {len(candidates)}")

    evaluations = await ai.rerank_and_explain(
        user_prompt=prompt,
        target_tropes=parse_res.target_tropes,
        exclude_tropes=[],
        candidates=candidates
    )

    print("\n TOP MATCHES RETURNED TO USER:")
    for i, cand in enumerate(candidates[:5], 1):
        t = cand.get("title")
        ms = cand.get("match_score", 0)
        reason = evaluations.get(t.lower().strip()).why_it_matches if evaluations.get(t.lower().strip()) else "N/A"
        print(f"   {i}. [{t}] (Match Score: {ms}%)")
        print(f"      Reasoning: {reason[:120]}...\n")

if __name__ == "__main__":
    asyncio.run(test_hiding_power_user_query())
