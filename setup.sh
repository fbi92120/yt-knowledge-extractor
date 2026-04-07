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

# ─── Étape 4 — Alias terminal ──────────────────────────────────────────────

echo "⚡ Installation de l'alias terminal..."
echo ""

ALIAS_LINE='alias yt="$HOME/Projects/yt-knowledge-extractor/.venv/bin/python $HOME/Projects/yt-knowledge-extractor/extract.py"'
ZSHRC="$HOME/.zshrc"

if grep -q 'alias yt=' "$ZSHRC" 2>/dev/null; then
    echo "   → Alias 'yt' déjà présent dans ~/.zshrc, non modifié"
else
    echo "" >> "$ZSHRC"
    echo "# YT Knowledge Extractor" >> "$ZSHRC"
    echo "$ALIAS_LINE" >> "$ZSHRC"
    echo "   ✓ Alias ajouté dans ~/.zshrc"
    echo "   → Pour l'activer immédiatement : source ~/.zshrc"
fi

echo ""
echo "   Usage : yt [URL YouTube]"
echo "   Exemple : yt https://youtu.be/T_GqhyYqTD4"
echo ""

# ─── Étape 5 — Environnement virtuel + dépendances Python ─────────────────

echo "🐍 Création de l'environnement virtuel et installation des dépendances..."

# Cherche python3.12 en priorité, sinon python3.11, sinon python3 (doit être >= 3.10)
if command -v python3.12 &> /dev/null; then
    PYTHON_BIN=python3.12
elif command -v python3.11 &> /dev/null; then
    PYTHON_BIN=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_BIN=python3
else
    echo "   ✗ Aucun Python 3 trouvé — installer Python 3.10+ (ex: brew install python@3.12)"
    exit 1
fi

echo "   → Python utilisé : $($PYTHON_BIN --version)"

if [ ! -d .venv ]; then
    $PYTHON_BIN -m venv .venv
    echo "   ✓ Environnement virtuel créé : .venv/"
else
    echo "   → .venv existe déjà, non recréé"
fi

.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "   ✓ Dépendances installées dans .venv/"

echo ""

# ─── Étape 5 — Générer une première fiche (optionnel) ──────────────────────

echo "🎬 Générer une première fiche..."
echo ""
echo "   Vous pouvez tester l'outil maintenant sur une vidéo YouTube."
echo "   Laisser vide pour utiliser la vidéo de référence du projet."
echo "   (https://youtu.be/T_GqhyYqTD4 — Le SamourAI)"
echo ""
read -p "   URL YouTube [vidéo de référence] : " YOUTUBE_URL
YOUTUBE_URL=${YOUTUBE_URL:-https://youtu.be/T_GqhyYqTD4}

echo ""

# Vérifier que la clé API est configurée avant de lancer
if grep -q "^GEMINI_API_KEY=AIza" .env 2>/dev/null; then
    echo "   Clé API détectée. Lancement en cours..."
    echo ""
    .venv/bin/python extract.py "$YOUTUBE_URL"
else
    echo "   ⚠️  Clé API non configurée dans .env"
    echo "   → Renseigner GEMINI_API_KEY dans .env puis lancer :"
    echo "      .venv/bin/python extract.py \"$YOUTUBE_URL\""
fi

echo ""

# ─── Résumé ────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════╗"
echo "║              Installation terminée           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Usage :"
echo "  python extract.py [URL YouTube]"
echo ""
echo "Exemples :"
echo "  python extract.py https://youtu.be/T_GqhyYqTD4"
echo "  python extract.py https://www.youtube.com/watch?v=T_GqhyYqTD4"
echo ""
echo "Documentation complète : README.md"
echo ""
