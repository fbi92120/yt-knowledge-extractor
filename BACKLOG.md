# BACKLOG.md — YT Knowledge Extractor

## Bugs connus

### [MINOR] Ghost directories avant confirmation overwrite
**Date** : inconnue
**Source** : gstack /review — adversarial synthesis
**Description** : build_file_path crée les dossiers avant 
la confirmation overwrite. Si l'utilisateur répond N, 
le dossier vide reste dans le vault.
**Priorité** : basse — outil personnel, impact cosmétique
**Fix** : déplacer mkdir après confirmation positive

### [BUG] Vérification fichier existant après appel LLM
**Date** : 2026-04-18 10:30
**Source** : production
**Description** : le pipeline appelait Gemini avant de vérifier
  si la fiche existait déjà. Tokens et temps gaspillés si l'utilisateur
  répond N.
**Fix** : vérification déplacée à l'étape 7, avant tout appel LLM.
**Statut** : corrigé dans SPECS.md V1.7 — implémenté

### [BUG] --gist publie le transcript
**Date** : 2026-04-18 10:30
**Source** : production
**Description** : --gist publiait la fiche complète transcript inclus.
**Fix** : contenu tronqué avant le séparateur transcript avant publication.
**Statut** : corrigé

### [BUG] --gist régénère une fiche existante sans confirmation
**Date** : 2026-04-18 10:30
**Source** : production
**Description** : yt "URL" --gist sur fiche existante déclenchait
  le pipeline complet sans demander confirmation.
**Fix** : détection fiche existante → publication directe sans régénération.
**Statut** : corrigé

## Gaps de spec

### Déduplication URLs — paramètres ?si= non nettoyés
**Date** : 2026-04-18 10:30
**Projet** : yt-extractor
**Source** : production — batch validation V1.1
**Description** : URLs avec ?si= traitées comme distinctes 
  de la même URL sans paramètre. Génère des doublons en batch.
**Action** : Normaliser l'URL (extraire video_id) 
  avant déduplication dans le pipeline batch
**Statut** : ouvert

### [GAP DE SPEC] Pas de flag --model en CLI
**Date** : 2026-04-18 10:30
**Source** : production
**Description** : changer de modèle nécessitait d'éditer config.yml.
  Incohérent avec model= disponible dans le format batch .txt.
**Fix** : flag --model NOM_MODELE ajouté, compatible --gist.
**Statut** : spécifié V1.7 — implémenté

### [MINOR] Logique métier _extract_model_from_fiche() dans extract.py
**Date** : 2026-04-18 10:53
**Source** : implémentation V1.7 — Claude Code
**Description** : fonction qui lit le header de la fiche pour extraire
  le modèle placée dans extract.py au lieu de src/.
  Viole le principe orchestrateur passif.
**Fix** : déplacer dans src/writer.py
**Priorité** : basse — fonctionnel, impact architectural uniquement


---

## Tests manquants identifiés

### transcript.py
**Date** : inconnue

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
**Date** : inconnue

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
**Date** : inconnue

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
**Date** : inconnue

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
**Date** : inconnue

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
**Date** : inconnue

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
