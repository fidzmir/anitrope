import httpx

url = 'https://graphql.anilist.co'

query_search = """
query ($search: String) {
  Page(page: 1, perPage: 5) {
    media(search: $search, type: ANIME, sort: [POPULARITY_DESC]) {
      id
      title {
        english
        romaji
      }
    }
  }
}
"""

query_popular = """
query {
  Page(page: 1, perPage: 10) {
    media(type: ANIME, sort: [POPULARITY_DESC]) {
      id
      title {
        english
        romaji
      }
    }
  }
}
"""

res_multi = httpx.post(url, json={'query': query_search, 'variables': {'search': 'comedy action'}})
print('Search "comedy action":', res_multi.json().get('data', {}).get('Page', {}).get('media'))

res_single = httpx.post(url, json={'query': query_search, 'variables': {'search': 'comedy'}})
print('\nSearch "comedy":', [m['title'] for m in res_single.json().get('data', {}).get('Page', {}).get('media', [])])

res_pop = httpx.post(url, json={'query': query_popular})
print('\nPopular AniList Anime:', [m['title'] for m in res_pop.json().get('data', {}).get('Page', {}).get('media', [])])
