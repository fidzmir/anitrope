import httpx

res = httpx.post('http://127.0.0.1:8000/api/search', json={'prompt': 'komedi anime sekaligus action yang kocak', 'media_type': 'anime'})
data = res.json()
results = data['results']

print(f"Total Items Returned: {len(results)}")
print("\nTop 5 Highest Rated Items:")
for r in results[:5]:
    score_mal = r.get('score') or 'N/A'
    score_al = r.get('anilist_score') or 'N/A'
    print(f"- {r['title']} | MAL Score: {score_mal} | AL Score: {score_al}")

print("\nBottom 3 Lowest Rated Items:")
for r in results[-3:]:
    score_mal = r.get('score') or 'N/A'
    score_al = r.get('anilist_score') or 'N/A'
    print(f"- {r['title']} | MAL Score: {score_mal} | AL Score: {score_al}")
