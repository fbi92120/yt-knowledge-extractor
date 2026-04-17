#!/bin/bash
# gist-publish.sh — publie un fichier Markdown sur GitHub Gist
# Usage : ./gist-publish.sh ma-fiche.md
# Prérequis : GITHUB_TOKEN dans l'environnement ou dans ~/.env

set -e

# --- Config ---
TOKEN="${GITHUB_TOKEN}"
if [ -z "$TOKEN" ] && [ -f "$HOME/.env" ]; then
  TOKEN=$(grep GITHUB_TOKEN "$HOME/.env" | cut -d'=' -f2)
fi

if [ -z "$TOKEN" ]; then
  echo "❌ GITHUB_TOKEN manquant."
  echo "   Exporte-le : export GITHUB_TOKEN=ghp_xxx"
  echo "   Ou ajoute GITHUB_TOKEN=ghp_xxx dans ~/.env"
  exit 1
fi

# --- Fichier ---
FILE="$1"
if [ -z "$FILE" ]; then
  echo "Usage : $0 <fichier.md>"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "❌ Fichier introuvable : $FILE"
  exit 1
fi

FILENAME=$(basename "$FILE")
CONTENT=$(cat "$FILE")

# --- Appel API GitHub ---
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/gists \
  -d "$(jq -n \
    --arg fname "$FILENAME" \
    --arg content "$CONTENT" \
    '{
      "description": "",
      "public": true,
      "files": {
        ($fname): { "content": ($content) }
      }
    }'
  )")

# --- Résultat ---
URL=$(echo "$RESPONSE" | jq -r '.html_url')

if [ "$URL" = "null" ] || [ -z "$URL" ]; then
  echo "❌ Erreur API GitHub :"
  echo "$RESPONSE" | jq -r '.message // .'
  exit 1
fi

echo "✅ Gist publié : $URL"
