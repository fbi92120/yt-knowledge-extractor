# STATS — yt-knowledge-extractor

*Mesures générées le 2026-07-26. Commandes à exécuter depuis la racine du dépôt.*

## yt-knowledge-extractor

- **Date du premier commit** : 2026-04-05
  `git log --reverse --format='%ad' --date=short | head -1`
- **Date du dernier commit** : 2026-07-10
  `git log -1 --format='%ad' --date=short`
- **Nombre total de commits** : 40
  `git rev-list --count HEAD`
- **Nombre de jours calendaires distincts avec au moins un commit** : 11
  `git log --format='%ad' --date=short | sort -u | wc -l`
- **Durée calendaire entre premier et dernier commit** : 95 jours
  `git log --format='%at' | sort -n | awk 'NR==1{f=$1} END{printf "%d jours\n", ($1-f)/86400}'`
- **Plus longue interruption entre deux commits** : 56,99 jours
  `git log --format='%at' | sort -n | awk 'NR>1{g=$1-p; if(g>m)m=g} {p=$1} END{printf "%.2f jours\n", m/86400}'`
- **Nombre de fichiers de code, et lignes de code par langage** (hors `.venv`, `.git`, `__pycache__`, `output`) :
  - `.py` : 32 fichiers, 4663 lignes
  - `.sh` : 3 fichiers, 281 lignes
  - `.yml` : 1 fichier, 22 lignes

  Comptage fichiers : `find . -name '*.py' -not -path './.venv/*' -not -path './__pycache__/*' -not -path './output/*' | wc -l` (répéter par extension)
  Comptage lignes : `find . -name '*.py' -not -path './.venv/*' -not -path './__pycache__/*' -not -path './output/*' -print0 | xargs -0 cat | wc -l`
- **Nombre de fichiers markdown de documentation, et lignes totales** : 13 fichiers, 3371 lignes (documentation rédigée).
  Correction d'une mesure initiale trop inclusive (« 16 fichiers, 5468 lignes ») : elle comptait du contenu qui n'est pas de la documentation — 3 fiches d'exemple sous `examples/` (~2199 lignes) et 2 fiches de sortie sous `output/` (~1582 lignes), toutes des sorties de l'outil. Exclues ici.
  `find . -name '*.md' -not -path './.git/*' -not -path './.venv/*' -not -path './.pytest_cache/*' -not -path './examples/*' -not -path './output/*' | wc -l`
  `find . -name '*.md' -not -path './.git/*' -not -path './.venv/*' -not -path './.pytest_cache/*' -not -path './examples/*' -not -path './output/*' -print0 | xargs -0 cat | wc -l`
  Note inter-dépôts : `METHODE_SPECS_CO-CONSTRUCTION.md` (910 lignes) est une copie du document porté par vibe-coding-governed ; à ne compter qu'une seule fois dans un total portefeuille.
- **Nombre de tests, et commande utilisée pour les compter** : 189 fonctions `def test_` dans 13 fichiers `test_*.py`
  `grep -rE '^\s*def test_' --include='*.py' --exclude-dir=.venv . | wc -l`
  (Mesure la déclaration de fonctions de test ; ne lance pas la collecte pytest.)
- **Part du code réservée aux tests** : 59,0 % (2750 lignes de test sur 4663 lignes `.py` au total ; 15 fichiers `test_*.py` + contenu de `tests/`)
  Lignes de test : `find . -name '*.py' \( -name 'test_*.py' -o -path '*/tests/*' \) -not -path './.venv/*' -not -path './__pycache__/*' -print0 | xargs -0 cat | wc -l`
  Total `.py` : `find . -name '*.py' -not -path './.venv/*' -not -path './__pycache__/*' -print0 | xargs -0 cat | wc -l`
- **Taille moyenne d'une fonction Python (hors test)** : 30,4 lignes (médiane 20 ; min 3, max 256) sur 44 fonctions dans 17 fichiers.
  Mesuré par script AST : `ast.FunctionDef` + `end_lineno - lineno + 1`, sur les `.py` hors `tests/` et `test_*.py`.
- **Le code est-il commenté / documenté ?** : oui, principalement par docstrings.
  - Docstrings : fonctions 43/44 (98 %), classes 15/15 (100 %), modules 1/17 (6 %).
  - Commentaires inline : 49 pour 1444 lignes de code (ratio 0,03).
  - Lecture : documentation quasi systématique au niveau fonctions/classes (cohérent avec le bootstrap « fichiers vides + docstrings » de la méthode) ; peu de commentaires inline et peu de docstrings de module.
- **Version courante déclarée, si elle figure quelque part** :
  - `SPECS.md` : Version 1.8 (2026-05-08) — `grep -m1 -i version SPECS.md`
  - `CLAUDE.projects.md` : Version 1.0
  - `METHODE_SPECS_CO-CONSTRUCTION.md` (copie locale) : Version 7.3

---

## Autres mesures (critères de livraison)

- **Modules source** (.py hors test) : 17 — `find . -name '*.py' -not -path './.venv/*' ! -name 'test_*.py' -not -path './tests/*' | wc -l`
- **Dépendances runtime** : 7 (youtube-transcript-api, yt-dlp, python-slugify, pyyaml, python-dotenv, requests, yaspin) + pytest — `grep -vE '^\s*#|^\s*$' requirements.txt`
- **Ratio documentation / code** : 1,17 : 1 (5468 lignes `.md` de doc pour 4663 lignes `.py`)
- **Annotations de type** : présentes (59 occurrences `->` / `from __future__ import annotations`)
- **Packaging installable** (pyproject.toml / setup.py) : absent — installation via `setup.sh`
- **Intégration continue** (.github/workflows) : absente
- **Outillage lint / format / typecheck** (ruff / black / mypy) : absent
- **LICENSE** : présent

