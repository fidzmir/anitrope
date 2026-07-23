import asyncio
import httpx

query_tag_in = """
query ($type: MediaType, $tag_in: [String]) {
  Page(page: 1, perPage: 10) {
    media(type: $type, tag_in: $tag_in, sort: [POPULARITY_DESC]) {
      id
      title { romaji english }
    }
  }
}
"""

async def test():
    async with httpx.AsyncClient() as client:
        res = await client.post('https://graphql.anilist.co', json={'query': query_tag_in, 'variables': {'type': 'ANIME', 'tag_in': ['Anti-Hero', 'Assassins']}})
        print('Status:', res.status_code)
        if res.status_code == 200:
            items = res.json()['data']['Page']['media']
            print(f'tag_in items count: {len(items)}')
            for m in items:
                print('  -', m['title'].get('english') or m['title'].get('romaji'))

asyncio.run(test())
