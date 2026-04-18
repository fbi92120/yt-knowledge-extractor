from __future__ import annotations

"""Point d'entrée CLI — YT Knowledge Extractor.

Usage :
    python extract.py [URL]                                             ← mode unitaire
    python extract.py [URL] [--gist] [--model NOM]                      ← mode unitaire + options
    python extract.py fichier.txt [--dry-run] [--gist] [--model NOM]    ← mode batch
    python extract.py --dry-run fichier.txt                             ← ordre alternatif

Orchestre le pipeline complet sans logique métier — tout est dans src/.
"""

import os
import re
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


def _find_existing_fiche(config: dict, video_id: str) -> Path | None:
    """Recherche une fiche existante dans le vault contenant video_id (hors v1/).

    Recherche locale uniquement — aucun appel réseau.
    Retourne le premier chemin trouvé, ou None.
    """
    output_config = config.get("output", {})
    mode = output_config.get("mode", "local")
    if mode == "obsidian":
        base = Path(output_config.get("vault_path", "")).expanduser()
    else:
        base = Path(output_config.get("local_path", "./output"))

    if not base.exists():
        return None

    for md_file in base.rglob("*.md"):
        if "v1" in md_file.parts:
            continue
        try:
            if video_id in md_file.read_text(encoding="utf-8"):
                return md_file
        except (OSError, UnicodeDecodeError):
            continue

    return None


def _extract_model_from_fiche(path: Path) -> str | None:
    """Extrait le nom du modèle depuis le header d'une fiche existante.

    Cherche **Model** : NOM dans les 20 premières lignes.
    Retourne None si absent (fiche sans header modèle ou format inconnu).
    """
    try:
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                m = re.search(r'\*\*Model\*\*\s*:\s*(\S+)', line)
                if m:
                    return m.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    return None


def _run_single(
    config: dict,
    url: str,
    gist: bool = False,
    model_override: str | None = None,
) -> None:
    """Pipeline complet pour une URL unique."""
    # Appliquer la surcharge modèle
    if model_override:
        config = {**config, "llm": {**config["llm"], "model": model_override}}

    current_model = config["llm"]["model"]

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    # --gist + fiche existante : publication directe ou dialog modèle différent
    skip_existence_check = False
    preempt_overwrite = False

    if gist:
        existing = _find_existing_fiche(config, video_id)
        if existing:
            existing_model = _extract_model_from_fiche(existing)
            needs_regen = bool(model_override and existing_model != current_model)

            if not needs_regen:
                # Même modèle ou pas de surcharge → publication directe sans régénération
                try:
                    gist_url = publish_gist(existing)
                    print(f"✓ Fiche existante : {existing}")
                    print(f"✓ Gist : {gist_url}")
                except (GhNotFoundError, GhNotAuthenticatedError, GhPublishError) as e:
                    print(f"⚠ {e}", file=sys.stderr)
                    print(f"✓ Fiche locale préservée : {existing}")
                return

            # Modèle différent → dialog avec options + gist
            if existing_model is not None:
                prompt = (
                    f"Ce fichier existe déjà : {existing} (généré avec {existing_model})\n"
                    f"Modèle différent : {current_model}\n"
                    f"(a) Archiver en v1/ et régénérer + gist   (r) Remplacer + gist   (N) Annuler\n> "
                )
            else:
                prompt = (
                    f"Ce fichier existe déjà : {existing} (modèle inconnu)\n"
                    f"Modèle actuel : {current_model}\n"
                    f"(a) Archiver en v1/ et régénérer + gist   (r) Remplacer + gist   (N) Annuler\n> "
                )
            try:
                answer = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nAnnulé.", file=sys.stderr)
                sys.exit(1)

            if answer not in ("a", "r"):
                print("Annulé.")
                sys.exit(0)

            if answer == "a":
                archive_existing(existing)
            else:
                preempt_overwrite = True
            skip_existence_check = True

    # Pipeline normal (génération)
    language_warning: str | None = None
    warnings: list[str] = []
    result_path = None

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

            # Vérification existence fichier AVANT appel LLM
            overwrite = preempt_overwrite

            if not skip_existence_check and file_path.exists():
                sp.stop()
                existing_model = _extract_model_from_fiche(file_path)
                try:
                    if existing_model == current_model:
                        answer = input(
                            f"Ce fichier existe déjà : {file_path} (généré avec {current_model})\n"
                            f"Écraser ? (o/N) "
                        )
                        if answer.strip().lower() not in ("o", "oui", "y", "yes"):
                            print("Écriture annulée par l'utilisateur.")
                            sys.exit(0)
                        overwrite = True
                    elif existing_model is not None:
                        answer = input(
                            f"Ce fichier existe déjà : {file_path} (généré avec {existing_model})\n"
                            f"Modèle différent : {current_model}\n"
                            f"(a) Archiver en v1/ et régénérer   (r) Remplacer   (N) Annuler\n> "
                        )
                        a = answer.strip().lower()
                        if a not in ("a", "r"):
                            print("Annulé.")
                            sys.exit(0)
                        if a == "a":
                            archive_existing(file_path)
                            # Fichier déplacé, overwrite reste False
                        else:
                            overwrite = True
                    else:
                        answer = input(
                            f"Ce fichier existe déjà : {file_path} (modèle inconnu)\n"
                            f"Modèle actuel : {current_model}\n"
                            f"(a) Archiver en v1/ et régénérer   (r) Remplacer   (N) Annuler\n> "
                        )
                        a = answer.strip().lower()
                        if a not in ("a", "r"):
                            print("Annulé.")
                            sys.exit(0)
                        if a == "a":
                            archive_existing(file_path)
                        else:
                            overwrite = True
                except (EOFError, KeyboardInterrupt):
                    print("\nAnnulé.", file=sys.stderr)
                    sys.exit(1)
                sp.start()

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


