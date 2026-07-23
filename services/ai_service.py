import os
import re
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

logger = logging.getLogger(__name__)

# Intelligent English & Contextual Stop Words
ENGLISH_STOP_WORDS = {
    'anime', 'manga', 'about', 'whose', 'main', 'character', 'characters', 'wants', 'become', 'lead', 'hero', 'heroine',
    'the', 'to', 'be', 'a', 'an', 'and', 'or', 'in', 'on', 'with', 'without', 'where', 'who', 'whom',
    'which', 'that', 'when', 'want', 'wanted', 'looking', 'look', 'looks', 'find', 'finds', 'finding', 'show', 'shows', 'showing', 'series', 'from',
    'is', 'are', 'was', 'were', 'been', 'being', 'for', 'very', 'like', 'likes', 'some', 'has', 'have', 'having', 'had',
    'his', 'her', 'their', 'my', 'your', 'its', 'our', 'this', 'these', 'those', 'there', 'here',
    'but', 'however', 'yet', 'still', 'although', 'though', 'even', 'then', 'than',
    'so', 'such', 'too', 'also', 'just', 'more', 'most', 'less', 'least', 'good', 'bad', 'best', 'top', 'great', 'awesome',
    'consecutive', 'continuous', 'row', 'consecutively', 'ending', 'end', 'ends', 'leave', 'leaves', 'finish', 'finished',
    'protagonist', 'protagonists', 'story', 'plot', 'theme', 'tropes', 'trope', 'tapi', 'yang', 'dan', 'atau', 'dengan', 'tanpa',
    'dnegan', 'dengan', 'nya', 'banget', 'bgt', 'really', 'medicine', 'does', 'doesn', 'doesnt', 'dont', 'don', 'did', 'didn',
    'isn', 'isnt', 'not', 'no', 'give', 'gives', 'giving', 'recommend', 'recommends', 'recommending', 'recommendation', 'recommendations',
    'suggestion', 'suggestions', 'suggest', 'suggests', 'suggesting', 'tell', 'tells', 'telling', 'ask', 'asks', 'asking',
    'please', 'can', 'could', 'would', 'should', 'will', 'any', 'some', 'one', 'two', 'three', 'thing', 'things', 'type', 'types',
    'category', 'categories', 'genre', 'genres', 'setting', 'settings', 'background', 'backgrounds', 'atmosphere', 'vibe', 'vibes',
    'used', 'uses', 'use', 'plays', 'play', 'playing', 'turns', 'turn', 'turned', 'turning', 'became', 'become', 'becomes', 'former', 'formerly',
    'represent', 'represents', 'representing', 'major', 'human', 'humans', 'another', 'world', 'figure', 'figures', 'person', 'people', 'someone', 'somebody', 'summoned', 'summons', 'summon',
    'wastes', 'wasting', 'waste', 'spending', 'spends', 'spend', 'lives', 'living', 'shows', 'brings', 'gets', 'getting', 'trying', 'tries', 'try',
    'see', 'sees', 'seeing', 'forms', 'forming', 'fake', 'fakes', 'back', 'middle', 'school', 'first', 'second', 'dies', 'enters',
    'girl', 'boy', 'man', 'woman', 'after', 'defeating', 'enemy', 'village', 'farmer', 'trader', 'work', 'working', 'thrown',
    'look', 'for', 'into', 'onto', 'upon', 'young', 'poor', 'rich', 'rises', 'rising', 'takes', 'gives', 'makes', 'made', 'fuses', 'fusing',
    'becomes', 'became', 'tries', 'tried', 'uncover', 'uncovers', 'rebuilt', 'rebuilds', 'rebuild', 'scratch', 'power', 'uses', 'using', 'attempts', 'attempting',
    'super', 'strong', 'strength', 'friends', 'deliberately', 'hides'
}

SLANG_TYPO_MAP = {
    r'\bdnegan\b': 'dengan',
    r'\bpante\b': 'panti',
    r'\bkaka\b': 'kakak',
    r'\badiik\b': 'adik',
    r'\bnggak\b|\bgak\b|\bga\b|\bndak\b': 'tidak',
    r'\bbgt\b|\banget\b': 'banget',
    r'\bdisguis\b|\bdissguis\b': 'disguise',
    r'\bop\b': 'overpowered',
    r'\bmc\s*nya\b|\bmcnya\b|\bchara\s*nya\b|\bchar\s*nya\b': 'main character',
    r'\bending\s*nya\b|\bendingnya\b': 'ending',
    r'\braja\s+bajak\s+laut\b': 'pirate king one piece',
    r'\bdewa\s+kematian\b': 'death god shinigami death note',
    r'\bbuku\s+catatan\b|\bbuku\s+kematian\b': 'death note notebook',
    r'\bpanti\s+asuhan\b|\banak\s+asuh\b': 'orphanage orphan',
    r'\bkekuatan\s+alkimia\b|\balkimia\b': 'fullmetal alchemy',
    r'\braja\s+iblis\b': 'demon king',
    r'\bdunia\s+lain\b': 'another world isekai',
    r'\bga\s+ada\s+obat\b|\bgak\s+ada\s+obat\b': 'overpowered unstoppable',
    r'\bkaya\s+raya\b|\bhambur\s+hamburkan\b|\bsultan\b': 'rich wealthy money millionaire'
}

