# BACKLOG.md — YT Knowledge Extractor

**Version** : 1.2  
**Date** : 2026-05-08  
**Auteur** : François Biller  
**Statut** : Mise à jour — 6 entrées ajoutées suite à co-construction SPECS V1.8 (4 entrées spec + 2 entrées méthodologiques)  
**Repo** : https://github.com/fbi92120/yt-knowledge-extractor  

---

## Bugs connus

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

### Feature --export — copie d'une fiche dans un dossier hors iCloud
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
**Statut** : ouvert — spec validée, implémentation à lancer

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
