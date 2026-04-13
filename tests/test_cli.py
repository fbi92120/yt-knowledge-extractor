from __future__ import annotations

"""Tests CLI — comportement de extract.py sans appel API.

Couvre :
- Mode interactif (input() prompt) déclenché quand aucun argument
- Validation URL en mode interactif
- Cas d'entrée vide
- Cas d'erreur de parsing URL
- Confirmation fichier existant (overwrite) : acceptation et refus
- Orchestration de la confirmation dans extract.main() (mocks pipeline)
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.writer import write_note


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


def test_write_note_existing_file_raises(tmp_path):
    """write_note lève FileExistsError si le fichier existe et overwrite=False."""
    f = tmp_path / "note.md"
    f.write_text("ancien contenu", encoding="utf-8")
    with pytest.raises(FileExistsError, match=str(f)):
        write_note(f, "nouveau contenu", [])


def test_write_note_existing_file_overwrite(tmp_path):
    """write_note écrase le fichier si overwrite=True."""
    f = tmp_path / "note.md"
    f.write_text("ancien contenu", encoding="utf-8")
    write_note(f, "nouveau contenu", [], overwrite=True)
    assert f.read_text(encoding="utf-8") == "nouveau contenu"


def test_write_note_new_file(tmp_path):
    """write_note crée le fichier sans confirmation si inexistant."""
    f = tmp_path / "note.md"
    write_note(f, "contenu", [])
    assert f.read_text(encoding="utf-8") == "contenu"


# ---------------------------------------------------------------------------
# Tests d'orchestration — extract.main() avec pipeline mocké
# ---------------------------------------------------------------------------

_DUMMY_METADATA = {
    "channel": "TestChannel",
    "upload_date": "2024-01-01",
    "title": "Test Video",
    "description": "",
    "duration": "10:00",
    "chapters": None,
}

_DUMMY_CONFIG = {
    "llm": {"provider": "test", "model": "test"},
    "transcript_language": "fr",
    "output_language": "fr",
}


def _make_spinner_mock():
    sp = MagicMock()
    sp.__enter__ = MagicMock(return_value=sp)
    sp.__exit__ = MagicMock(return_value=False)
    return sp


def test_overwrite_confirmation_refused(tmp_path):
    """extract.main() sort proprement (code 0) si l'utilisateur refuse l'écrasement."""
    import extract

    existing = tmp_path / "testchannel" / "2024-01-01-test-video.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("ancien contenu", encoding="utf-8")

    with (
        patch.object(sys, "argv", ["extract.py", "https://youtu.be/T_GqhyYqTD4"]),
        patch("extract.load_config", return_value=_DUMMY_CONFIG),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouveau contenu"),
        patch("extract.validate_note", return_value=(None, [])),
        patch("extract.build_file_path", return_value=existing),
        patch("extract.yaspin", return_value=_make_spinner_mock()),
        patch("builtins.input", return_value="N"),
    ):
        with pytest.raises(SystemExit) as exc:
            extract.main()
        assert exc.value.code == 0

    assert existing.read_text(encoding="utf-8") == "ancien contenu"


def test_overwrite_confirmation_accepted(tmp_path):
    """extract.main() écrase le fichier si l'utilisateur confirme avec 'o'."""
    import extract

    existing = tmp_path / "testchannel" / "2024-01-01-test-video.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("ancien contenu", encoding="utf-8")

    with (
        patch.object(sys, "argv", ["extract.py", "https://youtu.be/T_GqhyYqTD4"]),
        patch("extract.load_config", return_value=_DUMMY_CONFIG),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouveau contenu"),
        patch("extract.validate_note", return_value=(None, [])),
        patch("extract.build_file_path", return_value=existing),
        patch("extract.yaspin", return_value=_make_spinner_mock()),
        patch("builtins.input", return_value="o"),
        patch("builtins.print"),
    ):
        extract.main()

    assert existing.read_text(encoding="utf-8") == "nouveau contenu"
