import asyncio
import logging
from services.mal_service import MALService
from services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_suite")

async def test_dynamic_scenarios():
    mal_service = MALService()
    ai_service = AIService()

    test_queries = [
        "anime yang mc nya kaya raya dan menghambur hamburkan uang",
        "anime tentang karakter yang bisa melihat hantu dan roh disekitarnya",
        "anime tentang mc yang pura-pura bodoh padahal sebenarnya genius adu otak",
        "anime dimana mc nya dikhianati dan dibuang lalu balik untuk balas dendam",
        "anime perjalanan waktu time loop untuk menyelamatkan seseorang",
        "anime tentang mc yang bikin kerajaan sendiri di dunia lain",
        "anime romantis dimana karakter utamanya pura-pura pacaran",
        "anime sekolah dimana murid-muridnya bertarung pakai pikiran dan judi",
        "anime tentang dokter atau ahli obat yang masuk ke dunia fantasi",
        "anime dimana karakter utamanya menjadi bos mafia atau komplotan kejahatan",
        "anime olahraga tentang sepak bola dengan persaingan ketat",
        "anime tentang detektif yang memecahkan kasus pembunuhan misterius",
        "anime tentang karakter yang terjebak di dalam game virtual reality",
        "anime band musik dimana anggotanya pemalu tapi jago main gitar",
        "anime yang karakter karakternya mereprentasikan tujuh dosa besar manusia"
    ]

    print("\n" + "=" * 90)
    print("STARTING DYNAMIC USER TESTING SUITE (15 SCENARIOS)")
    print("=" * 90)

    success_count = 0

    for i, prompt in enumerate(test_queries, 1):
        print(f"\n[{i}/15] TEST USER PROMPT: '{prompt}'")
        
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

    print("\n" + "=" * 90)
    print(f"TEST SUITE SUMMARY: {success_count}/15 SCENARIOS PASSED ({round(success_count/15*100)}% SUCCESS RATE)")
    print("=" * 90)

if __name__ == "__main__":
    asyncio.run(test_dynamic_scenarios())
