#!/bin/bash
# Usage: bash get_fiche.sh <numéro> "slug-partiel"
# Exemple: bash get_fiche.sh 3 "deux-philosophies"

VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/YT-Knowledge"
NUM="$1"
SEARCH="$2"

if [ -z "$NUM" ] || [ -z "$SEARCH" ]; then
  echo "Usage: bash get_fiche.sh <numéro> \"slug-partiel\""
  echo "Exemple: bash get_fiche.sh 3 \"deux-philosophies\""
  exit 1
fi

FILE=$(find "$VAULT" -name "*${SEARCH}*" -type f | head -1)

if [ -z "$FILE" ]; then
  echo "❌ Aucune fiche trouvée pour : $SEARCH"
  exit 1
fi

DEST="$HOME/Desktop/fiche${NUM}-V11.md"
cp "$FILE" "$DEST"
echo "✅ Copié sur le Bureau : fiche${NUM}.md"
echo "   Source : $(basename "$FILE")"
