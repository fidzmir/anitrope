import re
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"

_CACHE: Dict[str, Any] = {}
_LAST_REQUEST_TIME = 0.0

SEARCH_MEDIA_QUERY = """
query ($search: String, $type: MediaType, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: $type, isAdult: false) {
      id
      idMal
      isAdult
      title {
        romaji
        english
        native
      }
      coverImage {
        extraLarge
        large
      }
      description(asHtml: false)
      averageScore
      episodes
      chapters
      status
      genres
      tags {
        name
        rank
        isMediaSpoiler
      }
      siteUrl
      externalLinks {
        id
        site
        url
        type
        icon
      }
    }
  }
}
"""

TAG_GENRE_MEDIA_QUERY = """
query ($type: MediaType, $genre_in: [String], $tag_in: [String], $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: $type, genre_in: $genre_in, tag_in: $tag_in, isAdult: false, sort: [POPULARITY_DESC]) {
      id
      idMal
      isAdult
      title {
        romaji
        english
        native
      }
      coverImage {
        extraLarge
        large
      }
      description(asHtml: false)
      averageScore
      episodes
      chapters
      status
      genres
      tags {
        name
        rank
        isMediaSpoiler
      }
      siteUrl
      externalLinks {
        id
        site
        url
        type
        icon
      }
    }
  }
}
"""

ANILIST_TAG_CORRECTIONS = {
    "demons": "Demons",
    "demon": "Demons",
    "assassin": "Assassins",
    "assassins": "Assassins",
    "heroes": "Superhero",
    "hero": "Superhero",
    "super powers": "Super Power",
    "superpowers": "Super Power",
    "super power": "Super Power",
    "overpowered": "Super Power",
    "anti-heroes": "Anti-Hero",
    "antihero": "Anti-Hero",
    "anti-hero": "Anti-Hero",
    "reincarnation": "Reincarnation",
    "isekai": "Isekai",
    "magic": "Magic",
    "school": "School",
    "time travel": "Time Manipulation",
    "time loop": "Time Loop",
    "mecha": "Real Robot",
    "robot": "Real Robot",
    "survival": "Survival",
    "revenge": "Revenge",
    "military": "Military",
    "martial arts": "Martial Arts",
    "espionage": "Espionage",
    "spy": "Espionage",
    "secret identity": "Espionage",
    "person in hiding": "Espionage",
    "hiding power": "Super Power",
    "cultivation": "Cultivation",
    "wuxia": "Wuxia",
    "tragedy": "Tragedy",
    "crime": "Crime",
    "food": "Food",
    "cooking": "Food",
    "gourmet": "Food",
    "music": "Band",
    "mythology": "Mythology",
    "politics": "Politics",
    "war": "War",
    "cyberpunk": "Cyberpunk",
    "steampunk": "Steampunk",
    "parody": "Parody",
    "yuri": "Yuri",
    "boys love": "Boys' Love",
    "bl": "Boys' Love",
    "harem": "Female Harem",
    "reverse harem": "Male Harem",
}


_ANILIST_CACHE: Dict[str, List[Dict[str, Any]]] = {}

