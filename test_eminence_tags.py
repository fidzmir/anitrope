import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        res = await client.post('https://graphql.anilist.co', json={'query': '''
        query {
          eminence: Media(search: "Eminence in Shadow", type: ANIME) {
            title { english romaji }
            tags { name category }
          }
          mahouka: Media(search: "Mahouka Koukou no Rettousei", type: ANIME) {
            title { english romaji }
            tags { name category }
          }
        }
        '''})
        if res.status_code == 200:
            data = res.json()['data']
            print('Eminence Tags:', [(t['name'], t['category']) for t in data['eminence']['tags']])
            print('\nMahouka Tags:', [(t['name'], t['category']) for t in data['mahouka']['tags']])

asyncio.run(test())
