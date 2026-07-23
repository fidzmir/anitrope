import os
import re
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.mal_service import MALService
from services.ai_service import AIService
from services.news_service import NewsService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hyper_anime_finder")

mal_service = MALService()
ai_service = AIService()
news_service = NewsService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await mal_service.close()
    await news_service.close()

app = FastAPI(
    title="Hyper-Specific Mood & Trope Finder for Anime & Manga",
    description="Pencari anime/manga berbasis situasi dan trope spesifik dengan AI & MyAnimeList API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    prompt: str
    media_type: Optional[str] = "anime" # 'anime' or 'manga'

# Preset Trope Pills for quick selection
PRESET_TROPES = [
    {
        "label": "Romance MC Tidak Peka",
        "prompt": "Cari anime romantis yang karakter utamanya tidak peka, tapi ending-nya tidak menggantung.",
        "category": "Romance",
        "type": "anime"
    },
    {
        "label": "Manga Isekai Bisnis/Jualan",
        "prompt": "Cari manga isekai yang MC-nya fokus jualan/bisnis, bukan bertarung.",
        "category": "Isekai",
        "type": "manga"
    },
    {
        "label": "MC Overpowered Pura-pura Lemah",
        "prompt": "Cari anime fantasi dengan MC super kuat tapi sengaja menyembunyikan kekuatannya dari teman-temannya.",
        "category": "Action",
        "type": "anime"
    },
    {
        "label": "Wholesome Slice of Life Cuteness",
        "prompt": "Cari anime slice of life yang sangat tenang, wholesome, tanpa drama berat untuk penyembuhan stres.",
        "category": "Healing",
        "type": "anime"
    },
    {
        "label": "Manga Thriller Psychological Mind Games",
        "prompt": "Cari manga misteri psikologis dengan pertarungan adu otak intens ala Death Note atau Liar Game.",
        "category": "Thriller",
        "type": "manga"
    }
]

@app.get("/api/health")
async def health_check():
    has_mal_client = bool(mal_service.mal_client_id)
    return {
        "status": "online",
        "ai_engine": "100% Local Fast Concept Engine (Zero External AI Calls)",
        "gemini_active": False,
        "anilist_active": True,
        "mal_client_id_active": has_mal_client,
        "data_source": "Dual Database: AniList GraphQL + Official MyAnimeList API v2"
    }

@app.get("/api/tropes")
async def get_preset_tropes():
    return PRESET_TROPES

@app.get("/api/featured")
async def get_featured(media_type: str = "anime"):
    normalized_type = "manga" if media_type.lower() == "manga" else "anime"
    items = await mal_service.get_top_items(type_str=normalized_type, limit=6)
    return {"media_type": normalized_type, "items": items}

@app.get("/api/news")
async def get_latest_news():
    news = await news_service.fetch_latest_news()
    return {"count": len(news), "items": news}

@app.post("/api/search")
async def search_tropes(req: SearchRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt search tidak boleh kosong.")

    media_type = "manga" if req.media_type and req.media_type.lower() == "manga" else "anime"
    logger.info(f"Processing query: '{prompt}' [Media: {media_type}]")

    # Step 1: Parse user query into parameters using Gemini 2.0 Flash
    parse_result = await ai_service.parse_query(prompt, default_media_type=media_type)
    logger.info(f"Parsed strategy -> Keywords: {parse_result.keywords}, Target Tropes: {parse_result.target_tropes}")

    # Step 2: Fetch candidate items strictly using parsed tags, genres, and keywords
    candidates = await mal_service.fetch_candidates(
        keywords=parse_result.keywords,
        target_tropes=parse_result.target_tropes,
        anilist_tags=parse_result.anilist_tags,
        genres=parse_result.genres,
        clean_keyword=parse_result.clean_keyword,
        type_str=parse_result.media_type,
        limit=25
    )

    if not candidates:
        return {
            "prompt": prompt,
            "search_meta": {
                "keywords": parse_result.keywords,
                "target_tropes": parse_result.target_tropes,
                "media_type": parse_result.media_type
            },
            "results": []
        }

    # Step 3: Rerank & explain Top candidate items
    evaluations = await ai_service.rerank_and_explain(
        user_prompt=prompt,
        target_tropes=parse_result.target_tropes,
        exclude_tropes=parse_result.exclude_tropes,
        candidates=candidates
    )

    # Combine metadata and AI evaluations (Strictly excluding match_score == 0)
    final_results = []
    for cand in candidates:
        mal_id = cand.get("mal_id")
        anilist_id = cand.get("anilist_id")
        title_key = cand.get("title", "").lower().strip()
        clean_t = re.sub(r'[^a-zA-Z0-9\s]', '', title_key).strip()

        ev = evaluations.get(title_key) or evaluations.get(clean_t) or (evaluations.get(mal_id) if mal_id else None) or (evaluations.get(anilist_id) if anilist_id else None)
        
        if not ev:
            for k, val in evaluations.items():
                if isinstance(k, str) and len(k) >= 4 and (k in title_key or title_key in k):
                    ev = val
                    break
        
        match_score = ev.match_score if ev else cand.get("match_score", 0)
        why_matches = ev.why_it_matches if ev else cand.get("why_it_matches", "")
        trope_tags = (ev.trope_tags if ev else (cand.get("tags") or cand.get("genres") or []))[:4]

        if match_score > 0 and why_matches and "Tidak cocok" not in why_matches:
            cand_copy = dict(cand)
            cand_copy["match_score"] = match_score
            cand_copy["why_it_matches"] = why_matches
            cand_copy["trope_tags"] = trope_tags
            final_results.append(cand_copy)

    # Sort results by Top Matched Trope Relevance FIRST, then Rating Score SECOND
    final_results.sort(
        key=lambda x: (x.get("match_score", 0), x.get("score_rank", 0), x.get("score") or x.get("anilist_score") or 0.0),
        reverse=True
    )

    return {
        "prompt": prompt,
        "search_meta": {
            "keywords": parse_result.keywords,
            "target_tropes": parse_result.target_tropes,
            "exclude_tropes": parse_result.exclude_tropes,
            "media_type": parse_result.media_type
        },
        "results": final_results
    }

# Serve Static Frontend Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
async def serve_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
