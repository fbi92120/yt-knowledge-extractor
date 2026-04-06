# CLAUDE.md — Global
# Emplacement cible : ~/.claude/CLAUDE.md
# Portée : tous les projets Claude Code sur cette machine
#
# INSTALLATION :
#   Option 1 : lancer ./setup.sh à la racine du repo (recommandé)
#   Option 2 : copier manuellement
#              mkdir -p ~/.claude && cp CLAUDE.global.md ~/.claude/CLAUDE.md
#
# Ce fichier est lu par Claude Code au démarrage de chaque session,
# quel que soit le projet ouvert.

---

## Méthode — principes universels

Ces principes s'appliquent à tous les projets sans exception.
Ils sont issus de la méthode de co-construction des specs documentée
dans METHODE_SPECS_CO-CONSTRUCTION.md.

- Co-construire les specs dans Claude.ai avant de commencer à coder
- Un prompt = un module = un test avant de passer au suivant
- Ne jamais patcher : toute divergence remonte aux specs d'abord
- Ne jamais prendre de décision d'architecture seul : signaler et attendre

## Dérive de spec — règle absolue

Une spec qui change pendant le codage révèle une décision non tranchée
en amont — pas une raison de patcher.

Si une évolution de spec semble nécessaire pendant le codage :
1. Stopper l'implémentation immédiatement
2. Formuler précisément ce qui change et pourquoi
3. Attendre validation humaine avant de reprendre

Signal d'alarme obligatoire :

> 🚨 SPEC MANQUANTE : [description précise de ce qui n'est pas couvert]

Ne jamais continuer sans avoir reçu une instruction explicite
en réponse à ce signal.

## Constitution minimale de tout projet

Ces règles s'appliquent même en l'absence de constitution spécifique :

- Aucun chemin ou clé hardcodé — toujours `config.yml` + `.env`
- `.env` dans `.gitignore` — vérifié avant le premier commit
- Entrées utilisateur validées avant tout traitement
- Comportement défini si une clé API est absente (message lisible, pas crash)

## Tests — stratégie en deux temps

- Les modules à contrat fixe défini dans les specs ont leurs tests
  écrits **avant** le code du module
- On ne modifie jamais un test pour qu'il s'adapte au code produit
- Le test d'intégration (smoke) est écrit après le pipeline complet

## Gouvernance Claude.ai / Claude Code

- Claude.ai cadre le problème, définit les specs, arbitre les décisions
- Claude Code implémente dans ce cadre
- Toute proposition qui dépasse le cadre du prompt en cours →
  utiliser le signal 🚨 SPEC MANQUANTE et attendre l'arbitrage
- L'humain exerce son jugement à chaque étape —
  il orchestre, il valide, il décide

## Rôle de l'humain

Sur les tâches de définition, d'arbitrage, de validation et du jugement,
l'humain n'est pas remplaçable :

- Définir le problème réel
- Exercer son jugement sur ce qui est produit
- Trancher les décisions de spec
- Geler les specs avant l'implémentation
- Contrôler la stratégie de test
- Valider l'alignement final avec le besoin réel

Un humain qui ne juge plus — qui valide sans évaluer —
a délégué ce qu'il ne doit pas déléguer.
