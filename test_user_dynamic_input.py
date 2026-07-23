import asyncio
import logging
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService
from services.mal_service import MALService

logging.basicConfig(level=logging.WARNING)

async def test_dynamic_user_queries():
    ai = AIService()
    mal = MALService()

    # User-like dynamic, non-short test descriptions
    user_queries = [
        # Query 1: Crossdressing twin in all-boys dormitory
        "anime skolah yang di asramanya cowo semua tetapi ada satu orang yang nyamar sebagai cewe sebagai kembaran salah satu cowo",
        
        # Query 2: Reincarnated as Otome Game Villainess
        "anime dimana karakter utamanya meninggal lalu masuk ke dalam game otome sebagai karakter penjahat wanita yang ditakdirkan mati dan mencoba bertahan hidup",

        # Query 3: Spy forming fake family
        "anime tentang mata-mata yang membentuk keluarga palsu dengan anak yang bisa membaca pikiran dan istri seorang pembunuh bayaran",

        # Query 4: Time loop save first love
        "anime di mana mc terlempar kembali ke masa lalu saat masih SMP untuk menyelamatkan pacar pertamanya yang tewas tertabrak truk",

        # Query 5: Retired hero living slow life in village
        "anime pahlawan terkuat setelah mengalahkan musuh memilih pensiun dan hidup tenang di desa sebagai petani atau pedagang",

        # Query 6: Immortal being learning human emotions
        "anime tentang makhluk abadi yang tidak punya perasaan belajar tentang kehidupan dan emosi manusia melalui perjalanan panjang ratusan tahun",

        # Query 7: Boarding school secret relationship between enemy nations
        "anime sekolah berasrama di mana dua ketua dari dua negara bermusuhan berpura-pura saling benci tapi sebenarnya diam-diam pacaran",

        # Query 8: Dense MC romance anime with good non-hanging ending
        "Cari anime romantis yang karakter utamanya tidak peka, tapi ending-nya tidak menggantung.",

        # Query 9: Pharmacist / Apothecary in ancient palace
        "anime tentang gadis ahli obat atau apoteker yang diculik dan bekerja di istana kerajaan memecahkan berbagai kasus racun dan misteri",

        # Query 10: Rich MC squandering money
        "anime yang mc nya kaya raya dan menghambur hamburkan uang untuk menyelesaikan kasus"
    ]

    print("\n==========================================================================================")
    print("TESTING DYNAMIC INPUT DESCRIPTIONS (USER SIMULATION)")
    print("==========================================================================================\n")

    for idx, query in enumerate(user_queries, 1):
        print(f"--- QUERY {idx}: '{query}' ---")
        parse_res = await ai.parse_query(query)
        print(f"Parsed Tags: {parse_res.anilist_tags}")
        print(f"Parsed Genres: {parse_res.genres}")
        print(f"Clean Keyword: '{parse_res.clean_keyword}'")
        print(f"Keywords: {parse_res.keywords}")

        candidates = await mal.fetch_candidates(
            keywords=parse_res.keywords,
            target_tropes=parse_res.target_tropes,
            anilist_tags=parse_res.anilist_tags,
            genres=parse_res.genres,
            clean_keyword=parse_res.clean_keyword,
            type_str="anime",
            limit=15
        )

        evals = await ai.rerank_and_explain(
            user_prompt=query,
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

            score = ev.match_score if ev else c.get("match_score", 0)
            why = ev.why_it_matches if ev else c.get("why_it_matches", "")
            if score > 0:
                scored_items.append((score, c.get("title"), why, c.get("genres", []), c.get("tags", [])))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        print(f"Total Candidates: {len(candidates)} | Top Recommendations:")
        for score, title, why, g, t in scored_items[:3]:
            print(f"  * [{score}%] {title}")
            print(f"    Reasoning: {why}")
            print(f"    Genres/Tags: {g[:3]} / {t[:3]}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(test_dynamic_user_queries())
