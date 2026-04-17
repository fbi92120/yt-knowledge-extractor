from __future__ import annotations

"""Publication GitHub Gist depuis une fiche Markdown locale.

Utilise le GitHub CLI (gh) comme outil système — aucune dépendance Python supplémentaire.
Authentification gérée par : gh auth login (scope gist requis).
"""

import shutil
import subprocess
from pathlib import Path


class GhNotFoundError(Exception):
    """gh (GitHub CLI) n'est pas installé."""


class GhNotAuthenticatedError(Exception):
    """gh est installé mais pas authentifié (gh auth login requis)."""


class GhPublishError(Exception):
    """La création du gist a échoué."""


def _check_gh_available() -> None:
    """Vérifie que gh est installé. Lève GhNotFoundError sinon."""
    if not shutil.which("gh"):
        raise GhNotFoundError(
            "gh non installé — publication impossible. Installer : https://cli.github.com"
        )


def _check_gh_authenticated() -> None:
    """Vérifie que gh est authentifié. Lève GhNotAuthenticatedError sinon."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GhNotAuthenticatedError("gh non authentifié — lancez : gh auth login")


def publish_gist(file_path: Path) -> str:
    """Publie file_path en tant que GitHub Gist secret.

    Args:
        file_path: chemin vers le fichier Markdown à publier.

    Returns:
        URL du gist créé (ex. https://gist.github.com/user/abc123).

    Raises:
        GhNotFoundError: si gh n'est pas installé.
        GhNotAuthenticatedError: si gh n'est pas authentifié.
        GhPublishError: si la création du gist échoue.
    """
    _check_gh_available()
    _check_gh_authenticated()

    result = subprocess.run(
        ["gh", "gist", "create", "--secret", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GhPublishError(result.stderr.strip() or "Erreur inconnue lors de la publication")

    return result.stdout.strip()
