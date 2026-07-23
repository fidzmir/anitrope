import httpx
from deep_translator import GoogleTranslator
import re

headers = {'X-MAL-CLIENT-ID': '2bddf3a94b3a97b4c78b8657dd063240'}
fields = 'id,title,main_picture,synopsis,mean,genres'

def test_global_search(prompt):
    translated = GoogleTranslator(source='auto', target='en').translate(prompt)
    stop_en = {'anime', 'manga', 'about', 'whose', 'main', 'character', 'wants', 'become', 'the', 'to', 'be', 'a', 'an', 'and', 'or', 'in', 'on', 'with', 'where', 'who', 'which', 'that', 'when', 'want', 'looking', 'find', 'show', 'series', 'from', 'is', 'are', 'for'}
    raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', translated.lower())
    clean_keywords = [w for w in raw_words if w not in stop_en]

    search_q = ' '.join(clean_keywords)
    res_search = httpx.get('https://api.myanimelist.net/v2/anime', params={'q': search_q, 'limit': 15, 'fields': fields}, headers=headers)
    items_search = [e['node'] for e in res_search.json().get('data', [])]

    for kw in clean_keywords[:2]:
        res_kw = httpx.get('https://api.myanimelist.net/v2/anime', params={'q': kw, 'limit': 10, 'fields': fields}, headers=headers)
        items_search.extend([e['node'] for e in res_kw.json().get('data', [])])

    res_pop = httpx.get('https://api.myanimelist.net/v2/anime/ranking', params={'ranking_type': 'bypopularity', 'limit': 50, 'fields': fields}, headers=headers)
    items_pop = [e['node'] for e in res_pop.json().get('data', [])]

    all_candidates = {item['id']: item for item in items_search + items_pop}
    unique_kws = list(set(clean_keywords))
    bigrams = [f'{clean_keywords[i]} {clean_keywords[i+1]}' for i in range(len(clean_keywords)-1)]

    scored_results = []
    for cid, item in all_candidates.items():
        text = (item.get('title', '') + ' ' + item.get('synopsis', '') + ' ' + ' '.join([g['name'] for g in item.get('genres', [])])).lower()
        score = 0
        matched_kws = 0

        for bg in bigrams:
            if bg in text:
                score += text.count(bg) * 30

        for kw in unique_kws:
            if kw in text:
                score += text.count(kw) * 5
                matched_kws += 1

        coverage_ratio = matched_kws / len(unique_kws) if unique_kws else 1.0
        score = score * (1 + coverage_ratio * 2)

        if score > 0:
            scored_results.append((round(score, 1), item['title'], item.get('mean')))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    print(f'\nPrompt: "{prompt}"')
    print(f'Translated: "{translated}"')
    print('Top Match:', scored_results[0] if scored_results else 'None')

if __name__ == "__main__":
    test_global_search("anime bajak laut yang peran utamanya ingin jadi raja bajak laut")
    test_global_search("anime tentang dewa kematian dan buku catatan misterius")
    test_global_search("anime pahlawan perisai di dunia lain")
