from __future__ import annotations

"""Point d'entrée CLI — YT Knowledge Extractor.

Usage : python extract.py [URL]

Orchestre le pipeline complet :
1. Lecture configuration (config.yml + .env)
2. Extraction métadonnées YouTube
3. Extraction transcript horodaté
4. Vérification fenêtre de contexte LLM (dans generator)
5. Génération de la fiche via LLM
6. Validation de la structure
7. Écriture du fichier Markdown
8. Confirmation terminal

Aucune logique métier ici — tout est délégué à src/.
"""

import os
import sys

import yaml
from dotenv import load_dotenv

from src.transcript import extract_video_id, fetch_transcript, format_transcript_for_prompt
from src.metadata import fetch_metadata
from src.generator import generate_note
from src.validator import validate_note
from src.writer import build_file_path, write_note


def load_config() -> dict:
    """Charge config.yml et .env. Injecte la clé API dans la config LLM."""
    load_dotenv()

    config_path = os.path.join(os.path.dirname(__file__), "config.yml")
    if not os.path.exists(config_path):
        print("Erreur : config.yml introuvable. Copiez config.yml.example vers config.yml.")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    api_key_env = config["llm"].get("api_key_env", "")
    if api_key_env:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            print(f"Erreur : variable d'environnement {api_key_env} non définie dans .env")
            sys.exit(1)
        config["llm"]["api_key"] = api_key

    return config


def main():
    """Pipeline principal."""
    if len(sys.argv) < 2:
        print("Usage : python extract.py [URL YouTube]")
        sys.exit(1)

    url = sys.argv[1]

    # 1. Configuration
    config = load_config()

    # 2. Extraction video_id
    video_id = extract_video_id(url)

    # 3. Extraction métadonnées
    print("Extraction des métadonnées...")
    metadata = fetch_metadata(url)
    print(f"  → {metadata['title']} ({metadata['duration']})")

    # 4. Extraction transcript
    language = config.get("transcript_language", "fr")
    print(f"Extraction du transcript ({language})...")
    segments, actual_language = fetch_transcript(video_id, language)
    if actual_language != language:
        print(f"  ⚠ Langue {language} non disponible. Utilisation de {actual_language}.")
    print(f"  → {len(segments)} segments extraits")

    formatted_transcript = format_transcript_for_prompt(segments)

    # 5. Génération fiche via LLM
    print(f"Génération de la fiche via {config['llm']['provider']}...")
    note = generate_note(config, video_id, url, metadata, segments, formatted_transcript)

    # 6. Validation
    _, warnings = validate_note(note)
    if warnings:
        print("  ⚠ Avertissements de validation :")
        for w in warnings:
            print(f"    - {w}")
    else:
        print("  → Validation OK")

    # 7. Écriture fichier
    file_path = build_file_path(
        config, metadata["channel"], metadata["upload_date"], metadata["title"]
    )
    result_path = write_note(file_path, note, warnings)

    # 8. Confirmation
    print(f"\n✓ Fiche créée : {result_path}")


if __name__ == "__main__":
    main()