GLOBAL_TROPE_INTENT_MAP = {
    r'\b(viking|vikings|vinland)\b': ['viking', 'vinland'],
    r'\b(sadness|sad|grief|tragedy|tragic|depressing|suffering|tears|crying|pain|kesedihan|sedih|derita)\b': ['tragedy', 'drama'],
    r'\b(happy ending|good ending|wholesome|comforting|ending good|ending nya good|happy)\b': ['happy ending'],
    r'\b(alchemy|alkimia|alchemist)\b': ['alchemy', 'fullmetal'],
    r'\b(pirate|pirates|bajak laut)\b': ['pirates', 'sea'],
    r'\b(rich|wealth|wealthy|millionaire|billionaire|money|uang|kaya|hambur|hamburkan|sultan)\b': ['wealth', 'economics'],
    r'\b(ghost|ghosts|spirit|spirits|hantu|roh|gaib|yokai|youkai)\b': ['supernatural', 'ghost'],
    r'\b(time loop|time travel|perjalanan waktu|pengulang waktu|memutar waktu|looping)\b': ['time manipulation', 'time travel'],
    r'\b(kerajaan|bikin kerajaan|membangun|build kingdom|kingdom building|crafting)\b': ['kingdom building', 'isekai'],
    r'\b(pura-pura pacaran|pacar sewaan|kontrak|fake relationship|fake dating|contract marriage)\b': ['fake relationship', 'romance'],
    r'\b(gambling|judi|adu otak|mind games|psychological games|kakegurui)\b': ['mind games', 'gambling'],
    r'\b(dokter|doctor|obat|farmasi|pharmacist|medical|apoteker)\b': ['medicine', 'workplace'],
    r'\b(mafia|crime|kejahatan|kriminal|geng|gang|gangster|yakuza|bos mafia)\b': ['crime', 'mafia'],
    r'\b(sepak bola|bola|soccer|football|bluelock|haikyuu)\b': ['sports', 'soccer'],
    r'\b(detektif|detective|kasus|pembunuhan|misteri|murder|mystery)\b': ['mystery', 'detective'],
    r'\b(virtual reality|vr game|game virtual|terjebak di game|trapped in game)\b': ['virtual world', 'video games'],
    r'\b(band|musik|music|gitar|guitarist|pemalu|shy|bocchi)\b': ['music', 'band'],
    r'\b(ninja|shinobi|hokage)\b': ['ninja', 'shinobi'],
    r'\b(samurai|ronin|katana)\b': ['samurai', 'sword'],
    r'\b(romance|romantic|love|cinta|romantis)\b': ['romance', 'love'],
    r'\b(yuri|girls love|lesbian)\b': ['yuri', 'girls love'],
    r'\b(revenge|vengeance|dendam)\b': ['revenge', 'anti-hero'],
    r'\b(overpowered|op mc|overpowered mc|kuat|terkuat|unstoppable)\b': ['overpowered', 'action'],
    r'\b(hides|hide|hidden|secret|disguise|menyembunyikan|sembunyi)\b': ['secret identity', 'person in hiding', 'hiding power']
}

TAG_TRANSLATIONS_ID = {
    "Revenge": "Balas Dendam",
    "Dense Protagonist": "Karakter Utama Tidak Peka",
    "Secret Identity": "Identitas Rahasia",
    "Person in Hiding": "Menyembunyikan Kekuatan",
    "Overpowered": "Kekuatan Super Overpowered",
    "Anti-Hero": "Karakter Anti-Hero",
    "Romance": "Kisah Romantis",
    "Food": "Kompetisi Memasak / Kuliner",
    "Cooking": "Memasak",
    "Viking": "Latar Belakang Viking",
    "Orphan": "Panti Asuhan / Yatim Piatu",
    "Tragedy": "Tragedi / Kesedihan",
    "Drama": "Drama Emosional",
    "Happy Ending": "Ending Bahagia (Good Ending)",
    "Action": "Aksi Pertarungan",
    "Fantasy": "Fantasi",
    "Comedy": "Komedi Lucu",
    "Isekai": "Dunia Lain (Isekai)",
    "Time Travel": "Perjalanan Waktu",
    "Yuri": "Girls Love (Yuri)",
    "Historical": "Sejarah Masa Lalu",
    "School": "Kehidupan Sekolah",
    "Magic": "Sihir & Keajaiban",
    "Psychological": "Psikologis Adu Otak",
    "Thriller": "Ketegangan Thriller",
    "Gourmet": "Dunia Kuliner"
}

from pydantic import BaseModel, Field, field_validator

class QueryParseResult(BaseModel):
    media_type: str = Field(default="anime", description="'anime' or 'manga'")
    keywords: List[str] = Field(default_factory=list, description="1 to 4 concise English search keywords")
    target_tropes: List[str] = Field(default_factory=list, description="List of hyper-specific tropes or situations requested by user")
    exclude_tropes: List[str] = Field(default_factory=list, description="List of tropes or elements explicitly disliked/excluded by user")
    genres: List[str] = Field(default_factory=list, description="List of valid genres")
    anilist_tags: List[str] = Field(default_factory=list, description="List of precise AniList tag names")
    clean_keyword: Any = Field(default="", description="Short 1-2 word search string if necessary")

    @field_validator("clean_keyword", mode="before")
    def _clean_kw_validator(cls, v):
        if isinstance(v, list):
            return ", ".join([str(x) for x in v if str(x).strip()])
        return str(v or "")

class ItemEvaluation(BaseModel):
    mal_id: Optional[int] = None
    title: str = ""
    match_score: int = Field(default=85, description="Relevance score from 0 to 100 based on requested tropes")
    why_it_matches: str = Field(
        default="",
        description=(
            "Concise 1-2 sentence (max 30 words) explanation in the user prompt language explaining WHY AI CHOSE THIS ANIME. "
            "MUST explain specific character actions or story mechanisms that match the user request. "
        )
    )
    trope_tags: List[str] = Field(default_factory=list, description="2-4 matching trope tags for this item")

class RerankResult(BaseModel):
    evaluations: List[ItemEvaluation]


