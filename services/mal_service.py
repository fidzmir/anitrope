import os
import re
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from services.anilist_service import AniListService

logger = logging.getLogger(__name__)

OFFICIAL_MAL_BASE_URL = "https://api.myanimelist.net/v2"
JIKAN_BASE_URL = "https://api.jikan.moe/v4"

_CACHE: Dict[str, Any] = {}
_LAST_REQUEST_TIME = 0.0

GENERIC_WORDS = {
    "action", "fantasy", "great", "best", "good", "lot", "deliberately",
    "anime", "manga", "main", "character", "mc", "show", "series", "friends", "friend",
    "people", "world", "story", "life", "day", "time", "find", "look", "search", "tapi",
    "dengan", "sengaja", "kekuatannya", "teman", "temannya", "about", "like",
    "strength"
}

DEFAULT_FALLBACK_ANIME = [
    {
        "mal_id": 21,
        "anilist_id": 21,
        "url": "https://myanimelist.net/anime/21/One_Piece",
        "anilist_url": "https://anilist.co/anime/21",
        "title": "One Piece",
        "title_english": "One Piece",
        "image_url": "https://cdn.myanimelist.net/images/anime/6/73245l.jpg",
        "type": "TV",
        "episodes": 1100,
        "status": "Currently Airing",
        "score": 8.73,
        "anilist_score": 8.8,
        "synopsis": "Gol D. Roger was known as the 'Pirate King,' the strongest and most infamous being to have sailed the Grand Line...",
        "genres": ["Action", "Adventure", "Fantasy"],
        "tags": ["Pirates", "Shounen", "Super Power"],
        "media_category": "anime"
    },
    {
        "mal_id": 5114,
        "anilist_id": 5114,
        "url": "https://myanimelist.net/anime/5114/Fullmetal_Alchemist__Brotherhood",
        "anilist_url": "https://anilist.co/anime/5114",
        "title": "Fullmetal Alchemist: Brotherhood",
        "title_english": "Fullmetal Alchemist: Brotherhood",
        "image_url": "https://cdn.myanimelist.net/images/anime/1208/94745l.jpg",
        "type": "TV",
        "episodes": 64,
        "status": "Finished Airing",
        "score": 9.1,
        "anilist_score": 9.0,
        "synopsis": "After a horrific alchemy experiment goes wrong in the Elric household, brothers Edward and Alphonse are left in a catastrophic new reality...",
        "genres": ["Action", "Adventure", "Drama", "Fantasy"],
        "tags": ["Alchemy", "Military", "Orphan", "Shounen"],
        "media_category": "anime"
    }
]

DEFAULT_FALLBACK_MANGA = [
    {
        "mal_id": 114798,
        "anilist_id": 105658,
        "url": "https://myanimelist.net/manga/114798/Kusuriya_no_Hitorigoto",
        "anilist_url": "https://anilist.co/manga/105658",
        "title": "Kusuriya no Hitorigoto",
        "title_english": "The Apothecary Diaries",
        "image_url": "https://cdn.myanimelist.net/images/manga/3/218042l.jpg",
        "type": "Manga",
        "episodes": 70,
        "status": "Publishing",
        "score": 8.6,
        "anilist_score": 8.7,
        "synopsis": "Maomao, a young woman trained in herbal medicine, is kidnapped and sold to the inner palace of the imperial court...",
        "genres": ["Drama", "Mystery", "Historical"],
        "tags": ["Medicine", "Historical", "Female Protagonist"],
        "media_category": "manga"
    }
]


