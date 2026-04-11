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

## Configuration Obsidian

Si vous voulez que les fiches générées arrivent directement dans un coffre Obsidian synchronisé entre Mac et mobile :

1. **Installer Obsidian sur ordinateur** — https://obsidian.md/download
2. **Installer Obsidian mobile** — App Store (iOS) ou Google Play (Android)
3. **Créer un coffre dans le dossier iCloud natif Obsidian**
   - Sur Mac, le chemin est : `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`
   - Créer un sous-dossier `YT-Knowledge` à cet endroit (ce sera votre coffre)
4. **Mettre à jour `vault_path` dans `config.yml`** pour pointer vers ce sous-dossier :
   ```yaml
   vault_path: /Users/[user]/Library/Mobile Documents/iCloud~md~obsidian/Documents/YT-Knowledge
   ```
5. **Ouvrir Obsidian mobile** et sélectionner le coffre
   - *Utiliser mon coffre existant → iCloud → Connecté à iCloud*
   - Sélectionner `YT-Knowledge`

Vos fiches seront synchronisées automatiquement entre Mac et mobile via iCloud.

## Utilisation

Deux façons d'invoquer l'outil :

**Mode interactif (recommandé)** — pas de prise de tête avec les caractères spéciaux du shell :

```bash
yt
# Entrez le lien YouTube : <coller l'URL ici>
```

**Mode direct** — passer l'URL en argument (doit être entre guillemets car les URLs YouTube contiennent `?` et parfois `&`) :

```bash
yt "https://www.youtube.com/watch?v=VIDEO_ID"
# ou sans l'alias :
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Formats d'URL acceptés :**

```
https://youtu.be/VIDEO_ID
https://www.youtube.com/watch?v=VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
```

L'outil affiche un spinner avec l'étape courante et confirme le chemin de sortie à la fin :

```
✓ Fiche créée : file:///chemin/vers/vault/chaine-slug/2026-04-02-claude-mythos...md
```

Sur Terminal macOS, le chemin `file://` est cliquable et ouvre la fiche directement.

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

## Exemples

Voir [`examples/`](examples/) pour trois fiches générées par l'outil sur de vraies vidéos YouTube. Elles donnent une idée concrète de ce que produit le pipeline sans avoir à le lancer vous-même.

## Tests

```bash
pytest tests/
```

Les tests sont sautés automatiquement si `GEMINI_API_KEY` n'est pas définie — ils fonctionnent donc en CI sans secrets.

La vidéo de test de référence est [`T_GqhyYqTD4`](https://youtu.be/T_GqhyYqTD4) de la chaîne [@SamouraiDansant](https://www.youtube.com/@SamouraiDansant).

## Méthode

Ce projet a été construit avec la méthode [Vibe Coding, Governed](https://github.com/fbi92120/vibe-coding-governed) — specs avant le code, l'humain décide, le LLM exécute.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT — voir [LICENSE](LICENSE).
