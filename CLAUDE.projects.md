# CLAUDE.md — Projects
# Emplacement cible : ~/Projects/CLAUDE.md
# Portée : tous les projets dans le dossier ~/Projects/
#
# INSTALLATION :
#   Option 1 : lancer ./setup.sh à la racine du repo (recommandé)
#   Option 2 : copier manuellement
#              cp CLAUDE.projects.md ~/Projects/CLAUDE.md
#
# Ce fichier complète le CLAUDE.md global (~/.claude/CLAUDE.md).
# Il définit les conventions communes à tous les projets.

---

## Conventions communes à tous les projets

### Langues
- Code : anglais
- Commentaires dans le code : français
- Docs publiques (README.md, CONTRIBUTING.md, LICENSE) : anglais
  → point d'entrée d'un visiteur GitHub, convention open-source standard
- Traductions du README : README.[lang].md (ex: README.fr.md)
- Docs internes (SPECS.md, PLAN.md, CLAUDE.md, méthodologie) : langue de l'équipe
  → français pour les projets de François par défaut
- Livrables générés : français par défaut, configurable

### Structure systématique de tout nouveau projet

```
[projet]/
├── README.md              # EN
├── README.fr.md           # FR
├── SPECS.md               # spécifications complètes
├── CLAUDE.md              # instructions projet
├── CLAUDE.global.md       # à placer dans ~/.claude/CLAUDE.md
├── CLAUDE.projects.md     # à placer dans ~/Projects/CLAUDE.md
├── setup.sh               # script d'installation
├── config.yml.example     # template configuration utilisateur
├── .env.example           # template variables d'environnement
├── .gitignore
├── requirements.txt
└── tests/
    ├── test_contract.py   # tests de contrat — avant les modules
    └── test_smoke.py      # test d'intégration — en dernier
```

### Environnement Python (tout projet Python)

- Chaque projet a son propre venv à la racine : `.venv/`
- `.venv/` est dans `.gitignore`
- Version Python cible : la plus récente stable supportée par les deps
  (aujourd'hui 3.12, via Homebrew : `brew install python@3.12`)
- `setup.sh` crée le venv et installe les deps dedans (PEP 668-compliant)
- Les alias terminal pointent vers `.venv/bin/python` en chemin absolu,
  jamais vers `python3` système
- `requirements.txt` inclut les deps runtime ET test (pas de split dev/prod
  tant que le projet n'en a pas besoin)

### Git — stratégie de commit

Commiter par bloc fonctionnel, pas par ligne. Format :

```
feat: [ce qui a été implémenté]
test: [tests ajoutés]
docs: [documentation ajoutée]
fix:  [patch inévitable — expliquer pourquoi dans le corps du commit]
```

### Sécurité — vérification avant tout premier commit

- [ ] `.env` absent du staging (`git status` ne doit pas le montrer)
- [ ] `.gitignore` contient `.env`, `config.yml`, dossiers de sortie
- [ ] Aucune clé ou valeur réelle dans les fichiers `.example`
- [ ] Aucun chemin personnel hardcodé dans le code
