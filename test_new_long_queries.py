import asyncio
import logging
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService
from services.mal_service import MALService

logging.basicConfig(level=logging.INFO)

async def test_new_user_scenarios():
    ai = AIService()
    mal = MALService()

    new_long_queries = [
        # Scenario 1: Solo Leveling / Shadow Monarch
        "Cari anime tentang hunter terlemah berstatus E-rank yang hampir mati di dalam dungeon ganda misterius lalu mendapatkan sistem rahasia untuk bisa menaikkan level sendiri dan memanggil tentara bayangan pemburu",
        
        # Scenario 2: Mushoku Tensei / Jobless Reincarnation
        "Cari anime tentang neet pengangguran umur 34 tahun yang mati tertabrak truk saat menyelamatkan remaja, lalu lahir kembali di dunia sihir sebagai bayi bernama Rudeus yang belajar sihir sejak kecil",

        # Scenario 3: Classroom of the Elite / Ayanokouji Manipulation
        "Cari anime sekolah elit khusus pemerintah di mana murid-muridnya diberi poin bulanan untuk belanja, tapi MC-nya sengaja menyembunyikan kejeniusannya dan memanipulasi teman-temannya dari belakang layar agar kelas D bisa naik ke kelas A",

        # Scenario 4: Chainsaw Man / Pochita
        "Cari anime tentang pemuda miskin yang terlilit utang yakuza lalu menyatu dengan iblis gergaji mesin peliharaannya untuk menjadi pemburu iblis pemerintah keselamatan publik",

        # Scenario 5: Bleach / Shinigami Substitute
        "Cari anime tentang remaja SMA yang bisa melihat hantu lalu mendadak mendapatkan kekuatan dewa kematian shinigami dari seorang gadis pedang untuk melindungi keluarganya dari serangan makhluk monster hollow",

        # Scenario 6: No Game No Life / Blank Disarmed World
        "Cari anime tentang dua bersaudara gamer jenius tak terkalahkan yang dipanggil oleh dewa ke dunia fantasi di mana semua perselisihan dan konflik antar ras diselesaikan melalui permainan dan game tanpa kekerasan",

        # Scenario 7: Dr. Stone / Science Civilization Rebuild
        "Cari anime tentang jenius sains yang bangkit dari pembekuan batu setelah ribuan tahun di bumi pasca-apokaliptik dan berusaha membangun kembali peradaban manusia dari nol menggunakan kekuatan ilmu pengetahuan fisik dan kimia",

        # Scenario 8: Oshi no Ko / Idol Reincarnation Murder Mystery
        "Cari anime tentang seorang dokter yang terbunuh lalu bereinkarnasi menjadi anak kembar dari idol terkenal kesayangannya, lalu berusaha mengungkap misteri pembunuhan ibunya di dunia industri hiburan",

        # Scenario 9: Code Geass / Absolute Command Rebel Zero
        "Cari anime tentang pangeran terbuang yang mendapatkan kekuatan mata misterius untuk memerintah siapa saja agar mematuhi perintahnya, lalu memimpin pemberontakan bertopeng sebagai Zero melawan kekaisaran adidaya",

        # Scenario 10: Initial D / Mountain Tofu Delivery Street Racer
        "Cari anime tentang pemuda pengantar tahu di gunung yang tidak tertarik pada balapan tapi ternyata memiliki teknik mengemudi mobil tua Toyota AE86 yang sangat hebat mengalahkan pembalap liar profesional"
    ]

    print("\n==========================================================================================")
    print("NEW DYNAMIC USER TESTING SUITE - 10 LONG DETAILED SCENARIOS")
    print("==========================================================================================\n")

    success_count = 0

    for i, prompt in enumerate(new_long_queries, 1):
        print(f"[{i}/10] LONG PROMPT: '{prompt}'")
        parse_res = await ai.parse_query(prompt, default_media_type="anime")
        print(f" -> Extracted Tags: {parse_res.anilist_tags}")
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
            print(" TOP RECOMMENDATIONS:")
            for cand in top_candidates:
                t = cand.get("title")
                ms = cand.get("match_score", 0)
                reason = evaluations.get(t.lower().strip()).why_it_matches if evaluations.get(t.lower().strip()) else "N/A"
                print(f"   * [{t}] (Match Score: {ms}%)")
                print(f"     Reasoning: {reason[:120]}...")
        else:
            print("  [FAIL] 0 Candidates Fetched!")
        print("\n")

    print("==========================================================================================")
    print(f"NEW LONG DESCRIPTION TEST SUMMARY: {success_count}/10 SCENARIOS PASSED ({round(success_count/10*100)}% SUCCESS RATE)")
    print("==========================================================================================\n")

if __name__ == "__main__":
    asyncio.run(test_new_user_scenarios())
