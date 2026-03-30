# 📝 SEO Brief Generator

Générateur de briefs SEO basé sur l'analyse concurrentielle, propulsé par Claude AI.

## Fonctionnalités

- **Analyse SERP** : Récupère automatiquement le Top 5 Google via DataForSEO
- **Scraping concurrent** : Analyse la structure Hn, le nombre de mots, les balises SEO
- **Génération IA** : Brief complet généré par Claude (title, meta, H1, structure Hn, FAQ)
- **Adaptation au site cible** : Ton éditorial et branding intégrés
- **Multi-export** : .docx (Google Docs), Markdown Surfer SEO, Markdown SEO Quantum
- **Mode bulk** : Jusqu'à 100 briefs en une seule passe

## Installation

```bash
# Cloner le projet
cd seo_brief_generator

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## Configuration requise

| Service | Requis | Usage |
|---------|--------|-------|
| **Clé API Anthropic** | ✅ Oui | Génération des briefs via Claude |
| **DataForSEO** | ⚡ Optionnel | Récupération automatique du Top 5 SERP |

## Utilisation

### Brief unique

1. Renseignez vos clés API dans la sidebar
2. Entrez votre mot-clé cible
3. Choisissez le mode (Top 5 SERP ou URLs manuelles)
4. Configurez les options (FAQ, niveau de détail, site cible)
5. Cliquez sur "Générer le brief"
6. Exportez dans le format souhaité

### Briefs en masse

1. Configurez les paramètres globaux dans la sidebar
2. Allez dans l'onglet "Briefs en masse"
3. Collez vos mots-clés (1 par ligne) ou importez un CSV/Excel
4. Lancez la génération
5. Téléchargez le ZIP contenant tous les briefs

### Format CSV/Excel attendu

| mot_cle | urls |
|---------|------|
| chaussures running | https://site1.fr/page, https://site2.fr/page |
| basket homme | |

- Colonne **mot-clé** : obligatoire
- Colonne **URLs** : optionnelle, URLs séparées par des virgules

## Structure du projet

```
seo_brief_generator/
├── app.py              # Application Streamlit principale
├── serp_api.py         # Intégration DataForSEO
├── scraper.py          # Scraping des pages concurrentes
├── site_analyzer.py    # Analyse du site cible
├── brief_generator.py  # Génération du brief via Claude
├── export_utils.py     # Export DOCX & Markdown
├── requirements.txt    # Dépendances Python
└── README.md           # Ce fichier
```
