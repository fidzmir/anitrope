import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        query = """
        query ($search: String, $type: MediaType) {
          Page(page: 1, perPage: 5) {
            media(search: $search, type: $type, isAdult: false) {
              id
              title {
                romaji
                english
              }
            }
          }
        }
        """
        res = await client.post("https://graphql.anilist.co", json={"query": query, "variables": {"search": "Nanatsu no Taizai", "type": "ANIME"}})
        print("Status:", res.status_code)
        print("Data:", res.json())

if __name__ == "__main__":
    asyncio.run(test())
