# CLAUDE.md — YT Knowledge Extractor

## Projet

- **Nom** : YT Knowledge Extractor
- **Type** : CLI Python — extraction de connaissances depuis YouTube
- **Specs** : `SPECS.md`
- **Plan d'implémentation** : `PLAN.md` (séquence de 10 prompts)

## Avancement

- Prompt 1 — Bootstrap : **fait**
- Prompt 2 — Transcript (`src/transcript.py`) : **fait + testé**
- Prompt 3 — Métadonnées (`src/metadata.py`) : **fait + testé**
- Prompt 4 — Couche LLM (`src/llm/`) : **fait + testé**
- Prompt 5 — Générateur (`src/generator.py`) : **fait + testé**
- Prompt 6 — Validateur (`src/validator.py`) : **fait + testé**
- Prompt 7 — Writer (`src/writer.py`) : **fait + testé**
- Prompt 8 — Point d'entrée (`extract.py`) : **fait + testé** (hors appel API réel)
- Prompt 9 — Tests : **fait + validé** (8/8 en end-to-end réel avec Gemini 2.5 Flash)
- Prompt 10 — Documentation : **fait** (README.md, README.fr.md, CONTRIBUTING.md, LICENSE)

**Projet V1 terminé.** Les 10 prompts sont implémentés, testés et documentés.

## Règles de travail

1. **Un prompt = un module testé et validé.** Un prompt n'est terminé que quand son module passe ses tests.
2. **Problèmes transversaux signalés, pas corrigés.** Si un problème transversal est identifié en cours de prompt, le signaler dans le résumé final mais ne pas le corriger avant que le test du module en cours soit passé.
3. **Un problème transversal = une étape dédiée**, proposée après validation du module en cours.

## Problèmes transversaux identifiés

- **Python 3.9** : yt-dlp affiche un warning de dépréciation. Le projet cible Python 3.10+ (SPECS.md). `from __future__ import annotations` a été ajouté dans tous les fichiers `src/` pour compatibilité 3.9.
- ~~**Groq free tier inexploitable pour vidéos > ~5 min**~~ : documenté dans config.yml.example, README et CONTRIBUTING. Gemini est maintenant le provider par défaut.
- ~~**Provider Gemini ajouté mais non documenté**~~ : ajouté dans `.env.example`, `config.yml.example`, README.md, README.fr.md.
- ~~**`config.yml.example` incohérent**~~ : provider par défaut passé de Groq à Gemini (`gemini-2.5-flash`).

## Stack

- Python 3.10+ (fonctionne sur 3.9 avec `__future__` annotations)
- Pas de SDK LLM — tous les providers utilisent `requests` directement
- Dépendances : voir `requirements.txt`

## Commandes

```bash
pip install -r requirements.txt
cp config.yml.example config.yml
cp .env.example .env
# Ajouter clé Groq dans .env
python extract.py [URL YouTube]
pytest tests/
```

## Langue de communication

- Répondre en français par défaut