def _run_batch(
    config: dict,
    batch_path: Path,
    dry_run: bool,
    cli_gist: bool = False,
    cli_model: str | None = None,
) -> None:
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
    # Modèle affiché en tête : priorité cli > fichier > config
    display_model = cli_model or file_default_model or config_model
    # Intention gist globale (header fichier ou CLI)
    global_gist = file_default_gist or cli_gist

    if dry_run:
        any_gist = global_gist or any(e.gist for e in entries)
        if any_gist:
            print("⚠ --gist ignoré en mode dry-run.")
        print(f"[DRY-RUN] {total} URL(s) à traiter — modèle : {display_model}\n")
        for i, entry in enumerate(entries, 1):
            effective_entry_model = cli_model or entry.model
            model = resolve_model(effective_entry_model, file_default_model, config_model)
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
            effective_entry_model = cli_model or entry.model
            model = resolve_model(effective_entry_model, file_default_model, config_model)
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

                written_path = write_note(file_path, note, warnings, overwrite=False)
                print(f"  ✓ {written_path}")

                # Publication gist si demandée
                gist_suffix = ""
                if resolved_gist:
                    try:
                        gist_url = publish_gist(written_path)
                        gist_suffix = f" → {gist_url}"
                        gist_count += 1
                    except (GhNotFoundError, GhNotAuthenticatedError, GhPublishError) as e:
                        gist_suffix = f" → Erreur gist : {e}"

                log.write(f"✓ {entry.url} → {written_path}{archived_tag}{gist_suffix}\n")
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

    # Parsing --model NOM (index-based, consume deux tokens)
    model_override: str | None = None
    args: list[str] = []
    i = 0
    while i < len(raw_args):
        if raw_args[i] == "--model":
            if i + 1 < len(raw_args):
                model_override = raw_args[i + 1]
                i += 2
            else:
                print("Erreur : --model nécessite un argument.", file=sys.stderr)
                sys.exit(1)
        elif raw_args[i] not in ("--dry-run", "--gist"):
            args.append(raw_args[i])
            i += 1
        else:
            i += 1

    if args:
        first_arg = args[0]
        if first_arg.endswith(".txt"):
            _run_batch(config, Path(first_arg), dry_run, cli_gist=gist, cli_model=model_override)
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

    _run_single(config, url, gist=gist, model_override=model_override)


if __name__ == "__main__":
    main()
