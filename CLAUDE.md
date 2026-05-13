# CLAUDE.md — Projet YT Knowledge Extractor

**Version** : 1.1  
**Date** : 2026-05-13  
**Auteur** : François Biller  
**Statut** : V1.8 livrée — feature `--export` implémentée. Migration de l'entête vers le format conforme aux conventions projet (bloc gras). Ajout d'une section "État courant" pour traçabilité d'avancement. Mention "Gemini gratuit" nuancée — voir BACKLOG.  
**Repo** : https://github.com/fbi92120/yt-knowledge-extractor  

Emplacement cible : `~/Projects/yt-knowledge-extractor/CLAUDE.md`  
Portée : ce projet uniquement.

Ce fichier complète les conventions transversales définies dans :  
https://github.com/fbi92120/vibe-coding-governed  
(CLAUDE.global.md, CLAUDE.projects.md, METHODE_SPECS_CO-CONSTRUCTION.md)

---

## Ce projet

Outil CLI Python qui extrait la connaissance d'une vidéo YouTube
et génère une fiche structurée en Markdown sauvegardée dans un vault Obsidian.

Repo    : https://github.com/fbi92120/yt-knowledge-extractor  
Specs   : SPECS.md — lire avant toute implémentation  
Méthode : METHODE_SPECS_CO-CONSTRUCTION.md

## État courant

| Version | Date | Contenu |
|---|---|---|
| V1.0 | 2026-04-06 | Pipeline initial : transcript + metadata + LLM + writer + validator + tests. Provider par défaut : `gemini-2.5-flash`. |
| V1.6 | 2026-04-14 | Feature `--gist` : publication GitHub Gist secret depuis la CLI via `gh`. |
| V1.7 | 2026-04-18 | Feature `--model` (priorité cascade), vérification fiche existante AVANT appel LLM, batch processing avec format `# model:` et `gist` par URL. |
| V1.8 | 2026-05-13 | Feature `--export` : copie d'une fiche du vault vers `~/Documents/yt-exports/` + ouverture Finder. Résout le drag & drop iCloud → Claude.ai. Combinable avec `--gist`, rejet en mode batch. |

**Validation V1.8** : 8/8 tests EX-01 à EX-08 passants. Suite complète :
195/195 sans smoke, 188/188 avec smoke. Zéro régression V1.6/V1.7.

**Suivi ouvert** : voir BACKLOG.md V1.3 — 2 items signalés à
l'implémentation V1.8 (duplication navigation vault, test robustesse
`open_in_finder`). Plus 7 items préexistants dont déplacement de
`_extract_model_from_fiche()` hors de `extract.py`.

## Stack technique

```
Python 3.12 via .venv/ (venv local, PEP 668-compliant — voir setup.sh)
youtube-transcript-api    # extraction transcript + timestamps
yt-dlp                    # extraction métadonnées YouTube
python-slugify            # génération slug ASCII depuis titre
pyyaml + python-dotenv    # lecture config.yml et .env
requests                  # appels API LLM
gh (GitHub CLI)           # publication gist — outil système, pas pip
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

| Provider | Variable env | Coût |
|---|---|---|
| gemini | GEMINI_API_KEY | Gratuit jusqu'à quota free tier — provider par défaut (voir BACKLOG : mention "gratuit" du périmètre MVP à nuancer) |
| groq | GROQ_API_KEY | Free tier limité ~6k tokens, inutilisable vidéos > 5min |
| anthropic | ANTHROPIC_API_KEY | Non gratuit (~0,05€/vidéo) |
| openai | OPENAI_API_KEY | Non gratuit |
| ollama | — | Gratuit (local) |

## Comportements aux limites — décisions actées

| Situation | Comportement |
|---|---|
| Sous-titres absents | Erreur terminal, pas de fichier |
| Langue demandée absente | Fallback + avertissement terminal |
| Chapitres YouTube natifs présents | Utilisés comme base du chapitrage |
| Contexte modèle insuffisant | Bloquer avec tokens requis vs disponibles |
| Fiche < 6 blocs chapitrage | Sauvegarder + avertissement en tête |
| Fiche < 3 concepts | Sauvegarder + avertissement en tête |
| Fichier existant, même modèle | Demander confirmation (o/N) AVANT appel LLM |
| Fichier existant, modèle différent | Options (a) archiver v1/ / (r) remplacer / (N) annuler AVANT appel LLM |
| Erreur API LLM | Erreur terminal avec code HTTP, pas de fichier |
| `--export` + fichier batch .txt | Rejet avec erreur explicite (non supporté en batch) |
| `--export` + `--dry-run` | Avertissement, exécution normale (rien à simuler) |
| `gh` non installé ou non authentifié pour `--gist` | Erreur lisible, fiche locale préservée |

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
Ce projet V1 a suivi la séquence de PLAN.md sans test_contract.py —
la méthode a été extraite a posteriori.

PLAN.md décrit la séquence réellement exécutée sur ce projet en V1.

### Pour les features ajoutées après V1 (V1.6, V1.7, V1.8)

Pattern validé sur 3 features : 1 prompt unique = 1 livrable testable
incluant module(s) `src/`, câblage `extract.py`, mise à jour
`config.yml.example` si besoin, et tests dédiés. Voir le prompt de
livraison V1.8 (`--export`) comme modèle de référence.

## Conventions de branches

Pour les features significatives :
- Créer une branche : `git checkout -b feature/nom-feature`
- Travailler sur la branche
- Lancer `/review` sur la branche avant de merger
- Merger sur main via PR ou `git merge`

Pour les corrections mineures et hotfixes :
- Commit direct sur main acceptable

## Gestion des documents de spec

Tout document de spec modifié inclut la date ET l'heure de dernière
modification dans son header (ex. `**Date** : 2026-04-13 14:30`).

Toute spec doit avoir un entête conforme aux règles inviolables :
`**Version**`, `**Date**`, `**Auteur**`, `**Statut**`, `**Repo**`.

Toute modification d'un fichier .md structurant existant doit
incrémenter la version ET la date.

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

## Problèmes transversaux — pattern de gestion

Pattern validé sur V1.8 : si pendant l'implémentation d'un prompt,
Claude Code identifie des problèmes transversaux (incohérences,
duplications, tests manquants), il les SIGNALE en fin de réponse
sous "⚠️ Problèmes transversaux identifiés" mais ne les CORRIGE PAS
dans le même prompt. Chaque transversal devient une entrée BACKLOG
pour un prompt dédié.

Règle : "1 prompt = 1 livrable testable" implique aussi
"1 prompt ≠ refactor opportuniste".
