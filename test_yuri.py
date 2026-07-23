import httpx
from deep_translator import GoogleTranslator

prompt = 'yuri with big boobs'
translated = GoogleTranslator(source='auto', target='en').translate(prompt)
print('Translated:', translated)

headers = {'X-MAL-CLIENT-ID': '2bddf3a94b3a97b4c78b8657dd063240'}
fields = 'id,title,main_picture,synopsis,mean,genres'

# Fetch search results for yuri on MAL
res_search = httpx.get('https://api.myanimelist.net/v2/anime', params={'q': 'yuri', 'limit': 15, 'fields': fields}, headers=headers)
items_search = [e['node'] for e in res_search.json().get('data', [])]
print('MAL Yuri Search Count:', len(items_search))
for item in items_search[:5]:
    genres = [g['name'] for g in item.get('genres', [])]
    t = item.get('title', '').encode('ascii', 'ignore').decode('ascii')
    print(f"- {t} | Score: {item.get('mean')} | Genres: {genres}")

# Query AniList GraphQL for yuri
query_anilist = """
query ($search: String) {
  Page(page: 1, perPage: 25) {
    media(search: $search, type: ANIME, sort: [POPULARITY_DESC]) {
      id
      idMal
      title { english romaji }
      description(asHtml: false)
      averageScore
      genres
      tags { name rank }
      siteUrl
    }
  }
}
"""
res_al = httpx.post('https://graphql.anilist.co', json={'query': query_anilist, 'variables': {'search': 'yuri'}})
al_items = res_al.json().get('data', {}).get('Page', {}).get('media', [])
print('\nAniList Yuri Items Count:', len(al_items))
for item in al_items[:5]:
    tags = [t['name'] for t in item.get('tags', [])[:5]]
    title = (item['title']['romaji'] or '').encode('ascii', 'ignore').decode('ascii')
    print(f"- {title} | Genres: {item['genres']} | Tags: {tags}")
