# BACKLOG.md — YT Knowledge Extractor

**Version** : 1.6  
**Date** : 2026-07-10
**Auteur** : François Biller  
**Statut** : V1.8 livrée — --export fermé, 2 items transversaux ajoutés à l'implémentation.
  Ajout section "Dette de documentation — cohérence SPECS/code" (audit préparation bench Qwen 3 8B local).
  Ajout de 2 pistes futures (--dump-prompts, format {chapters}) — session bench llm-lab.  
**Repo** : https://github.com/fbi92120/yt-knowledge-extractor  

---

## Bugs connus

### [MINOR] check_archived_fiche() duplique la navigation vault de _find_existing_fiche()
**Projet** : yt-extractor
**Date** : 2026-05-13
**Source** : implémentation V1.8 — problème transversal identifié
**Description** : `src/export.py::check_archived_fiche()` relit la config output
  (mode, vault_path, local_path) et itère les `.md` du vault, exactement comme
  `extract.py::_find_existing_fiche()`. La duplication deviendra une dette si
  la logique de navigation vault évolue (nouveau mode, chemin alternatif, etc.).
**Action** : Déplacer `_find_existing_fiche()` dans `src/` (ex. `src/vault.py`)
  et faire appel à cette version unique depuis `extract.py` et `src/export.py`.
  À traiter dans le même prompt que le déplacement de `_extract_model_from_fiche()`.
**Priorité** : basse — pas de bogue actuel, dette de cohérence
**Statut** : ouvert

