from __future__ import annotations

"""Tests unitaires — src/batch.py + intégration batch dans extract.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.batch import parse_batch_file, resolve_model, archive_existing, BatchEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "urls.txt"
    f.write_text(content, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# parse_batch_file — fichier vide / blancs / commentaires
# ---------------------------------------------------------------------------

def test_parse_empty_file(tmp_path):
    f = _write(tmp_path, "")
    default_model, entries = parse_batch_file(f)
    assert default_model is None
    assert entries == []


def test_parse_blank_lines_only(tmp_path):
    f = _write(tmp_path, "\n\n   \n")
    _, entries = parse_batch_file(f)
    assert entries == []


def test_parse_comments_only(tmp_path):
    f = _write(tmp_path, "# commentaire\n# autre commentaire\n")
    default_model, entries = parse_batch_file(f)
    assert default_model is None
    assert entries == []


def test_parse_model_directive(tmp_path):
    f = _write(tmp_path, "# model: gemini-2.5-flash\n")
    default_model, entries = parse_batch_file(f)
    assert default_model == "gemini-2.5-flash"
    assert entries == []


def test_parse_comment_without_model_directive_ignored(tmp_path):
    f = _write(tmp_path, "# ceci est un commentaire ordinaire\n")
    default_model, _ = parse_batch_file(f)
    assert default_model is None


def test_parse_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_batch_file(tmp_path / "inexistant.txt")


# ---------------------------------------------------------------------------
# parse_batch_file — URLs
# ---------------------------------------------------------------------------

def test_parse_url_no_model(tmp_path):
    f = _write(tmp_path, "https://youtu.be/ABC123\n")
    _, entries = parse_batch_file(f)
    assert len(entries) == 1
    assert entries[0].url == "https://youtu.be/ABC123"
    assert entries[0].model is None


def test_parse_url_with_model_override(tmp_path):
    f = _write(tmp_path, "https://youtu.be/ABC123 model=claude-haiku-4-5\n")
    _, entries = parse_batch_file(f)
    assert len(entries) == 1
    assert entries[0].url == "https://youtu.be/ABC123"
    assert entries[0].model == "claude-haiku-4-5"


def test_parse_multiple_urls(tmp_path):
    content = (
        "https://youtu.be/AAA\n"
        "https://youtu.be/BBB model=gpt-4o\n"
        "https://youtu.be/CCC\n"
    )
    f = _write(tmp_path, content)
    _, entries = parse_batch_file(f)
    assert len(entries) == 3
    assert entries[0].url == "https://youtu.be/AAA"
    assert entries[0].model is None
    assert entries[1].url == "https://youtu.be/BBB"
    assert entries[1].model == "gpt-4o"
    assert entries[2].url == "https://youtu.be/CCC"
    assert entries[2].model is None


def test_parse_full_example(tmp_path):
    """Exemple complet : directive + commentaires + URLs mixtes."""
    content = (
        "# model: gemini-2.5-flash\n"
        "https://youtu.be/XXX\n"
        "https://youtu.be/YYY model=claude-haiku-4-5\n"
        "# commentaire\n"
        "\n"
        "https://youtu.be/ZZZ\n"
    )
    f = _write(tmp_path, content)
    default_model, entries = parse_batch_file(f)
    assert default_model == "gemini-2.5-flash"
    assert len(entries) == 3
    assert entries[0].model is None
    assert entries[1].model == "claude-haiku-4-5"
    assert entries[2].model is None


# ---------------------------------------------------------------------------
# resolve_model — priorité
# ---------------------------------------------------------------------------

def test_resolve_model_entry_wins_over_all():
    assert resolve_model("entry-model", "file-model", "config-model") == "entry-model"


def test_resolve_model_file_default_wins_over_config():
    assert resolve_model(None, "file-model", "config-model") == "file-model"


def test_resolve_model_config_used_when_no_override():
    assert resolve_model(None, None, "config-model") == "config-model"


def test_resolve_model_empty_string_entry_falls_through_to_file():
    """Chaîne vide est falsy → le file_default prend la priorité."""
    assert resolve_model("", "file-model", "config-model") == "file-model"


def test_resolve_model_all_none_except_config():
    assert resolve_model(None, None, "gemini-2.0-flash") == "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# archive_existing
# ---------------------------------------------------------------------------

def test_archive_existing_nonexistent_returns_none(tmp_path):
    result = archive_existing(tmp_path / "missing.md")
    assert result is None


def test_archive_existing_moves_file_to_v1(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("contenu original", encoding="utf-8")
    archive_path = archive_existing(f)
    assert archive_path is not None
    assert archive_path == tmp_path / "v1" / "note.md"
    assert archive_path.exists()
    assert archive_path.read_text(encoding="utf-8") == "contenu original"


def test_archive_existing_original_no_longer_exists(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("contenu", encoding="utf-8")
    archive_existing(f)
    assert not f.exists()


def test_archive_existing_creates_v1_dir(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("x", encoding="utf-8")
    assert not (tmp_path / "v1").exists()
    archive_existing(f)
    assert (tmp_path / "v1").is_dir()


def test_archive_existing_returns_archive_path(tmp_path):
    f = tmp_path / "2024-01-01-titre.md"
    f.write_text("contenu", encoding="utf-8")
    result = archive_existing(f)
    assert result == tmp_path / "v1" / "2024-01-01-titre.md"


# ---------------------------------------------------------------------------
# Intégration — extract._run_batch() via mocks
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


def test_run_batch_dry_run_prints_urls(tmp_path, capsys):
    import extract

    content = (
        "# model: gemini-2.5-flash\n"
        "https://youtu.be/AAA\n"
        "https://youtu.be/BBB model=claude-haiku-4-5\n"
    )
    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(content, encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=True)
    captured = capsys.readouterr()

    assert "DRY-RUN" in captured.out
    assert "https://youtu.be/AAA" in captured.out
    assert "https://youtu.be/BBB" in captured.out
    assert "gemini-2.5-flash" in captured.out
    assert "claude-haiku-4-5" in captured.out


def test_run_batch_dry_run_no_generate(tmp_path, capsys):
    """En dry-run, generate_note n'est jamais appelé."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    with patch("extract.generate_note") as mock_gen:
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=True)
        mock_gen.assert_not_called()


