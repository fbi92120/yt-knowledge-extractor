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
- Documentation (README, SPECS) : anglais
- README.fr.md : français si audience francophone
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
