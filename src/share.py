from __future__ import annotations

"""Publication GitHub Gist depuis une fiche Markdown locale.

Utilise le GitHub CLI (gh) comme outil système — aucune dépendance Python supplémentaire.
Authentification gérée par : gh auth login (scope gist requis).
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

_TRANSCRIPT_MARKER = "---\n<!-- TRANSCRIPT HORODATÉ COMPLET"


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


def _strip_transcript(content: str) -> str:
    """Retourne le contenu tronqué avant le bloc transcript horodaté.

    Si le marqueur n'est pas trouvé, retourne le contenu intact.
    La fiche locale reste inchangée — seul le contenu publié est tronqué.
    """
    idx = content.find(_TRANSCRIPT_MARKER)
    if idx == -1:
        return content
    return content[:idx].rstrip() + "\n"


def publish_gist(file_path: Path) -> str:
    """Publie la fiche (sans transcript) en tant que GitHub Gist secret.

    Le contenu publié est tronqué avant le séparateur
    --- <!-- TRANSCRIPT HORODATÉ COMPLET. La fiche locale reste intacte.

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

    content = file_path.read_text(encoding="utf-8")
    gist_content = _strip_transcript(content)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / file_path.name
        tmp_file.write_text(gist_content, encoding="utf-8")

        result = subprocess.run(
            ["gh", "gist", "create", str(tmp_file)],
            capture_output=True,
            text=True,
        )

    if result.returncode != 0:
        raise GhPublishError(result.stderr.strip() or "Erreur inconnue lors de la publication")

    return result.stdout.strip()
