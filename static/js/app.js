// App Logic & API Communication
// SETTING LINK AFFILIATE (Ganti URL ini dengan link affiliate Shopee/Tokopedia/Involve Asia/Popunder Anda)
window.AFFILIATE_REDIRECT_URL = window.AFFILIATE_REDIRECT_URL || "https://shope.ee/YOUR_AFFILIATE_LINK";
const DEFAULT_FALLBACK_IMAGE = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400"><rect width="300" height="400" fill="%231e293b"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%23a855f7" font-family="sans-serif" font-size="20" font-weight="bold">No Cover</text></svg>`;

document.addEventListener("DOMContentLoaded", () => {
  const state = {
    mediaType: "anime", // 'anime' or 'manga'
    currentPrompt: "",
    isSearching: false,
  };

  // DOM Elements
  const mediaTabAnime = document.getElementById("tab-anime");
  const mediaTabManga = document.getElementById("tab-manga");
  const searchInput = document.getElementById("search-input");
  const btnSearch = document.getElementById("btn-search");
  const tropePillsContainer = document.getElementById("trope-pills");
  const resultsContainer = document.getElementById("results-container");
  const searchMetaBar = document.getElementById("search-meta-bar");
  const aiStatusBadge = document.getElementById("ai-status-badge");
  const resultsSectionTitle = document.getElementById("results-section-title");

  // News Modal DOM Elements
  const newsModal = document.getElementById("news-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const modalNewsSource = document.getElementById("modal-news-source");
  const modalNewsDate = document.getElementById("modal-news-date");
  const modalNewsTitle = document.getElementById("modal-news-title");
  const modalImageWrap = document.getElementById("modal-image-wrap");
  const modalNewsImage = document.getElementById("modal-news-image");
  const modalNewsDesc = document.getElementById("modal-news-desc");
  const modalNewsLink = document.getElementById("modal-news-link");

  // Anime Detail Modal DOM Elements
  const animeDetailModal = document.getElementById("anime-detail-modal");
  const btnCloseAnimeModal = document.getElementById("btn-close-anime-modal");
  const animeModalImg = document.getElementById("anime-modal-img");
  const animeModalScore = document.getElementById("anime-modal-score");
  const animeModalMatchScore = document.getElementById("anime-modal-match-score");
  const animeModalTitle = document.getElementById("anime-modal-title");
  const animeModalSubtitle = document.getElementById("anime-modal-subtitle");
  const animeModalEpisodes = document.getElementById("anime-modal-episodes");
  const animeModalStatus = document.getElementById("anime-modal-status");
  const animeModalCategory = document.getElementById("anime-modal-category");
  const animeModalGenres = document.getElementById("anime-modal-genres");
  const animeModalSynopsis = document.getElementById("anime-modal-synopsis");
  const animeModalAiBox = document.getElementById("anime-modal-ai-box");
  const animeModalAiMatch = document.getElementById("anime-modal-ai-match");
  const animeModalFreeStreams = document.getElementById("anime-modal-free-streams");
  const animeModalPremiumStreams = document.getElementById("anime-modal-premium-streams");
  const animeModalAnilistLink = document.getElementById("anime-modal-anilist-link");
  const animeModalMalLink = document.getElementById("anime-modal-mal-link");

  // Language Switcher DOM Elements
  const langBtnId = document.getElementById("lang-btn-id");
  const langBtnEn = document.getElementById("lang-btn-en");
  state.language = localStorage.getItem("anitrope_lang") || "id";

  // Event Listeners Registration (MUST BE FIRST)
  if (langBtnId) langBtnId.addEventListener("click", () => switchLanguage("id"));
  if (langBtnEn) langBtnEn.addEventListener("click", () => switchLanguage("en"));

  if (mediaTabAnime) mediaTabAnime.addEventListener("click", () => switchMedia("anime"));
  if (mediaTabManga) mediaTabManga.addEventListener("click", () => switchMedia("manga"));
  
  if (btnSearch) btnSearch.addEventListener("click", handleSearch);
  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleSearch();
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener("click", closeNewsModal);
  }
  if (newsModal) {
    newsModal.addEventListener("click", (e) => {
      if (e.target === newsModal) closeNewsModal();
    });
  }

  if (btnCloseAnimeModal) {
    btnCloseAnimeModal.addEventListener("click", closeAnimeDetailModal);
  }
  if (animeDetailModal) {
    animeDetailModal.addEventListener("click", (e) => {
      if (e.target === animeDetailModal) closeAnimeDetailModal();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeNewsModal();
      closeAnimeDetailModal();
    }
  });

  // Info Modals Logic (About, Privacy, Disclaimer)
  setupInfoModal("nav-about", "foot-about", "about-modal", "btn-close-about");
  setupInfoModal("nav-privacy", "foot-privacy", "privacy-modal", "btn-close-privacy");
  setupInfoModal("nav-disclaimer", "foot-disclaimer", "disclaimer-modal", "btn-close-disclaimer");

  // Home Nav Reset
  const resetHome = (e) => {
    if (e) e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (state.currentPrompt) {
      if (searchInput) searchInput.value = "";
      state.currentPrompt = "";
      loadFeaturedContent();
    }
  };
  document.getElementById("nav-home")?.addEventListener("click", resetHome);
  document.getElementById("foot-home")?.addEventListener("click", resetHome);

  function setupInfoModal(navId, footId, modalId, closeBtnId) {
    const modal = document.getElementById(modalId);
    const closeBtn = document.getElementById(closeBtnId);
    const openModal = (e) => {
      if (e) e.preventDefault();
      if (modal) modal.style.display = "flex";
    };
    const closeModal = (e) => {
      if (e) e.preventDefault();
      if (modal) modal.style.display = "none";
    };

    document.getElementById(navId)?.addEventListener("click", openModal);
    document.getElementById(footId)?.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
      });
    }
  }

  // Initial Startup
  initHealthCheck();
  loadPresetTropes();
  loadFeaturedContent();
  initNewsFeed();
  switchLanguage(state.language);

  // Switch Language (ID / EN)
  function switchLanguage(lang) {
    state.language = lang;
    localStorage.setItem("anitrope_lang", lang);
    if (lang === "id") {
      if (langBtnId) langBtnId.classList.add("active");
      if (langBtnEn) langBtnEn.classList.remove("active");
    } else {
      if (langBtnEn) langBtnEn.classList.add("active");
      if (langBtnId) langBtnId.classList.remove("active");
    }
    updateUIStrings();
  }

  function updateUIStrings() {
    try {
      const isEn = state.language === "en";
      const navHome = document.getElementById("nav-home");
      const navAbout = document.getElementById("nav-about");
      const navPrivacy = document.getElementById("nav-privacy");
      const navDisclaimer = document.getElementById("nav-disclaimer");
      const heroTitle = document.querySelector(".hero-title");
      const heroDesc = document.querySelector(".hero-desc");
      const sectionLabelExamples = document.querySelector(".preset-tropes-section .section-label");
      const modalSynopsisH3 = document.querySelector(".anime-modal-section h3");
      const modalAiHeader = document.querySelector(".ai-match-header");
      const modalWatchH3 = document.querySelector(".streaming-section h3");

      if (navHome) navHome.textContent = isEn ? "Home" : "Beranda";
      if (navAbout) navAbout.textContent = isEn ? "About" : "Tentang";
      if (navPrivacy) navPrivacy.textContent = isEn ? "Privacy" : "Privasi";
      if (navDisclaimer) navDisclaimer.textContent = isEn ? "Disclaimer" : "Penafian";

      if (heroTitle) {
        heroTitle.innerHTML = isEn 
          ? 'Find Titles Based on <span>Specific Tropes & Situations</span>'
          : 'Temukan Judul Berdasarkan <span>Situasi & Trope Spesifik</span>';
      }
      if (heroDesc) {
        heroDesc.textContent = isEn
          ? 'Tired of generic categories on MyAnimeList? Describe any unique situation or trope you want in natural language.'
          : 'Bosan dengan kategori umum MyAnimeList? Tuliskan situasi atau trope spesifik yang Anda inginkan dalam bahasa alami.';
      }

      if (sectionLabelExamples) {
        sectionLabelExamples.innerHTML = isEn ? '<span>💡</span> Try Example Specific Searches:' : '<span>💡</span> Coba Contoh Pencarian Spesifik:';
      }

      if (btnSearch) {
        btnSearch.innerHTML = isEn ? '<span>⚡</span> Search Trope' : '<span>⚡</span> Cari Trope';
      }

      if (searchInput) {
        if (state.mediaType === "anime") {
          searchInput.placeholder = isEn 
            ? 'Example: "Romance anime with dense MC and conclusive ending..."'
            : 'Contoh: "Cari anime romantis MC tidak peka ending tuntas..."';
        } else {
          searchInput.placeholder = isEn 
            ? 'Example: "Isekai manga where MC focuses on shopkeeping/merchant..."'
            : 'Contoh: "Cari manga isekai MC fokus jualan/bisnis..."';
        }
      }

      if (resultsSectionTitle && !state.currentPrompt) {
        resultsSectionTitle.textContent = isEn 
          ? (state.mediaType === "anime" ? "🔥 Trending & Top Rated Anime" : "🔥 Trending & Top Rated Manga")
          : (state.mediaType === "anime" ? "🔥 Trending & Top Rated Anime" : "🔥 Trending & Top Rated Manga");
      }

      if (modalSynopsisH3) modalSynopsisH3.textContent = isEn ? "📖 Summary / Synopsis" : "📖 Ringkasan / Sinopsis";
      if (modalAiHeader) modalAiHeader.textContent = isEn ? "💡 Why It Matches Your Trope:" : "💡 Kenapa Cocok dengan Trope:";
      if (modalWatchH3) modalWatchH3.textContent = isEn ? "📺 Official Streaming Platforms (Where to Watch)" : "📺 Tempat Nonton Resmi (Where to Watch)";

      renderPresetTropes();
    } catch (err) {
      console.warn("Error updating UI strings:", err);
    }
  }

  function formatWhyText(text) {
    if (!text) return "";
    if (state.language === "en") {
      return text
        .replace(/^Alasan dipilih:\s*/gi, "Why selected: ")
        .replace(/mengangkat alur cerita/gi, "features storyline")
        .replace(/yang secara khusus berfokus pada/gi, "focusing specifically on")
        .replace(/menonjolkan elemen alur/gi, "highlights story elements of")
        .replace(/yang sangat relevan/gi, "which are highly relevant")
        .replace(/berfokus pada tema utama/gi, "focuses on main themes in");
    } else {
      return text
        .replace(/^Why selected:\s*/gi, "Alasan dipilih: ")
        .replace(/features storyline/gi, "mengangkat alur cerita")
        .replace(/focusing specifically on/gi, "yang secara khusus berfokus pada")
        .replace(/highlights story elements of/gi, "menonjolkan elemen alur")
        .replace(/which are highly relevant/gi, "yang sangat relevan")
        .replace(/focuses on main themes in/gi, "berfokus pada tema utama");
    }
  }

  // Switch Media (Anime / Manga)
  function switchMedia(type) {
    if (state.mediaType === type) return;
    state.mediaType = type;
    
    if (type === "anime") {
      mediaTabAnime.classList.add("active");
      mediaTabManga.classList.remove("active");
    } else {
      mediaTabManga.classList.add("active");
      mediaTabAnime.classList.remove("active");
    }

    updateUIStrings();

    if (state.currentPrompt) {
      handleSearch();
    } else {
      loadFeaturedContent();
    }
  }

  // Health Check
  async function initHealthCheck() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (aiStatusBadge) {
        if (data.gemini_active) {
          aiStatusBadge.innerHTML = `<span class="status-dot"></span> AI Engine: Gemini 2.0 Flash`;
        } else {
          aiStatusBadge.innerHTML = `<span class="status-dot" style="background:#fbbf24;box-shadow:0 0 8px #fbbf24;"></span> Keyword Rerank Engine (No API Key)`;
        }
      }
    } catch (e) {
      console.warn("Health check error:", e);
    }
  }

  // Load Preset Tropes
  let cachedPresetTropes = [];

  async function loadPresetTropes() {
    try {
      const res = await fetch("/api/tropes");
      cachedPresetTropes = await res.json();
      renderPresetTropes();
    } catch (e) {
      console.error("Error loading tropes:", e);
    }
  }

  function renderPresetTropes() {
    if (!tropePillsContainer || !cachedPresetTropes || !cachedPresetTropes.length) return;
    const isEn = state.language === "en";
    tropePillsContainer.innerHTML = "";
    
    cachedPresetTropes.forEach(t => {
      const pill = document.createElement("button");
      pill.className = "trope-pill";
      const label = isEn ? (t.label_en || t.label) : t.label;
      const prompt = isEn ? (t.prompt_en || t.prompt) : t.prompt;
      pill.innerHTML = `<span>✨</span> ${escapeHtml(label)}`;
      pill.addEventListener("click", () => {
        if (t.type) {
          state.mediaType = t.type;
          if (t.type === "anime") {
            mediaTabAnime.classList.add("active");
            mediaTabManga.classList.remove("active");
          } else {
            mediaTabManga.classList.add("active");
            mediaTabAnime.classList.remove("active");
          }
        }
        searchInput.value = prompt;
        handleSearch();
      });
      tropePillsContainer.appendChild(pill);
    });
  }

  // Load Featured Content on startup
  async function loadFeaturedContent() {
    renderSkeletonLoading(6);
    searchMetaBar.style.display = "none";
    resultsSectionTitle.textContent = `🔥 Trending & Top Rated ${state.mediaType === "anime" ? "Anime" : "Manga"}`;

    try {
      const res = await fetch(`/api/featured?media_type=${state.mediaType}`);
      const data = await res.json();
      renderFeaturedGrid(data.items);
    } catch (e) {
      showToast("Gagal memuat rekomendasi awal.");
    }
  }

  // Main Search Handler
  async function handleSearch() {
    const prompt = searchInput.value.trim();
    if (!prompt) {
      showToast("Silakan masukkan query situasi atau trope yang ingin dicari.");
      return;
    }

    state.currentPrompt = prompt;
    state.isSearching = true;
    btnSearch.disabled = true;
    btnSearch.innerHTML = `<span>⏳</span> Menganalisis...`;
    
    renderSkeletonLoading(5);
    resultsSectionTitle.textContent = `🎯 Hasil Pencarian Hyper-Specific Trope`;

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt,
          media_type: state.mediaType
        })
      });

      if (!res.ok) throw new Error("Search request failed");

      const data = await res.json();
      renderSearchMeta(data.search_meta);
      renderResultsGrid(data.results);

    } catch (e) {
      console.error("Search error:", e);
      showToast("Gagal memproses pencarian. Pastikan server terhubung.");
      renderEmptyState("Terjadi kesalahan saat memproses query.");
    } finally {
      state.isSearching = false;
      btnSearch.disabled = false;
      btnSearch.innerHTML = `<span>⚡</span> Cari Trope`;
    }
  }

  // Render Search Meta Info Bar
  function renderSearchMeta(meta) {
    if (!meta) {
      searchMetaBar.style.display = "none";
      return;
    }
    
    searchMetaBar.style.display = "flex";
    const keywordsHtml = (meta.keywords || []).map(k => `<span class="meta-chip">#${k}</span>`).join(" ");
    const tropesHtml = (meta.target_tropes || []).map(t => `<span class="meta-chip" style="color:#c084fc;border-color:rgba(168,85,247,0.4);background:rgba(168,85,247,0.12)">🎯 ${t}</span>`).join(" ");

    searchMetaBar.innerHTML = `
      <div class="meta-title">
        Strategi AI: Kategori <strong>${meta.media_type.toUpperCase()}</strong>
      </div>
      <div class="meta-tags">
        ${keywordsHtml}
        ${tropesHtml}
      </div>
    `;
  }

  // Render Results Cards Grid
  function renderResultsGrid(results) {
    if (!results || results.length === 0) {
      renderEmptyState("Tidak ditemukan judul yang cocok dengan kombinasi trope ini. Coba ubah kata kunci.");
      return;
    }

    resultsContainer.innerHTML = "";
    results.forEach((item) => {
      const card = document.createElement("div");
      card.className = "card";

      const fallbackImg = DEFAULT_FALLBACK_IMAGE;
      const imageSrc = item.image_url || fallbackImg;
      const matchScore = item.match_score || 80;
      
      const malScoreBadge = item.score ? `MAL ★ ${item.score}` : "";
      const anilistScoreBadge = item.anilist_score ? `AL ★ ${item.anilist_score}` : "";
      const scoreDisplay = [malScoreBadge, anilistScoreBadge].filter(Boolean).join(" | ") || "★ N/A";
      
      const episodeText = item.episodes ? `${item.episodes} ${item.media_category === 'anime' ? 'Eps' : 'Ch'}` : (item.status || "");

      // Combined genre & AniList trope tags
      const genreChips = (item.genres || []).slice(0, 2).map(t => `<span class="trope-chip">${t}</span>`).join("");
      const tagChips = (item.tags || item.trope_tags || []).slice(0, 3).map(t => `<span class="anilist-tag-chip">🏷️ ${t}</span>`).join("");

      const malUrl = item.url || (item.mal_id ? `https://myanimelist.net/${item.media_category || 'anime'}/${item.mal_id}` : null);
      const anilistUrl = item.anilist_url || (item.anilist_id ? `https://anilist.co/${item.media_category || 'anime'}/${item.anilist_id}` : null);

      card.innerHTML = `
        <div class="card-image-wrap">
          <img class="card-image" src="${imageSrc}" alt="${escapeHtml(item.title)}" onerror="this.onerror=null;this.src=DEFAULT_FALLBACK_IMAGE;" loading="lazy">
          <div class="card-image-overlay"></div>
          <div class="score-badge">${scoreDisplay}</div>
          <div class="match-score-pill">🔥 ${matchScore}% Trope Match</div>
        </div>
        <div class="card-body">
          <h3 class="card-title">${escapeHtml(item.title_english || item.title)}</h3>
          <div class="card-sub-title">${escapeHtml(item.title)}</div>
          
          <div class="trope-tags">
            ${genreChips}
            ${tagChips}
          </div>

          <p class="card-synopsis">${escapeHtml(item.synopsis || 'Sinopsis tidak tersedia.')}</p>

          <div class="ai-match-box">
            <div class="ai-match-header">${state.language === 'en' ? '💡 Why It Matches Your Trope:' : '💡 Kenapa Cocok:'}</div>
            <div class="ai-match-text">${escapeHtml(formatWhyText(item.why_it_matches || (state.language === 'en' ? 'Matches your search criteria and trope preferences.' : 'Cocok dengan kriteria pencarian dan preferensi trope yang Anda cari.')))}</div>
          </div>

          <div class="card-footer">
            <div class="card-meta-info">${episodeText}</div>
            <div class="card-source-links">
              ${anilistUrl ? `<a href="${anilistUrl}" target="_blank" rel="noopener" class="btn-anilist-link">AniList ↗</a>` : ''}
              ${malUrl ? `<a href="${malUrl}" target="_blank" rel="noopener" class="btn-mal-link">MAL ↗</a>` : ''}
            </div>
          </div>
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (e.target.closest("a")) return;
        openAnimeDetailModal(item);
      });

      resultsContainer.appendChild(card);
    });
  }

  // Render Featured Items (Initial state)
  function renderFeaturedGrid(items) {
    if (!items || items.length === 0) return;
    resultsContainer.innerHTML = "";
    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "card";
      const fallbackImg = DEFAULT_FALLBACK_IMAGE;
      const scoreBadge = item.score ? `MAL ★ ${item.score}` : (item.anilist_score ? `AL ★ ${item.anilist_score}` : "N/A");
      const tropeChips = (item.genres || []).slice(0, 3)
        .map(t => `<span class="trope-chip">${t}</span>`).join("");

      const malUrl = item.url;
      const anilistUrl = item.anilist_url;

      card.innerHTML = `
        <div class="card-image-wrap">
          <img class="card-image" src="${item.image_url || fallbackImg}" alt="${escapeHtml(item.title)}" onerror="this.onerror=null;this.src=DEFAULT_FALLBACK_IMAGE;">
          <div class="card-image-overlay"></div>
          <div class="score-badge">${scoreBadge}</div>
        </div>
        <div class="card-body">
          <h3 class="card-title">${escapeHtml(item.title_english || item.title)}</h3>
          <div class="card-sub-title">${escapeHtml(item.title)}</div>
          
          <div class="trope-tags">
            ${tropeChips}
          </div>

          <p class="card-synopsis">${escapeHtml(item.synopsis || 'Sinopsis tidak tersedia.')}</p>

          <div class="card-footer">
            <div class="card-meta-info">${item.status || ''}</div>
            <div class="card-source-links">
              ${anilistUrl ? `<a href="${anilistUrl}" target="_blank" rel="noopener" class="btn-anilist-link">AniList ↗</a>` : ''}
              ${malUrl ? `<a href="${malUrl}" target="_blank" rel="noopener" class="btn-mal-link">MAL ↗</a>` : ''}
            </div>
          </div>
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (e.target.closest("a")) return;
        openAnimeDetailModal(item);
      });

      resultsContainer.appendChild(card);
    });
  }

  // Open Anime Detail Modal
  function openAnimeDetailModal(item) {
    if (!animeDetailModal) return;

    const fallbackImg = DEFAULT_FALLBACK_IMAGE;
    animeModalImg.src = item.image_url || fallbackImg;
    animeModalImg.onerror = () => {
      animeModalImg.onerror = null;
      animeModalImg.src = DEFAULT_FALLBACK_IMAGE;
    };

    const malScoreBadge = item.score ? `MAL ★ ${item.score}` : "";
    const anilistScoreBadge = item.anilist_score ? `AL ★ ${item.anilist_score}` : "";
    animeModalScore.textContent = [malScoreBadge, anilistScoreBadge].filter(Boolean).join(" | ") || "★ N/A";

    const matchScore = item.match_score || 85;
    animeModalMatchScore.textContent = `🔥 ${matchScore}% Trope Match`;

    animeModalTitle.textContent = item.title_english || item.title;
    animeModalSubtitle.textContent = item.title !== (item.title_english || item.title) ? item.title : (item.title_romaji || "");

    const categoryText = (item.media_category || item.type || "anime").toUpperCase();
    const episodeText = item.episodes ? `📺 ${item.episodes} ${categoryText === 'MANGA' ? 'Chapters' : 'Episodes'}` : "📺 -";
    animeModalEpisodes.textContent = episodeText;
    animeModalStatus.textContent = item.status || "FINISHED";
    animeModalCategory.textContent = categoryText;

    // Genres & Trope Tags
    const genreChips = (item.genres || []).map(g => `<span class="trope-chip">${escapeHtml(g)}</span>`).join("");
    const tagChips = (item.tags || item.trope_tags || []).map(t => `<span class="anilist-tag-chip">🏷️ ${escapeHtml(t)}</span>`).join("");
    animeModalGenres.innerHTML = genreChips + tagChips;

    animeModalSynopsis.textContent = item.synopsis || "Sinopsis tidak tersedia.";

    if (item.why_it_matches) {
      animeModalAiMatch.textContent = formatWhyText(item.why_it_matches);
      animeModalAiBox.style.display = "block";
    } else {
      animeModalAiBox.style.display = "none";
    }

    // External Source links
    const malUrl = item.url || (item.mal_id ? `https://myanimelist.net/${item.media_category || 'anime'}/${item.mal_id}` : null);
    const anilistUrl = item.anilist_url || (item.anilist_id ? `https://anilist.co/${item.media_category || 'anime'}/${item.anilist_id}` : null);

    if (anilistUrl) {
      animeModalAnilistLink.href = anilistUrl;
      animeModalAnilistLink.style.display = "inline-flex";
    } else {
      animeModalAnilistLink.style.display = "none";
    }

    if (malUrl) {
      animeModalMalLink.href = malUrl;
      animeModalMalLink.style.display = "inline-flex";
    } else {
      animeModalMalLink.style.display = "none";
    }

    // Render Free & Premium Streaming Links
    renderStreamingButtons(item);

    animeDetailModal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeAnimeDetailModal() {
    if (!animeDetailModal) return;
    animeDetailModal.style.display = "none";
    document.body.style.overflow = "auto";
  }

  function renderStreamingButtons(item) {
    if (!animeModalFreeStreams || !animeModalPremiumStreams) return;

    animeModalFreeStreams.innerHTML = "";
    animeModalPremiumStreams.innerHTML = "";

    const titleEncoded = encodeURIComponent(item.title_english || item.title);
    let streams = item.streaming_links || [];

    // Fallback streaming links if externalLinks missing
    if (!streams || streams.length === 0) {
      streams = [
        { site: "YouTube (Muse Asia)", url: `https://www.youtube.com/results?search_query=Muse+Asia+${titleEncoded}`, is_free: true },
        { site: "YouTube (Ani-One)", url: `https://www.youtube.com/results?search_query=Ani-One+${titleEncoded}`, is_free: true },
        { site: "Bilibili / Bstation", url: `https://www.bilibili.tv/en/search?q=${titleEncoded}`, is_free: true },
        { site: "iQIYI", url: `https://www.iq.com/search?query=${titleEncoded}`, is_free: true },
        { site: "Crunchyroll", url: `https://www.crunchyroll.com/search?q=${titleEncoded}`, is_free: false },
        { site: "Netflix", url: `https://www.netflix.com/search?q=${titleEncoded}`, is_free: false }
      ];
    }

    const freeList = streams.filter(s => s.is_free);
    const premiumList = streams.filter(s => !s.is_free);

    if (freeList.length === 0) {
      animeModalFreeStreams.innerHTML = `<span style="font-size:0.8rem;color:var(--text-muted);">Tidak ada link nonton gratis langsung. Coba cari di YouTube Muse Asia / Ani-One.</span>`;
    } else {
      freeList.forEach(s => {
        const btn = createStreamButton(s, true);
        animeModalFreeStreams.appendChild(btn);
      });
    }

    if (premiumList.length === 0) {
      animeModalPremiumStreams.innerHTML = `<span style="font-size:0.8rem;color:var(--text-muted);">Tidak ada platform premium terdaftar.</span>`;
    } else {
      premiumList.forEach(s => {
        const btn = createStreamButton(s, false);
        animeModalPremiumStreams.appendChild(btn);
      });
    }
  }

  function createStreamButton(stream, isFree) {
    const btn = document.createElement("a");
    btn.className = `btn-stream-link ${isFree ? 'btn-stream-free' : 'btn-stream-premium'}`;
    btn.target = "_blank";
    btn.rel = "noopener sponsored";

    const icon = isFree ? "▶" : "🔒";
    const siteName = stream.site || "Stream";
    btn.innerHTML = `<span>${icon}</span> ${escapeHtml(siteName)}`;

    const targetAffiliate = stream.affiliate_url || window.AFFILIATE_REDIRECT_URL;
    const isConfigured = targetAffiliate && targetAffiliate !== "#" && !targetAffiliate.includes("YOUR_AFFILIATE_LINK");
    let clickedOnce = false;

    btn.addEventListener("click", (e) => {
      if (isConfigured && !clickedOnce) {
        e.preventDefault();
        clickedOnce = true;
        btn.classList.add("clicked-once");
        btn.innerHTML = `<span>▶</span> Lanjut Nonton ${escapeHtml(siteName)}`;
        window.open(targetAffiliate, "_blank");
      } else if (isConfigured && clickedOnce) {
        e.preventDefault();
        window.open(stream.url || "#", "_blank");
      }
    });

    if (!isConfigured) {
      btn.href = stream.url || "#";
    }

    return btn;
  }

  // Skeleton Loading Grid
  function renderSkeletonLoading(count = 5) {
    resultsContainer.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const skel = document.createElement("div");
      skel.className = "skeleton-card";
      skel.innerHTML = `
        <div class="skeleton-box skeleton-img"></div>
        <div class="skeleton-box skeleton-title"></div>
        <div class="skeleton-box skeleton-text-short"></div>
        <div class="skeleton-box skeleton-box-ai"></div>
        <div class="skeleton-box skeleton-text"></div>
        <div class="skeleton-box skeleton-text-short"></div>
      `;
      resultsContainer.appendChild(skel);
    }
  }

  // Empty State
  function renderEmptyState(message) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>Hasil Tidak Ditemukan</h3>
        <p>${message}</p>
      </div>
    `;
  }

  // Toast System
  function showToast(message) {
    let toastContainer = document.querySelector(".toast-container");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.className = "toast-container";
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<span>💡</span> ${escapeHtml(message)}`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3500);
  }

  // Escape HTML helper
  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // ==========================================
  // LIVE ANIME NEWS TICKER & MODAL LOGIC
  // ==========================================
  async function initNewsFeed() {
    const tickerTrack = document.getElementById("news-ticker-track");
    if (!tickerTrack) return;

    try {
      const res = await fetch("/api/news");
      if (res.ok) {
        const data = await res.json();
        if (data.items && data.items.length > 0) {
          renderNewsTicker(data.items);
          return;
        }
      }
    } catch (e) {
      console.error("Failed to load news feed, retrying in 2s:", e);
    }

    // Auto-retry once after 2.5 seconds if server was warming up
    setTimeout(async () => {
      try {
        const res = await fetch("/api/news");
        if (res.ok) {
          const data = await res.json();
          if (data.items && data.items.length > 0) {
            renderNewsTicker(data.items);
          }
        }
      } catch (err) {
        console.error("Retry news fetch failed:", err);
      }
    }, 2500);
  }

  function renderNewsTicker(items) {
    const tickerTrack = document.getElementById("news-ticker-track");
    if (!tickerTrack) return;

    tickerTrack.innerHTML = "";
    
    // Duplicate array for seamless infinite marquee scrolling
    const newsList = [...items, ...items];

    newsList.forEach((item, index) => {
      const sourceClass = (item.source || "").toLowerCase().includes("crunchyroll") ? "crunchyroll" : "";
      const el = document.createElement("a");
      el.className = "news-ticker-item";
      el.href = "#";
      const imgTag = item.image_url ? `<img class="news-ticker-thumb" src="${escapeHtml(item.image_url)}" alt="News thumbnail" />` : "";
      el.innerHTML = `
        ${imgTag}
        <span class="news-source-badge ${sourceClass}">${escapeHtml(item.source)}</span>
        <span>${escapeHtml(item.title)}</span>
        <span style="color: var(--border-glass); margin: 0 0.5rem;">•</span>
      `;
      el.addEventListener("click", (e) => {
        e.preventDefault();
        openNewsModal(item);
      });
      tickerTrack.appendChild(el);
    });
  }

  function openNewsModal(item) {
    if (!newsModal) return;

    const sourceClass = (item.source || "").toLowerCase().includes("crunchyroll") ? "crunchyroll" : "";
    modalNewsSource.className = `news-source-badge ${sourceClass}`;
    modalNewsSource.textContent = item.source;

    modalNewsDate.textContent = item.pub_date || "Terbaru";
    modalNewsTitle.textContent = item.title;
    modalNewsDesc.textContent = item.description || "Klik 'Baca Selengkapnya di Artikel Asli' untuk membaca berita selengkapnya.";
    modalNewsLink.href = item.link || "#";

    if (item.image_url) {
      modalNewsImage.src = item.image_url;
      modalImageWrap.style.display = "block";
    } else {
      modalImageWrap.style.display = "none";
    }

    newsModal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeNewsModal() {
    if (!newsModal) return;
    newsModal.style.display = "none";
    document.body.style.overflow = "auto";
  }
});
