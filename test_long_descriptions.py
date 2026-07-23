import asyncio
import logging
from services.mal_service import MALService
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_long_suite")

async def test_long_description_scenarios():
    mal_service = MALService()
    ai_service = AIService()

    long_queries = [
        # Scenario 1: Crossdressing / All Boys Dorm Twin Disguise (User's Exact Query)
        "anime skolah yang di asramanya cowo semua tetapi ada satu orang yang nyamar sebagai cewe sebagai kembaran salah satu cowo",
        
        # Scenario 2: Villainess Reincarnation in Otome Game
        "anime dimana karakter utamanya meninggal lalu masuk ke dalam game otome sebagai karakter penjahat wanita yang ditakdirkan mati dan mencoba bertahan hidup",
        
        # Scenario 3: Undercover Spy / Fake Family
        "anime tentang mata-mata yang membentuk keluarga palsu dengan anak yang bisa membaca pikiran dan istri seorang pembunuh bayaran",
        
        # Scenario 4: Time Loop / Save Girl from Accident
        "anime di mana mc terlempar kembali ke masa lalu saat masih SMP untuk menyelamatkan pacar pertamanya yang tewas tertabrak truk",
        
        # Scenario 5: Otaku Programmer Reincarnated as Mecha Pilot
        "anime tentang programmer otaku robot yang meninggal lalu bereinkarnasi ke dunia sihir dan merancang robot mecha sendiri",
        
        # Scenario 6: Demon Lord Working at Fast Food Restaurant
        "anime tentang raja iblis dari dunia lain yang terdampar di bumi modern dan terpaksa bekerja paruh waktu di restoran cepat saji",
        
        # Scenario 7: MMORPG Guild Leader Stuck with Loyal Monsters
        "anime tentang pemain game online terkuat yang terjebak bersama kastil dan seluruh bawahan monster yang sangat setia kepadanya",
        
        # Scenario 8: Retired Hero Slow Life in Countryside
        "anime pahlawan terkuat setelah mengalahkan musuh memilih pensiun dan hidup tenang di desa sebagai petani atau pedagang",
        
        # Scenario 9: Immortal Being Learning Human Emotions over Centuries
        "anime tentang makhluk abadi yang tidak punya perasaan belajar tentang kehidupan dan emosi manusia melalui perjalanan panjang ratusan tahun",
        
        # Scenario 10: High School Boarding School Secret Relationship Between Enemy Countries
        "anime sekolah berasrama di mana dua ketua dari dua negara bermusuhan berpura-pura saling benci tapi sebenarnya diam-diam pacaran"
    ]

    print("\n" + "=" * 95)
    print("STARTING DYNAMIC TESTING SUITE FOR LONG, DETAILED DESCRIPTIONS (10 SCENARIOS)")
    print("=" * 95)

    success_count = 0

    for i, prompt in enumerate(long_queries, 1):
        print(f"\n[{i}/10] LONG PROMPT: '{prompt}'")
        
        # Step 1: Concept Parsing
        parse_res = await ai_service.parse_query(prompt, default_media_type="anime")
        print(f" -> Extracted Tags: {parse_res.anilist_tags}")
        print(f" -> Clean Search KW: '{parse_res.clean_keyword}'")

        # Step 2: Fetch Candidates
        candidates = await mal_service.fetch_candidates(
            keywords=parse_res.keywords,
            type_str="anime",
            limit=15,
            anilist_tags=parse_res.anilist_tags,
            genres=parse_res.genres,
            target_tropes=parse_res.target_tropes,
            clean_keyword=parse_res.clean_keyword
        )
        print(f" -> Candidates Fetched: {len(candidates)}")

        # Step 3: Local Reasoning Evaluation
        evaluations = await ai_service.rerank_and_explain(
            user_prompt=prompt,
            target_tropes=parse_res.target_tropes,
            exclude_tropes=[],
            candidates=candidates
        )

        top_candidates = candidates[:3]
        if top_candidates:
            success_count += 1
            print(" TOP RECOMMENDATIONS:")
            for cand in top_candidates:
                t = cand.get("title")
                ms = cand.get("match_score", 0)
                reason = evaluations.get(t.lower().strip()).why_it_matches if evaluations.get(t.lower().strip()) else "N/A"
                print(f"   * [{t}] (Match Score: {ms}%)")
                print(f"     Reasoning: {reason[:120]}...")
        else:
            print("  [FAIL] 0 Candidates Fetched!")

    print("\n" + "=" * 95)
    print(f"LONG DESCRIPTION TEST SUMMARY: {success_count}/10 SCENARIOS PASSED ({round(success_count/10*100)}% SUCCESS RATE)")
    print("=" * 95)

if __name__ == "__main__":
    asyncio.run(test_long_description_scenarios())
