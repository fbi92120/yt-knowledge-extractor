# SPECS.md — YT Knowledge Extractor

**Version** : 1.0  
**Date** : 2026-04-05  
**Auteur** : François Biller  
**Statut** : Validé — prêt pour implémentation  
**Repo** : https://github.com/fbi92120/yt-knowledge-extractor  
**Chaîne de test** : [@SamouraiDansant](https://www.youtube.com/@SamouraiDansant)

---

## Bloc 0 — Constitution

*Règles non négociables. Aucune exception, aucune déviation dans le code ou dans les prompts.*

1. **Jamais inventer un timestamp** — si un élément ne peut pas être ancré temporellement, il est produit sans timestamp plutôt qu'avec un timestamp approximatif.
2. **Citations textuelles ou absentes** — les formulations notables sont reproduites mot pour mot depuis le transcript, ou elles n'apparaissent pas.
3. **"Mes notes" toujours vide** — cette section n'est jamais générée par le LLM. Elle reste un espace blanc balisé.
4. **Définitions de l'auteur uniquement** — un concept est défini tel que l'auteur le définit dans la vidéo, jamais avec une définition générique externe.
5. **Sources filtrées strictement** — une source n'est conservée que si elle a un auteur ou un titre identifiable. Les liens génériques, réseaux sociaux et mentions commerciales sont ignorés.
6. **Lecture complète avant structuration** — le transcript complet est envoyé au LLM en une seule fois. Pas de traitement par morceaux qui fragmenterait la cohérence globale.
7. **Fiche incomplète signalée** — si la fiche générée ne respecte pas les minimums (chapitrage < 6 blocs, < 3 concepts), elle est sauvegardée avec un avertissement visible en tête de fichier.
8. **Contexte insuffisant bloquant** — si le modèle configuré ne peut pas accueillir le transcript complet, le script bloque avec un message explicite. Il ne tronque pas silencieusement.

---

## Bloc 1 — Vue d'ensemble

### Objectif

Script CLI Python qui extrait la connaissance d'une vidéo YouTube et génère une fiche structurée en Markdown, sauvegardée dans un vault Obsidian ou un dossier local.

Conçu pour un usage personnel d'abord, installable par d'autres utilisateurs via GitHub.

### Périmètre MVP (V1)

- Traitement d'une seule vidéo à la fois
- Interface CLI : `python extract.py [URL]`
- Transcript via sous-titres YouTube (pas de transcription audio)
- Génération de fiche via LLM (Groq par défaut, gratuit)
- Sauvegarde Markdown dans vault Obsidian ou dossier local
- Configuration via `config.yml` et `.env` — aucun chemin ou clé hardcodé

### Hors scope V1

- Traitement en batch de plusieurs vidéos
- Interface graphique ou web
- Recherche cross-vidéos (V2)
- Multi-utilisateurs simultanés (V3 SaaS)
- Transcription audio via Whisper (fallback si sous-titres absents)

### Évolutions prévues

- **V2 — Recherche cross-vidéos** : le transcript horodaté complet conservé dans chaque fiche constitue le corpus. Requête sémantique sur l'ensemble des vidéos traitées.
- **V3 — SaaS** : la logique métier est isolée de la couche CLI dès la V1 pour faciliter cette évolution. Aucune logique dans `extract.py` — tout passe par `src/`.

---

## Bloc 2 — Architecture technique

### Stack

```
Python 3.10+
youtube-transcript-api    # extraction transcript + timestamps
yt-dlp                    # extraction métadonnées YouTube
python-slugify            # génération slug ASCII depuis titre
pyyaml                    # lecture config.yml
python-dotenv             # lecture .env
requests                  # appels API LLM (tous providers)
```

### Structure du repo

```
yt-knowledge-extractor/
├── README.md                  # EN — installation + usage
├── README.fr.md               # FR — même contenu
├── SPECS.md                   # ce document
├── config.yml.example         # template configuration utilisateur
├── .env.example               # template variables d'environnement
├── .gitignore                 # config.yml, .env, output/
├── extract.py                 # point d'entrée CLI — orchestration uniquement
├── requirements.txt
├── src/
│   ├── transcript.py          # extraction transcript + timestamps
│   ├── metadata.py            # extraction métadonnées + filtrage sources
│   ├── generator.py           # génération fiche (orchestration LLM)
│   ├── writer.py              # écriture fichier Markdown + slug
│   ├── validator.py           # validation structure fiche produite
│   └── llm/
│       ├── base.py            # interface abstraite LLMProvider
│       ├── groq.py            # provider Groq (défaut)
│       ├── anthropic.py       # provider Claude API
│       ├── openai.py          # provider OpenAI
│       └── ollama.py          # provider Ollama local
└── tests/
    ├── test_smoke.py          # URL de référence fixe
    └── test_structure.py      # validation sections obligatoires
```

### Configuration utilisateur

`config.yml` (copié depuis `config.yml.example`) :

```yaml
# Langue du transcript à extraire
transcript_language: fr

# Provider LLM : groq | anthropic | openai | ollama
llm:
  provider: groq
  model: llama-3.3-70b-versatile
  api_key_env: GROQ_API_KEY    # nom de la variable dans .env

# Destination des fiches générées
output:
  mode: obsidian               # obsidian | local
  vault_path: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/YT-Knowledge
  local_path: ./output         # utilisé si mode: local

# Langue de la fiche générée
output_language: fr
```

`.env` (copié depuis `.env.example`) :

```
GROQ_API_KEY=gsk_...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### Flux de traitement

```
1.  Réception URL YouTube
2.  Extraction video_id
3.  Extraction métadonnées (titre, chaîne, durée, description, chapitres natifs)
4.  Extraction transcript horodaté (langue configurée)
5.  Vérification taille contexte vs modèle configuré → BLOQUE si insuffisant
6.  Filtrage sources intellectuelles depuis description YouTube
7.  Construction prompt (system + transcript complet)
8.  Envoi au LLM configuré
9.  Réception fiche brute
10. Validation structure (sections, minimums)
11. Génération slug ASCII depuis titre
12. Construction chemin fichier
13. Demande confirmation si fichier existant
14. Écriture fichier Markdown (avec avertissements en tête si nécessaire)
15. Confirmation terminal (chemin fichier créé)
```

### Structure du fichier de sortie

```
[vault_path]/
  └── [nom-chaîne]/
        └── [YYYY-MM-DD]-[slug-ascii].md
```

Exemple :
```
YT-Knowledge/
  └── samourai-dansant/
        └── 2026-04-05-jai-teste-deepseek-pendant-5-jours.md
```

---

## Bloc 3 — Prompt système LLM

*En anglais. Instruction envoyée au LLM à chaque génération de fiche.*

```
You are a knowledge extraction assistant. Your task is to analyze
a YouTube video transcript and produce a structured knowledge note
in {output_language}.

## Output structure — follow exactly, in this order

### 1. Header (do not label this section)
# [Video title]
**URL** : {url} · **Channel** : {channel} · **Processed** : {date} · **Duration** : {duration}

### 2. Central thesis
## Thèse centrale
3 to 5 sentences. What is the video's main argument or position?
What idea does the author defend from start to finish?

### 3. Inferred chapter breakdown
## Chapitrage inféré
A markdown table with 6 to 12 thematic blocks.
Columns: # | Bloc thématique | Début | Lien direct

Rules:
- Infer the structure from the content — there is no predefined outline.
- If native YouTube chapters are provided in {chapters}, use them as a base and refine.
- Format timestamps as HH:MM:SS.
- Generate direct links as: https://youtu.be/{video_id}?t={seconds}
- Choose granularity based on content density (6 blocks minimum, 12 maximum).

### 4. Idea map
## Carte des idées
A narrative paragraph (not a list) describing how the arguments connect.
Include inline timestamps at key transitions: [▶ HH:MM:SS](link)
Show the logical progression: what the author starts from,
what tension or problem is identified, how it is resolved or concluded.

### 5. Key concepts
## Concepts clés
For each significant concept identified in the video:

#### [Concept name] [▶ HH:MM:SS](link)
**Définition selon l'auteur** : how the author defines it in their own words — never a generic definition.
**Exemple utilisé** : the specific example the author uses to illustrate the concept.

Minimum 3 concepts required.
If fewer than 3 are identifiable, prepend the entire output with:
⚠️ AVERTISSEMENT : moins de 3 concepts identifiés dans cette vidéo.

### 6. Notable formulations
## Formulations notables
Direct quotes from the transcript, reproduced verbatim — never paraphrased.

Format:
> "Exact quote as spoken"
> [▶ HH:MM:SS](link)

### 7. Open questions
## Questions ouvertes
2 to 3 questions raised by the video but left unanswered.
These are intellectual tensions, implications, or "what next?" questions
the content surfaces — not comprehension questions about what was said.

### 8. Personal notes
## Mes notes
*(espace libre)*

DO NOT generate any content in this section.
Leave only the heading and the italic placeholder exactly as shown above.

### 9. Sources and references
## Sources & références
Filtered from the YouTube video description provided in {description}.

Include ONLY sources with an identifiable author or title:
books, articles, studies, named websites, named tools.

Ignore: social media links, generic URLs, sponsor mentions,
channel promotion, affiliate links, timestamps-only references.

Format: - [Title or author name](URL)

If no qualifying sources are found: write exactly "Aucune source identifiée."

### 10. Full timestamped transcript
---
<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->

Paste the full transcript here, one segment per line.
Format: [HH:MM:SS] text

## Absolute rules — never violate these
1. Never invent a timestamp. If you cannot anchor an element, omit the timestamp rather than approximating.
2. Notable quotes must be verbatim from the transcript. Never paraphrase a citation.
3. Concept definitions must reflect the author's own usage, never a generic or Wikipedia definition.
4. Do not generate any content for "Mes notes". Leave it empty.
5. Read the full transcript before structuring. Do not process by chunks.
6. The sources section contains only items from {description}, never invented references.
```

---

## Bloc 4 — Comportements aux limites

| Situation | Comportement attendu |
|---|---|
| Sous-titres absents | Erreur terminal : *"Aucun sous-titre disponible pour cette vidéo. Envisagez yt-dlp + Whisper (hors scope V1)."* Aucun fichier créé. |
| Langue demandée absente | Fallback sur langue disponible la plus proche + avertissement terminal : *"Langue [fr] non disponible. Utilisation de [en]."* |
| Chapitres YouTube natifs présents | Transmis au LLM via `{chapters}` pour servir de base au chapitrage inféré. |
| Contexte modèle insuffisant | Blocage avec message : *"Modèle [X] : fenêtre de contexte insuffisante ([N] tokens disponibles, [M] requis). Utilisez Groq (128k) ou un modèle 32k+."* Aucun fichier créé. |
| Chapitrage généré < 6 blocs | Sauvegarde + avertissement en tête de fiche : *"⚠️ Chapitrage incomplet : [N] blocs détectés, minimum 6 attendus."* |
| Concepts générés < 3 | Sauvegarde + avertissement en tête de fiche (géré dans le prompt + validateur). |
| Erreur API LLM | Erreur terminal avec code HTTP. Aucun fichier créé. |
| Vidéo privée ou supprimée | Erreur terminal. Aucun fichier créé. |
| Fichier déjà existant | Demande de confirmation : *"Ce fichier existe déjà : [chemin]. Écraser ? (o/N)"* Aucune action sans confirmation explicite. |
| Description YouTube vide | Section sources affiche "Aucune source identifiée." sans erreur. |

---

## Bloc 5 — Stratégie de test

### Test de smoke

URL de référence fixe : `https://youtu.be/T_GqhyYqTD4`  
Chaîne : `@SamouraiDansant`  
Transcript FR auto-généré disponible, 697 segments validés.

```bash
python extract.py https://youtu.be/T_GqhyYqTD4
# Résultat attendu : fichier .md créé, non vide, aucune erreur terminal
```

### Test de structure (automatisé)

`tests/test_structure.py` vérifie sur le fichier généré :

- [ ] Les 8 sections obligatoires sont présentes (Thèse centrale, Chapitrage, Carte des idées, Concepts clés, Formulations notables, Questions ouvertes, Mes notes, Sources & références)
- [ ] Le tableau de chapitrage contient entre 6 et 12 lignes
- [ ] Au moins 3 concepts sont présents
- [ ] Au moins 1 formulation notable est présente
- [ ] La section "Mes notes" ne contient que le placeholder italic — aucun contenu généré
- [ ] Le transcript complet est présent après le séparateur `---`
- [ ] Au moins 1 lien `?t=` est valide (format numérique en secondes)

### Checklist de relecture humaine

Après chaque génération, 5 questions à se poser avant de valider la fiche :

1. **Thèse centrale** : reflète-elle vraiment la position de l'auteur — ou est-ce une reformulation générique qui pourrait s'appliquer à n'importe quelle vidéo sur le même sujet ?
2. **Chapitrage** : les timestamps correspondent-ils à des transitions réelles dans la vidéo ? Vérifier 2-3 liens au hasard.
3. **Concepts** : les définitions sont-elles celles de l'auteur, ou des définitions Wikipedia reformulées ?
4. **Citations** : les formulations notables sont-elles mot pour mot, ou légèrement paraphrasées ?
5. **Questions ouvertes** : sont-elles intellectuellement honnêtes — ou des questions rhétoriques avec réponse implicite dans le texte ?

---

## Annexe — Structure de fiche de référence

*Template de sortie attendu pour chaque vidéo traitée.*

```markdown
# [Titre de la vidéo]
**URL** : https://youtu.be/XXXX · **Channel** : Nom de la chaîne · **Processed** : 2026-04-05 · **Duration** : 45:12

## Thèse centrale
3 à 5 phrases. La position défendue, l'idée directrice de bout en bout.

## Chapitrage inféré
| # | Bloc thématique | Début | Lien direct |
|---|---|---|---|
| 1 | Mise en contexte | 00:00:00 | [▶](https://youtu.be/XXXX?t=0) |
| 2 | ... | 00:05:30 | [▶](https://youtu.be/XXXX?t=330) |

## Carte des idées
Paragraphe narratif décrivant la logique argumentative avec timestamps inline.
L'auteur part de [concept A] [▶ 00:01:20](lien), identifie la tension [▶ 00:08:45](lien),
pour aboutir à [conclusion] [▶ 00:38:10](lien).

## Concepts clés

### Nom du concept [▶ 00:12:34](https://youtu.be/XXXX?t=754)
**Définition selon l'auteur** : telle que formulée dans la vidéo.
**Exemple utilisé** : l'exemple spécifique employé pour illustrer.

## Formulations notables
> "Citation exacte telle que prononcée dans la vidéo"
> [▶ 00:18:22](https://youtu.be/XXXX?t=1102)

## Questions ouvertes
1. Question soulevée par la vidéo sans réponse donnée.
2. Tension ou implication non résolue.

## Mes notes
*(espace libre)*

## Sources & références
- [Titre de l'ouvrage ou article](URL)
- [Nom de l'auteur — titre](URL)

---
<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->
[00:00:00] Texte du premier segment...
[00:00:05] Suite du transcript...
```

---

*Fin des spécifications V1.0*  
*Document suivant : `README.md` — installation et usage*
