import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        query = """
        query ($search: String, $type: MediaType) {
          Page(page: 1, perPage: 5) {
            media(search: $search, type: $type, isAdult: false) {
              id
              idMal
              title {
                english
                romaji
              }
              coverImage { large }
              description(asHtml: false)
              averageScore
              episodes
              status
              genres
              tags { name rank }
            }
          }
        }
        """
        terms = ["Nanatsu no Taizai", "Rurouni Kenshin", "The Rising of the Shield Hero"]
        for t in terms:
            res = await client.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": t, "type": "ANIME"}})
            print(f"Term: '{t}' -> Status: {res.status_code}")
            if res.status_code == 200:
                data = res.json().get("data", {}).get("Page", {}).get("media", [])
                print("  Titles:", [x.get("title") for x in data[:3]])
            else:
                print("  Err:", res.text[:200])
            await asyncio.sleep(0.7)

if __name__ == "__main__":
    asyncio.run(test())
