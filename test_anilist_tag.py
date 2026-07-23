import asyncio
import httpx

query_tag_in = """
query ($type: MediaType, $tag_in: [String], $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: $type, tag_in: $tag_in, sort: [POPULARITY_DESC]) {
      id
      title { romaji english }
    }
  }
}
"""

query_tag = """
query ($type: MediaType, $tag: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: $type, tag: $tag, sort: [POPULARITY_DESC]) {
      id
      title { romaji english }
    }
  }
}
"""

async def test():
    async with httpx.AsyncClient() as client:
        res1 = await client.post('https://graphql.anilist.co', json={'query': query_tag_in, 'variables': {'type': 'ANIME', 'tag_in': ['Secret Identity'], 'page': 1, 'perPage': 5}})
        print('tag_in Status:', res1.status_code)
        if res1.status_code == 200:
            items = res1.json()['data']['Page']['media']
            print(f'tag_in items count: {len(items)}')
            for m in items:
                print('  -', m['title'].get('english') or m['title'].get('romaji'))

        res2 = await client.post('https://graphql.anilist.co', json={'query': query_tag, 'variables': {'type': 'ANIME', 'tag': 'Secret Identity', 'page': 1, 'perPage': 5}})
        print('tag Status:', res2.status_code)
        if res2.status_code == 200:
            items = res2.json()['data']['Page']['media']
            print(f'tag items count: {len(items)}')
            for m in items:
                print('  -', m['title'].get('english') or m['title'].get('romaji'))

asyncio.run(test())
