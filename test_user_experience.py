import asyncio
import logging
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService
from services.mal_service import MALService

logging.getLogger("httpx").setLevel(logging.WARNING)

async def test_user_queries():
    ai = AIService()
    mal = MALService()

    queries = [
        "anime yang karakter karakternya mereprentasikan tujuh dosa besar manusia",
        "anime pahlawan yang di panggil ke dunia lain dan menjadi sosok yang sangat kuat",
        "dulunya pembunuh bayaran tetapi kemudian berubah menjadi baik"
    ]

    for q in queries:
        print("\n" + "="*80)
        print(f"USER PROMPT: '{q}'")
        parse_res = await ai.parse_query(q)
        print(f"-> Extracted Tags: {parse_res.anilist_tags}")
        print(f"-> Search Keyword: '{parse_res.clean_keyword}'")

        candidates = await mal.fetch_candidates(
            keywords=parse_res.keywords,
            target_tropes=parse_res.target_tropes,
            anilist_tags=parse_res.anilist_tags,
            genres=parse_res.genres,
            clean_keyword=parse_res.clean_keyword,
            type_str="anime"
        )
        print(f"Total Candidates Fetched: {len(candidates)}")

        evals = await ai.rerank_and_explain(
            user_prompt=q,
            target_tropes=parse_res.target_tropes,
            exclude_tropes=[],
            candidates=candidates
        )

        scored_items = []
        for c in candidates:
            mal_id = c.get("mal_id")
            anilist_id = c.get("anilist_id")
            title_key = c.get("title", "").lower().strip()
            clean_t = re.sub(r'[^a-zA-Z0-9\s]', '', title_key).strip()

            ev = evals.get(title_key) or evals.get(clean_t) or (evals.get(mal_id) if mal_id else None) or (evals.get(anilist_id) if anilist_id else None)
            
            if not ev:
                for k, val in evals.items():
                    if isinstance(k, str) and len(k) >= 4 and (k in title_key or title_key in k):
                        ev = val
                        break

            score = ev.match_score if ev else 0
            why = ev.why_it_matches if ev else "No reasoning"
            if score > 0:
                scored_items.append((score, c.get("title"), why))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        print("\nTOP 5 AI RECOMMENDATIONS & REASONING:")
        for score, title, why in scored_items[:5]:
            print(f"  [Score {score}] {title}")
            print(f"   Reasoning: {why}\n")

if __name__ == "__main__":
    asyncio.run(test_user_queries())
