import httpx

prompt = "anime action balas dendam dengan latar belakang viking"
res = httpx.post('http://127.0.0.1:8000/api/search', json={'prompt': prompt, 'media_type': 'anime'}, timeout=30.0)
print("Search Status Code:", res.status_code)
if res.status_code == 200:
    data = res.json()
    results = data['results']
    print(f"Total Results: {len(results)}")
    print("\nTop 5 Results:")
    for r in results[:5]:
        t = r['title'].encode('ascii', 'ignore').decode('ascii')
        match = r.get('match_score')
        score = r.get('score') or r.get('anilist_score')
        print(f"- [{match}% Match] {t} | Rating: {score}")
