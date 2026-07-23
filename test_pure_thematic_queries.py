import asyncio
import logging
import sys

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService
from services.mal_service import MALService

logging.basicConfig(level=logging.INFO)

async def test_pure_thematic_scenarios():
    ai = AIService()
    mal = MALService()

    # 10 Purely Thematic / Non-Title-Specific Descriptions
    thematic_queries = [
        # Skenario 1: Romantis dense protagonist & salah paham
        "cari anime romantis tentang karakter cowo yang sangat tidak peka terhadap perasaan cewe di sekitarnya dan sering terjadi salah paham kocak",
        
        # Skenario 2: MC menyembunyikan kekuatan super overpowered
        "cari anime isekai di mana karakter utamanya sengaja berpura-pura lemah dan rakyat biasa padahal punya kekuatan sihir paling kuat tak tertandingi",

        # Skenario 3: Anti-hero membalas dendam
        "cari anime aksi tentang karakter utama anti-hero yang dikhianati oleh teman atau organisasinya lalu merencanakan pembalasan dendam yang kejam",

        # Skenario 4: Misteri pembunuhan & detektif
        "cari anime misteri teka-teki pembunuhan berantai yang menegangkan di mana detektifnya mencoba memecahkan kasus-kasus rumit",

        # Skenario 5: Olahraga & perjuangan tim bawah
        "cari anime olahraga tentang tim underdog yang awalnya diremehkan tapi berlatih keras hingga bisa mengikuti kejuaraan tingkat nasional",

        # Skenario 6: Slice of life kuliner & memasak
        "cari anime santai tentang memasak dan kuliner di mana setiap episode memperlihatkan makanan lezat yang membuat menggugah selera",

        # Skenario 7: Peperangan militer & taktik strategi
        "cari anime sejarah peperangan militer antar kerajaan di mana pemimpinnya menggunakan taktik strategi cerdas untuk menangkap benteng musuh",

        # Skenario 8: Komedi persahabatan anak sekolah
        "cari anime komedi sekolah yang sangat lucu menceritakan tingkah konyol sekelompok sahabat dalam kehidupan sehari-hari",

        # Skenario 9: Horor gaib & hantu
        "cari anime horor menyeramkan tentang orang yang bisa melihat makhluk halus gaib di sekitarnya dan berusaha bertahan hidup",

        # Skenario 10: Perjalanan fantasi & eksplorasi dunia
        "cari anime petualangan fantasi tentang perjalanan menjelajahi dunia luas yang indah bersama teman-teman baru"
    ]

    print("\n==========================================================================================")
    print("PURE THEMATIC & NON-TITLE SPECIFIC USER TEST SUITE (10 SCENARIOS)")
    print("==========================================================================================\n")

    success_count = 0

    for i, prompt in enumerate(thematic_queries, 1):
        print(f"[{i}/10] THEMATIC PROMPT: '{prompt}'")
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

        top_candidates = candidates[:3]
        if top_candidates:
            success_count += 1
            print(" TOP MATCHING ANIME FOR USER:")
            for cand in top_candidates:
                t = cand.get("title")
                ms = cand.get("match_score", 0)
                reason = evaluations.get(t.lower().strip()).why_it_matches if evaluations.get(t.lower().strip()) else "N/A"
                print(f"   * [{t}] (Match Score: {ms}%)")
                print(f"     Reasoning: {reason[:110]}...")
        else:
            print("  [FAIL] 0 Candidates Fetched!")
        print("\n")

    print("==========================================================================================")
    print(f"THEMATIC TEST SUMMARY: {success_count}/10 SCENARIOS PASSED ({round(success_count/10*100)}% SUCCESS RATE)")
    print("==========================================================================================\n")

if __name__ == "__main__":
    asyncio.run(test_pure_thematic_scenarios())