class AniListService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=12.0,
            headers={
                "User-Agent": "AniTropeHyperSpecificFinder/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    async def close(self):
        await self.client.aclose()

    async def _rate_limit_delay(self):
        global _LAST_REQUEST_TIME
        now = asyncio.get_event_loop().time()
        elapsed = now - _LAST_REQUEST_TIME
        if elapsed < 0.85:
            await asyncio.sleep(0.85 - elapsed)
        _LAST_REQUEST_TIME = asyncio.get_event_loop().time()

    async def _query_graphql(self, query: str, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        import json
        cache_key = json.dumps(variables, sort_keys=True)
        if cache_key in _ANILIST_CACHE and _ANILIST_CACHE[cache_key]:
            return _ANILIST_CACHE[cache_key]

        for attempt in range(3):
            try:
                await self._rate_limit_delay()
                payload = {"query": query, "variables": variables}
                res = await self.client.post(ANILIST_GRAPHQL_URL, json=payload)
                if res.status_code == 200:
                    items = res.json().get("data", {}).get("Page", {}).get("media", [])
                    print(f"[DEBUG AniList Query] Var: {variables} | Count: {len(items)}")
                    if items:
                        _ANILIST_CACHE[cache_key] = items
                    return items
                elif res.status_code == 429:
                    print(f"[DEBUG AniList 429 Rate Limit] Var: {variables}")
                    logger.warning("AniList 429 Rate Limit. Sleeping 4.0s before retry...")
                    await asyncio.sleep(4.0)
                else:
                    print(f"[DEBUG AniList Error] Var: {variables} | Status: {res.status_code} | Text: {res.text[:150]}")
            except Exception as e:
                logger.error(f"AniList GraphQL query error: {str(e)}")
        return []

    async def fetch_candidates(
        self,
        keywords: List[str],
        anilist_tags: Optional[List[str]] = None,
        genres: Optional[List[str]] = None,
        clean_keyword: str = "",
        type_str: str = "anime",
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetches anime or manga candidates from AniList GraphQL API strictly using extracted tags, genres, and keywords.
        """
        media_type = "MANGA" if type_str.lower() == "manga" else "ANIME"
        tags_key = ",".join(anilist_tags or [])
        genres_key = ",".join(genres or [])
        search_query = " ".join(keywords).strip()

        cache_key = f"anilist:{media_type}:{tags_key}:{genres_key}:{clean_keyword}:{search_query}:{limit}"
        if cache_key in _CACHE and _CACHE[cache_key]:
            return _CACHE[cache_key]

        raw_media_pool: Dict[int, Dict[str, Any]] = {}

        # 1. Search Query First (Query ONCE using primary term to save API rate limits)
        if clean_keyword:
            primary_term = clean_keyword.split(",")[0].strip() if "," in clean_keyword else clean_keyword.strip()
            if primary_term:
                search_items = await self._query_graphql(
                    SEARCH_MEDIA_QUERY,
                    {"search": primary_term, "type": media_type, "page": 1, "perPage": 20}
                )
                for item in search_items:
                    raw_media_pool[item["id"]] = item

        # 2. Tag & Genre-Based Fetching (try multiple tags until one returns results)
        tag_found = False
        if anilist_tags:
            for tag_candidate in anilist_tags[:3]:  # Try up to 3 tags
                primary_tag = ANILIST_TAG_CORRECTIONS.get(tag_candidate.lower(), tag_candidate)
                tag_items = await self._query_graphql(
                    TAG_GENRE_MEDIA_QUERY,
                    {"type": media_type, "tag_in": [primary_tag], "page": 1, "perPage": 25}
                )
                for item in tag_items:
                    raw_media_pool[item["id"]] = item
                if tag_items:
                    tag_found = True
                    break  # Stop once a tag returns results

        # Genre fallback: fetch when tag_in returned 0 OR pool is still small
        if genres and (not tag_found or len(raw_media_pool) < 10):
            genre_items = await self._query_graphql(
                TAG_GENRE_MEDIA_QUERY,
                {
                    "type": media_type,
                    "genre_in": [genres[0]],
                    "page": 1,
                    "perPage": 25
                }
            )
            for item in genre_items:
                raw_media_pool[item["id"]] = item

        # Keyword Fallback: Search using keywords if candidate pool is still small (< 5)
        if len(raw_media_pool) < 5 and keywords:
            for kw in keywords[:3]:
                if len(kw) >= 3:
                    kw_items = await self._query_graphql(
                        SEARCH_MEDIA_QUERY,
                        {"search": kw, "type": media_type, "page": 1, "perPage": 15}
                    )
                    for item in kw_items:
                        raw_media_pool[item["id"]] = item

        # Process and format items
        candidates = []
        ADULT_KEYWORDS = {"hentai", "erotica", "adult", "explicit", "nsfw", "18+", "borderline h"}

        for item_id, item in raw_media_pool.items():
            if item.get("isAdult"):
                continue

            genres_list = item.get("genres", [])
            if any(g.lower() in ADULT_KEYWORDS for g in genres_list):
                continue

            tags_data = item.get("tags", [])
            clean_tags = [
                t.get("name") for t in tags_data
                if t.get("name") and not t.get("isMediaSpoiler") and (t.get("rank") or 0) >= 35
            ]

            if any(t.lower() in ADULT_KEYWORDS for t in clean_tags):
                continue

            titles = item.get("title", {})
            primary_title = titles.get("english") or titles.get("romaji") or titles.get("native")
            cover = item.get("coverImage", {})
            img_url = cover.get("extraLarge") or cover.get("large")

            avg_score = item.get("averageScore")
            score_10 = round(avg_score / 10.0, 2) if avg_score else None

            desc_clean = item.get("description") or ""
            desc_clean = re.sub(r'<br\s*/?>', '\n', desc_clean, flags=re.IGNORECASE)
            desc_clean = re.sub(r'</?p>', '\n\n', desc_clean, flags=re.IGNORECASE)
            desc_clean = re.sub(r'<[^>]+>', '', desc_clean)
            desc_clean = re.sub(r'\n{3,}', '\n\n', desc_clean).strip()

            raw_links = item.get("externalLinks") or []
            streaming_links = []
            FREE_KEYWORDS = {"youtube", "bilibili", "bstation", "iqiyi", "iq", "muse asia", "ani-one", "tubi", "pluto"}
            for ext in raw_links:
                site = ext.get("site") or ""
                url = ext.get("url") or ""
                link_type = ext.get("type") or ""
                if link_type == "STREAMING" or any(p in site.lower() for p in ["crunchyroll", "netflix", "bilibili", "iqiyi", "hulu", "amazon", "youtube", "funimation", "vrv", "hidive"]):
                    is_free = any(k in site.lower() for k in FREE_KEYWORDS)
                    streaming_links.append({
                        "site": site,
                        "url": url,
                        "is_free": is_free,
                        "icon": ext.get("icon")
                    })

            candidates.append({
                "anilist_id": item.get("id"),
                "mal_id": item.get("idMal"),
                "anilist_url": item.get("siteUrl") or f"https://anilist.co/{media_type.lower()}/{item.get('id')}",
                "url": f"https://myanimelist.net/{media_type.lower()}/{item.get('idMal')}" if item.get("idMal") else f"https://anilist.co/{media_type.lower()}/{item.get('id')}",
                "title": primary_title,
                "title_english": titles.get("english") or primary_title,
                "title_romaji": titles.get("romaji") or primary_title,
                "image_url": img_url,
                "type": media_type,
                "episodes": item.get("episodes") if media_type == "ANIME" else item.get("chapters"),
                "status": item.get("status"),
                "anilist_score": score_10,
                "score": score_10,
                "synopsis": desc_clean,
                "genres": item.get("genres", []),
                "tags": clean_tags[:8],
                "streaming_links": streaming_links,
                "source": "AniList",
                "media_category": media_type.lower()
            })

        logger.info(f"AniList GraphQL returned {len(candidates)} total candidates.")
        _CACHE[cache_key] = candidates
        return candidates

    async def get_popular_items(self, type_str: str = "anime", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top popular items from AniList GraphQL API."""
        return await self.fetch_candidates(keywords=[], type_str=type_str, limit=limit)
