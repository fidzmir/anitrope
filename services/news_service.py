import re
import html
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ANN_RSS_URL = "https://www.animenewsnetwork.com/news/rss.xml"
CRUNCHYROLL_RSS_URL = "https://www.crunchyroll.com/news/feed"

# High-resolution anime headline cover images fallback
HEADLINE_FALLBACK_IMAGES: List[str] = [
    "https://cdn.myanimelist.net/images/anime/1018/141042.jpg", # Blue Lock / Action
    "https://cdn.myanimelist.net/images/anime/1000/140484.jpg", # Sousou no Frieren / Fantasy
    "https://cdn.myanimelist.net/images/anime/1141/142503.jpg", # Re:Zero / Drama
    "https://cdn.myanimelist.net/images/anime/1286/99889.jpg",  # Demon Slayer / Shounen
    "https://cdn.myanimelist.net/images/anime/1935/127974.jpg", # Oshi no Ko / Idol
    "https://cdn.myanimelist.net/images/anime/1171/109222.jpg", # Kaguya-sama / Romance
    "https://cdn.myanimelist.net/images/anime/1307/134261.jpg"  # Jujutsu Kaisen / Action
]

# Initial instant fallback items with thumbnails
INITIAL_NEWS_FALLBACK: List[Dict[str, Any]] = [
    {
        "id": "ann-1",
        "title": "Agri Uma's Studio Cabana Manga Gets TV Anime Project",
        "link": "https://www.animenewsnetwork.com/news",
        "pub_date": "Terbaru",
        "source": "ANN",
        "description": "Pengumuman resmi adaptasi serial anime TV untuk manga populer Studio Cabana.",
        "image_url": "https://cdn.myanimelist.net/images/anime/1171/109222.jpg"
    },
    {
        "id": "crunchyroll-2",
        "title": "To You in the Beyond Anime Film Reveals New Trailer & Theme Song",
        "link": "https://www.crunchyroll.com/news",
        "pub_date": "Terbaru",
        "source": "Crunchyroll",
        "description": "Trailer terbaru film anime To You in the Beyond mengungkap lagu tema utama dan jajaran pengisi suara baru.",
        "image_url": "https://cdn.myanimelist.net/images/anime/1000/140484.jpg"
    },
    {
        "id": "ann-3",
        "title": "Live-Action Blue Lock Film Previews Entrance Exam Video",
        "link": "https://www.animenewsnetwork.com/news",
        "pub_date": "Terbaru",
        "source": "ANN",
        "description": "Cuplikan video ujian masuk film live-action Blue Lock resmi dirilis.",
        "image_url": "https://cdn.myanimelist.net/images/anime/1018/141042.jpg"
    }
]

_NEWS_CACHE: List[Dict[str, Any]] = list(INITIAL_NEWS_FALLBACK)
_LAST_FETCH_TIME = 0.0
CACHE_DURATION = 900.0  # 15 minutes cache


class NewsService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            },
            follow_redirects=True
        )

    async def close(self):
        await self.client.aclose()

    def _clean_html_text(self, html_content: str) -> str:
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ").strip()
        text = re.sub(r'\s+', ' ', text)
        return html.unescape(text)

    def _extract_image_url(self, item_soup, description_html: str, title: str) -> str:
        # 1. Look for <media:content url="..."> or <enclosure url="..."> or <media:thumbnail>
        media_content = item_soup.find(["media:content", "enclosure", "media:thumbnail"])
        if media_content and media_content.get("url"):
            return media_content.get("url")

        # 2. Look for <img> src inside description HTML
        if description_html:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description_html, re.IGNORECASE)
            if match:
                img_src = match.group(1)
                if img_src.startswith("http"):
                    return img_src

        # 3. Fallback to curated high-res anime headline cover image
        idx = abs(hash(title)) % len(HEADLINE_FALLBACK_IMAGES)
        return HEADLINE_FALLBACK_IMAGES[idx]

    async def _fetch_rss_feed(self, url: str, source_name: str) -> List[Dict[str, Any]]:
        news_items = []
        try:
            res = await self.client.get(url)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "xml")
                items = soup.find_all("item")

                for item in items[:12]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_elem = item.find("pubdate") or item.find("pubDate")
                    desc_elem = item.find("description")

                    title = html.unescape(title_elem.get_text().strip()) if title_elem else ""
                    link = link_elem.get_text().strip() if link_elem else ""
                    pub_date = pub_elem.get_text().strip() if pub_elem else ""
                    desc_html = desc_elem.get_text() if desc_elem else ""

                    if not title or not link:
                        continue

                    clean_desc = self._clean_html_text(desc_html)
                    img_url = self._extract_image_url(item, desc_html, title)

                    news_items.append({
                        "id": f"{source_name.lower()}-{abs(hash(link))}",
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "source": source_name,
                        "description": clean_desc or "Klik 'Baca Selengkapnya' untuk membaca artikel berita lengkap.",
                        "image_url": img_url
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS feed from {source_name} ({url}): {str(e)}")

        return news_items

    async def _fetch_jikan_fallback(self) -> List[Dict[str, Any]]:
        """Fallback news from Jikan API v4 Top Anime if RSS feeds are unreachable."""
        items = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://api.jikan.moe/v4/top/anime?limit=10")
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    for entry in data:
                        title = entry.get("title", "")
                        images = entry.get("images", {}).get("jpg", {})
                        img_url = images.get("large_image_url") or images.get("image_url")
                        items.append({
                            "id": f"jikan-{entry.get('mal_id')}",
                            "title": f"Popular Anime Spotlight: {title}",
                            "link": entry.get("url") or f"https://myanimelist.net/anime/{entry.get('mal_id')}",
                            "pub_date": entry.get("status") or "Airing",
                            "source": "Jikan Spotlight",
                            "description": entry.get("synopsis", ""),
                            "image_url": img_url
                        })
        except Exception as e:
            logger.error(f"Jikan fallback fetch error: {str(e)}")
        return items

    async def fetch_latest_news(self) -> List[Dict[str, Any]]:
        global _NEWS_CACHE, _LAST_FETCH_TIME
        now = asyncio.get_event_loop().time()

        if _NEWS_CACHE and (now - _LAST_FETCH_TIME) < CACHE_DURATION and len(_NEWS_CACHE) > len(INITIAL_NEWS_FALLBACK):
            return _NEWS_CACHE

        logger.info("Fetching fresh anime news from ANN RSS & Crunchyroll feeds...")
        ann_task = asyncio.create_task(self._fetch_rss_feed(ANN_RSS_URL, "ANN"))
        cr_task = asyncio.create_task(self._fetch_rss_feed(CRUNCHYROLL_RSS_URL, "Crunchyroll"))

        ann_news = await ann_task
        cr_news = await cr_task

        combined_news = []
        max_len = max(len(ann_news), len(cr_news))
        for i in range(max_len):
            if i < len(ann_news):
                combined_news.append(ann_news[i])
            if i < len(cr_news):
                combined_news.append(cr_news[i])

        if not combined_news:
            logger.info("RSS feeds empty or unreachable, fetching Jikan fallback spotlight...")
            combined_news = await self._fetch_jikan_fallback()

        if combined_news:
            _NEWS_CACHE = combined_news
            _LAST_FETCH_TIME = now

        return _NEWS_CACHE
