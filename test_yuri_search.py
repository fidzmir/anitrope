import httpx

res = httpx.post('http://127.0.0.1:8000/api/search', json={'prompt': 'yuri with big boobs', 'media_type': 'anime'}, timeout=30.0)
print("Status Code:", res.status_code)
if res.status_code != 200:
    print("Response text:", res.text)
else:
    data = res.json()
    results = data['results']
    print(f"Total Items Returned: {len(results)}")
    print("\nTop Returned Anime for 'yuri with big boobs':")
    for r in results[:10]:
        t = r['title'].encode('ascii', 'ignore').decode('ascii')
        score_mal = r.get('score') or 'N/A'
        score_al = r.get('anilist_score') or 'N/A'
        tags = r.get('tags', [])[:4]
        print(f"- {t} | Match: {r.get('match_score')}% | MAL: {score_mal} | AL: {score_al} | Tags: {tags}")
