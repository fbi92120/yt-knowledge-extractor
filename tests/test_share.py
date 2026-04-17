from __future__ import annotations

"""Tests unitaires — src/share.py + comportements --gist dans extract.py (GI-01 à GI-10).

Tous les tests utilisent des mocks réseau. Aucun appel réel à GitHub.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.share import (
    GhNotAuthenticatedError,
    GhNotFoundError,
    GhPublishError,
    publish_gist,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DUMMY_CONFIG = {
    "llm": {"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "test"},
    "transcript_language": "fr",
    "output_language": "fr",
    "output": {"mode": "local", "local_path": "./output"},
}

_DUMMY_METADATA = {
    "channel": "TestChannel",
    "upload_date": "2024-01-01",
    "title": "Test Video",
    "description": "",
    "duration": "10:00",
    "chapters": None,
}


def _make_spinner():
    """Crée un mock yaspin utilisable comme context manager."""
    sp = MagicMock()
    sp.__enter__ = MagicMock(return_value=sp)
    sp.__exit__ = MagicMock(return_value=False)
    return sp


def _make_gh_run(*side_effects):
    """Construit un mock subprocess.run avec les retours spécifiés."""
    return [MagicMock(returncode=r, stdout=o, stderr=e) for r, o, e in side_effects]


# ---------------------------------------------------------------------------
# GI-04 / GI-05 / GI-06 — publish_gist() directement
# ---------------------------------------------------------------------------

def test_gi04_gh_not_installed_raises(tmp_path):
    """GI-04 : gh absent → GhNotFoundError."""
    f = tmp_path / "note.md"
    f.write_text("contenu", encoding="utf-8")

    with patch("src.share.shutil.which", return_value=None):
        with pytest.raises(GhNotFoundError, match="gh non installé"):
            publish_gist(f)


def test_gi05_gh_not_authenticated_raises(tmp_path):
    """GI-05 : gh non authentifié → GhNotAuthenticatedError."""
    f = tmp_path / "note.md"
    f.write_text("contenu", encoding="utf-8")

    with (
        patch("src.share.shutil.which", return_value="/usr/bin/gh"),
        patch("src.share.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not logged in")
        with pytest.raises(GhNotAuthenticatedError, match="gh non authentifié"):
            publish_gist(f)


def test_gi06_gh_create_fails_raises(tmp_path):
    """GI-06 : gh gist create échoue → GhPublishError."""
    f = tmp_path / "note.md"
    f.write_text("contenu", encoding="utf-8")

    with (
        patch("src.share.shutil.which", return_value="/usr/bin/gh"),
        patch("src.share.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),       # auth status OK
            MagicMock(returncode=1, stdout="", stderr="erreur réseau"),  # gist create KO
        ]
        with pytest.raises(GhPublishError, match="erreur réseau"):
            publish_gist(f)


def test_publish_gist_returns_url(tmp_path):
    """publish_gist() retourne l'URL sur succès."""
    f = tmp_path / "note.md"
    f.write_text("contenu", encoding="utf-8")

    with (
        patch("src.share.shutil.which", return_value="/usr/bin/gh"),
        patch("src.share.subprocess.run") as mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="https://gist.github.com/user/abc123\n", stderr=""),
        ]
        url = publish_gist(f)

    assert url == "https://gist.github.com/user/abc123"


# ---------------------------------------------------------------------------
# GI-01 — _run_single + fiche existante → publication sans régénération
# ---------------------------------------------------------------------------

def test_gi01_gist_existing_file_no_regeneration(tmp_path, capsys):
    """GI-01 : --gist + fiche existante → publish_gist appelé, generate_note NON appelé."""
    import extract

    existing = tmp_path / "note.md"
    existing.write_text("contenu existant", encoding="utf-8")

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=existing),
        patch("extract.generate_note") as mock_gen,
        patch("extract.publish_gist", return_value="https://gist.github.com/user/abc") as mock_pub,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", gist=True)

    mock_gen.assert_not_called()
    mock_pub.assert_called_once_with(existing)
    captured = capsys.readouterr()
    assert "https://gist.github.com/user/abc" in captured.out


def test_gi01_gist_existing_file_local_preserved_on_error(tmp_path, capsys):
    """GI-01 variante : erreur gist → fiche locale intacte, pas de crash."""
    import extract

    existing = tmp_path / "note.md"
    existing.write_text("contenu existant", encoding="utf-8")

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=existing),
        patch("extract.generate_note"),
        patch("extract.publish_gist", side_effect=GhNotFoundError("gh non installé")),
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", gist=True)

    assert existing.exists()
    assert existing.read_text(encoding="utf-8") == "contenu existant"
    captured = capsys.readouterr()
    assert "gh non installé" in captured.err


# ---------------------------------------------------------------------------
# GI-02 — _run_single + fiche inexistante → génération puis publication
# ---------------------------------------------------------------------------

