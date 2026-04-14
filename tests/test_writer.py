from __future__ import annotations

"""Tests unitaires — src/writer.py (generate_slug, build_file_path, write_note).

Les tests write_note couvrant FileExistsError et overwrite simple
sont dans test_cli.py — ce fichier couvre les cas manquants.
"""

import pytest
from pathlib import Path

from src.writer import generate_slug, build_file_path, write_note


# ---------------------------------------------------------------------------
# generate_slug
# ---------------------------------------------------------------------------

def test_generate_slug_accents_produces_ascii():
    slug = generate_slug("J'ai testé ça avec é à ç")
    assert slug == slug.encode("ascii", errors="ignore").decode()


def test_generate_slug_long_title_truncated_to_80():
    title = "A" * 100
    assert len(generate_slug(title)) <= 80


def test_generate_slug_empty_string():
    result = generate_slug("")
    assert isinstance(result, str)


def test_generate_slug_normal_title():
    result = generate_slug("Deep Work — Cal Newport")
    assert "deep-work" in result
    assert "cal-newport" in result


def test_generate_slug_special_chars_removed():
    result = generate_slug("Hello! World? #1")
    assert "!" not in result
    assert "?" not in result
    assert "#" not in result


# ---------------------------------------------------------------------------
# build_file_path
# ---------------------------------------------------------------------------

def test_build_file_path_local_mode(tmp_path):
    config = {"output": {"mode": "local", "local_path": str(tmp_path)}}
    result = build_file_path(config, "TestChannel", "2024-01-01", "Deep Work")
    assert result.suffix == ".md"
    assert "2024-01-01" in result.name
    assert str(tmp_path) in str(result)


def test_build_file_path_obsidian_mode(tmp_path):
    config = {"output": {"mode": "obsidian", "vault_path": str(tmp_path)}}
    result = build_file_path(config, "TestChannel", "2024-01-01", "Deep Work")
    assert str(tmp_path) in str(result)
    assert result.suffix == ".md"


def test_build_file_path_no_mode_key_defaults_local():
    """Clé 'mode' absente → mode local par défaut."""
    config = {"output": {"local_path": "./output"}}
    result = build_file_path(config, "Chan", "2024-01-01", "Title")
    assert "output" in str(result)


def test_build_file_path_no_local_path_defaults_output():
    """Clé 'local_path' absente → chemin par défaut './output'."""
    config = {"output": {}}
    result = build_file_path(config, "Chan", "2024-01-01", "Title")
    assert "output" in str(result)


def test_build_file_path_does_not_create_directory(tmp_path):
    """build_file_path ne crée pas de dossier (bug ghost dirs corrigé)."""
    config = {"output": {"mode": "local", "local_path": str(tmp_path)}}
    result = build_file_path(config, "NewChannel", "2024-01-01", "Title")
    # Le dossier channel (parent du fichier) ne doit pas exister
    assert not result.parent.exists()


def test_build_file_path_channel_slug_in_path(tmp_path):
    config = {"output": {"mode": "local", "local_path": str(tmp_path)}}
    result = build_file_path(config, "My Channel!", "2024-01-01", "Title")
    assert "my-channel" in str(result)


def test_build_file_path_filename_includes_date_and_slug(tmp_path):
    config = {"output": {"mode": "local", "local_path": str(tmp_path)}}
    result = build_file_path(config, "Chan", "2024-06-15", "Atomic Habits")
    assert result.name.startswith("2024-06-15-")
    assert "atomic-habits" in result.name


# ---------------------------------------------------------------------------
# write_note — warnings
# ---------------------------------------------------------------------------

def test_write_note_with_warnings_prefixes_header(tmp_path):
    f = tmp_path / "note.md"
    write_note(f, "contenu", ["Avertissement 1", "Avertissement 2"])
    content = f.read_text(encoding="utf-8")
    assert "\u26a0\ufe0f" in content  # ⚠️
    assert "Avertissement 1" in content
    assert "Avertissement 2" in content
    assert content.endswith("contenu")


def test_write_note_empty_warnings_no_header(tmp_path):
    f = tmp_path / "note.md"
    write_note(f, "contenu", [])
    assert f.read_text(encoding="utf-8") == "contenu"


def test_write_note_creates_nested_parent_directory(tmp_path):
    """write_note crée les dossiers parents s'ils n'existent pas."""
    nested = tmp_path / "sub" / "dir" / "note.md"
    write_note(nested, "contenu", [])
    assert nested.exists()
    assert nested.read_text(encoding="utf-8") == "contenu"


def test_write_note_warnings_with_overwrite(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("ancien", encoding="utf-8")
    write_note(f, "nouveau", ["Warn"], overwrite=True)
    content = f.read_text(encoding="utf-8")
    assert "\u26a0\ufe0f" in content  # ⚠️
    assert "nouveau" in content
    assert "ancien" not in content