def test_run_batch_empty_file_exits(tmp_path):
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("# only comments\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)
    assert exc.value.code == 0


def test_run_batch_missing_file_exits(tmp_path):
    import extract

    with pytest.raises(SystemExit) as exc:
        extract._run_batch(_DUMMY_CONFIG, tmp_path / "missing.txt", dry_run=False)
    assert exc.value.code == 1


def test_run_batch_invalid_url_counted_as_failure(tmp_path, capsys):
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("not-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)
    captured = capsys.readouterr()
    assert "1 échec" in captured.out


def test_run_batch_summary_printed(tmp_path, capsys):
    """Le résumé final est toujours affiché."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("not-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)
    captured = capsys.readouterr()
    assert "Résumé" in captured.out


def test_run_batch_archives_existing_file(tmp_path, capsys):
    """Une fiche existante est archivée avant régénération."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    existing = tmp_path / "testchannel" / "2024-01-01-test-video.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("ancienne fiche", encoding="utf-8")

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouvelle fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", return_value=existing),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    captured = capsys.readouterr()
    # "[archivée v1]" est dans le log, pas dans le terminal
    assert (existing.parent / "v1" / existing.name).exists()
    assert "1 archivée" in captured.out


def test_run_batch_log_created(tmp_path, capsys):
    """Un fichier batch-*.log est créé dans le même dossier que le fichier batch."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("not-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    logs = list(tmp_path.glob("batch-*.log"))
    assert len(logs) == 1


def test_run_batch_log_header(tmp_path, capsys):
    """Le log contient l'en-tête avec date et modèle."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("# model: gemini-2.5-flash\nnot-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "# Batch log —" in content
    assert "# model: gemini-2.5-flash" in content


def test_run_batch_log_failure_entry(tmp_path, capsys):
    """Le log contient ✗ pour les URLs en échec."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("not-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "✗ not-a-url → Erreur" in content


def test_run_batch_log_success_entry(tmp_path, capsys):
    """Le log contient ✓ + chemin pour les URLs traitées avec succès."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")
    note_path = tmp_path / "note.md"

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.write_note"),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "✓ https://youtu.be/AAA →" in content


def test_run_batch_log_archived_tag(tmp_path, capsys):
    """Le log contient [archivée v1] pour les fiches archivées."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    existing = tmp_path / "testchannel" / "2024-01-01-test-video.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("ancienne fiche", encoding="utf-8")

    with (
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouvelle fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", return_value=existing),
    ):
        extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "[archivée v1]" in content


def test_run_batch_log_summary_line(tmp_path, capsys):
    """Le log se termine par la ligne # Résumé."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("not-a-url\n", encoding="utf-8")

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=False)

    log = next(tmp_path.glob("batch-*.log"))
    content = log.read_text(encoding="utf-8")
    assert "# Résumé :" in content