class MALService:
    def __init__(self):
        self.mal_client_id = os.getenv("MAL_CLIENT_ID")
        if self.mal_client_id == "your_mal_client_id_here":
            self.mal_client_id = None

        self.client = httpx.AsyncClient(
            timeout=12.0,
            headers={"User-Agent": "HyperSpecificAnimeFinder/1.0"}
        )
        self.anilist = AniListService()

    async def close(self):
        await self.client.aclose()
        await self.anilist.close()

    async def _rate_limit_delay(self):
        global _LAST_REQUEST_TIME
        now = asyncio.get_event_loop().time()
        elapsed = now - _LAST_REQUEST_TIME
        if elapsed < 0.30:
            await asyncio.sleep(0.30 - elapsed)
        _LAST_REQUEST_TIME = asyncio.get_event_loop().time()

    async def fetch_candidates(
        self,
        keywords: List[str],
        target_tropes: Optional[List[str]] = None,
        anilist_tags: Optional[List[str]] = None,
        genres: Optional[List[str]] = None,
        clean_keyword: str = "",
        type_str: str = "anime",
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Hybrid multi-strategy retrieval pool across Official MAL API v2 and AniList GraphQL.
        """
        media_type = "manga" if type_str.lower() == "manga" else "anime"
        search_query = clean_keyword if clean_keyword else " ".join(keywords).strip()
        tags_str = ",".join(anilist_tags or [])
        genres_str = ",".join(genres or [])

        cache_key = f"hybrid:candidates:{media_type}:{tags_str}:{genres_str}:{search_query}:{limit}"
        if cache_key in _CACHE:
            return _CACHE[cache_key]

        candidate_pool: Dict[str, Dict[str, Any]] = {}
        headers = {"X-MAL-CLIENT-ID": self.mal_client_id} if self.mal_client_id else {}
        fields = "id,title,main_picture,synopsis,mean,rank,genres,num_episodes,num_chapters,status"

        # Run AniList GraphQL query and MAL queries concurrently
        try:
            anilist_task = asyncio.create_task(
                self.anilist.fetch_candidates(
                    keywords=keywords,
                    anilist_tags=anilist_tags,
                    genres=genres,
                    clean_keyword=clean_keyword,
                    type_str=media_type,
                    limit=limit
                )
            )

            # Official MAL Strategy A (Individual Clean Keyword Terms)
            mal_candidates = []
            if self.mal_client_id:
                clean_terms = [clean_keyword] if clean_keyword else [kw for kw in keywords if len(kw) >= 3 and kw.lower() not in GENERIC_WORDS][:2]

                for term in clean_terms[:2]:
                    try:
                        await self._rate_limit_delay()
                        res = await self.client.get(
                            f"{OFFICIAL_MAL_BASE_URL}/{media_type}",
                            params={"q": term, "limit": 15, "fields": fields},
                            headers=headers
                        )
                        if res.status_code == 200:
                            for entry in res.json().get("data", []):
                                mal_candidates.append(entry.get("node", {}))
                    except Exception as e:
                        logger.error(f"MAL fetch error for '{term}': {str(e)}")

            anilist_results = await anilist_task

            # Populate candidate pool with AniList items
            for item in anilist_results:
                title_key = item["title"].lower().strip()
                candidate_pool[title_key] = item

            # Merge MAL candidates into pool
            for node in mal_candidates:
                title_key = node.get("title", "").lower().strip()
                pic = node.get("main_picture", {})
                img_url = pic.get("large") or pic.get("medium")
                genres_list = [g.get("name") for g in node.get("genres", []) if g.get("name")]

                if title_key in candidate_pool:
                    # Update existing AniList candidate with MAL ID, URL, and score
                    candidate_pool[title_key]["mal_id"] = node.get("id")
                    candidate_pool[title_key]["url"] = f"https://myanimelist.net/{media_type}/{node.get('id')}"
                    if node.get("mean"):
                        candidate_pool[title_key]["score"] = node.get("mean")
                else:
                    candidate_pool[title_key] = {
                        "mal_id": node.get("id"),
                        "anilist_id": None,
                        "url": f"https://myanimelist.net/{media_type}/{node.get('id')}",
                        "anilist_url": None,
                        "title": node.get("title"),
                        "title_english": node.get("title"),
                        "image_url": img_url,
                        "type": media_type.upper(),
                        "episodes": node.get("num_episodes") if media_type == "anime" else node.get("num_chapters"),
                        "status": node.get("status"),
                        "score": node.get("mean"),
                        "anilist_score": None,
                        "synopsis": node.get("synopsis", "No synopsis available."),
                        "media_category": media_type
                    }
        except Exception as e:
            logger.error(f"Hybrid fetch error: {str(e)}")

        if not candidate_pool:
            return []

        # =========================================================================
        # HYBRID SEMANTIC SCORER (Synopsis + MAL Genres + AniList Trope Tags)
        # =========================================================================
        eval_tropes = target_tropes if target_tropes else keywords
        clean_kws = [k.lower() for k in eval_tropes if len(k) >= 3]
        bigrams = [f"{clean_kws[i]} {clean_kws[i+1]}" for i in range(len(clean_kws)-1)]
        ADULT_KEYWORDS = {"hentai", "erotica", "adult", "explicit", "nsfw", "18+", "borderline h"}
        scored_items = []

        for title_key, item in candidate_pool.items():
            title = item.get("title", "")
            synopsis = item.get("synopsis", "")
            genres_text = " ".join(item.get("genres", []))
            tags_text = " ".join(item.get("tags", []))
            
            full_text = f"{title} {synopsis} {genres_text} {tags_text}".lower()

            # Strict 18+ / Hentai / Ecchi / Adult Content Filter
            if item.get("isAdult"):
                continue

            labels_lower = set([g.lower() for g in item.get("genres", [])] + [t.lower() for t in item.get("tags", [])])
            if any(ak in label for ak in ADULT_KEYWORDS for label in labels_lower):
                continue
            if any(ak in title.lower() for ak in ["hentai", "erotica", "ecchi", "h-anime", "18+"]):
                continue

            score = 25
            matched_kws = 0

            # Bigram phrase match (e.g. 'pirate king' awards +35 points)
            for bg in bigrams:
                if bg in full_text:
                    score += full_text.count(bg) * 35

            # Keyword match (+6 points per match)
            for kw in set(clean_kws):
                if kw in full_text:
                    score += full_text.count(kw) * 6
                    matched_kws += 1

            # Extra Boost if matching AniList Trope Tag
            for tag in item.get("tags", []):
                tag_lower = tag.lower()
                for kw in clean_kws:
                    if kw in tag_lower:
                        score += 15 # Bonus +15 for matching exact AniList trope tag!

            # Direct Target Title Match Bonus (+100 points)
            if clean_keyword:
                clean_terms = [t.strip().lower() for t in re.split(r'[,;\n]+', clean_keyword) if len(t.strip()) >= 3]
                all_title_text = f"{title} {item.get('title_english', '')} {item.get('title_romaji', '')}".lower()
                for term in clean_terms:
                    if term in all_title_text:
                        score += 100
                    elif len(term) >= 4:
                        significant_parts = [p for p in term.split() if len(p) >= 4]
                        matched_parts = sum(1 for p in significant_parts if p in all_title_text)
                        if len(significant_parts) >= 2 and matched_parts >= 2:
                            score += 60  # Multi-word partial match (e.g. 2+ words match)
                        elif len(significant_parts) == 1 and matched_parts == 1:
                            score += 30  # Single significant word match

            # Conflict & Theme Bonus/Penalty Engine
            genres_lower = [g.lower() for g in item.get("genres", [])]
            tags_lower = [t.lower() for t in item.get("tags", [])]
            all_labels = set(genres_lower + tags_lower)

            # Rule 1: Sadness / Tragedy Requested
            is_sad_query = any(k in ["tragedy", "drama", "sadness", "tearjerker", "grief"] for k in clean_kws)
            if is_sad_query:
                if "drama" in all_labels or "tragedy" in all_labels or "tearjerker" in all_labels:
                    score += 50 # Bonus +50 for Drama/Tragedy tag
                if ("comedy" in all_labels or "parody" in all_labels or "gag humor" in all_labels) and not ("drama" in all_labels or "tragedy" in all_labels):
                    score -= 150 # Penalty -150 for pure comedy when sadness requested

            # Rule 2: Yuri / Girls Love Requested
            is_yuri_query = any(k in ["yuri", "girls love", "lesbian"] for k in clean_kws)
            if is_yuri_query:
                if "yuri" in all_labels or "girls love" in all_labels:
                    score += 60
                else:
                    score -= 150 # Penalty for non-yuri anime when yuri requested

            # Rule 3: Comedy Requested
            is_comedy_query = any(k in ["comedy", "funny", "slapstick", "parody"] for k in clean_kws)
            if is_comedy_query and "comedy" in all_labels:
                score += 40

            # Rule 4: Romance Requested (Must have Romance genre or tag!)
            is_romance_query = any(k in ["romance", "romantic", "love", "cinta", "romantis"] for k in clean_kws)
            if is_romance_query:
                has_romance_label = any("romance" in l or "romantic" in l for l in all_labels)
                if has_romance_label:
                    score += 60
                else:
                    score -= 200 # Heavy penalty for non-romance anime when romance is requested!

            # Rule 5: Sports Requested
            is_sports_query = any(k in ["sports", "sport", "baseball", "basketball", "volleyball", "soccer", "football"] for k in clean_kws)
            if is_sports_query:
                has_sports_label = any("sports" in l or "sport" in l for l in all_labels)
                if has_sports_label:
                    score += 60
                else:
                    score -= 200

            # Rule 6: Horror Requested
            is_horror_query = any(k in ["horror", "scary", "horor", "seram", "hantu"] for k in clean_kws)
            if is_horror_query:
                has_horror_label = any("horror" in l or "supernatural" in l or "gore" in l or "mystery" in l for l in all_labels)
                if has_horror_label:
                    score += 60
                else:
                    score -= 200

            # Rule 7: Isekai Requested
            is_isekai_query = any(k in ["isekai", "reincarnation", "summoned", "another world"] for k in clean_kws)
            if is_isekai_query:
                has_isekai_label = any("isekai" in l or "reincarnation" in l or "summoned" in l for l in all_labels)
                if has_isekai_label:
                    score += 50
                else:
                    score -= 100

            # Rule 8: Hiding Power / Secret Identity Requested
            is_hiding_query = any(k in ["person in hiding", "secret identity", "hides", "hidden", "secret", "disguise", "menyembunyikan", "sembunyi", "rahasia"] for k in clean_kws) or any(t in ["Person in Hiding", "Secret Identity"] for t in item.get("tags", []))
            if is_hiding_query:
                has_hiding_label = any(l in ["person in hiding", "secret identity", "chunibyou", "disguise"] for l in all_labels) or any(w in full_text for w in ["hides his", "hides her", "secret identity", "hides strength", "hides power", "disguise", "conceal", "secretly", "pretends", "eminence in shadow", "mob psycho", "hidden power", "conceals his", "conceals her", "true power"])
                if has_hiding_label:
                    score += 90 # Heavy boost +90 for anime where MC hides power
                else:
                    score -= 40 # Mild penalty for anime that don't match hiding concept

            # Rule 8: Mecha / Robots Requested
            is_mecha_query = any(k in ["mecha", "robot", "gundam"] for k in clean_kws)
            if is_mecha_query:
                has_mecha_label = any("mecha" in l or "robot" in l for l in all_labels)
                if has_mecha_label:
                    score += 60
                else:
                    score -= 200

            # Rule 9: Gourmet / Cooking Requested
            is_cooking_query = any(k in ["gourmet", "cooking", "food", "kuliner", "memasak", "koki", "chef", "chefs"] for k in clean_kws)
            if is_cooking_query:
                has_cooking_label = any("gourmet" in l or "cooking" in l or "food" in l for l in all_labels) or "cook" in full_text
                if has_cooking_label:
                    score += 60
                else:
                    score -= 200

            # Keyword Coverage Multiplier & Honest Match Verification
            specific_kws = [k for k in clean_kws if k.lower() not in GENERIC_WORDS]
            
            clean_terms_matched = False
            if clean_keyword:
                clean_terms = [t.strip().lower() for t in re.split(r'[,;\n]+', clean_keyword) if len(t.strip()) >= 3]
                all_title_text = f"{title} {item.get('title_english', '')} {item.get('title_romaji', '')}".lower()
                clean_terms_matched = any(ct in all_title_text for ct in clean_terms)

            # Trust the scoring engine: if score is high enough, the keywords/bigrams/rules
            # already validated relevance. Only apply strict specificity filter for low scores.
            if score >= 50 or clean_terms_matched:
                has_specific_match = True
            elif specific_kws and any(sk in full_text for sk in specific_kws):
                has_specific_match = True
            elif anilist_tags and item.get("tags"):
                has_tag_match = any(
                    any(at.lower() in t.lower() or t.lower() in at.lower() for at in anilist_tags)
                    for t in item.get("tags", [])
                )
                has_specific_match = has_tag_match
            else:
                has_specific_match = score > 25  # Only pass if score is above base (had keyword matches)

            if score <= 0 or not has_specific_match:
                final_score = 0.0
                match_pct = 0
            else:
                coverage_ratio = matched_kws / len(clean_kws) if clean_kws else 1.0
                final_score = score * (1 + coverage_ratio * 2.5)
                match_pct = min(98, max(70, round(70 + (coverage_ratio * 28))))

            item_copy = dict(item)
            item_copy["score_rank"] = round(final_score, 1)
            item_copy["match_score"] = match_pct

            if match_pct > 0 and not item_copy.get("why_it_matches"):
                syn = item.get("synopsis", "").strip()
                tags = item.get("tags") or item.get("genres") or []
                matching_labels = [t for t in tags if any(len(k) >= 3 and k.lower() in t.lower() for k in eval_tropes)]
                
                first_sent = ""
                if syn and not syn.startswith("No synopsis"):
                    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', syn) if len(s.strip()) > 15]
                    if sentences:
                        first_sent = sentences[0]
                        if len(first_sent) > 160:
                            first_sent = first_sent[:157] + "..."

                if first_sent and matching_labels:
                    labels_str = ", ".join(matching_labels[:3])
                    item_copy["why_it_matches"] = f"{first_sent} [Fokus Trope: {labels_str}]"
                elif first_sent:
                    item_copy["why_it_matches"] = first_sent
                elif matching_labels:
                    labels_str = ", ".join(matching_labels[:3])
                    item_copy["why_it_matches"] = f"Mengangkat serial '{title}' yang berfokus pada elemen {labels_str}."
                else:
                    genres_str = ", ".join(tags[:3]) if tags else "cerita utama"
                    item_copy["why_it_matches"] = f"Mengangkat serial '{title}' dengan genre utama {genres_str}."

            if match_pct > 0 and final_score > 0:
                scored_items.append(item_copy)

        # Sort candidate items by Trope Match Relevance FIRST, then Rating Score SECOND
        scored_items.sort(
            key=lambda x: (x["score_rank"], x.get("score") or x.get("anilist_score") or 0.0),
            reverse=True
        )

        results = [item for item in scored_items[:limit]]
        _CACHE[cache_key] = results
        return results

    async def get_top_items(self, type_str: str = "anime", limit: int = 6) -> List[Dict[str, Any]]:
        """Fetch top items combining AniList and MAL rankings."""
        media_type = "manga" if type_str.lower() == "manga" else "anime"
        cache_key = f"hybrid:top:{media_type}:{limit}"
        if cache_key in _CACHE:
            return _CACHE[cache_key]

        results = []
        if self.mal_client_id:
            try:
                await self._rate_limit_delay()
                url = f"{OFFICIAL_MAL_BASE_URL}/{media_type}/ranking"
                params = {"ranking_type": "all", "limit": limit, "fields": "id,title,main_picture,synopsis,mean,genres"}
                headers = {"X-MAL-CLIENT-ID": self.mal_client_id}
                res = await self.client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    for entry in res.json().get("data", []):
                        node = entry.get("node", {})
                        pic = node.get("main_picture", {})
                        results.append({
                            "mal_id": node.get("id"),
                            "anilist_id": None,
                            "url": f"https://myanimelist.net/{media_type}/{node.get('id')}",
                            "anilist_url": None,
                            "title": node.get("title"),
                            "title_english": node.get("title"),
                            "image_url": pic.get("large") or pic.get("medium"),
                            "type": media_type.upper(),
                            "score": node.get("mean"),
                            "anilist_score": node.get("mean"),
                            "synopsis": node.get("synopsis", ""),
                            "genres": [g.get("name") for g in node.get("genres", []) if g.get("name")],
                            "media_category": media_type
                        })
                    if results:
                        _CACHE[cache_key] = results
                        return results
            except Exception as e:
                logger.error(f"Official MAL ranking fetch error: {str(e)}")

        # AniList fallback for top items
        try:
            results = await self.anilist.get_popular_items(type_str=media_type, limit=limit)
        except Exception:
            pass

        if not results:
            results = DEFAULT_FALLBACK_MANGA if media_type == "manga" else DEFAULT_FALLBACK_ANIME

        _CACHE[cache_key] = results[:limit]
        return results[:limit]
