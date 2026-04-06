#!/bin/bash
# setup.sh — Installation de YT Knowledge Extractor
# À lancer une fois après avoir cloné le repo
#
# Ce script :
#   1. Place les fichiers CLAUDE.md aux bons endroits
#   2. Copie les fichiers de configuration exemple
#   3. Installe les dépendances Python
#
# Usage : ./setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    YT Knowledge Extractor — Installation     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── Étape 1 — Informations personnelles ───────────────────────────────────

echo "📋 Quelques informations pour personnaliser votre installation."
echo ""

read -p "Votre nom (pour la documentation) : " USER_NAME
read -p "Votre compte GitHub : " GITHUB_USER
echo ""
echo "Chemin de votre vault Obsidian (laisser vide pour utiliser ./output)"
read -p "Vault path [./output] : " VAULT_PATH
VAULT_PATH=${VAULT_PATH:-./output}

echo ""

# ─── Étape 2 — Fichiers CLAUDE.md ──────────────────────────────────────────

echo "📁 Installation des fichiers CLAUDE.md..."

# Niveau global
mkdir -p ~/.claude
if [ -f ~/.claude/CLAUDE.md ]; then
    echo "   ⚠️  ~/.claude/CLAUDE.md existe déjà."
    read -p "   Écraser ? (o/N) : " OVERWRITE_GLOBAL
    if [[ "$OVERWRITE_GLOBAL" =~ ^[Oo]$ ]]; then
        cp CLAUDE.global.md ~/.claude/CLAUDE.md
        echo "   ✓ ~/.claude/CLAUDE.md mis à jour"
    else
        echo "   → Ignoré"
    fi
else
    cp CLAUDE.global.md ~/.claude/CLAUDE.md
    echo "   ✓ ~/.claude/CLAUDE.md créé"
fi

# Niveau Projects
PROJECTS_DIR="$(dirname "$(pwd)")"
if [ -f "$PROJECTS_DIR/CLAUDE.md" ]; then
    echo "   ⚠️  $PROJECTS_DIR/CLAUDE.md existe déjà."
    read -p "   Écraser ? (o/N) : " OVERWRITE_PROJECTS
    if [[ "$OVERWRITE_PROJECTS" =~ ^[Oo]$ ]]; then
        sed "s/\[GITHUB\]/$GITHUB_USER/g" CLAUDE.projects.md > "$PROJECTS_DIR/CLAUDE.md"
        echo "   ✓ $PROJECTS_DIR/CLAUDE.md mis à jour"
    else
        echo "   → Ignoré"
    fi
else
    sed "s/\[GITHUB\]/$GITHUB_USER/g" CLAUDE.projects.md > "$PROJECTS_DIR/CLAUDE.md"
    echo "   ✓ $PROJECTS_DIR/CLAUDE.md créé"
fi

# Niveau projet — déjà présent, juste substituer [GITHUB]
sed -i.bak "s/\[GITHUB\]/$GITHUB_USER/g" CLAUDE.md && rm CLAUDE.md.bak
echo "   ✓ CLAUDE.md (projet) personnalisé"

echo ""

# ─── Étape 3 — Configuration ───────────────────────────────────────────────

echo "⚙️  Configuration..."

if [ ! -f config.yml ]; then
    cp config.yml.example config.yml
    # Substituer le chemin du vault
    sed -i.bak "s|vault_path:.*|vault_path: $VAULT_PATH|g" config.yml && rm config.yml.bak
    echo "   ✓ config.yml créé depuis config.yml.example"
    echo "   → Vault path : $VAULT_PATH"
else
    echo "   → config.yml existe déjà, non modifié"
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "   ✓ .env créé depuis .env.example"
    echo "   ⚠️  Renseigner votre clé API dans .env avant d'utiliser le script"
else
    echo "   → .env existe déjà, non modifié"
fi

echo ""

# ─── Étape 4 — Dépendances Python ──────────────────────────────────────────

echo "🐍 Installation des dépendances Python..."

if command -v python3 &> /dev/null; then
    python3 -m pip install -r requirements.txt --quiet
    echo "   ✓ Dépendances installées"
else
    echo "   ✗ Python 3 non trouvé — installer Python 3.10+ et relancer"
    exit 1
fi

echo ""

# ─── Résumé ────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════╗"
echo "║              Installation terminée           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Prochaines étapes :"
echo "  1. Renseigner votre clé API dans .env"
echo "     ex : GROQ_API_KEY=gsk_..."
echo ""
echo "  2. Vérifier le vault path dans config.yml"
echo "     vault_path: $VAULT_PATH"
echo ""
echo "  3. Lancer le test de référence :"
echo "     python extract.py https://youtu.be/T_GqhyYqTD4"
echo ""
echo "Documentation complète : README.md"
echo ""