def test_dry_run_model_in_header_not_per_line(tmp_path, capsys):
    """En dry-run, le modèle par défaut est en tête — pas répété sous chaque URL."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "# model: gemini-2.5-flash\nhttps://youtu.be/AAA\nhttps://youtu.be/BBB\n",
        encoding="utf-8",
    )

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=True)
    captured = capsys.readouterr()

    # Modèle dans le header
    assert "modèle : gemini-2.5-flash" in captured.out
    # Pas de ligne "Modèle : xxx" sous chaque URL (les URLs sans override n'ont pas de ligne modèle)
    lines = captured.out.splitlines()
    url_lines = [l for l in lines if "youtu.be/AAA" in l or "youtu.be/BBB" in l]
    for line in url_lines:
        assert "modèle" not in line


def test_dry_run_model_inline_for_override(tmp_path, capsys):
    """En dry-run, le modèle est affiché en ligne uniquement si surcharge par URL."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text(
        "# model: gemini-2.5-flash\n"
        "https://youtu.be/AAA\n"
        "https://youtu.be/BBB model=claude-haiku-4-5\n",
        encoding="utf-8",
    )

    extract._run_batch(_DUMMY_CONFIG, batch_file, dry_run=True)
    captured = capsys.readouterr()

    lines = captured.out.splitlines()
    aaa_line = next(l for l in lines if "youtu.be/AAA" in l)
    bbb_line = next(l for l in lines if "youtu.be/BBB" in l)

    assert "modèle" not in aaa_line          # pas de surcharge → pas de modèle inline
    assert "claude-haiku-4-5" in bbb_line    # surcharge → modèle inline


# ---------------------------------------------------------------------------
# Intégration — détection mode batch dans extract.main()
# ---------------------------------------------------------------------------

def test_main_detects_txt_file_as_batch(tmp_path, capsys):
    """extract.main() dispatche vers le mode batch quand arg = .txt."""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    with (
        patch.object(sys, "argv", ["extract.py", str(batch_file)]),
        patch("extract.load_config", return_value=_DUMMY_CONFIG),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche"),
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.build_file_path", return_value=tmp_path / "note.md"),
        patch("extract.write_note"),
    ):
        extract.main()

    captured = capsys.readouterr()
    assert "Résumé" in captured.out


def test_main_dry_run_flag_before_file(tmp_path, capsys):
    """--dry-run accepté avant le fichier : extract.py --dry-run file.txt"""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    with (
        patch.object(sys, "argv", ["extract.py", "--dry-run", str(batch_file)]),
        patch("extract.load_config", return_value=_DUMMY_CONFIG),
    ):
        extract.main()

    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out


def test_main_dry_run_flag_after_file(tmp_path, capsys):
    """--dry-run accepté après le fichier : extract.py file.txt --dry-run"""
    import extract

    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://youtu.be/AAA\n", encoding="utf-8")

    with (
        patch.object(sys, "argv", ["extract.py", str(batch_file), "--dry-run"]),
        patch("extract.load_config", return_value=_DUMMY_CONFIG),
    ):
        extract.main()

    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out
