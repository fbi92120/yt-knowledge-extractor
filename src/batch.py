from __future__ import annotations

"""Traitement batch d'URLs YouTube depuis un fichier texte.

Toute la logique métier batch est ici — extract.py se contente
d'orchestrer les appels.

Format du fichier .txt accepté :
    # model: gemini-2.5-flash        ← modèle par défaut (optionnel)
    https://youtu.be/xxxx             ← utilise le modèle par défaut
    https://youtu.be/yyyy model=claude-haiku-4-5  ← surcharge par URL
    # commentaire ordinaire ignoré
                                      ← ligne vide ignorée

Priorité modèle : URL > # model: fichier > config.yml
"""

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BatchEntry:
    """Une entrée du fichier batch : URL + modèle optionnel."""

    url: str
    model: str | None  # None → utiliser le modèle par défaut résolu


def parse_batch_file(path: Path) -> tuple[str | None, list[BatchEntry]]:
    """Parse le fichier batch et retourne (default_model, entries).

    Lignes traitées :
    - Vides ou blanc seul → ignorées
    - Commençant par # → directive si « # model: NOM », sinon ignorée
    - Autres → URL avec surcharge modèle optionnelle (model=NOM)

    Args:
        path: chemin vers le fichier .txt

    Returns:
        (modèle_par_défaut | None, liste de BatchEntry)

    Raises:
        FileNotFoundError: si le fichier n'existe pas
    """
    default_model: str | None = None
    entries: list[BatchEntry] = []

    text = path.read_text(encoding="utf-8")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            m = re.match(r"^#\s*model:\s*(\S+)", line)
            if m:
                default_model = m.group(1)
            continue
        # Ligne URL — surcharge modèle optionnelle : "URL model=NOM"
        m = re.match(r"^(\S+)\s+model=(\S+)", line)
        if m:
            entries.append(BatchEntry(url=m.group(1), model=m.group(2)))
        else:
            url = line.split()[0]
            entries.append(BatchEntry(url=url, model=None))

    return default_model, entries


def resolve_model(
    entry_model: str | None,
    file_default_model: str | None,
    config_model: str,
) -> str:
    """Résout le modèle effectif selon la priorité décroissante.

    Priorité : ligne URL > directive # model: > config.yml
    """
    return entry_model or file_default_model or config_model


def archive_existing(file_path: Path) -> Path | None:
    """Archive une fiche existante dans le sous-dossier v1/.

    Si file_path n'existe pas, retourne None sans effet de bord.
    Sinon, déplace le fichier vers file_path.parent / "v1" / file_path.name
    et retourne le chemin d'archive.

    Args:
        file_path: chemin de la fiche à archiver si elle existe

    Returns:
        Chemin de l'archive créée, ou None si aucune fiche existante.
    """
    if not file_path.exists():
        return None

    archive_dir = file_path.parent / "v1"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / file_path.name
    shutil.move(str(file_path), archive_path)
    return archive_path
