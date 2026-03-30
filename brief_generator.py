"""
SEO Brief generator using Claude API.
Creates structured briefs based on competitor analysis.
"""
import json
import re
import anthropic


def generate_brief(
    keyword: str,
    competitor_data: list,
    anthropic_key: str,
    word_range: str,
    avg_words: int,
    detail_level: str = "Titres + indications de contenu",
    include_faq: bool = True,
    faq_count: int = 3,
    include_brand_section: bool = True,
    brand_name: str = "",
    site_context: dict | None = None,
    language_code: str = "fr",
) -> dict:
    """
    Generate a complete SEO brief using Claude.

    Returns dict with:
        - title: optimized title tag
        - meta_description: optimized meta description
        - h1: article title
        - structure: list of {level, title, description?}
        - faq: list of {question, answer_guideline}
        - word_range: recommended word count range
        - error: error message if any
    """
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)

        # Build competitor analysis summary
        competitor_summary = _build_competitor_summary(competitor_data)

        # Build site context info
        site_info = ""
        if site_context:
            site_info = f"""
## Contexte du site cible
- Nom du site : {site_context.get('name', 'Non renseigné')}
- Ton éditorial détecté : {site_context.get('tone', 'professionnel')}
- Description : {site_context.get('description', 'N/A')}
- Domaine : {site_context.get('domain', 'N/A')}

Le brief doit être adapté au ton et au style éditorial de ce site.
"""

        # Build structure instructions
        include_descriptions = detail_level == "Titres + indications de contenu"
        structure_instruction = ""
        if include_descriptions:
            structure_instruction = """Pour chaque H2/H3, ajoute un champ "description" avec 1-2 phrases d'indication de contenu (ce que le rédacteur doit couvrir dans cette section)."""
        else:
            structure_instruction = """Ne fournis que les titres H2/H3, sans descriptions."""

        # Build brand section instruction
        brand_instruction = ""
        if include_brand_section and brand_name:
            brand_instruction = f"""
Ajoute un dernier H2 avant la FAQ (ou en dernier si pas de FAQ) qui met en avant la marque/entreprise "{brand_name}".
Ce H2 doit être pertinent par rapport au mot-clé et montrer l'expertise/la valeur ajoutée de "{brand_name}" sur ce sujet.
"""

        # Build FAQ instruction
        faq_instruction = ""
        if include_faq:
            faq_instruction = f"""
Génère exactement {faq_count} questions FAQ pertinentes et complémentaires au contenu du brief.
Les questions doivent être celles que se poseraient réellement les internautes.
Pour chaque question, fournis une guideline de réponse (pas la réponse complète, mais les points clés à aborder).
"""

        # Adapt structure depth to word range
        structure_depth_guide = _get_structure_depth(word_range)

        # Language mapping
        language_names = {
            "fr": "français", "en": "anglais", "de": "allemand", "es": "espagnol",
            "it": "italien", "pt": "portugais", "nl": "néerlandais", "pl": "polonais",
            "cs": "tchèque", "ro": "roumain", "hu": "hongrois", "sv": "suédois",
            "no": "norvégien", "da": "danois", "fi": "finnois", "ru": "russe",
            "uk": "ukrainien", "tr": "turc", "ja": "japonais", "ko": "coréen",
            "zh": "chinois", "id": "indonésien", "th": "thaï", "vi": "vietnamien",
            "ar": "arabe", "he": "hébreu", "ms": "malais",
        }
        lang_name = language_names.get(language_code, "français")
        language_instruction = ""
        if language_code != "fr":
            language_instruction = f"""
## LANGUE
IMPORTANT : Le brief entier (title, meta description, H1, tous les titres H2/H3, descriptions, FAQ) doit être rédigé en **{lang_name}**.
Le mot-clé cible est en {lang_name}, le contenu doit donc être entièrement dans cette langue.
"""

        # Build the prompt
        prompt = f"""Tu es un expert SEO senior spécialisé dans la création de briefs éditoriaux optimisés.

## Objectif
Crée un brief SEO complet pour le mot-clé : **"{keyword}"**
{language_instruction}

## Données concurrentielles
{competitor_summary}

## Nombre de mots moyen des concurrents : {avg_words} mots
## Intervalle de mots recommandé : {word_range} mots

{site_info}

## Instructions pour le brief

### 1. Title tag (balise title)
- Entre 50 et 70 caractères
- Doit contenir le mot-clé "{keyword}"
- Doit être accrocheur et inciter au clic
- OBLIGATOIRE : Le title doit se terminer par " - {brand_name if brand_name else '[Nom de la marque]'}"
- Exemple de format : "Mot-clé principal : phrase accrocheuse - {brand_name if brand_name else 'Marque'}"

### 2. Meta description
- Entre 140 et 150 caractères
- Doit commencer par un verbe d'action
- Doit contenir le mot-clé "{keyword}"
- Doit inciter au clic

### 3. H1 (titre de l'article)
- Doit être différent du title tag
- Doit contenir le mot-clé ou une variante proche
- Doit être engageant et clair

### 4. Structure Hn (plan de l'article)
{structure_instruction}
{structure_depth_guide}
{brand_instruction}

La structure doit être cohérente, couvrir le sujet de manière exhaustive,
et s'inspirer des meilleures pratiques observées chez les concurrents
tout en apportant de la valeur ajoutée.

### 5. FAQ
{faq_instruction if include_faq else "Pas de FAQ demandée."}
{"IMPORTANT pour la FAQ : La FAQ doit être structurée avec un H2 'FAQ' ou 'Questions fréquentes' dans la structure, puis chaque question individuelle doit être un H3 sous ce H2. Intègre la FAQ directement dans le champ 'structure' du JSON en plus du champ 'faq'. C'est-à-dire : ajoute un élément H2 pour la FAQ et des éléments H3 pour chaque question dans le tableau 'structure'." if include_faq else ""}

## Format de réponse
Réponds UNIQUEMENT en JSON valide, sans markdown, sans commentaires, avec cette structure exacte :

{{
    "title": "Le title tag optimisé",
    "meta_description": "La meta description optimisée commençant par un verbe d'action",
    "h1": "Le H1 de l'article",
    "structure": [
        {{"level": "H2", "title": "Titre du H2", "description": "Indication de contenu (si demandé)"}},
        {{"level": "H3", "title": "Titre du H3", "description": "Indication de contenu (si demandé)"}},
        ...
    ],
    "faq": [
        {{"question": "Question 1 ?", "answer_guideline": "Points clés à aborder..."}},
        ...
    ]
}}

{"Si le niveau de détail ne demande pas de descriptions, n'inclus pas le champ description dans structure." if not include_descriptions else ""}
{"Si pas de FAQ, retourne une liste vide pour faq." if not include_faq else ""}
"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = message.content[0].text.strip()

        # Clean potential markdown wrappers
        response_text = re.sub(r"^```json\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

        brief = json.loads(response_text)

        # Validate structure
        if "title" not in brief or "h1" not in brief:
            return {"error": "Structure de réponse invalide"}

        # Ensure defaults
        brief.setdefault("meta_description", "")
        brief.setdefault("structure", [])
        brief.setdefault("faq", [])

        return brief

    except json.JSONDecodeError as e:
        return {"error": f"Erreur de parsing JSON: {str(e)}"}
    except anthropic.APIError as e:
        return {"error": f"Erreur API Claude: {str(e)}"}
    except Exception as e:
        return {"error": f"Erreur inattendue: {str(e)}"}


def _build_competitor_summary(competitor_data: list) -> str:
    """Build a text summary of competitor analysis."""
    if not competitor_data:
        return """Aucune donnée concurrentielle disponible pour ce mot-clé.
