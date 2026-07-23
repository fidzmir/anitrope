import asyncio
import httpx

query = """
query ($type: MediaType, $tag_in: [String], $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: $type, tag_in: $tag_in, sort: [POPULARITY_DESC]) {
      id
      title { romaji english }
      tags { name }
    }
  }
}
"""

async def test():
    async with httpx.AsyncClient() as client:
        tags = ["Person in Hiding", "Secret Identity", "Overpowered", "Chuunibyou"]
        for t in tags:
            res = await client.post('https://graphql.anilist.co', json={'query': query, 'variables': {'type': 'ANIME', 'tag_in': [t], 'page': 1, 'perPage': 5}})
            if res.status_code == 200:
                items = res.json()['data']['Page']['media']
                print(f"Tag '{t}' returned {len(items)} items:")
                for m in items:
                    print('  -', m['title'].get('english') or m['title'].get('romaji'))

asyncio.run(test())
