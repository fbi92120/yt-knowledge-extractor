# YT Knowledge Extractor

Extraction de connaissance structurée depuis les vidéos YouTube vers des fiches Markdown — prêtes pour votre vault Obsidian ou un dossier local.

*[English version available](README.md)*

## Ce que l'outil fait

À partir d'une URL YouTube, ce CLI :

1. Récupère le transcript horodaté et les métadonnées
2. Envoie le transcript complet à un LLM (Gemini par défaut)
3. Génère une fiche de connaissance structurée en Markdown avec :
   - Thèse centrale
   - Chapitrage inféré avec liens horodatés cliquables
   - Carte des idées
   - Concepts clés (définis par l'auteur)
   - Formulations notables reproduites mot pour mot
   - Questions ouvertes
   - Section "Mes notes" vide
   - Sources filtrées depuis la description de la vidéo
   - Transcript horodaté complet (réservé v2 pour la recherche cross-vidéos)

Tout le contenu est ancré sur des timestamps réels — aucune approximation, aucun lien inventé.

## Prérequis

- Python 3.10+ (fonctionne sur 3.9 avec un warning de dépréciation)
- Une clé API gratuite pour l'un des providers : **Gemini** (recommandé), Groq, Anthropic, OpenAI — ou une instance Ollama locale

## Installation

```bash
git clone https://github.com/fbi92120/yt-knowledge-extractor.git
cd yt-knowledge-extractor
pip install -r requirements.txt
```

## Configuration

```bash
cp config.yml.example config.yml
cp .env.example .env
```

Éditez `.env` et ajoutez votre clé API :

```
GEMINI_API_KEY=AIza...
```

Obtenez une clé Gemini gratuite sur [ai.google.dev](https://ai.google.dev/).

Éditez `config.yml` pour définir le mode de sortie (`obsidian` ou `local`) et le chemin de votre vault Obsidian ou de votre dossier local.

## Utilisation

```bash
python extract.py https://youtu.be/T_GqhyYqTD4
```

L'outil affiche la progression à chaque étape et confirme le chemin de sortie :

```
Extraction des métadonnées...
  → Claude Mythos : le modèle secret... (24:28)
Extraction du transcript (fr)...
  → 697 segments extraits
Génération de la fiche via gemini...
  → Validation OK

✓ Fiche créée : /chemin/vers/vault/chaine-slug/2026-04-02-claude-mythos...md
```

## Providers LLM

Le projet supporte plusieurs providers LLM via une interface unifiée. Changez de provider en éditant `config.yml`.

| Provider | Exemple de modèle | Free tier | Notes |
|---|---|---|---|
| **Gemini** (défaut) | `gemini-2.5-flash` | Oui, généreux | Contexte 1M tokens, gère facilement les longs transcripts |
| Groq | `llama-3.3-70b-versatile` | Limité | Free tier plafonné à ~6k tokens par requête — inutilisable pour vidéos > ~5 min |
| Anthropic | `claude-sonnet-4-5` | Non | Stub uniquement, implémentation à venir |
| OpenAI | `gpt-4o` | Non | Stub uniquement, implémentation à venir |
| Ollama | modèle local | Local | Stub uniquement, implémentation à venir |

**Pourquoi Gemini par défaut ?** Google AI Studio offre un free tier avec une fenêtre de contexte de 1M tokens. Le free tier de Groq, malgré les 128k de contexte annoncés côté modèle, applique une limite par requête d'environ 6k tokens qui le rend inutilisable pour la plupart des vidéos YouTube.

## Structure de sortie

```
[vault_path]/
  └── [chaine-slug]/
        └── [YYYY-MM-DD]-[titre-slug].md
```

Chaque fiche contient 10 sections (voir `SPECS.md` Bloc 3 pour le template exact).

## Tests

```bash
pytest tests/
```

Les tests sont sautés automatiquement si `GEMINI_API_KEY` n'est pas définie — ils fonctionnent donc en CI sans secrets.

La vidéo de test de référence est [`T_GqhyYqTD4`](https://youtu.be/T_GqhyYqTD4) de la chaîne [@SamouraiDansant](https://www.youtube.com/@SamouraiDansant).

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT — voir [LICENSE](LICENSE).