def test_gi02_gist_new_file_generate_then_publish(tmp_path, capsys):
    """GI-02 : --gist + fiche inexistante → generate_note appelé puis publish_gist."""
    import extract

    note_path = tmp_path / "note.md"
    # Le fichier n'existe pas encore

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=note_path),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/xyz") as mock_pub,
    ):
        extract._run_single(_DUMMY_CONFIG, "https://youtu.be/ABC123", gist=True)

    mock_gen.assert_called_once()
    mock_pub.assert_called_once_with(note_path)
    captured = capsys.readouterr()
    assert "https://gist.github.com/user/xyz" in captured.out


# ---------------------------------------------------------------------------
# GI-03 — --gist + --dry-run → pas de publication, avertissement
# ---------------------------------------------------------------------------

def test_gi03_gist_dry_run_no_publish(tmp_path, capsys):
    """GI-03 : --gist + --dry-run → publish_gist non appelé, avertissement affiché."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("# gist\nhttps://youtu.be/AAA\n", encoding="utf-8")

    with patch("extract.publish_gist") as mock_pub:
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=True, cli_gist=True)
        mock_pub.assert_not_called()

    captured = capsys.readouterr()
    assert "--gist ignoré en mode dry-run" in captured.out


# ---------------------------------------------------------------------------
# GI-07 — batch + # gist en entête → toutes les URLs publiées
# ---------------------------------------------------------------------------

def test_gi07_batch_header_gist_all_urls_published(tmp_path, capsys):
    """GI-07 : # gist en entête → publish_gist appelé pour chaque URL réussie."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "# gist\nhttps://youtu.be/AAA\nhttps://youtu.be/BBB\n",
        encoding="utf-8",
    )
    note_a = tmp_path / "note_a.md"
    note_b = tmp_path / "note_b.md"

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", side_effect=[note_a, note_b]),
        patch("extract.write_note", side_effect=[note_a, note_b]),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/x") as mock_pub,
        patch("extract.extract_video_id", return_value="ID"),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    assert mock_pub.call_count == 2

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "# gist: true" in content
    assert "gist(s) publiés" in content


# ---------------------------------------------------------------------------
# GI-08 — batch + gist sur une ligne → uniquement cette ligne publiée
# ---------------------------------------------------------------------------

def test_gi08_batch_per_line_gist_only_that_line(tmp_path, capsys):
    """GI-08 : gist sur une ligne → publish_gist appelé une seule fois."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "https://youtu.be/AAA\nhttps://youtu.be/BBB gist\n",
        encoding="utf-8",
    )
    note_a = tmp_path / "note_a.md"
    note_b = tmp_path / "note_b.md"

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", side_effect=[note_a, note_b]),
        patch("extract.write_note", side_effect=[note_a, note_b]),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/y") as mock_pub,
        patch("extract.extract_video_id", return_value="ID"),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    # Uniquement BBB (gist=True) → 1 seul appel
    assert mock_pub.call_count == 1
    mock_pub.assert_called_once_with(note_b)


# ---------------------------------------------------------------------------
# GI-09 — batch + génération échouée → pas de gist, pas de blocage
# ---------------------------------------------------------------------------

def test_gi09_batch_generation_fails_no_gist_no_crash(tmp_path, capsys):
    """GI-09 : génération échouée → gist non tenté, URL suivante traitée normalement."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "# gist\nhttps://youtu.be/FAIL\nhttps://youtu.be/OK\n",
        encoding="utf-8",
    )
    note_ok = tmp_path / "note_ok.md"

    call_count = {"n": 0}

    def fetch_meta_side(*_a, **_kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Erreur réseau simulée")
        return _DUMMY_METADATA

    with (
        patch("extract.fetch_metadata", side_effect=fetch_meta_side),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", return_value=note_ok),
        patch("extract.write_note", return_value=note_ok),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/ok") as mock_pub,
        patch("extract.extract_video_id", return_value="ID"),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    # Seule la 2e URL (OK) a publié un gist
    assert mock_pub.call_count == 1
    captured = capsys.readouterr()
    assert "1 échec" in captured.out

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "✗ https://youtu.be/FAIL → Erreur" in content
    assert "✓ https://youtu.be/OK →" in content


# ---------------------------------------------------------------------------
# GI-10 — batch + gist échoue → erreur loggée, URL suivante non bloquée
# ---------------------------------------------------------------------------

def test_gi10_batch_gist_fails_error_logged_no_crash(tmp_path, capsys):
    """GI-10 : gist échoue → erreur dans le log, URL suivante traitée normalement."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "# gist\nhttps://youtu.be/AAA\nhttps://youtu.be/BBB\n",
        encoding="utf-8",
    )
    note_a = tmp_path / "note_a.md"
    note_b = tmp_path / "note_b.md"

    gist_call = {"n": 0}

    def publish_side(path):
        gist_call["n"] += 1
        if gist_call["n"] == 1:
            raise GhPublishError("timeout réseau")
        return "https://gist.github.com/user/bbb"

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", side_effect=[note_a, note_b]),
        patch("extract.write_note", side_effect=[note_a, note_b]),
        patch("extract.publish_gist", side_effect=publish_side),
        patch("extract.extract_video_id", return_value="ID"),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    captured = capsys.readouterr()
    assert "2 succès" in captured.out

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "Erreur gist : timeout réseau" in content
    assert "https://gist.github.com/user/bbb" in content
    assert "# Résumé" in content
