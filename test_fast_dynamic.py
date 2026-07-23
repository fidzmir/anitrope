import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8')

from services.ai_service import AIService

async def test_fast_parsing():
    ai = AIService()

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

    print("\n" + "="*80)
    print("FAST PARSING & CONCEPT EXTRACTION EVALUATION")
    print("="*80 + "\n")

    for i, q in enumerate(user_queries, 1):
        res = await ai.parse_query(q)
        print(f"[{i}] PROMPT: '{q}'")
        print(f"    Tags: {res.anilist_tags}")
        print(f"    Genres: {res.genres}")
        print(f"    Clean KW: '{res.clean_keyword}'")
        print(f"    Keywords: {res.keywords}\n")

if __name__ == "__main__":
    asyncio.run(test_fast_parsing())
