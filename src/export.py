from __future__ import annotations

"""Export d'une fiche vers un dossier local hors iCloud — flag --export (V1.8).

Responsabilités :
- Résoudre le répertoire d'export depuis la config (fallback ~/Documents/yt-exports/).
- Copier la fiche source vers export_directory (écrasement silencieux).
- Ouvrir le Finder sur le répertoire d'export (macOS uniquement).
- Détecter si une fiche existe uniquement dans un sous-dossier v1/ archivé.
"""

import shutil
import subprocess
from pathlib import Path


def resolve_export_directory(config: dict) -> Path:
    """Résout et crée si absent le répertoire d'export depuis la config.

    Fallback : ~/Documents/yt-exports/ si export_directory absent ou None.
    """
    raw = config.get("export_directory") or "~/Documents/yt-exports"
    directory = Path(str(raw)).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def export_fiche(source_path: Path, export_directory: Path) -> Path:
    """Copie source_path dans export_directory. Retourne le chemin destination.

    Écrasement silencieux si un fichier du même nom existe déjà.
    Shutil.copy2 force la matérialisation iCloud avant lecture.
    """
    dest = export_directory / source_path.name
    shutil.copy2(source_path, dest)
    return dest


def open_in_finder(directory: Path) -> None:
    """Ouvre le Finder macOS sur directory.

    Si la commande `open` n'existe pas (non-macOS), affiche un avertissement
    sans lever d'exception.
    """
    try:
        subprocess.run(["open", str(directory)], check=False)
    except FileNotFoundError:
        print(f"Finder non disponible sur ce système. Fiche copiée dans : {directory}")


def check_archived_fiche(config: dict, video_id: str) -> bool:
    """Vérifie si une fiche contenant video_id existe dans un sous-dossier v1/.

    Permet de distinguer "aucune fiche" de "fiche archivée non exportable".
    """
    output_config = config.get("output", {})
    mode = output_config.get("mode", "local")
    if mode == "obsidian":
        base = Path(output_config.get("vault_path", "")).expanduser()
    else:
        base = Path(output_config.get("local_path", "./output"))

    if not base.exists():
        return False

    for md_file in base.rglob("*.md"):
        if "v1" not in md_file.parts:
            continue
        try:
            if video_id in md_file.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeDecodeError):
            continue

    return False