### [MINOR] open_in_finder() — comportement si subprocess.run code non-zéro non testé
**Projet** : yt-extractor
**Date** : 2026-05-13
**Source** : implémentation V1.8 — problème transversal identifié
**Description** : `open_in_finder()` utilise `check=False` (comportement par défaut
  de subprocess.run), donc un code de retour non-zéro de la commande `open` est
  silencieux. Aucun test ne couvre ce cas (ex. : répertoire inexistant au moment
  de l'appel). La commande `open` sur macOS retourne toujours 0 en pratique,
  mais la robustesse n'est pas garantie.
**Action** : Ajouter un test EX-09 : mocker subprocess.run pour retourner code 1,
  vérifier qu'aucune exception n'est levée et que la copie est préservée.
**Priorité** : très basse — cas théorique, macOS retourne toujours 0
**Statut** : ouvert

### [MINOR] Ghost directories avant confirmation overwrite
**Source** : gstack /review — adversarial synthesis
**Description** : build_file_path crée les dossiers avant 
la confirmation overwrite. Si l'utilisateur répond N, 
le dossier vide reste dans le vault.
**Priorité** : basse — outil personnel, impact cosmétique
**Fix** : déplacer mkdir après confirmation positive

## Gaps de spec

### Déduplication URLs — paramètres ?si= non nettoyés
**Projet** : yt-extractor
**Source** : production — batch validation V1.1
**Description** : URLs avec ?si= traitées comme distinctes 
  de la même URL sans paramètre. Génère des doublons en batch.
**Action** : Normaliser l'URL (extraire video_id) 
  avant déduplication dans le pipeline batch
**Statut** : ouvert

### Feature `--stats` — mesure tokens et coût par extraction
**Projet** : yt-extractor
**Date** : 2026-07-09
**Source** : co-construction llm-lab (transmission depuis projet YT archive)
**Description** : YT Extractor ne logge pas les tokens consommés par appel LLM. 
  Information utile pour comprendre les coûts réels par vidéo, anticiper les 
  limites de contexte, et surtout comparer YT Extractor + Gemini avec YT Extractor 
  + provider Ollama/local dans le contexte du projet llm-lab.
  L'API Gemini renvoie déjà `usage_metadata` avec `prompt_token_count`, 
  `candidates_token_count`, `total_token_count` — l'information existe, elle 
  n'est simplement pas exposée.
**Action** : Implémenter flag `--stats` sur `extract.py` affichant en terminal 
  input/output/total tokens + coût estimé Gemini. Implémenter flag `--stats-json` 
  pour sortie fichier machine-lisable `stats-YYYY-MM-DD-slug.json`. Étendre 
  progressivement aux autres providers

### Piste feature : flag `--dump-prompts`
**Projet** : yt-extractor
**Date** : 2026-07-09
**Source** : session bench llm-lab (Qwen 3 8B via Ollama)
**Description** : Pour reproduire fidèlement le comportement runtime de YT
  Extractor sur un bench externe, `src/generator.py` a dû être instrumenté
  temporairement pour intercepter `system_prompt` et `user_prompt` juste
  avant l'appel LLM et les écrire sur disque, puis revert la modification.
**Piste** : formaliser ce mécanisme en flag CLI `--dump-prompts` (ou
  `--dry-capture`). Comportement proposé :
  - Exécute le pipeline complet (metadata, transcript, formatage)
  - Écrit `system_prompt.txt`, `user_prompt.txt`, `metadata.json` dans un
    dossier (par défaut `./dump/` ou paramétrable)
  - N'appelle PAS le LLM, n'écrit PAS de fiche, ne publie PAS de gist
  - Exit propre avec confirmation terminal
**Cas d'usage** :
  - Debugging d'un prompt qui produit une sortie inattendue
  - Benchmark comparatif entre providers (Gemini, Claude, Ollama...) sur le
    même input
  - Reproductibilité d'un cas de génération pour analyse post-mortem
**Priorité** : basse — pas de blocage V1.x, à envisager si besoins
  récurrents de bench externe
**Statut** : ouvert

### Piste évolution SPECS : format d'injection de `{chapters}`
**Projet** : yt-extractor
**Date** : 2026-07-09
**Source** : lecture de code `src/generator.py:158` confirmée le 2026-07-09
**Description** : La substitution du placeholder `{chapters}` dans le system
  prompt utilise `str()` sur une `list[dict]` Python — soit une
  représentation type `[{'title': 'Introduction', 'start_time': 0.0}, ...]`
  avec `start_time` en float secondes.
**Friction potentielle** : le reste du prompt exige des timestamps au
  format HH:MM:SS. Le LLM doit convertir mentalement 690.0 → 00:11:30. Sur
  Gemini 2.5 Flash, aucun impact observé. Sur modèles plus petits (< 30B,
  ex. Qwen 3 8B), la charge cognitive peut dégrader la qualité du
  chapitrage inféré.
**Piste** : passer à un format lisible aligné sur la convention du reste
  du prompt. Proposition :
  ```
  00:00:00 - Introduction
  00:00:50 - The Disappearing Signal
  00:02:23 - Friction Was Infrastructure
  ...
  ```
  Un chapitre par ligne, timestamp en HH:MM:SS, séparateur explicite,
  titre à la fin. Cohérent avec le format transcript et avec les liens
  `?t=SECONDS` attendus en sortie.
**Prérequis avant action** : bench comparatif à mener dans llm-lab
  (Qwen 3 8B, format actuel vs format proposé) pour mesurer l'impact réel
  sur la qualité du chapitrage. Ne pas modifier avant preuve.
**Priorité** : basse tant que Gemini reste provider par défaut. Devient
  moyenne si intégration Ollama en provider principal.
**Statut** : ouvert — bench comparatif requis avant action

### ~~Feature --export — copie d'une fiche dans un dossier hors iCloud~~
**Projet** : yt-extractor
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : Spécifiée dans SPECS V1.8 mais non encore implémentée.
  Permet de copier une fiche du vault Obsidian vers un dossier local
  accessible via Finder (~/Documents/yt-exports/ par défaut), pour ajouter
  la fiche à un projet Claude.ai ou la partager manuellement.
  Résout le problème iCloud : les fiches dans le vault ne sont pas toujours
  téléchargées localement, ce qui empêche le drag & drop direct.
**Action** : Implémenter src/export.py + câblage CLI dans extract.py +
  test_export.py (8 tests EX-01 à EX-08). Voir SPECS V1.8 Bloc 2 (flux),
  Bloc 4 (comportements aux limites), Bloc 5 (tableau des tests),
  Annexe V1.8 (12 décisions de conception).
**Statut** : ~~fermé — livré 2026-05-13, commit d33d0fc (8/8 tests EX-01 à EX-08)~~

### Gemini n'est plus gratuit — corriger la mention "gratuit" du périmètre MVP
**Projet** : yt-extractor
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : SPECS V1.7 et V1.8 mentionnent "Gemini par défaut, gratuit"
  dans le périmètre MVP (Bloc 1). Cette mention est devenue inexacte —
  Gemini est facturé environ 5-10 centimes par fiche, avec un discount batch
  de -50%.
**Action** : Remplacer "gratuit" par "~5-10 centimes par fiche, discount batch -50%"
  dans le périmètre MVP. À intégrer dans un amendement V1.8.1 ou V1.9.
**Statut** : ouvert

### Gist en batch — rendre explicite "1 gist par fiche"
**Projet** : yt-extractor
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : SPECS V1.7 et V1.8 décrivent implicitement que --gist en mode 
  batch produit un gist distinct par fiche (visible dans le format du log :
  une URL gist par ligne). Mais cette logique n'est pas écrite explicitement.
  Un lecteur pourrait imaginer un gist agrégé contenant plusieurs fiches.
**Action** : Ajouter une mention explicite dans Bloc 2 ou Bloc 4 :
  "--gist en batch : un gist distinct par fiche. Pas de gist agrégé."
**Statut** : ouvert

### Gist — rendre explicite l'exclusion de la transcription
**Projet** : yt-extractor
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : SPECS V1.7 mentionne dans Bloc 2 : "Publication gist secret 
  (contenu tronqué avant le transcript)". Cette logique mérite une ligne 
  dédiée dans Bloc 4 (Comportements aux limites) car elle décrit un comportement 
  important : la fiche complète vit dans Obsidian, mais le gist publié exclut 
  la section 10 (transcription horodatée).
**Action** : Ajouter dans Bloc 4 : "--gist : la transcription horodatée 
  (section 10) est exclue du contenu publié. Le gist contient uniquement les 
  sections 1-9 (jusqu'aux Sources & références)."
**Statut** : ouvert

### BACKLOG.md sans entête — V1.0 initiale non conforme
**Projet** : yt-extractor
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : Le BACKLOG.md initial du repo n'avait pas d'entête conforme
  à la convention du projet (Version, Date, Auteur, Statut, Repo). Cette
  erreur initiale a été corrigée dans la V1.1 du 2026-05-08, mais elle
  signale un manque dans la convention : aucune règle n'imposait
  explicitement l'entête sur les fichiers .md structurants.
**Action** : Documenter la règle "tout .md structurant a une entête"
  dans CLAUDE.projects.md ou CLAUDE.global.md.
**Statut** : ouvert

### Vérifier la conformité aux conventions avant chaque livrable .md
**Projet** : tous projets
**Date** : 2026-05-08
**Source** : co-construction SPECS V1.8
**Description** : Lors de la mise à jour de BACKLOG.md, l'entête conforme
  n'a pas été ajoutée. L'erreur a été détectée par l'humain, pas par
  l'assistant. Indique un manque de checklist méthodologique avant
  livrable.
**Action** : Ajouter dans CLAUDE.global.md ou METHODE_SPECS_CO-CONSTRUCTION.md
  une checklist explicite "vérifications avant livrable" : entête conforme,
  pattern de nommage, lecture des conventions du projet.
**Statut** : ouvert

---

## Dette de documentation — cohérence SPECS/code

### SPECS Bloc 3 induit en erreur sur la structure du prompt (system vs user)
**Projet** : yt-extractor
**Date** : 2026-07-09
**Source** : audit de cohérence SPECS vs code — préparation bench Qwen 3 8B local
**Description** : SPECS.md Bloc 3 présente un unique bloc "Prompt système LLM"
  alors que le code sépare explicitement system prompt et user prompt.
  Réalité code :
  - `src/generator.py:16-142` contient `SYSTEM_PROMPT_TEMPLATE` (structure
    et règles de sortie uniquement)
  - `src/generator.py::build_user_prompt(formatted_transcript, filtered_sources)`
    construit le user prompt avec les headers "## Transcript complet\n" puis,
    conditionnellement, "## Sources extraites de la description\n"
  - `src/llm/base.py` ne fait que consommer les deux prompts déjà formatés
**Impact** : lecture littérale des SPECS induit en erreur sur ce qui est
  effectivement envoyé au LLM. Le scaffold markdown du user prompt n'est
  documenté nulle part.
**Action** : amender SPECS.md Bloc 3 pour distinguer explicitement "prompt
  système" et "prompt user" avec le scaffold réel. Ne pas toucher au code —
  dette de documentation uniquement.
**Statut** : ouvert

### Commentaire "réservé v2" obsolète sur la section 10 de la fiche
**Projet** : yt-extractor
**Date** : 2026-07-09
**Source** : audit de cohérence SPECS vs code — préparation bench Qwen 3 8B local
**Description** : SPECS.md Bloc 3 section 10 contient le commentaire
  `<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->`. `src/generator.py:228-229`
  réutilise pourtant `formatted_transcript` pour écrire la section 10 dès la V1 —
  la section est bien populée dans chaque fiche générée depuis V1.0.
**Impact** : commentaire trompeur dans le prompt envoyé au LLM à chaque
  génération. Aucun impact fonctionnel, mais pollution du contexte et
  contradiction avec le comportement observé.
**Action proposée** : retirer le commentaire "réservé v2" du
  `SYSTEM_PROMPT_TEMPLATE` dans `src/generator.py`, et amender SPECS.md
  Bloc 3 section 10 en conséquence. Décision à valider avec François avant
  toute modification de code.
**Statut** : ouvert — décision à valider

---

## Tests manquants identifiés

### transcript.py

**`format_timestamp(seconds)`** — aucun test unitaire
- `0` → `"00:00:00"`
- `3599` → `"00:59:59"` (boundary avant 1h)
- `3600` → `"01:00:00"` (boundary exact 1h)
- `7261` → `"02:01:01"` (>2h)
- `84.9` → `"00:01:24"` (troncature float, pas arrondi)
- Valeur négative → comportement indéfini (jamais documenté)

**`format_transcript_for_prompt(segments)`** — aucun test unitaire
- Liste vide → chaîne vide
- Segment avec texte vide ou espaces → `strip()` applied
- Segment avec `start=0.0` → `"[00:00:00] text"`

**`extract_video_id(url)`** — partiellement testé (URL invalide uniquement)
- `/shorts/ID` → retourne ID
- `/embed/ID` → retourne ID
- URL avec paramètres supplémentaires (`?t=42&list=...`) → retourne ID
- URL avec trailing slash (ex. `youtu.be/ID/`) → comportement actuel : retourne `"ID/"` au lieu de `"ID"` (**bug potentiel**)

**`fetch_transcript` — fallback langue (Bloc 4)**
- Langue demandée absente → fallback vers langue disponible + actual_language ≠ language
- Sous-titres désactivés → `NoTranscriptError`
- Vidéo indisponible → `NoTranscriptError`
- (Nécessitent des mocks réseau)

---

### metadata.py

**`filter_sources(description)`** — aucun test unitaire
- Description vide → `""`
- Lignes avec domaine exclu (instagram.com) → filtrées
- Lignes avec mot-clé commercial (sponsor, affilié) → filtrées
- Ligne = URL seule sans contexte textuel → filtrée
- Ligne = texte + URL identifiable (titre, auteur) → conservée
- Ligne sans URL ressemblant à une référence (guillemets, tiret) → conservée
- Description sans aucune source qualifiée → `""`

**`extract_chapters(info)`** — aucun test unitaire
- `info` sans clé "chapters" → `None`
- `info["chapters"] = []` → `None` (falsy)
- Chapitres avec champs manquants (title absent) → title = ""

**`_format_duration(seconds)`** — aucun test unitaire
- `0` → `"00:00"`
- Négatif → `"00:00"`
- `3599` → `"59:59"`
- `3600` → `"01:00:00"`
- `7261` → `"02:01:01"`

**`fetch_metadata` — upload_date mal formé (Bloc 4)**
- `upload_date_raw = ""` → passthrough `""`
- `upload_date_raw = "2024"` (4 chars) → passthrough `"2024"`
- (Nécessite un mock yt-dlp)

---

### generator.py

**`build_system_prompt()`** — aucun test unitaire
- `chapters=None` → injecte `"None (infer from content)"`
- `chapters=[...]` → injecte `str(chapters)` dans le prompt
- Toutes les variables `{placeholder}` sont substituées sans KeyError

**`build_user_prompt()`** — aucun test unitaire
- `filtered_sources=""` → pas de section "Sources extraites" dans le prompt
- `filtered_sources` non vide → section présente

**`validate_context_fit` / `ContextTooLargeError` (Bloc 4)**
- Modèle absent de `CONTEXT_WINDOWS` → pas d'erreur
- Prompt qui tient dans la fenêtre → pas d'erreur
- Prompt 1 token au-dessus de la limite → `ContextTooLargeError` avec message détaillé
- (Test unitaire pur possible sans appel réseau)

---

### validator.py

**`validate_note(content)`** — aucun test unitaire (couvert seulement via smoke test)
- Fiche complète valide → `(True, [])`
- Chaque section manquante individuellement → 1 avertissement précis
- Chapitrage = 5 lignes → avertissement (< 6)
- Chapitrage = 13 lignes → avertissement (> 12)
- Concepts = 2 → avertissement
- Aucune formulation notable → avertissement
- "Mes notes" avec contenu généré → avertissement
- "Mes notes" avec placeholder exact → pas d'avertissement
- Marqueur transcript absent → avertissement
- Marqueur présent mais aucun segment `[HH:MM:SS]` → avertissement
- Aucun lien `?t=` → avertissement

**`build_warning_header(warnings)`** — aucun test unitaire
- Liste vide → `""`
- Une entrée → header avec 1 bullet
- Plusieurs entrées → header avec N bullets

---

### writer.py

**`generate_slug(title)`** — aucun test unitaire
- Titre avec accents (`é`, `à`, `ç`) → slug ASCII
- Titre > 80 chars → tronqué à 80
- Titre vide → slug vide ou comportement slugify

**`build_file_path(config, ...)`** — aucun test unitaire
- `mode="obsidian"` → base = `vault_path`
- `mode="local"` → base = `local_path`
- Clé `mode` absente → défaut `"local"`
- Clé `local_path` absente → défaut `"./output"`

**`write_note(file_path, content, warnings)`** — partiellement testé
- `warnings` non vides → header d'avertissement préfixé dans le fichier
- `warnings` non vides + `overwrite=True` → header + nouveau contenu
- Répertoire parent inexistant → `FileNotFoundError` (contrat non documenté)

---

### llm/ — src/llm/__init__.py + base.py

**`get_provider(provider_name, ...)`** — aucun test unitaire
- Provider inconnu → `ValueError` avec message listant les providers disponibles
- Chaque provider connu → retourne une instance de la bonne classe

**`LLMProvider.validate_context_fit()`** — aucun test unitaire
- Modèle absent de `CONTEXT_WINDOWS` → retourne `None` sans erreur
- Prompt qui tient → pas d'erreur
- Prompt 1 token au-dessus → `ContextTooLargeError`
- Prompt exactement à la limite → pas d'erreur

**`LLMProvider.estimate_tokens(text)`** — aucun test unitaire
- Chaîne vide → `0`
- Texte connu → valeur attendue selon heuristique `len/3.5`

# Annexes
## Prompt Claude Code — ajout mesure tokens dans YT Extractor

Contexte : YT Extractor V1.8. Provider par défaut : Gemini via 
src/llm/gemini.py. Chaque appel à l'API Gemini renvoie un objet 
usage_metadata avec prompt_token_count, candidates_token_count, 
total_token_count.

Objectif : ajouter un flag --stats à extract.py qui affiche en 
fin de traitement un résumé des tokens consommés pour la génération.

Contraintes :
- Ne pas modifier le comportement par défaut. Sans --stats, aucune 
  sortie supplémentaire.
- Toucher uniquement à extract.py et src/llm/gemini.py (a minima).
- Format de sortie terminal proposé :
  📊 Tokens consommés :
    - Input  : X (prompt système + transcript + métadonnées)
    - Output : Y (fiche générée)
    - Total  : Z
    - Coût estimé Gemini 2.5 Flash : $A.AA (à ~$0.30/1M input, 
      $2.50/1M output)
- Étendre à --stats-json pour sortie machine-lisable dans un fichier 
  stats-YYYY-MM-DD-slug.json à côté de la fiche.
- Ajouter un test simple dans tests/test_stats.py qui mock la 
  réponse Gemini et vérifie le format d'affichage.
- Ne PAS toucher aux autres providers (openai, anthropic, ollama, 
  groq) — chaque provider ayant sa propre convention pour 
  usage_metadata, ce serait un prompt séparé.

Livrable attendu : diff prêt à merger, test passant, mise à jour 
README avec la nouvelle option.

🚨 SPEC MANQUANTE potentielle : le format exact d'usage_metadata 
retourné par le SDK Gemini utilisé (à vérifier avant implémentation, 
peut être un dict ou un objet).
