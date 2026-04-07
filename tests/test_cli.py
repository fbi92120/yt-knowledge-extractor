from __future__ import annotations

"""Tests CLI — comportement de extract.py sans appel API.

Couvre :
- Mode interactif (input() prompt) déclenché quand aucun argument
- Validation URL en mode interactif
- Cas d'entrée vide
- Cas d'erreur de parsing URL
"""

import subprocess
import sys
from pathlib import Path

import pytest


PROJECT = Path(__file__).resolve().parent.parent
CONFIG_YML = PROJECT / "config.yml"
PYTHON = sys.executable  # use the same interpreter pytest is running on


def _require_config():
    if not CONFIG_YML.exists():
        pytest.skip("config.yml absent — test CLI sauté")


def _run_extract(stdin_input: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "extract.py"],
        input=stdin_input,
        capture_output=True,
        text=True,
        cwd=str(PROJECT),
    )


def test_interactive_prompt_empty_input():
    """Mode interactif + entrée vide → exit 1 + 'Aucune URL fournie'."""
    _require_config()
    result = _run_extract("\n")
    assert result.returncode == 1
    assert "Aucune URL fournie" in (result.stdout + result.stderr)


def test_interactive_prompt_invalid_url():
    """Mode interactif + URL bidon → exit 1 + erreur URL non reconnue."""
    _require_config()
    result = _run_extract("not-a-url\n")
    assert result.returncode == 1
    assert "URL YouTube non reconnue" in (result.stdout + result.stderr)


def test_interactive_prompt_eof():
    """Mode interactif + EOF immédiat → exit 1 + message d'annulation."""
    _require_config()
    # Aucune entrée du tout (stdin fermé) → input() lève EOFError
    result = subprocess.run(
        [PYTHON, "extract.py"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=str(PROJECT),
    )
    assert result.returncode == 1
    assert "Annulé" in (result.stdout + result.stderr)


def test_argument_mode_invalid_url():
    """Mode argument + URL bidon → exit 1 + erreur URL non reconnue (chemin existant)."""
    _require_config()
    result = subprocess.run(
        ["python3", "extract.py", "not-a-url"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT),
    )
    assert result.returncode == 1
    assert "URL YouTube non reconnue" in (result.stdout + result.stderr)
