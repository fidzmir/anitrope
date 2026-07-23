import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        terms = ["Nanatsu no Taizai", "Fullmetal Alchemist", "Rurouni Kenshin"]
        for t in terms:
            url = f"https://api.jikan.moe/v4/anime?q={t}&limit=5"
            res = await client.get(url)
            print(f"Term: '{t}' -> Status: {res.status_code}")
            if res.status_code == 200:
                data = res.json().get("data", [])
                print("  Titles:", [x.get("title") for x in data[:3]])
            else:
                print("  Response text:", res.text[:200])
            await asyncio.sleep(1.2)

if __name__ == "__main__":
    asyncio.run(test())