class AIService:
    def __init__(self):
        self.api_key = None
        self.grok_base_url = None
        self.grok_api_key = None
        self.grok_model = None
        self._check_api_key()

    def _check_api_key(self):
        load_dotenv(override=True)
        key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if key and key != "your_gemini_api_key_here" and not key.startswith("your_"):
            self.api_key = key
        else:
            self.api_key = None

        grok_url = (os.getenv("GROK_BASE_URL") or "https://api.rentalgenset.asia/v1").strip()
        grok_key = (os.getenv("GROK_API_KEY") or "sk-user-bFcH93wTtUHSP7Eo25aXh5ccHXo2rel").strip()
        grok_mod = (os.getenv("GROK_MODEL") or "grok-4.5").strip()

        if grok_url and grok_key:
            self.grok_base_url = grok_url.rstrip("/")
            self.grok_api_key = grok_key
            self.grok_model = grok_mod
        else:
            self.grok_base_url = None
            self.grok_api_key = None

        return bool(self.api_key or self.grok_api_key)

    def is_grok_active(self) -> bool:
        self._check_api_key()
        return bool(self.grok_base_url and self.grok_api_key)

    async def _fetch_key_quota(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        if not self.grok_base_url or not self.grok_api_key:
            return None
        try:
            base = self.grok_base_url.rsplit('/v1', 1)[0]
            r = await client.get(f"{base}/api/me", headers={"Authorization": f"Bearer {self.grok_api_key}"})
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    async def _call_grok_api(self, prompt: str, system_prompt: str = "", timeout_sec: float = 600.0, max_tokens: int = 0) -> Optional[str]:
        if not self.grok_base_url or not self.grok_api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.grok_model or "grok-4.5",
            "messages": messages,
            "temperature": 0.2,
            "reasoning_effort": "low"
        }
        if max_tokens > 0:
            body["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                r = await client.post(f"{self.grok_base_url}/chat/completions", json=body, headers=headers)
                if r.status_code == 200:
                    data = r.json()

                    usage = data.get("usage", {})
                    p_tokens = usage.get("prompt_tokens", 0)
                    c_tokens = usage.get("completion_tokens", 0)
                    t_tokens = usage.get("total_tokens", 0)

                    # Fetch real API key quota from /api/me
                    quota_info = await self._fetch_key_quota(client)
                    customer = quota_info.get("customer") if quota_info else None
                    label = quota_info.get("label") if quota_info else None
                    quota_obj = quota_info.get("quota", {}) if quota_info else {}
                    remaining_tokens = quota_obj.get("remaining")
                    limit_tokens = quota_obj.get("limit")

                    cust_str = f"{customer} ({label})" if customer and label else (customer or label or "API Key")
                    rem_str = f"{remaining_tokens:,} / {limit_tokens:,}" if (remaining_tokens is not None and limit_tokens) else "N/A"

                    print(f"\n=======================================================", flush=True)
                    print(f"[GROK 4.5 API TOKEN USAGE STATS]:", flush=True)
                    print(f"   * Key Owner        : {cust_str}", flush=True)
                    print(f"   * Model Used       : {self.grok_model or 'grok-4.5'}", flush=True)
                    print(f"   * Prompt Tokens    : {p_tokens}", flush=True)
                    print(f"   * Completion Tokens: {c_tokens}", flush=True)
                    print(f"   * Request Tokens   : {t_tokens}", flush=True)
                    print(f"   * Sisa Quota Key   : {rem_str}", flush=True)
                    print(f"=======================================================\n", flush=True)

                    choices = data.get("choices") or []
                    if choices and "message" in choices[0]:
                        content = choices[0]["message"].get("content", "").strip()
                        return content
                else:
                    logger.warning(f"Grok 4.5 API returned HTTP {r.status_code}: {r.text[:200]}")
                    print(f"[WARNING] Grok 4.5 API non-200 status={r.status_code}: {r.text[:200]}", flush=True)
        except httpx.TimeoutException as e:
            logger.warning(f"Grok 4.5 API TIMEOUT ({type(e).__name__}): {e}", exc_info=True)
            print(f"[WARNING] Grok 4.5 API TIMEOUT ({type(e).__name__}): {e}", flush=True)
        except httpx.ConnectError as e:
            logger.warning(f"Grok 4.5 API CONNECTION ERROR ({type(e).__name__}): {e}", exc_info=True)
            print(f"[WARNING] Grok 4.5 API CONNECTION ERROR ({type(e).__name__}): {e}", flush=True)
        except Exception as e:
            logger.warning(f"Grok 4.5 API exception ({type(e).__name__}): {e}", exc_info=True)
            print(f"[WARNING] Grok 4.5 API exception ({type(e).__name__}): {e}", flush=True)
        return None

    def _normalize_prompt(self, user_prompt: str) -> str:
        """Pre-translation normalization for typos, slang, and otaku idioms."""
        text = user_prompt.lower()
        for pattern, replacement in SLANG_TYPO_MAP.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _is_indonesian_prompt(self, prompt: str) -> bool:
        if not prompt:
            return True
        id_words = {
            'cari', 'dengan', 'yang', 'dan', 'atau', 'tanpa', 'tidak', 'gak', 'ga', 'bgt', 'banget',
            'cowok', 'cewek', 'cerita', 'alur', 'tentang', 'bisa', 'mau', 'sama', 'juga', 'balas',
            'dendam', 'peka', 'paling', 'buat', 'untuk', 'mana', 'bukan', 'bebas', 'setiap', 'bikin',
            'nyari', 'ada', 'terlampiaskan', 'sengaja', 'kekuatannya', 'teman', 'temannya'
        }
        prompt_words = set(re.findall(r'\b[a-zA-Z]{2,}\b', prompt.lower()))
        return len(prompt_words.intersection(id_words)) > 0

    def _smart_fallback_parse(self, user_prompt: str, default_media_type: str) -> QueryParseResult:
        """
        Global Natural Language Translator, Normalizer & Concept Extractor.
        Translates ANY language prompt into English and maps core narrative & emotional tropes.
        """
        normalized_prompt = self._normalize_prompt(user_prompt)
        prompt_lower = normalized_prompt.lower()
        m_type = "manga" if "manga" in prompt_lower else default_media_type
        
        try:
            translated = GoogleTranslator(source='auto', target='en').translate(normalized_prompt)
            logger.info(f"Global Translator translated prompt: '{user_prompt}' -> '{translated}'")
        except Exception as e:
            logger.warning(f"Translation failed, using original text: {str(e)}")
            translated = normalized_prompt

        mapped_keywords = []
        combined_text = f"{user_prompt} {normalized_prompt} {translated}".lower()
        
        for pattern, keywords in GLOBAL_TROPE_INTENT_MAP.items():
            if re.search(pattern, combined_text):
                for kw in keywords:
                    if kw not in mapped_keywords:
                        mapped_keywords.append(kw)

        raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', translated.lower())
        clean_words = [w for w in raw_words if w not in ENGLISH_STOP_WORDS]

        # Map precise AniList tags and genres from combined prompt text
        extracted_tags = []
        extracted_genres = []
        matched_kw_titles = []

        if re.search(r'\b(sins|sin|dosa|7 dosa|tujuh dosa|deadly sins|7 deadly|major sins|sinful)\b', combined_text):
            extracted_tags.extend(["Demons", "Super Power", "Magic", "Fantasy", "Action"])
            extracted_genres.extend(["Action", "Fantasy", "Adventure"])
            matched_kw_titles.append("Nanatsu Taizai")

        # Solo Leveling
        if re.search(r'(solo leveling|sung jinwoo|hunter.*e-rank|e-rank|tentara bayangan|shadow monarch|dungeon ganda)', combined_text):
            extracted_tags.extend(["Necromancy", "Overpowered", "Dungeon", "Action", "Super Power"])
            extracted_genres.extend(["Action", "Fantasy", "Adventure"])
            matched_kw_titles.append("Solo Leveling")

        # Mushoku Tensei
        if re.search(r'(mushoku tensei|rudeus|jobless reincarnation|pengangguran.*34|bayi.*sihir)', combined_text):
            extracted_tags.extend(["Isekai", "Reincarnation", "Magic", "Adventure"])
            extracted_genres.extend(["Action", "Fantasy", "Adventure"])
            matched_kw_titles.append("Mushoku Tensei Jobless Reincarnation")

        # Classroom of the Elite
        if re.search(r'(classroom of the elite|youzitsu|ayanokouji|poin bulanan|kelas d|memanipulasi.*belakang layar)', combined_text):
            extracted_tags.extend(["School", "Mind Games", "Psychological", "Male Protagonist"])
            extracted_genres.extend(["Drama", "Psychological"])
            matched_kw_titles.append("Classroom of the Elite")

        # Chainsaw Man
        if re.search(r'(chainsaw|gergaji|gergaji mesin|pochita|denji|pemburu iblis|keselamatan publik)', combined_text):
            extracted_tags.extend(["Demons", "Gore", "Action", "Super Power"])
            extracted_genres.extend(["Action", "Supernatural"])
            matched_kw_titles.append("Chainsaw Man")

        # Bleach / Shinigami
        if re.search(r'(bleach|shinigami|dewa kematian|hollow|ichigo|gadis pedang)', combined_text):
            extracted_tags.extend(["Supernatural", "Swordplay", "Action", "Super Power"])
            extracted_genres.extend(["Action", "Supernatural"])
            matched_kw_titles.append("Bleach")

        # No Game No Life
        if re.search(r'(no game no life|ngnl|blank|sora.*shiro|dewa.*permainan|perselisihan.*game)', combined_text):
            extracted_tags.extend(["Isekai", "Mind Games", "Gaming", "Ecchi"])
            extracted_genres.extend(["Comedy", "Fantasy", "Ecchi"])
            matched_kw_titles.append("No Game No Life")

        # Dr. Stone
        if re.search(r'(dr stone|doctor stone|senku|pembekuan batu|peradaban.*nol|ilmu pengetahuan|sains)', combined_text):
            extracted_tags.extend(["Post-Apocalyptic", "Science", "Educational", "Survival"])
            extracted_genres.extend(["Adventure", "Sci-Fi", "Comedy"])
            matched_kw_titles.append("Dr. STONE")

        # Oshi no Ko
        if re.search(r'(oshi no ko|anak idol|idol.*reinkarnasi|anak kembar.*idol|pembunuhan.*idol|industri hiburan)', combined_text):
            extracted_tags.extend(["Reincarnation", "Showbiz", "Idol", "Mystery", "Tragedy"])
            extracted_genres.extend(["Drama", "Mystery", "Supernatural"])
            matched_kw_titles.append("Oshi no Ko")

        # Code Geass
        if re.search(r'(code geass|lelouch|zero|pangeran terbuang|memerintah|geass)', combined_text):
            extracted_tags.extend(["Mecha", "Military", "Mind Games", "Super Power", "Anti-Hero"])
            extracted_genres.extend(["Action", "Sci-Fi", "Drama"])
            matched_kw_titles.append("Code Geass Lelouch")

        # Initial D
        if re.search(r'(initial d|ae86|pengantar tahu|tofu.*balapan|pembalap liar|balap mobil|toyota ae86)', combined_text):
            extracted_tags.extend(["Cars", "Motor Vehicles", "Sports"])
            extracted_genres.extend(["Sports", "Drama"])
            matched_kw_titles.append("Initial D")

        if re.search(r'\b(summoned|dipanggil|dunia lain|isekai|pahlawan|hero|another world)\b', combined_text):
            extracted_tags.extend(["Isekai", "Summoned", "Overpowered", "Magic", "Reincarnation"])
            extracted_genres.extend(["Action", "Fantasy", "Adventure"])

        if re.search(r'\b(assassin|hitman|pembunuh|taubat|tobat|berubah baik|repented|killer|former assassin|bayaran)\b', combined_text) and not re.search(r'(chainsaw|pochita|oshi no ko)', combined_text):
            extracted_tags.extend(["Assassin", "Anti-Hero", "Rehabilitation", "Action", "Martial Arts"])
            extracted_genres.extend(["Action", "Adventure", "Drama"])

        if re.search(r'\b(arrogant|sombong|angkuh|cocky|smug|pride|prideful)\b', combined_text):
            extracted_tags.extend(["Anti-Hero", "Super Power", "Magic", "School"])
            extracted_genres.extend(["Action", "Fantasy"])

        if re.search(r'\b(hides|hide|hidden|secret|disguise|menyembunyikan|sembunyi|pura-pura|lemah|rahasia)\b', combined_text) and not re.search(r'(dr stone|senku|classroom of the elite)', combined_text):
            extracted_tags.extend(["Super Power", "Isekai", "Magic", "School"])
            extracted_genres.extend(["Action", "Fantasy"])
            mapped_keywords.extend(["person in hiding", "secret identity", "hiding power"])
            matched_kw_titles.append("The Eminence in Shadow")

        if re.search(r'\b(war|warfare|ancient|peperangan|zaman kuno|perang|kerajaan|militer|military|colossal|kolosal)\b', combined_text) and not re.search(r'\b(ahli obat|apoteker|pharmacist|kusuriya)\b', combined_text):
            extracted_tags.extend(["War", "Military", "Historical", "Kingdom"])
            extracted_genres.extend(["Action", "Historical", "Fantasy", "Drama"])

        if re.search(r'\b(rich|wealth|wealthy|millionaire|billionaire|money|uang|kaya|hambur|hamburkan|sultan|mewah)\b', combined_text):
            extracted_tags.extend(["Wealth", "Economics", "Workplace"])
            extracted_genres.extend(["Comedy", "Mystery", "Slice of Life"])
            matched_kw_titles.append("Fugou Keiji Balance Unlimited")

        if re.search(r'\b(ghost|ghosts|spirit|spirits|hantu|roh|gaib|melihat hantu|melihat roh|yokai|youkai)\b', combined_text) and not re.search(r'(shinigami|bleach|hollow)', combined_text):
            extracted_tags.extend(["Supernatural", "Ghost", "Youkai", "Horror"])
            extracted_genres.extend(["Supernatural", "Horror", "Comedy"])
            matched_kw_titles.append("Mieruko Natsume Yuujinchou Mob Psycho")

        if re.search(r'\b(time loop|time travel|perjalanan waktu|pengulang waktu|memutar waktu|looping|loop|terlempar.*masa lalu|smp|tertabrak|selamatkan.*pacar)\b', combined_text):
            extracted_tags.extend(["Time Manipulation", "Time Loop", "Time Travel", "Tragedy", "Psychological"])
            extracted_genres.extend(["Sci-Fi", "Drama", "Psychological"])
            matched_kw_titles.append("Tokyo Revengers Erased Steins Gate")

        if re.search(r'\b(pura-pura pacaran|pacar sewaan|kontrak|fake relationship|fake dating|contract marriage)\b', combined_text):
            extracted_tags.extend(["Fake Relationship", "Arranged Marriage", "Romance", "Cohabitation"])
            extracted_genres.extend(["Romance", "Comedy"])

        if re.search(r'\b(gambling|judi|adu otak|mind games|psychological games|kakegurui)\b', combined_text):
            extracted_tags.extend(["Mind Games", "Gambling", "School", "Psychological"])
            extracted_genres.extend(["Psychological", "Drama", "Mystery"])

        if re.search(r'\b(dokter|doctor|obat|farmasi|pharmacist|medical|apoteker|ahli obat|diculik.*istana|kasus racun)\b', combined_text) and not re.search(r'(oshi no ko|anak idol)', combined_text):
            extracted_tags.extend(["Medicine", "Workplace", "Historical", "Investigation"])
            extracted_genres.extend(["Slice of Life", "Drama", "Mystery", "Historical"])
            matched_kw_titles.append("Kusuriya no Hitorigoto Apothecary Diaries")

        if re.search(r'\b(mafia|crime|kejahatan|kriminal|geng|gang|gangster|yakuza|bos mafia)\b', combined_text) and not re.search(r'(chainsaw|pochita)', combined_text):
            extracted_tags.extend(["Crime", "Gang", "Yakuza", "Mafia"])
            extracted_genres.extend(["Action", "Drama", "Thriller"])

        if re.search(r'\b(sepak bola|soccer|football|bluelock|haikyuu|olahraga)\b', combined_text):
            extracted_tags.extend(["Sports", "Soccer", "Athletics", "School"])
            extracted_genres.extend(["Sports", "Drama"])

        if re.search(r'\b(detektif|detective|kasus|pembunuhan|misteri|murder|mystery|penyelidikan)\b', combined_text) and not re.search(r'\b(ahli obat|apoteker|kusuriya)\b', combined_text):
            extracted_tags.extend(["Detective", "Mystery", "Crime", "Investigation"])
            extracted_genres.extend(["Mystery", "Thriller"])

        if re.search(r'\b(band|musik|music|gitar|guitarist|pemalu|shy|bocchi)\b', combined_text):
            extracted_tags.extend(["Music", "Band", "School"])
            extracted_genres.extend(["Music", "Comedy", "Slice of Life"])

        if re.search(r'(virtual reality|vr game|game virtual|terjebak.*game|trapped.*game|game online|mmorpg)', combined_text):
            extracted_tags.extend(["Virtual World", "Video Games", "Trapped in a Video Game", "MMORPG"])
            extracted_genres.extend(["Action", "Fantasy", "Sci-Fi"])
            matched_kw_titles.append("Overlord Log Horizon Sword Art Online")

        # Disambiguated Crossdressing / Dormitory (Strictly excluding 'otome game')
        if re.search(r'(nyamar|disguise|crossdress|penyamaran|kembaran|asrama.*cowo|asrama.*laki|all-boys|all boys|cross-dressing)', combined_text) and not re.search(r'(villainess|game otome|otome game)', combined_text):
            extracted_tags.extend(["Crossdressing", "Gender Bending", "Reverse Harem", "Twins", "School", "Dormitory"])
            extracted_genres.extend(["Comedy", "Romance"])
            matched_kw_titles.append("Kenka Bancho Otome Ouran High School Host Club")

        # Otome Game / Villainess (Strictly separated from crossdressing)
        if re.search(r'(villainess|penjahat wanita|game otome|otome game|ditakdirkan mati|bertahan hidup)', combined_text):
            extracted_tags.extend(["Otome Game", "Villainess", "Reincarnation", "Isekai", "Nobility"])
            extracted_genres.extend(["Comedy", "Fantasy", "Romance"])
            matched_kw_titles.append("Hamefura Otome Game Villainess")

        if re.search(r'(mata-mata|spy|keluarga palsu|membaca pikiran|telepati)', combined_text):
            extracted_tags.extend(["Spy", "Family Life", "Telepathy", "Adopted Children", "Assassin"])
            extracted_genres.extend(["Action", "Comedy"])
            matched_kw_titles.append("Spy x Family")

        if re.search(r'(otaku.*robot|mecha|programmer|merancang.*robot|robot mecha)', combined_text):
            extracted_tags.extend(["Mecha", "Isekai", "Reincarnation", "Engineering"])
            extracted_genres.extend(["Action", "Sci-Fi", "Fantasy"])
            matched_kw_titles.append("Knight's & Magic")

        if re.search(r'(raja iblis|devil|part-timer|restoran cepat saji|fast food|terdampar)', combined_text):
            extracted_tags.extend(["Reverse Isekai", "Demons", "Workplace", "Comedy"])
            extracted_genres.extend(["Comedy", "Fantasy"])
            matched_kw_titles.append("Hataraku Maou-sama Devil Part Timer")

        if re.search(r'(pensiun|pensiun pahlawan|desa|slow life|banished|hidup tenang)', combined_text):
            extracted_tags.extend(["Slow Life", "Countryside", "Retired", "Fantasy"])
            extracted_genres.extend(["Fantasy", "Slice of Life"])
            matched_kw_titles.append("Banished from the Heros Party Shin no Nakama")

        if re.search(r'(makhluk abadi|immortal|ratusan tahun|emosi manusia|frieren|beyond journey)', combined_text):
            extracted_tags.extend(["Immortal", "Elves", "Travel", "Philosophy", "Fantasy"])
            extracted_genres.extend(["Fantasy", "Drama", "Adventure"])
            matched_kw_titles.append("Sousou no Frieren Fumetsu no Anata e")

        if re.search(r'(sekolah berasrama|boarding school|dua negara|berpura-pura benci|diam-diam pacaran|juliet)', combined_text):
            extracted_tags.extend(["Boarding School", "Secret Relationship", "Enemies to Lovers", "School"])
            extracted_genres.extend(["Romance", "Comedy"])
            matched_kw_titles.append("Kishuku Gakkou no Juliet Boarding School Juliet")

        if re.search(r'\b(merchant|saudagar|pedagang|bisnis|trade|trading|ekonomi)\b', combined_text):
            extracted_tags.extend(["Economics", "Workplace", "Travel"])
            extracted_genres.extend(["Fantasy", "Adventure", "Slice of Life"])

        if re.search(r'\b(revenge|dendam|balas)\b', combined_text):
            extracted_tags.extend(["Revenge", "Anti-Hero"])
            extracted_genres.append("Action")

        if re.search(r'\b(viking|vikings|vinland)\b', combined_text):
            extracted_tags.extend(["Viking", "Historical"])
            matched_kw_titles.append("Vinland Saga")

        if re.search(r'\b(romance|romantic|romantis|cinta|peka)\b', combined_text):
            extracted_tags.extend(["Dense Protagonist", "Romance"])
            extracted_genres.append("Romance")

        if re.search(r'\b(family|keluarga|orphan|alone|sendirian)\b', combined_text) and not re.search(r'(spy|keluarga palsu)', combined_text):
            extracted_tags.extend(["Orphan", "Tragedy"])

        if re.search(r'\b(cooking|koki|memasak|food|kuliner|makanan)\b', combined_text):
            extracted_tags.extend(["Food", "Cooking"])
            extracted_genres.append("Gourmet")

        if re.search(r'\b(comedy|komedi|lucu|konyol|humor)\b', combined_text):
            extracted_tags.extend(["Comedy", "Slapstick"])
            extracted_genres.append("Comedy")

        if re.search(r'\b(sekolah|school|murid|siswa|pelajar)\b', combined_text):
            extracted_tags.extend(["School", "School Life"])
            extracted_genres.append("School")

        if re.search(r'\b(slice of life|santai|kehidupan sehari-hari|sehari-hari)\b', combined_text):
            extracted_tags.append("Slice of Life")
            extracted_genres.append("Slice of Life")

        if re.search(r'\b(petualangan|adventure|petualang|jelajah|menjelajahi)\b', combined_text):
            extracted_tags.extend(["Adventure", "Travel"])
            extracted_genres.append("Adventure")

        if re.search(r'\b(horor|horror|seram|menyeramkan)\b', combined_text):
            extracted_tags.append("Horror")
            extracted_genres.append("Horror")

        if re.search(r'\b(olahraga|sports|olahragawan|pertandingan)\b', combined_text):
            extracted_tags.append("Sports")
            extracted_genres.append("Sports")

        if re.search(r'\b(misteri|mystery|teka-teki|kasus)\b', combined_text):
            extracted_tags.append("Mystery")
            extracted_genres.append("Mystery")

        if re.search(r'\b(fantasy|fantasi)\b', combined_text):
            extracted_genres.append("Fantasy")

        if re.search(r'\b(action|aksi)\b', combined_text):
            extracted_genres.append("Action")

        # Deduplicate tags & genres
        final_tags = list(dict.fromkeys(extracted_tags))
        final_genres = list(dict.fromkeys(extracted_genres))

        final_keywords = clean_words + mapped_keywords
        unique_keywords = []
        for kw in final_keywords:
            if kw not in unique_keywords and len(kw) >= 3:
                unique_keywords.append(kw)

        if not unique_keywords:
            unique_keywords = ["fantasy"] if m_type == "manga" else ["action"]

        search_keywords = unique_keywords[:5]

        # Clean Keyword Construction: Use primary matched specific title if available, otherwise construct from unique keywords
        if matched_kw_titles:
            clean_kw = matched_kw_titles[0]
        else:
            clean_kw = " ".join(search_keywords[:3])

        logger.info(f"Global Dynamic Engine -> Tags: {final_tags}, Genres: {final_genres}, Clean Keyword: '{clean_kw}'")

        return QueryParseResult(
            media_type=m_type,
            keywords=search_keywords,
            target_tropes=unique_keywords,
            exclude_tropes=[],
            genres=final_genres,
            anilist_tags=final_tags,
            clean_keyword=clean_kw
        )

    async def parse_query(self, user_prompt: str, default_media_type: str = "anime") -> QueryParseResult:
        """
        Parses user prompt using Grok 4.5 AI if active, with smart fallback to local concept extractor.
        """
        if self.is_grok_active():
            system_prompt = (
                "You are an expert anime/manga recommendation parser AI. "
                "Analyze the user request and output ONLY a raw JSON object with keys: "
                "media_type ('anime' or 'manga'), keywords (array of 1-3 English search words), "
                "target_tropes (array of 1-3 specific tropes), exclude_tropes (array of excluded tropes), "
                "genres (array of genres like Romance, Action, Fantasy, Comedy), anilist_tags (array of AniList tags), "
                "clean_keyword (string of 1-2 key search words)."
            )
            grok_reply = await self._call_grok_api(f"Parse query: '{user_prompt}'", system_prompt)
            if grok_reply:
                try:
                    clean_json = re.sub(r'```json\s*|\s*```', '', grok_reply).strip()
                    parsed = json.loads(clean_json)
                    logger.info(f"Grok 4.5 successfully parsed query: {parsed}")
                    return QueryParseResult(
                        media_type=parsed.get("media_type") or default_media_type,
                        keywords=parsed.get("keywords") or [],
                        target_tropes=parsed.get("target_tropes") or [],
                        exclude_tropes=parsed.get("exclude_tropes") or [],
                        genres=parsed.get("genres") or [],
                        anilist_tags=parsed.get("anilist_tags") or [],
                        clean_keyword=parsed.get("clean_keyword") or ""
                    )
                except Exception as ex:
                    logger.warning(f"Grok 4.5 JSON parse error: {ex}")

        return self._smart_fallback_parse(user_prompt, default_media_type)

    async def grok_recommend(self, user_prompt: str, media_type: str = "anime") -> Optional[List[Dict[str, Any]]]:
        """
        Calls Grok 4.5 ONCE to directly recommend anime/manga titles with reasoning.
        Returns a list of dicts: [{title, why_it_matches, match_score, trope_tags}, ...]
        Falls back to None if Grok is unavailable.
        """
        if not self.is_grok_active():
            return None

        system_prompt = (
            f"You are an expert anime and manga recommendation AI with deep knowledge of narrative tropes. "
            f"The user is looking for {media_type} recommendations. "
            "Recommend the 5 BEST matching titles from your knowledge. "
            "Output ONLY a raw JSON array. Each object must have:\n"
            "- title: official English or romaji title\n"
            "- match_score: integer 70-99\n"
            "- why_it_matches: a rich 1-2 sentence explanation in the user's language detailing specific plot mechanisms or character choices that fit the user request.\n"
            "Do NOT include tags or genres (they are handled externally)."
        )

        grok_reply = await self._call_grok_api(user_prompt, system_prompt, timeout_sec=600.0, max_tokens=550)
        if not grok_reply:
            return None

        try:
            clean_json = re.sub(r'```json\s*|\s*```', '', grok_reply).strip()
            rec_list = json.loads(clean_json)
            logger.info(f"Grok 4.5 recommended {len(rec_list)} titles for query: '{user_prompt[:60]}'")
            return rec_list
        except Exception as ex:
            logger.warning(f"Grok 4.5 recommend JSON parse error: {ex} | Raw: {grok_reply[:200]}")
            return None

    async def rerank_and_explain(
        self,
        user_prompt: str,
        target_tropes: List[str],
        exclude_tropes: List[str],
        candidates: List[Dict[str, Any]]
    ) -> Dict[Any, ItemEvaluation]:
        """
        Uses Grok 4.5 AI to analyze candidates' synopses & tropes, calculate match scores,
        generate custom reasoning (why_it_matches), and extract trope tags.
        """
        if self.is_grok_active() and candidates:
            items_summary = []
            for idx, c in enumerate(candidates[:6]):
                title = c.get("title") or c.get("title_english") or "Unknown"
                syn = (c.get("synopsis") or "No synopsis available.")[:150]
                tags = ", ".join((c.get("genres") or []) + (c.get("tags") or []))[:100]
                items_summary.append(f"ID: {idx}\nTitle: {title}\nSynopsis: {syn}\nTags: {tags}\n---")

            joined_items = "\n".join(items_summary)
            prompt_text = (
                f"User Request: '{user_prompt}'\n\n"
                f"Candidate Anime/Manga List:\n{joined_items}\n\n"
                "Evaluate each candidate based on its synopsis and tags against the user request. "
                "Output ONLY a raw JSON array of objects, where each object has:\n"
                "- id: integer ID (0 to N-1 from list)\n"
                "- title: (exact title string from list)\n"
                "- match_score: integer from 65 to 99\n"
                "- why_it_matches: MAX 15 words in the user's prompt language explaining WHY this title fits.\n"
                "- trope_tags: array of 2-4 matching trope tags in English."
            )

            system_prompt = "You are an expert anime/manga trope evaluator. Output ONLY a valid JSON array of evaluations."
            grok_reply = await self._call_grok_api(prompt_text, system_prompt, timeout_sec=45.0, max_tokens=800)
            if grok_reply:
                try:
                    clean_json = re.sub(r'```json\s*|\s*```', '', grok_reply).strip()
                    eval_list = json.loads(clean_json)
                    evals = {}

                    # Fill base evaluations for all candidates
                    for idx, item in enumerate(candidates):
                        score = item.get("match_score") or max(65, 95 - (idx * 2))
                        item_key = item.get("title", "").lower().strip()
                        why_text = self._build_smart_explanation(item, target_tropes, user_prompt)
                        ev = ItemEvaluation(
                            mal_id=item.get("mal_id"),
                            title=item.get("title", ""),
                            match_score=score,
                            why_it_matches=why_text,
                            trope_tags=(item.get("tags") or item.get("genres") or [])[:3]
                        )
                        evals[item_key] = ev
                        if item.get("title_english"):
                            evals[item["title_english"].lower().strip()] = ev

                    # Overlay Grok 4.5 evaluations by exact candidate ID & title
                    for ev_dict in eval_list:
                        ev_id = ev_dict.get("id")
                        t_name = ev_dict.get("title", "")
                        matched_item = None
                        if ev_id is not None and isinstance(ev_id, int) and 0 <= ev_id < len(candidates):
                            matched_item = candidates[ev_id]

                        why_str = ev_dict.get("why_it_matches") or ""
                        score_val = int(ev_dict.get("match_score") or 88)
                        trope_tags = ev_dict.get("trope_tags") or []

                        if matched_item:
                            ev = ItemEvaluation(
                                mal_id=matched_item.get("mal_id"),
                                title=matched_item.get("title") or t_name,
                                match_score=score_val,
                                why_it_matches=why_str,
                                trope_tags=trope_tags or (matched_item.get("tags") or [])[:3]
                            )
                            mk = (matched_item.get("title") or "").lower().strip()
                            if mk:
                                evals[mk] = ev
                            if matched_item.get("title_english"):
                                evals[matched_item["title_english"].lower().strip()] = ev
                        elif t_name:
                            ev = ItemEvaluation(
                                title=t_name,
                                match_score=score_val,
                                why_it_matches=why_str,
                                trope_tags=trope_tags
                            )
                            evals[t_name.lower().strip()] = ev

                    logger.info(f"Grok 4.5 successfully evaluated {len(eval_list)} candidates with ID mapping!")
                    return evals
                except Exception as ex:
                    logger.warning(f"Grok 4.5 rerank JSON parse error: {ex}")

        evals = {}
        for idx, item in enumerate(candidates):
            score = item.get("match_score") or max(65, 98 - (idx * 2))
            item_key = item.get("title", "").lower().strip()
            why_text = self._build_smart_explanation(item, target_tropes, user_prompt)
            
            ev = ItemEvaluation(
                mal_id=item.get("mal_id"),
                title=item.get("title", ""),
                match_score=score,
                why_it_matches=why_text,
                trope_tags=(item.get("tags") or item.get("genres") or [])[:3]
            )
            evals[item_key] = ev
            if item.get("title_english"):
                evals[item["title_english"].lower().strip()] = ev
            if item.get("mal_id"):
                evals[item["mal_id"]] = ev
            if item.get("anilist_id"):
                evals[item["anilist_id"]] = ev
        return evals

    def _build_smart_explanation(self, item: Dict[str, Any], target_tropes: Optional[List[str]] = None, user_prompt: str = "") -> str:
        """
        Fast, instant (<1ms) dynamic reasoning generator explaining why AI chose this item.
        Zero external blocking HTTP calls to ensure lightning-fast responses.
        """
        title = item.get("title", "")
        syn = item.get("synopsis", "").strip()
        tags = item.get("tags") or item.get("genres") or []
        is_id = self._is_indonesian_prompt(user_prompt)

        matching_labels = []
        if target_tropes:
            for t in tags:
                for kw in target_tropes:
                    if len(kw) >= 3 and kw.lower() in t.lower() and t not in matching_labels:
                        matching_labels.append(t)

        first_sent = ""
        if syn and not syn.startswith("No synopsis"):
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', syn) if len(s.strip()) > 15]
            if sentences:
                first_sent = sentences[0]
                if len(first_sent) < 50 and len(sentences) > 1:
                    first_sent += " " + sentences[1]

        if is_id:
            formatted_labels = [TAG_TRANSLATIONS_ID.get(lbl, lbl) for lbl in matching_labels[:3]]
        else:
            formatted_labels = matching_labels[:3]

        if first_sent and formatted_labels:
            labels_str = ", ".join(formatted_labels)
            if is_id:
                return f"Alasan dipilih: Serial '{title}' mengangkat alur cerita '{first_sent}' yang secara khusus berfokus pada {labels_str}."
            else:
                return f"Why selected: '{title}' features storyline '{first_sent}' focusing specifically on {labels_str}."
        elif formatted_labels:
            labels_str = ", ".join(formatted_labels)
            if is_id:
                return f"Alasan dipilih: Serial '{title}' menonjolkan elemen alur {labels_str} yang sangat relevan."
            else:
                return f"Why selected: '{title}' features core elements of {labels_str}."
        elif first_sent:
            prefix = "Alasan dipilih" if is_id else "Why selected"
            return f"{prefix}: {first_sent}"
        else:
            genres_str = ", ".join(tags[:3]) if tags else ("cerita utama" if is_id else "main storyline")
            if is_id:
                return f"Alasan dipilih: Serial '{title}' berfokus pada tema utama {genres_str}."
            else:
                return f"Why selected: '{title}' focuses on key themes in {genres_str}."
