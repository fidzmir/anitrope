import httpx

prompt = "anime yang osis dan si cewe dan cowo nya tuh suka berantem tetapi mereka itu saling suka"
res = httpx.post('http://127.0.0.1:8000/api/search', json={'prompt': prompt, 'media_type': 'anime'}, timeout=30.0)
print("Status Code:", res.status_code)
if res.status_code == 200:
    data = res.json()
    results = data['results']
    print(f"Total Items Returned: {len(results)}")
    print("\nSearch Results (Strictly Sorted by Rating Score High to Low):")
    for r in results:
        t = r['title'].encode('ascii', 'ignore').decode('ascii')
        score_mal = r.get('score') or 'N/A'
        score_al = r.get('anilist_score') or 'N/A'
        print(f"- {t} | MAL: {score_mal} | AL: {score_al}")
