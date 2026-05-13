from __future__ import annotations

"""Tests unitaires — flag --export dans extract.py et src/export.py (EX-01 à EX-08).

Tous les tests mockent subprocess.run(["open", ...]) et les appels LLM.
Aucun appel système réel, aucun appel réseau.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.export import export_fiche, resolve_export_directory
from src.share import GhNotFoundError, GhNotAuthenticatedError, GhPublishError


# ---------------------------------------------------------------------------
# Helpers et fixtures
# ---------------------------------------------------------------------------

_DUMMY_CONFIG = {
    "llm": {"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "test"},
    "transcript_language": "fr",
    "output_language": "fr",
    "output": {"mode": "local", "local_path": "./output"},
    "export_directory": "~/Documents/yt-exports",
}

_DUMMY_METADATA = {
    "channel": "TestChannel",
    "upload_date": "2024-01-01",
    "title": "Test Video",
    "description": "",
    "duration": "10:00",
    "chapters": None,
}

_FICHE_WITH_MODEL = (
    "# Test Video\n"
    "**URL** : https://youtu.be/ABC123 · **Channel** : TestChannel"
    " · **Processed** : 2024-01-01 · **Duration** : 10:00 · **Model** : gemini-2.0-flash\n"
    "\n"
    "## Thèse centrale\nContenu de test.\n"
)

_FICHE_NO_MODEL = (
    "# Test Video\n"
    "**URL** : https://youtu.be/ABC123 · **Channel** : TestChannel\n"
    "\n"
    "## Thèse centrale\nContenu sans header modèle.\n"
)


def _make_spinner():
    sp = MagicMock()
    sp.__enter__ = MagicMock(return_value=sp)
    sp.__exit__ = MagicMock(return_value=False)
    return sp


# ---------------------------------------------------------------------------
# EX-01 — --export + fiche existante → copie + Finder + source intacte
# ---------------------------------------------------------------------------

def test_ex01_export_existing_fiche(tmp_path, capsys):
    """EX-01 : --export + fiche existante → copie + Finder + source intacte."""
    import extract

    source = tmp_path / "2024-01-01-test-video.md"
    source.write_text(_FICHE_WITH_MODEL, encoding="utf-8")
    export_dir = tmp_path / "exports"
    dest = export_dir / "2024-01-01-test-video.md"

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=source),
        patch("extract.resolve_export_directory", return_value=export_dir),
        patch("extract.export_fiche", return_value=dest) as mock_export,
        patch("extract.open_in_finder") as mock_open,
        patch("extract.generate_note") as mock_gen,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", export=True)

    mock_gen.assert_not_called()
    mock_export.assert_called_once_with(source, export_dir)
    mock_open.assert_called_once_with(export_dir)
    # Source vault intacte
    assert source.read_text(encoding="utf-8") == _FICHE_WITH_MODEL
    captured = capsys.readouterr()
    assert str(source) in captured.out
    assert str(dest) in captured.out


# ---------------------------------------------------------------------------
# EX-02 — --export + fiche inexistante + acceptation → pipeline + copie + Finder
# ---------------------------------------------------------------------------

def test_ex02_export_missing_fiche_accept_generation(tmp_path, capsys):
    """EX-02 : --export + inexistante + 'o' → pipeline déclenché puis copie + Finder."""
    import extract

    note_path = tmp_path / "2024-01-01-test-video.md"
    export_dir = tmp_path / "exports"
    dest = export_dir / "2024-01-01-test-video.md"

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=None),
        patch("extract.check_archived_fiche", return_value=False),
        patch("builtins.input", return_value="o"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=note_path),
        patch("extract.resolve_export_directory", return_value=export_dir),
        patch("extract.export_fiche", return_value=dest) as mock_export,
        patch("extract.open_in_finder") as mock_open,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", export=True)

    mock_gen.assert_called_once()
    mock_export.assert_called_once_with(note_path, export_dir)
    mock_open.assert_called_once_with(export_dir)


# ---------------------------------------------------------------------------
# EX-03 — --export + fiche inexistante + refus → aucun LLM, aucune copie
# ---------------------------------------------------------------------------

def test_ex03_export_missing_fiche_refuse_generation(tmp_path):
    """EX-03 : --export + inexistante + 'N' → exit 0, aucun LLM, aucune copie."""
    import extract

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=None),
        patch("extract.check_archived_fiche", return_value=False),
        patch("builtins.input", return_value="N"),
        patch("extract.generate_note") as mock_gen,
        patch("extract.export_fiche") as mock_export,
        patch("extract.open_in_finder") as mock_open,
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", export=True)

    assert exc_info.value.code == 0
    mock_gen.assert_not_called()
    mock_export.assert_not_called()
    mock_open.assert_not_called()


# ---------------------------------------------------------------------------
# EX-04 — --export + fichier déjà présent dans export_directory → écrasement silencieux
# ---------------------------------------------------------------------------

def test_ex04_export_silent_overwrite(tmp_path):
    """EX-04 : fichier déjà présent dans export_directory → écrasé silencieusement."""
    source = tmp_path / "2024-01-01-test-video.md"
    source.write_text("nouveau contenu", encoding="utf-8")

    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    existing_in_export = export_dir / "2024-01-01-test-video.md"
    existing_in_export.write_text("ancien contenu", encoding="utf-8")

    dest = export_fiche(source, export_dir)

    assert dest == existing_in_export
    assert dest.read_text(encoding="utf-8") == "nouveau contenu"


# ---------------------------------------------------------------------------
# EX-05 — --export + export_directory non configuré → création automatique
# ---------------------------------------------------------------------------

def test_ex05_no_export_directory_configured(tmp_path, monkeypatch):
    """EX-05 : export_directory absent → ~/Documents/yt-exports/ créé automatiquement."""
    monkeypatch.setenv("HOME", str(tmp_path))

    config: dict = {}  # Pas de export_directory

    result = resolve_export_directory(config)

    expected = tmp_path / "Documents" / "yt-exports"
    assert result == expected
    assert expected.exists()


# ---------------------------------------------------------------------------
# EX-06 — --export + --gist + fiche existante → copie + gist, deux confirmations
# ---------------------------------------------------------------------------

def test_ex06_export_and_gist_existing_fiche(tmp_path, capsys):
    """EX-06 : --export + --gist + fiche existante → copie + gist, confirmations distinctes."""
    import extract

    source = tmp_path / "2024-01-01-test-video.md"
    source.write_text(_FICHE_WITH_MODEL, encoding="utf-8")
    export_dir = tmp_path / "exports"
    dest = export_dir / "2024-01-01-test-video.md"

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=source),
        patch("extract.resolve_export_directory", return_value=export_dir),
        patch("extract.export_fiche", return_value=dest),
        patch("extract.open_in_finder"),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/xyz") as mock_gist,
        patch("extract.generate_note") as mock_gen,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", export=True, gist=True)

    mock_gen.assert_not_called()
    # Gist publié depuis la source vault (pas la copie exportée)
    mock_gist.assert_called_once_with(source)
    captured = capsys.readouterr()
    assert str(source) in captured.out
    assert str(dest) in captured.out
    assert "https://gist.github.com/user/xyz" in captured.out


# ---------------------------------------------------------------------------
# EX-07 — --export + fiche présente uniquement dans v1/ → erreur terminal explicite
# ---------------------------------------------------------------------------

def test_ex07_fiche_only_in_v1(tmp_path, capsys):
    """EX-07 : fiche uniquement dans v1/ → erreur terminal explicite, aucune copie."""
    import extract

    # Créer une fiche uniquement dans v1/ — _find_existing_fiche la rejette
    v1_dir = tmp_path / "channel" / "v1"
    v1_dir.mkdir(parents=True)
    (v1_dir / "2024-01-01-archived.md").write_text(
        "# Archived\n**URL** : https://youtu.be/ABC123\n",
        encoding="utf-8",
    )

    config = {
        **_DUMMY_CONFIG,
        "output": {"mode": "local", "local_path": str(tmp_path)},
    }

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.export_fiche") as mock_export,
        patch("extract.open_in_finder") as mock_open,
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(config, "https://youtu.be/ABC123", export=True)

    assert exc_info.value.code == 1
    mock_export.assert_not_called()
    mock_open.assert_not_called()
    captured = capsys.readouterr()
    assert "Aucune fiche courante" in captured.err
    assert "v1/" in captured.err


# ---------------------------------------------------------------------------
# EX-08 — --export + fiche sans header **Model** → copie réussie
# ---------------------------------------------------------------------------

def test_ex08_export_fiche_without_model_header(tmp_path, capsys):
    """EX-08 : fiche sans **Model** dans le header → copie réussie, aucun cas particulier."""
    import extract

    source = tmp_path / "2024-01-01-test-video.md"
    source.write_text(_FICHE_NO_MODEL, encoding="utf-8")
    export_dir = tmp_path / "exports"
    dest = export_dir / "2024-01-01-test-video.md"

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=source),
        patch("extract.resolve_export_directory", return_value=export_dir),
        patch("extract.export_fiche", return_value=dest) as mock_export,
        patch("extract.open_in_finder") as mock_open,
        patch("extract.generate_note") as mock_gen,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", export=True)

    mock_gen.assert_not_called()
    mock_export.assert_called_once_with(source, export_dir)
    mock_open.assert_called_once_with(export_dir)
    captured = capsys.readouterr()
    assert str(dest) in captured.out
