from __future__ import annotations

"""Point d'entrée CLI — YT Knowledge Extractor.

Usage :
    python extract.py [URL]                                ← mode unitaire
    python extract.py [URL] [--gist]                       ← mode unitaire + publication gist
    python extract.py fichier.txt [--dry-run] [--gist]     ← mode batch
    python extract.py --dry-run fichier.txt                ← ordre alternatif

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
from src.share import publish_gist, GhNotFoundError, GhNotAuthenticatedError, GhPublishError


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


def _run_single(config: dict, url: str, gist: bool = False) -> None:
    """Pipeline complet pour une URL unique."""
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    language_warning: str | None = None
    warnings: list[str] = []
    result_path = None
    gist_existing = False
    file_path_existing = None

    with yaspin(Spinners.dots, color="cyan") as sp:
        try:
            sp.text = "Extraction des métadonnées..."
            metadata = fetch_metadata(url)

            file_path = build_file_path(
                config,
                metadata["channel"],
                metadata["upload_date"],
                metadata["title"],
            )

            # --gist + fiche existante → pas de régénération, publication directe
            if gist and file_path.exists():
                gist_existing = True
                file_path_existing = file_path
                sp.ok("✓")
            else:
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

    # --gist + fiche existante : publier sans régénération
    if gist_existing and file_path_existing is not None:
        try:
            gist_url = publish_gist(file_path_existing)
            print(f"\n✓ Fiche : file://{file_path_existing.absolute()}")
            print(f"✓ Gist : {gist_url}")
        except (GhNotFoundError, GhNotAuthenticatedError, GhPublishError) as e:
            print(f"\n⚠ {e}", file=sys.stderr)
            print(f"✓ Fiche locale préservée : file://{file_path_existing.absolute()}")
        return

    if language_warning:
        print(f"⚠ {language_warning}")

    if warnings:
        print("⚠ Avertissements de validation :")
        for w in warnings:
            print(f"  - {w}")

    if gist and result_path:
        try:
            gist_url = publish_gist(result_path)
            print(f"\n✓ Fiche créée : file://{result_path.absolute()}")
            print(f"✓ Gist : {gist_url}")
        except (GhNotFoundError, GhNotAuthenticatedError, GhPublishError) as e:
            print(f"\n⚠ {e}", file=sys.stderr)
            print(f"✓ Fiche locale préservée : file://{result_path.absolute()}")
    else:
        print(f"\n✓ Fiche créée : file://{result_path.absolute()}")


def _run_batch(config: dict, batch_path: Path, dry_run: bool, cli_gist: bool = False) -> None:
    """Pipeline batch depuis un fichier d'URLs."""
    from datetime import datetime

    try:
        file_default_model, file_default_gist, entries = parse_batch_file(batch_path)
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable : {batch_path}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("Aucune URL trouvée dans le fichier.")
        sys.exit(0)

    total = len(entries)
    config_model = config["llm"]["model"]
    # Modèle affiché en tête : priorité fichier > config
    display_model = file_default_model or config_model
    # Intention gist globale (header fichier ou CLI)
    global_gist = file_default_gist or cli_gist

    if dry_run:
        any_gist = global_gist or any(e.gist for e in entries)
        if any_gist:
            print("⚠ --gist ignoré en mode dry-run.")
        print(f"[DRY-RUN] {total} URL(s) à traiter — modèle : {display_model}\n")
        for i, entry in enumerate(entries, 1):
            model = resolve_model(entry.model, file_default_model, config_model)
            if entry.model:
                print(f"[{i}/{total}] {entry.url} — modèle : {model}")
            else:
                print(f"[{i}/{total}] {entry.url}")
        return

    successes = 0
    failures = 0
    archived = 0
    gist_count = 0

    now = datetime.now()
    log_name = f"batch-{now.strftime('%Y-%m-%d-%H-%M')}.log"
    log_path = batch_path.parent / log_name

    print(f"[BATCH] {total} URL(s) — modèle : {display_model}\n")

    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"# Batch log — {now.strftime('%Y-%m-%d %H:%M')}\n")
        log.write(f"# model: {display_model}\n")
        if global_gist:
            log.write("# gist: true\n")
        log.write("\n")

        for i, entry in enumerate(entries, 1):
            model = resolve_model(entry.model, file_default_model, config_model)
            resolved_gist = entry.gist or global_gist
            if entry.model:
                print(f"[{i}/{total}] {entry.url} — modèle : {model}")
            else:
                print(f"[{i}/{total}] {entry.url}")

            try:
                video_id = extract_video_id(entry.url)
            except ValueError as e:
                print(f"  ✗ URL invalide : {e}")
                log.write(f"✗ {entry.url} → Erreur : {e}\n")
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
                archived_tag = ""
                if archive_path:
                    archived += 1
                    archived_tag = " [archivée v1]"

                write_note(file_path, note, warnings, overwrite=False)
                print(f"  ✓ {file_path}")

                # Publication gist si demandée
                gist_suffix = ""
                if resolved_gist:
                    try:
                        gist_url = publish_gist(file_path)
                        gist_suffix = f" → {gist_url}"
                        gist_count += 1
                    except (GhNotFoundError, GhNotAuthenticatedError, GhPublishError) as e:
                        gist_suffix = f" → Erreur gist : {e}"

                log.write(f"✓ {entry.url} → {file_path}{archived_tag}{gist_suffix}\n")
                successes += 1

            except Exception as e:
                print(f"  ✗ Erreur : {e}")
                log.write(f"✗ {entry.url} → Erreur : {e}\n")
                failures += 1

        summary = f"# Résumé : {successes} succès, {failures} échec(s), {archived} archivée(s)"
        if global_gist or any(e.gist for e in entries):
            summary += f", {gist_count} gist(s) publiés"
        log.write(f"\n{summary}\n")

    print(f"\nRésumé : {successes} succès, {failures} échec(s), {archived} archivée(s)")
    if global_gist or any(e.gist for e in entries):
        print(f"Gists publiés : {gist_count}")
    print(f"Log : {log_path}")


def main():
    """Dispatch selon les arguments : mode unitaire ou batch."""
    config = load_config()

    raw_args = sys.argv[1:]
    dry_run = "--dry-run" in raw_args
    gist = "--gist" in raw_args
    args = [a for a in raw_args if a not in ("--dry-run", "--gist")]

    if args:
        first_arg = args[0]
        if first_arg.endswith(".txt"):
            _run_batch(config, Path(first_arg), dry_run, cli_gist=gist)
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

    _run_single(config, url, gist=gist)


if __name__ == "__main__":
    main()
