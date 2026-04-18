# PLAN.md — Plan d'implémentation YT Knowledge Extractor

**Version** : 1.0  
**Date** : 2026-04-06 11:47  
**Méthode** : Séquence de 10 prompts séquentiels (un par un, chaque étape terminée avant la suivante)

---

## Prompt 1 — Bootstrap du projet

Créer la structure complète du projet selon SPECS.md.  
Créer tous les fichiers vides avec leurs docstrings.  
Créer `requirements.txt`, `config.yml.example`, `.env.example` et `.gitignore`.  
Ne pas implémenter la logique — structure uniquement.

**Fichiers :**
```
extract.py
requirements.txt
config.yml.example
.env.example
.gitignore
src/__init__.py
src/transcript.py
src/metadata.py
src/generator.py
src/writer.py
src/validator.py
src/llm/__init__.py
src/llm/base.py
src/llm/groq.py
src/llm/anthropic.py
src/llm/openai.py
src/llm/ollama.py
tests/__init__.py
tests/test_smoke.py
tests/test_structure.py
```

---

## Prompt 2 — Couche transcript (`src/transcript.py`)

Implémenter l'extraction du transcript horodaté via `youtube-transcript-api`.  
Retourne une liste de segments avec `start` (secondes) et `text`.  
Gère les cas d'erreur : sous-titres absents, langue non disponible (fallback + warning).

---

## Prompt 3 — Couche métadonnées (`src/metadata.py`)

Extraire via `yt-dlp` : titre, chaîne, durée, description, chapitres natifs YouTube.  
Filtrer les sources intellectuelles depuis la description : conserver uniquement les entrées avec auteur ou titre identifiable.

---

## Prompt 4 — Couche LLM (`src/llm/base.py` + `src/llm/groq.py`)

Implémenter la classe abstraite `LLMProvider` dans `base.py`.  
Implémenter le provider Groq concret dans `groq.py`.  
Le provider vérifie que la fenêtre de contexte est suffisante avant d'envoyer la requête.  
Si insuffisant : lève `ContextTooLargeError` avec tokens disponibles et requis.

---

## Prompt 5 — Générateur de fiche (`src/generator.py`)

Orchestre transcript + métadonnées + LLM pour produire la fiche Markdown complète.  
Template exact depuis SPECS.md Bloc 3.  
Le transcript horodaté (section 10) est ajouté programmatiquement après la réponse LLM — ne pas le laisser au LLM.

---

## Prompt 6 — Validateur (`src/validator.py`)

Vérifie sur la fiche générée :
- 8 sections obligatoires présentes
- Chapitrage : entre 6 et 12 lignes dans le tableau
- Au moins 3 concepts
- Au moins 1 formulation notable
- Section "Mes notes" vide (placeholder uniquement)
- Transcript complet présent après `---`
- Au moins 1 lien `?t=` valide

Retourne une liste d'avertissements (pas d'exception bloquante).

---

## Prompt 7 — Writer (`src/writer.py`)

Génère le slug ASCII depuis le titre via `python-slugify`.  
Construit le chemin : `[vault_path]/[chaîne-slug]/[YYYY-MM-DD]-[slug].md`.  
Crée les dossiers si nécessaires.  
Si le fichier existe, demande confirmation avant d'écraser.  
Préfixe les avertissements du validateur en tête de fichier si présents.

---

## Prompt 8 — Point d'entrée (`extract.py`)

CLI simple : `python extract.py [URL]`  
Orchestre dans l'ordre :
1. Lecture `config.yml` et `.env`
2. Extraction métadonnées
3. Extraction transcript
4. Vérification contexte LLM
5. Génération fiche
6. Validation
7. Écriture fichier
8. Confirmation terminal avec chemin du fichier créé

Zéro logique métier — tout délégué à `src/`.

---

## Prompt 9 — Tests (`tests/test_smoke.py` + `tests/test_structure.py`)

URL de référence : `https://youtu.be/T_GqhyYqTD4`  
Le smoke test vérifie que le fichier est créé et non vide.  
Le structure test vérifie les 8 points du validateur.

---

## Prompt 10 — Documentation

- `README.md` (EN) : description, prérequis, installation, configuration, usage, providers LLM, contribuer, licence
- `README.fr.md` (FR) : même contenu
- `CONTRIBUTING.md` : guide de contribution
- `LICENSE` : licence MIT (copyright François Biller 2026)

---

## Décisions architecturales

1. **Pas de SDK LLM** — tous les providers utilisent `requests` directement (dépendances minimales)
2. **Transcript ajouté programmatiquement** — section 10 garantie même si le LLM la tronque
3. **Estimation tokens conservative** — `len(text) / 3.5` + buffer 4000 → bloque tôt plutôt que tronquer
4. **Validateur = warnings, pas blocages** — seuls le contexte insuffisant et les sous-titres absents bloquent
5. **extract.py = zéro logique** — tout dans `src/` pour préparer V3 SaaS

---

## Vérification end-to-end

```bash
pip install -r requirements.txt
cp config.yml.example config.yml
cp .env.example .env
# Ajouter clé Gemini dans .env (GEMINI_API_KEY)
python extract.py https://youtu.be/T_GqhyYqTD4
# → Fichier .md créé, 10 sections, aucune erreur
pytest tests/
```
