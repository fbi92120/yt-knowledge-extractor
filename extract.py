from __future__ import annotations

"""Point d'entrée CLI — YT Knowledge Extractor.

Usage :
    python extract.py [URL]                         ← mode unitaire
    python extract.py fichier.txt [--dry-run]       ← mode batch
    python extract.py --dry-run fichier.txt         ← ordre alternatif

Orchestre le pipeline complet sans logique métier — tout est dans src/.
"""

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from yaspin import yaspin
from yaspin.spinners import Spinners

from src.transcript import extract_video_id, fetch_transcript, format_transcript_for_prompt
from src.metadata import fetch_metadata
from src.generator import generate_note
from src.validator import validate_note
from src.writer import build_file_path, write_note
from src.batch import parse_batch_file, resolve_model, archive_existing


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


def _run_single(config: dict, url: str) -> None:
    """Pipeline complet pour une URL unique."""
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    language_warning: str | None = None
    warnings: list[str] = []
    result_path = None

    with yaspin(Spinners.dots, color="cyan") as sp:
        try:
            sp.text = "Extraction des métadonnées..."
            metadata = fetch_metadata(url)

            sp.text = "Extraction du transcript..."
            language = config.get("transcript_language", "fr")
            segments, actual_language = fetch_transcript(video_id, language)
            if actual_language != language:
                language_warning = (
                    f"Langue {language} non disponible. Utilisation de {actual_language}."
                )
            formatted_transcript = format_transcript_for_prompt(segments)

            sp.text = f"Génération de la fiche via {config['llm']['provider']}..."
            note = generate_note(
                config, video_id, url, metadata, segments, formatted_transcript
            )

            _, warnings = validate_note(note)

            file_path = build_file_path(
                config,
                metadata["channel"],
                metadata["upload_date"],
                metadata["title"],
            )

            overwrite = False
            if file_path.exists():
                sp.stop()
                try:
                    answer = input(f"Ce fichier existe déjà : {file_path}\nÉcraser ? (o/N) ")
                except (EOFError, KeyboardInterrupt):
                    print("\nAnnulé.", file=sys.stderr)
                    sys.exit(1)
                if answer.strip().lower() not in ("o", "oui", "y", "yes"):
                    print("Écriture annulée par l'utilisateur.")
                    sys.exit(0)
                overwrite = True
                sp.start()

            sp.text = "Écriture dans le vault..."
            result_path = write_note(file_path, note, warnings, overwrite=overwrite)

            sp.ok("✓")
        except Exception as e:
            sp.fail("✗")
            print(f"\nErreur : {e}", file=sys.stderr)
            sys.exit(1)

    if language_warning:
        print(f"⚠ {language_warning}")

    if warnings:
        print("⚠ Avertissements de validation :")
        for w in warnings:
            print(f"  - {w}")

    print(f"\n✓ Fiche créée : file://{result_path.absolute()}")


def _run_batch(config: dict, batch_path: Path, dry_run: bool) -> None:
    """Pipeline batch depuis un fichier d'URLs."""
    try:
        file_default_model, entries = parse_batch_file(batch_path)
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable : {batch_path}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("Aucune URL trouvée dans le fichier.")
        sys.exit(0)

    total = len(entries)
    config_model = config["llm"]["model"]

    if dry_run:
        print(f"[DRY-RUN] {total} URL(s) à traiter\n")
        for i, entry in enumerate(entries, 1):
            model = resolve_model(entry.model, file_default_model, config_model)
            print(f"[{i}/{total}] {entry.url}")
            print(f"  Modèle : {model}")
        return

    successes = 0
    failures = 0
    archived = 0

    for i, entry in enumerate(entries, 1):
        model = resolve_model(entry.model, file_default_model, config_model)
        print(f"[{i}/{total}] {entry.url}... ({model})")

        try:
            video_id = extract_video_id(entry.url)
        except ValueError as e:
            print(f"  ✗ URL invalide : {e}")
            failures += 1
            continue

        entry_config = {**config, "llm": {**config["llm"], "model": model}}

        try:
            metadata = fetch_metadata(entry.url)
            language = config.get("transcript_language", "fr")
            segments, _ = fetch_transcript(video_id, language)
            formatted_transcript = format_transcript_for_prompt(segments)

            note = generate_note(
                entry_config, video_id, entry.url, metadata, segments, formatted_transcript
            )
            _, warnings = validate_note(note)

            file_path = build_file_path(
                entry_config,
                metadata["channel"],
                metadata["upload_date"],
                metadata["title"],
            )

            archive_path = archive_existing(file_path)
            if archive_path:
                print(f"  → Archivée : {archive_path}")
                archived += 1

            write_note(file_path, note, warnings, overwrite=False)
            print(f"  ✓ Créé : {file_path}")
            successes += 1

        except Exception as e:
            print(f"  ✗ Erreur : {e}")
            failures += 1

    print(f"\nRésumé : {successes} succès, {failures} échec(s), {archived} archivée(s)")


def main():
    """Dispatch selon les arguments : mode unitaire ou batch."""
    config = load_config()

    raw_args = sys.argv[1:]
    dry_run = "--dry-run" in raw_args
    args = [a for a in raw_args if a != "--dry-run"]

    if args:
        first_arg = args[0]
        if first_arg.endswith(".txt"):
            _run_batch(config, Path(first_arg), dry_run)
            return
        url = first_arg
    else:
        try:
            url = input("Entrez le lien YouTube : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAnnulé.", file=sys.stderr)
            sys.exit(1)
        if not url:
            print("Aucune URL fournie.", file=sys.stderr)
            sys.exit(1)

    _run_single(config, url)


if __name__ == "__main__":
    main()
