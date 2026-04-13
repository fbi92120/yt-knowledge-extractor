# CLAUDE.md — Projet YT Knowledge Extractor
# Emplacement cible : ~/Projects/yt-knowledge-extractor/CLAUDE.md
# Portée : ce projet uniquement
#
# Ce fichier complète les conventions transversales définies dans :
#   https://github.com/fbi92120/vibe-coding-governed
#   (CLAUDE.global.md, CLAUDE.projects.md, METHODE_SPECS_CO-CONSTRUCTION.md)

---

## Ce projet

Outil CLI Python qui extrait la connaissance d'une vidéo YouTube
et génère une fiche structurée en Markdown sauvegardée dans un vault Obsidian.

Repo    : https://github.com/fbi92120/yt-knowledge-extractor
Specs   : SPECS.md — lire avant toute implémentation
Méthode : METHODE_SPECS_CO-CONSTRUCTION.md

## Stack technique

```
Python 3.12 via .venv/ (venv local, PEP 668-compliant — voir setup.sh)
youtube-transcript-api    # extraction transcript + timestamps
yt-dlp                    # extraction métadonnées YouTube
python-slugify            # génération slug ASCII depuis titre
pyyaml + python-dotenv    # lecture config.yml et .env
requests                  # appels API LLM
```

## Constitution — règles absolues de ce projet

Ces règles ne peuvent jamais être violées, même si le résultat semble acceptable.

1. Jamais inventer un timestamp — si un élément ne peut pas être ancré,
   le produire sans timestamp plutôt qu'avec un approximatif
2. Citations textuelles ou absentes — jamais paraphrasées
3. Section "Mes notes" toujours vide — jamais générée par le LLM
4. Définitions de l'auteur uniquement — jamais des définitions génériques
5. Sources filtrées : auteur ou titre identifiable uniquement
6. Transcript complet envoyé en une seule fois — pas de chunking
7. Fiche incomplète : sauvegarder + avertissement en tête de fichier
8. Contexte LLM insuffisant : bloquer avec message explicite, pas tronquer
9. Déduction ancrée uniquement : toute inférence (thèse, transition,
   définition, question) rattachée à un segment du transcript.
   Si l'ancre n'existe pas : omission ou marquage [implicite]. Jamais d'approximation.

## Providers LLM disponibles

| Provider | Variable env | Gratuit |
|---|---|---|
| gemini | GEMINI_API_KEY | Oui (free tier) — provider par défaut |
| groq | GROQ_API_KEY | Limité ~6k tokens, inutilisable vidéos > 5min |
| anthropic | ANTHROPIC_API_KEY | Non (~0,05€/vidéo) |
| openai | OPENAI_API_KEY | Non |
| ollama | — | Oui (local) |

## Comportements aux limites — décisions actées

| Situation | Comportement |
|---|---|
| Sous-titres absents | Erreur terminal, pas de fichier |
| Langue demandée absente | Fallback + avertissement terminal |
| Chapitres YouTube natifs présents | Utilisés comme base du chapitrage |
| Contexte modèle insuffisant | Bloquer avec tokens requis vs disponibles |
| Fiche < 6 blocs chapitrage | Sauvegarder + avertissement en tête |
| Fiche < 3 concepts | Sauvegarder + avertissement en tête |
| Fichier existant | Demander confirmation, jamais écraser sans accord |
| Erreur API LLM | Erreur terminal avec code HTTP, pas de fichier |

## URL de référence pour les tests

```
https://youtu.be/T_GqhyYqTD4
Chaîne : @SamouraiDansant
Transcript : FR auto-généré, 697 segments
```

## Séquence d'implémentation — ordre obligatoire

```
1.  Bootstrap (structure + fichiers vides + docstrings)
2.  src/transcript.py
3.  src/metadata.py
4.  src/llm/base.py + src/llm/groq.py
5.  src/generator.py
6.  tests/test_contract.py    ← AVANT validateur et writer
7.  src/validator.py          ← implémenté pour passer les tests
8.  src/writer.py
9.  extract.py
10. tests/test_smoke.py       ← APRÈS pipeline complet
11. README.md + README.fr.md
```

Ne jamais paralléliser des étapes de cette séquence.
Ne jamais passer à l'étape N+1 sans que l'étape N soit validée.

Note : cette séquence décrit la méthode cible (TDD partiel).
Ce projet a suivi la séquence de PLAN.md sans test_contract.py —
la méthode a été extraite a posteriori.

PLAN.md décrit la séquence réellement exécutée sur ce projet.

## Gestion des documents de spec

Tout document de spec modifié inclut la date ET l'heure de dernière
modification dans son header (ex. `**Date** : 2026-04-13 14:30`).

## Signal d'alarme

Si un cas non couvert par les specs est rencontré :
> 🚨 SPEC MANQUANTE : [description précise]
Stopper et attendre une instruction explicite. Ne pas improviser.

**Règle absolue — gap détecté en production**
Tout gap détecté suit ce flux obligatoire :
1. Signaler : 🚨 SPEC MANQUANTE : [description précise]
2. Stopper — ne pas implémenter
3. Attendre validation dans Claude.ai
4. Recevoir l'instruction de mise à jour des specs
5. Implémenter uniquement après confirmation

Un gap implémenté sans mise à jour des specs préalable
est une dette de spec silencieuse.
