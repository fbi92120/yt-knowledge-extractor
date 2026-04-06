from __future__ import annotations

"""Écriture de la fiche Markdown dans le vault ou dossier local.

Génère le slug ASCII depuis le titre, construit le chemin
de destination, gère les conflits de fichiers existants,
et écrit le fichier final avec avertissements éventuels.
"""

from pathlib import Path

from slugify import slugify

from src.validator import build_warning_header


def generate_slug(title: str) -> str:
    """Génère un slug ASCII depuis le titre YouTube via python-slugify.

    Exemple : "J'ai testé DeepSeek pendant 5 jours" → "jai-teste-deepseek-pendant-5-jours"
    """
    return slugify(title, max_length=80)


def build_file_path(config: dict, channel: str, upload_date: str, title: str) -> Path:
    """Construit le chemin complet du fichier de sortie.

    Format : [vault_path]/[chaîne-slug]/[YYYY-MM-DD]-[slug].md
    Crée le sous-dossier chaîne si nécessaire.

    Returns:
        Path complet du fichier Markdown
    """
    output_config = config["output"]
    mode = output_config.get("mode", "local")

    if mode == "obsidian":
        base_path = Path(output_config["vault_path"]).expanduser()
    else:
        base_path = Path(output_config.get("local_path", "./output"))

    channel_slug = slugify(channel, max_length=60)
    title_slug = generate_slug(title)
    filename = f"{upload_date}-{title_slug}.md"

    dir_path = base_path / channel_slug
    dir_path.mkdir(parents=True, exist_ok=True)

    return dir_path / filename


def write_note(file_path: Path, content: str, warnings: list[str]) -> Path:
    """Écrit la fiche Markdown sur disque.

    - Demande confirmation si le fichier existe déjà
    - Préfixe les avertissements du validateur en tête de fiche
    - Écriture UTF-8

    Returns:
        Path du fichier écrit

    Raises:
        SystemExit: si l'utilisateur refuse l'écrasement
    """
    if file_path.exists():
        answer = input(f"Ce fichier existe déjà : {file_path}\nÉcraser ? (o/N) ")
        if answer.strip().lower() not in ("o", "oui", "y", "yes"):
            raise SystemExit("Écriture annulée par l'utilisateur.")

    header = build_warning_header(warnings)
    full_content = header + content if header else content

    file_path.write_text(full_content, encoding="utf-8")
    return file_path
