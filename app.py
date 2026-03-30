import streamlit as st
import json
import time
import re
import io
import csv
import zipfile
from datetime import datetime

# Import local modules
from scraper import scrape_url, extract_structure, count_words
from serp_api import get_top_results
from brief_generator import generate_brief
from export_utils import export_to_docx, export_to_html, export_to_raw_html
from site_analyzer import analyze_site



# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SEO Brief Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f766e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        opacity: 0.85;
        margin-top: 0.5rem;
        font-size: 1rem;
    }
    .brief-section {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .brief-section h3 {
        color: #0f172a;
        font-weight: 700;
        margin-bottom: 0.75rem;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f766e;
    }
    .metric-card .label {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📝 SEO Brief Generator</h1>
    <p>Générez des briefs SEO optimisés basés sur l'analyse concurrentielle</p>
</div>
""", unsafe_allow_html=True)

# ── Session State Init ───────────────────────────────────────────────────────
if "briefs" not in st.session_state:
    st.session_state.briefs = []
if "bulk_briefs" not in st.session_state:
    st.session_state.bulk_briefs = []

# ── Sidebar: API Keys & Global Settings ──────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    anthropic_key = st.text_input(
        "Clé API Anthropic",
        type="password",
        help="Votre clé API Claude pour la génération de briefs"
    )
    dataforseo_login = st.text_input(
        "DataForSEO Login",
        type="password",
        help="Votre login DataForSEO"
    )
    dataforseo_password = st.text_input(
        "DataForSEO Password",
        type="password",
        help="Votre mot de passe DataForSEO"
    )

    st.markdown("---")
    st.markdown("### 🌐 Site cible")
    target_site_url = st.text_input(
        "URL du site cible",
        placeholder="https://www.monsite.fr",
        help="URL du site sur lequel le contenu sera publié"
    )
    brand_name = st.text_input(
        "Nom de la marque / entreprise",
        placeholder="Ma Marque",
        help="Utilisé pour le H2 de marque avant la FAQ"
    )

    st.markdown("---")
    st.markdown("### 📋 Options du brief")

    detail_level = st.radio(
        "Niveau de détail",
        ["Titres H2/H3 uniquement", "Titres + indications de contenu"],
        index=1
    )

    include_faq = st.checkbox("Inclure une FAQ", value=True)
    if include_faq:
        faq_count = st.slider("Nombre de questions FAQ", 3, 5, 3)
    else:
        faq_count = 0

    include_brand_section = st.checkbox(
        "Inclure un H2 marque avant la FAQ",
        value=True,
        help="Ajoute un dernier H2 mettant en avant votre marque"
    )

    st.markdown("---")
    st.markdown("### 🔍 Source concurrentielle")
    source_mode = st.radio(
        "Mode d'analyse",
        ["Top 5 SERP (DataForSEO)", "URLs manuelles"],
        index=0
    )

    search_engine_location = st.selectbox(
        "Localisation Google",
        [
            "🇫🇷 France",
            "🇧🇪 Belgique (FR)", "🇧🇪 Belgique (NL)",
            "🇨🇭 Suisse (FR)", "🇨🇭 Suisse (DE)", "🇨🇭 Suisse (IT)",
            "🇨🇦 Canada (FR)", "🇨🇦 Canada (EN)",
            "🇱🇺 Luxembourg",
            "🇺🇸 États-Unis", "🇬🇧 Royaume-Uni", "🇮🇪 Irlande",
            "🇩🇪 Allemagne", "🇦🇹 Autriche",
            "🇪🇸 Espagne", "🇲🇽 Mexique", "🇦🇷 Argentine", "🇨🇴 Colombie", "🇨🇱 Chili",
            "🇮🇹 Italie",
            "🇵🇹 Portugal", "🇧🇷 Brésil",
            "🇳🇱 Pays-Bas",
            "🇵🇱 Pologne", "🇨🇿 République Tchèque", "🇷🇴 Roumanie", "🇭🇺 Hongrie",
            "🇸🇪 Suède", "🇳🇴 Norvège", "🇩🇰 Danemark", "🇫🇮 Finlande",
            "🇷🇺 Russie", "🇺🇦 Ukraine",
            "🇹🇷 Turquie",
            "🇯🇵 Japon", "🇰🇷 Corée du Sud", "🇨🇳 Chine",
            "🇮🇳 Inde", "🇮🇩 Indonésie", "🇹🇭 Thaïlande", "🇻🇳 Vietnam",
            "🇦🇺 Australie", "🇳🇿 Nouvelle-Zélande",
            "🇲🇦 Maroc", "🇹🇳 Tunisie", "🇩🇿 Algérie",
            "🇸🇦 Arabie Saoudite", "🇦🇪 Émirats Arabes Unis", "🇪🇬 Égypte",
            "🇿🇦 Afrique du Sud", "🇳🇬 Nigeria",
            "🇮🇱 Israël",
            "🇸🇬 Singapour", "🇲🇾 Malaisie", "🇵🇭 Philippines",
        ],
        index=0
    )
    # (se_domain, language_code, location_code) — DataForSEO codes
    location_map = {
        "🇫🇷 France": ("google.fr", "fr", 2250),
        "🇧🇪 Belgique (FR)": ("google.be", "fr", 2056),
        "🇧🇪 Belgique (NL)": ("google.be", "nl", 2056),
        "🇨🇭 Suisse (FR)": ("google.ch", "fr", 2756),
        "🇨🇭 Suisse (DE)": ("google.ch", "de", 2756),
        "🇨🇭 Suisse (IT)": ("google.ch", "it", 2756),
        "🇨🇦 Canada (FR)": ("google.ca", "fr", 2124),
        "🇨🇦 Canada (EN)": ("google.ca", "en", 2124),
        "🇱🇺 Luxembourg": ("google.lu", "fr", 2442),
        "🇺🇸 États-Unis": ("google.com", "en", 2840),
        "🇬🇧 Royaume-Uni": ("google.co.uk", "en", 2826),
        "🇮🇪 Irlande": ("google.ie", "en", 2372),
        "🇩🇪 Allemagne": ("google.de", "de", 2276),
        "🇦🇹 Autriche": ("google.at", "de", 2040),
        "🇪🇸 Espagne": ("google.es", "es", 2724),
        "🇲🇽 Mexique": ("google.com.mx", "es", 2484),
        "🇦🇷 Argentine": ("google.com.ar", "es", 2032),
        "🇨🇴 Colombie": ("google.com.co", "es", 2170),
        "🇨🇱 Chili": ("google.cl", "es", 2152),
        "🇮🇹 Italie": ("google.it", "it", 2380),
        "🇵🇹 Portugal": ("google.pt", "pt", 2620),
        "🇧🇷 Brésil": ("google.com.br", "pt", 2076),
        "🇳🇱 Pays-Bas": ("google.nl", "nl", 2528),
        "🇵🇱 Pologne": ("google.pl", "pl", 2616),
        "🇨🇿 République Tchèque": ("google.cz", "cs", 2203),
        "🇷🇴 Roumanie": ("google.ro", "ro", 2642),
        "🇭🇺 Hongrie": ("google.hu", "hu", 2348),
        "🇸🇪 Suède": ("google.se", "sv", 2752),
        "🇳🇴 Norvège": ("google.no", "no", 2578),
        "🇩🇰 Danemark": ("google.dk", "da", 2208),
        "🇫🇮 Finlande": ("google.fi", "fi", 2246),
        "🇷🇺 Russie": ("google.ru", "ru", 2643),
        "🇺🇦 Ukraine": ("google.com.ua", "uk", 2804),
        "🇹🇷 Turquie": ("google.com.tr", "tr", 2792),
        "🇯🇵 Japon": ("google.co.jp", "ja", 2392),
        "🇰🇷 Corée du Sud": ("google.co.kr", "ko", 2410),
        "🇨🇳 Chine": ("google.com", "zh", 2156),
        "🇮🇳 Inde": ("google.co.in", "en", 2356),
        "🇮🇩 Indonésie": ("google.co.id", "id", 2360),
        "🇹🇭 Thaïlande": ("google.co.th", "th", 2764),
        "🇻🇳 Vietnam": ("google.com.vn", "vi", 2704),
        "🇦🇺 Australie": ("google.com.au", "en", 2036),
        "🇳🇿 Nouvelle-Zélande": ("google.co.nz", "en", 2554),
        "🇲🇦 Maroc": ("google.co.ma", "fr", 2504),
        "🇹🇳 Tunisie": ("google.tn", "fr", 2788),
        "🇩🇿 Algérie": ("google.dz", "fr", 2012),
        "🇸🇦 Arabie Saoudite": ("google.com.sa", "ar", 2682),
        "🇦🇪 Émirats Arabes Unis": ("google.ae", "ar", 2784),
        "🇪🇬 Égypte": ("google.com.eg", "ar", 2818),
        "🇿🇦 Afrique du Sud": ("google.co.za", "en", 2710),
        "🇳🇬 Nigeria": ("google.com.ng", "en", 2566),
        "🇮🇱 Israël": ("google.co.il", "he", 2376),
        "🇸🇬 Singapour": ("google.com.sg", "en", 2702),
        "🇲🇾 Malaisie": ("google.com.my", "ms", 2458),
        "🇵🇭 Philippines": ("google.com.ph", "en", 2608),
    }


# ── Tabs: Single / Bulk ─────────────────────────────────────────────────────
tab_single, tab_bulk = st.tabs(["🎯 Brief unique", "📦 Briefs en masse"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SINGLE BRIEF
# ═══════════════════════════════════════════════════════════════════════════════
with tab_single:
    col1, col2 = st.columns([2, 1])

    with col1:
        keyword = st.text_input(
            "🔑 Mot-clé principal",
            placeholder="Entrez votre mot-clé cible...",
            key="single_keyword"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)

    if source_mode == "URLs manuelles":
        st.markdown("#### URLs concurrentes (1 à 5)")
        manual_urls = []
        for i in range(5):
            url = st.text_input(
                f"URL {i+1}",
                placeholder=f"https://concurrent{i+1}.fr/page",
                key=f"url_{i}",
                label_visibility="collapsed" if i > 0 else "visible"
            )
            if url.strip():
                manual_urls.append(url.strip())

    # ── Generate Button ──────────────────────────────────────────────────────
    generate_btn = st.button(
        "🚀 Générer le brief",
        type="primary",
        use_container_width=True,
        key="generate_single"
    )

    if generate_btn:
        # Validation
        errors = []
        if not keyword.strip():
            errors.append("Veuillez entrer un mot-clé.")
        if not anthropic_key:
            errors.append("Veuillez renseigner votre clé API Anthropic.")
        if source_mode == "Top 5 SERP (DataForSEO)" and (not dataforseo_login or not dataforseo_password):
            errors.append("Veuillez renseigner vos identifiants DataForSEO.")
        if source_mode == "URLs manuelles" and len(manual_urls) == 0:
            errors.append("Veuillez renseigner au moins une URL concurrente.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            with st.spinner("🔍 Analyse en cours..."):
                progress = st.progress(0, text="Initialisation...")

                # Step 1: Get competitor URLs
                competitor_urls = []
                if source_mode == "Top 5 SERP (DataForSEO)":
                    progress.progress(10, text="Récupération du Top 5 SERP...")
                    se_domain, lang, loc_code = location_map[search_engine_location]
                    serp_results = get_top_results(
                        keyword.strip(),
                        dataforseo_login,
                        dataforseo_password,
                        se_domain=se_domain,
                        language_code=lang,
                        location_code=loc_code,
                        top_n=5
                    )
                    if serp_results.get("error"):
                        st.error(f"Erreur DataForSEO: {serp_results['error']}")
                        st.stop()
                    competitor_urls = serp_results.get("urls", [])
                    if not competitor_urls:
                        st.warning("Aucun résultat SERP trouvé. Le brief sera généré uniquement à partir du mot-clé.")
                else:
                    competitor_urls = manual_urls

                # Step 2: Scrape competitor pages
                progress.progress(25, text="Scraping des pages concurrentes...")
                competitor_data = []
                if competitor_urls:
                    for i, url in enumerate(competitor_urls):
                        progress.progress(
                            25 + int(40 * (i / len(competitor_urls))),
                            text=f"Analyse de {url[:60]}..."
                        )
                        try:
                            page_content = scrape_url(url)
                            if page_content:
                                structure = extract_structure(page_content)
                                word_count = count_words(page_content)
                                competitor_data.append({
                                    "url": url,
                                    "structure": structure,
                                    "word_count": word_count,
                                    "title": page_content.get("title", ""),
                                    "meta_description": page_content.get("meta_description", ""),
                                })
                        except Exception as e:
                            st.warning(f"Impossible de scraper {url}: {str(e)}")

                if not competitor_data:
                    st.info("ℹ️ Aucune donnée concurrentielle disponible. Le brief sera généré uniquement sur la base du mot-clé.")

                # Step 3: Analyze target site (if provided)
                progress.progress(70, text="Analyse du site cible...")
                site_context = None
                if target_site_url:
                    try:
                        site_context = analyze_site(target_site_url)
                    except Exception:
                        site_context = {"name": brand_name or "", "tone": "professionnel"}

                # Step 4: Calculate word count range
                if competitor_data:
                    avg_words = sum(d["word_count"] for d in competitor_data) / len(competitor_data)
                else:
                    avg_words = 800  # default when no competitors
                if avg_words < 500:
                    word_range = "400-600"
                elif avg_words < 700:
                    word_range = "600-800"
                elif avg_words < 900:
                    word_range = "800-1000"
                elif avg_words < 1250:
                    word_range = "1000-1500"
                else:
                    word_range = "1500+"

                # Step 5: Generate brief with Claude
                progress.progress(80, text="Génération du brief avec Claude...")
                brief = generate_brief(
                    keyword=keyword.strip(),
                    competitor_data=competitor_data,
                    anthropic_key=anthropic_key,
                    word_range=word_range,
                    avg_words=int(avg_words),
                    detail_level=detail_level,
                    include_faq=include_faq,
                    faq_count=faq_count,
                    include_brand_section=include_brand_section,
                    brand_name=brand_name,
                    site_context=site_context,
                    language_code=location_map[search_engine_location][1],
                )

                progress.progress(100, text="Brief généré !")
                time.sleep(0.5)
                progress.empty()

                st.session_state.briefs.append({
                    "keyword": keyword.strip(),
                    "brief": brief,
                    "word_range": word_range,
                    "avg_words": int(avg_words),
                    "competitor_data": competitor_data,
                    "timestamp": datetime.now().isoformat(),
                })

    # ── Display Brief ────────────────────────────────────────────────────────
    if st.session_state.briefs:
        latest = st.session_state.briefs[-1]
        brief = latest["brief"]

        st.markdown("---")
        st.markdown(f"## 📄 Brief SEO : *{latest['keyword']}*")

        # Metrics row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("🔑 Mot-clé", latest["keyword"])
        with mcol2:
            st.metric("📊 Mots recommandés", latest["word_range"])
        with mcol3:
            st.metric("📈 Moyenne concurrents", f"{latest['avg_words']} mots")
        with mcol4:
            st.metric("🏆 Pages analysées", len(latest["competitor_data"]))

        # URLs analyzed
        if latest["competitor_data"]:
            st.markdown("### 🔗 URLs analysées (Top concurrents)")
            for i, comp in enumerate(latest["competitor_data"], 1):
                st.markdown(
                    f"**{i}.** [{comp['url']}]({comp['url']}) — "
                    f"*{comp.get('word_count', 0)} mots*"
                )

        # Brief content
        st.markdown("### 🏷️ Balises SEO")
        col_t, col_m = st.columns(2)
        with col_t:
            st.markdown(f"""
            <div class="brief-section">
                <h3>Title tag</h3>
                <p><strong>{brief.get('title', 'N/A')}</strong></p>
                <p style="color:#64748b;font-size:0.85rem;">{len(brief.get('title', ''))} caractères (recommandé: 50-70)</p>
            </div>
            """, unsafe_allow_html=True)
        with col_m:
            st.markdown(f"""
            <div class="brief-section">
                <h3>Meta description</h3>
                <p><strong>{brief.get('meta_description', 'N/A')}</strong></p>
                <p style="color:#64748b;font-size:0.85rem;">{len(brief.get('meta_description', ''))} caractères (recommandé: 140-150)</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="brief-section">
            <h3>H1 (Titre de l'article)</h3>
            <p style="font-size:1.2rem;font-weight:700;">{brief.get('h1', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Structure Hn
        st.markdown("### 📐 Structure du contenu")
        structure_md = ""
        for item in brief.get("structure", []):
            level = item.get("level", "H2")
            title = item.get("title", "")
            indent = "  " * (int(level[1]) - 2) if len(level) == 2 else ""
            structure_md += f"{indent}- **{level}** : {title}\n"
            if item.get("description") and detail_level == "Titres + indications de contenu":
                structure_md += f"{indent}  - *{item['description']}*\n"
        st.markdown(structure_md)

        # FAQ
        if brief.get("faq"):
            st.markdown("### ❓ FAQ (H2 → Questions en H3)")
            for i, q in enumerate(brief["faq"], 1):
                with st.expander(f"H3 — Q{i}: {q.get('question', '')}"):
                    st.write(q.get("answer_guideline", ""))

        # Word count recommendation
        st.markdown(f"""
        <div class="brief-section">
            <h3>📏 Recommandation de longueur</h3>
            <p>Sur la base des <strong>{len(latest['competitor_data'])} pages concurrentes</strong> analysées,
            la longueur moyenne est de <strong>{latest['avg_words']} mots</strong>.</p>
            <p>👉 Intervalle recommandé : <strong>{latest['word_range']} mots</strong></p>
        </div>
        """, unsafe_allow_html=True)

        # ── Export ───────────────────────────────────────────────────────────
        st.markdown("### 📤 Exporter le brief")

        docx_buffer = export_to_docx(brief, latest)
        st.download_button(
            "📥 Télécharger .docx (Google Docs / Word)",
            data=docx_buffer,
            file_name=f"brief_seo_{latest['keyword'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        # ── Copy-paste section ──────────────────────────────────────────────
        st.markdown("### 📋 Copier-coller le brief")
        st.markdown("*Cliquez sur le bouton pour copier le brief avec les titres H1/H2/H3 formatés. Collez ensuite dans Google Docs, Word, Notion, Surfer SEO, SEO Quantum…*")

        html_formatted = export_to_html(brief, latest)

        import streamlit.components.v1 as components
        components.html(f"""
        <div id="brief_content" style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            font-family: Arial, sans-serif;
            color: #1a1a1a;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
        ">
            {html_formatted}
        </div>
        <button id="copy_btn" onclick="
            const content = document.getElementById('brief_content');
            const range = document.createRange();
            range.selectNodeContents(content);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            document.execCommand('copy');
            sel.removeAllRanges();
            document.getElementById('copy_btn').innerText = '✅ Brief copié !';
            setTimeout(() => {{ document.getElementById('copy_btn').innerText = '📋 Copier le brief (H1, H2, H3 formatés)'; }}, 2500);
        " style="
            background: linear-gradient(135deg, #1a73e8, #4285f4);
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 12px;
        ">
            📋 Copier le brief (H1, H2, H3 formatés)
        </button>
        """, height=600, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: BULK
# ═══════════════════════════════════════════════════════════════════════════════
with tab_bulk:
    st.markdown("### 📦 Génération en masse")
    st.info("Les paramètres de la sidebar (site cible, FAQ, niveau de détail...) s'appliquent à tous les briefs.")

    bulk_input_mode = st.radio(
        "Mode d'entrée",
        ["Champ texte (1 mot-clé par ligne)", "Fichier CSV/Excel"],
        key="bulk_input_mode"
    )

    bulk_keywords = []

    if bulk_input_mode == "Champ texte (1 mot-clé par ligne)":
        keywords_text = st.text_area(
            "Mots-clés (1 par ligne, max 100)",
            height=200,
            placeholder="mot-clé 1\nmot-clé 2\nmot-clé 3",
            key="bulk_text"
        )
        if keywords_text.strip():
            lines = [l.strip() for l in keywords_text.strip().split("\n") if l.strip()]
            bulk_keywords = [{"keyword": l, "urls": []} for l in lines[:100]]

    else:
        uploaded_file = st.file_uploader(
            "Importer un fichier CSV ou Excel",
            type=["csv", "xlsx"],
            key="bulk_file"
        )
        if uploaded_file:
            try:
                import pandas as pd
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.dataframe(df.head(10))

                # Detect columns
                kw_col = st.selectbox(
                    "Colonne mot-clé",
                    df.columns.tolist(),
                    key="kw_col"
                )
                url_cols = [c for c in df.columns if c != kw_col]
                url_col = st.selectbox(
                    "Colonne URLs (optionnel)",
                    ["Aucune"] + url_cols,
                    key="url_col"
                )

                for _, row in df.head(100).iterrows():
                    kw = str(row[kw_col]).strip()
                    urls = []
                    if url_col != "Aucune" and pd.notna(row.get(url_col)):
                        urls = [u.strip() for u in str(row[url_col]).split(",") if u.strip()]
                    if kw and kw != "nan":
                        bulk_keywords.append({"keyword": kw, "urls": urls})
            except Exception as e:
                st.error(f"Erreur de lecture du fichier: {e}")

    if bulk_keywords:
        st.success(f"✅ {len(bulk_keywords)} mot(s)-clé(s) détecté(s)")

    # Bulk generate
    bulk_generate = st.button(
        "🚀 Lancer la génération en masse",
        type="primary",
        use_container_width=True,
        key="bulk_generate"
    )

    if bulk_generate and bulk_keywords:
        errors = []
        if not anthropic_key:
            errors.append("Veuillez renseigner votre clé API Anthropic.")
        if source_mode == "Top 5 SERP (DataForSEO)" and (not dataforseo_login or not dataforseo_password):
            errors.append("Veuillez renseigner vos identifiants DataForSEO pour le mode SERP.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.bulk_briefs = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()

            for idx, item in enumerate(bulk_keywords):
                kw = item["keyword"]
                urls = item["urls"]

                status_text.text(f"⏳ [{idx+1}/{len(bulk_keywords)}] Traitement de « {kw} »...")
                progress_bar.progress((idx) / len(bulk_keywords))

                try:
                    # Get competitor URLs
                    if urls:
                        competitor_urls = urls[:5]
                    elif source_mode == "Top 5 SERP (DataForSEO)":
                        se_domain, lang, loc_code = location_map[search_engine_location]
                        serp_results = get_top_results(
                            kw, dataforseo_login, dataforseo_password,
                            se_domain=se_domain, language_code=lang,
                            location_code=loc_code, top_n=5
                        )
                        competitor_urls = serp_results.get("urls", [])
                    else:
                        competitor_urls = []

                    # Scrape (if URLs available)
                    competitor_data = []
                    if competitor_urls:
                        for url in competitor_urls:
                            try:
                                page_content = scrape_url(url)
                                if page_content:
                                    structure = extract_structure(page_content)
                                    word_count = count_words(page_content)
                                    competitor_data.append({
                                        "url": url,
                                        "structure": structure,
                                        "word_count": word_count,
                                        "title": page_content.get("title", ""),
                                        "meta_description": page_content.get("meta_description", ""),
                                    })
                            except Exception:
                                pass

                    # Word range
                    if competitor_data:
                        avg_words = sum(d["word_count"] for d in competitor_data) / len(competitor_data)
                    else:
                        avg_words = 800  # default when no competitors
                    if avg_words < 500:
                        word_range = "400-600"
                    elif avg_words < 700:
                        word_range = "600-800"
                    elif avg_words < 900:
                        word_range = "800-1000"
                    elif avg_words < 1250:
                        word_range = "1000-1500"
                    else:
                        word_range = "1500+"

                    # Site context
                    site_context = None
                    if target_site_url and idx == 0:
                        try:
                            site_context = analyze_site(target_site_url)
                        except Exception:
                            site_context = {"name": brand_name or "", "tone": "professionnel"}

                    # Generate brief
                    brief = generate_brief(
                        keyword=kw,
                        competitor_data=competitor_data,
                        anthropic_key=anthropic_key,
                        word_range=word_range,
                        avg_words=int(avg_words),
                        detail_level=detail_level,
                        include_faq=include_faq,
                        faq_count=faq_count,
                        include_brand_section=include_brand_section,
                        brand_name=brand_name,
                        site_context=site_context,
                        language_code=location_map[search_engine_location][1],
                    )

                    if brief.get("error"):
                        st.session_state.bulk_briefs.append({
                            "keyword": kw, "status": "error",
                            "error": brief["error"]
                        })
                    else:
                        st.session_state.bulk_briefs.append({
                            "keyword": kw,
                            "status": "success",
                            "brief": brief,
                            "word_range": word_range,
                            "avg_words": int(avg_words),
                            "competitor_data": competitor_data,
                        })

                except Exception as e:
                    st.session_state.bulk_briefs.append({
                        "keyword": kw, "status": "error",
                        "error": str(e)
                    })

                # Rate limiting
                time.sleep(1)

            progress_bar.progress(1.0)
            status_text.text("✅ Génération terminée !")

    # ── Display bulk results ─────────────────────────────────────────────────
    if st.session_state.bulk_briefs:
        st.markdown("---")
        st.markdown("### 📊 Résultats")

        success_count = sum(1 for b in st.session_state.bulk_briefs if b["status"] == "success")
        error_count = sum(1 for b in st.session_state.bulk_briefs if b["status"] == "error")

        rc1, rc2 = st.columns(2)
        with rc1:
            st.metric("✅ Réussis", success_count)
        with rc2:
            st.metric("❌ Erreurs", error_count)

        # Export all as ZIP
        if success_count > 0:
            st.markdown("#### 📤 Export groupé")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in st.session_state.bulk_briefs:
                    if item["status"] != "success":
                        continue
                    kw_slug = re.sub(r'[^a-z0-9]+', '_', item["keyword"].lower()).strip('_')
                    latest_data = {
                        "keyword": item["keyword"],
                        "word_range": item["word_range"],
                        "avg_words": item["avg_words"],
                        "competitor_data": item["competitor_data"],
                    }
                    buf = export_to_docx(item["brief"], latest_data)
                    zf.writestr(f"brief_{kw_slug}.docx", buf.getvalue())

            zip_buffer.seek(0)
            st.download_button(
                "📥 Télécharger tous les briefs (.zip)",
                data=zip_buffer,
                file_name=f"briefs_seo_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                use_container_width=True
            )

        # Individual results
        for idx_bulk, item in enumerate(st.session_state.bulk_briefs):
            if item["status"] == "success":
                with st.expander(f"✅ {item['keyword']} — {item['word_range']} mots"):
                    b = item["brief"]
                    item_meta = {
                        "keyword": item["keyword"],
                        "word_range": item["word_range"],
                        "avg_words": item["avg_words"],
                        "competitor_data": item["competitor_data"],
                    }

                    # Download .docx
                    docx_buf = export_to_docx(b, item_meta)
                    kw_slug = re.sub(r'[^a-z0-9]+', '_', item["keyword"].lower()).strip('_')
                    st.download_button(
                        "📥 Télécharger .docx",
                        data=docx_buf,
                        file_name=f"brief_{kw_slug}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"bulk_docx_{idx_bulk}"
                    )

                    # Copyable brief with components.html
                    html_bulk = export_to_html(b, item_meta)
                    import streamlit.components.v1 as components
                    components.html(f"""
                    <div id="bulk_brief_{idx_bulk}" style="
                        background: white;
                        border: 1px solid #e2e8f0;
                        border-radius: 10px;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                        color: #1a1a1a;
                        line-height: 1.5;
                        font-size: 14px;
                        max-height: 400px;
                        overflow-y: auto;
                    ">
                        {html_bulk}
                    </div>
                    <button id="bulk_copy_{idx_bulk}" onclick="
                        const content = document.getElementById('bulk_brief_{idx_bulk}');
                        const range = document.createRange();
                        range.selectNodeContents(content);
                        const sel = window.getSelection();
                        sel.removeAllRanges();
                        sel.addRange(range);
                        document.execCommand('copy');
                        sel.removeAllRanges();
                        document.getElementById('bulk_copy_{idx_bulk}').innerText = '✅ Brief copié !';
                        setTimeout(() => {{ document.getElementById('bulk_copy_{idx_bulk}').innerText = '📋 Copier le brief (H1, H2, H3 formatés)'; }}, 2500);
                    " style="
                        background: linear-gradient(135deg, #1a73e8, #4285f4);
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 600;
                        cursor: pointer;
                        width: 100%;
                        margin-top: 10px;
                    ">
                        📋 Copier le brief (H1, H2, H3 formatés)
                    </button>
                    """, height=500, scrolling=True)
            else:
                with st.expander(f"❌ {item['keyword']} — Erreur"):
                    st.error(item.get("error", "Erreur inconnue"))