Génère le brief uniquement sur la base de ton expertise SEO et de ta connaissance du sujet.
Propose une structure pertinente et complète en te basant sur l'intention de recherche probable de l'internaute."""

    summary = ""
    for i, comp in enumerate(competitor_data, 1):
        summary += f"""
### Concurrent {i}: {comp['url']}
- **Title**: {comp.get('title', 'N/A')}
- **Meta description**: {comp.get('meta_description', 'N/A')}
- **Nombre de mots**: {comp.get('word_count', 0)}
- **Structure Hn**:
"""
        for h in comp.get("structure", []):
            indent = "  " * (int(h["level"][1]) - 1)
            summary += f"  {indent}{h['level']}: {h['text']}\n"
        summary += "\n"

    return summary


def _get_structure_depth(word_range: str) -> str:
    """Return structure depth guidelines based on word range."""
    guides = {
        "400-600": (
            "Pour un article de 400-600 mots, la structure doit rester simple :\n"
            "- 2 à 3 H2 maximum\n"
            "- 0 à 2 H3 au total\n"
            "- Pas de H4"
        ),
        "600-800": (
            "Pour un article de 600-800 mots :\n"
            "- 3 à 4 H2\n"
            "- 1 à 3 H3 au total\n"
            "- Pas de H4"
        ),
        "800-1000": (
            "Pour un article de 800-1000 mots :\n"
            "- 4 à 5 H2\n"
            "- 2 à 5 H3 au total\n"
            "- H4 optionnel"
        ),
        "1000-1500": (
            "Pour un article de 1000-1500 mots :\n"
            "- 5 à 7 H2\n"
            "- 3 à 8 H3 au total\n"
            "- H4 si pertinent"
        ),
        "1500+": (
            "Pour un article de plus de 1500 mots :\n"
            "- 6 à 10 H2\n"
            "- 5 à 12 H3 au total\n"
            "- H4 si pertinent pour des sous-sections détaillées"
        ),
    }
    return guides.get(word_range, guides["800-1000"])
