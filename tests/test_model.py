from __future__ import annotations

"""Tests unitaires — flag --model NOM_MODELE dans extract.py (MO-01 à MO-07).

Tous les tests utilisent des mocks. Aucun appel réseau réel.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures et helpers
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

# Fiche avec **Model** : gemini-2.5-flash dans le header
_FICHE_MODEL_FLASH = (
    "# Test Video\n"
    "**URL** : https://youtu.be/ABC123 · **Channel** : TestChannel"
    " · **Processed** : 2024-01-01 · **Duration** : 10:00 · **Model** : gemini-2.5-flash\n"
    "\n"
    "## Thèse centrale\n"
    "Contenu de test.\n"
)

# Fiche sans **Model** dans le header (format ancien)
_FICHE_NO_MODEL = (
    "# Test Video\n"
    "**URL** : https://youtu.be/ABC123 · **Channel** : TestChannel\n"
    "\n"
    "## Thèse centrale\n"
    "Contenu de test sans modèle.\n"
)


def _make_spinner():
    """Crée un mock yaspin utilisable comme context manager."""
    sp = MagicMock()
    sp.__enter__ = MagicMock(return_value=sp)
    sp.__exit__ = MagicMock(return_value=False)
    return sp


# ---------------------------------------------------------------------------
# MO-01 — --model X + fiche inexistante → génération avec modèle X
# ---------------------------------------------------------------------------

def test_mo01_model_override_new_file(tmp_path):
    """MO-01 : --model X + fiche inexistante → generate_note appelé avec config modèle X."""
    import extract

    note_path = tmp_path / "note.md"

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche générée") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=note_path),
    ):
        extract._run_single(
            _DUMMY_CONFIG,
            "https://youtu.be/ABC123",
            model_override="gemini-2.5-flash",
        )

    mock_gen.assert_called_once()
    called_config = mock_gen.call_args[0][0]
    assert called_config["llm"]["model"] == "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# MO-02 — --model X + fiche existante même modèle → "Écraser ?" avant LLM
# ---------------------------------------------------------------------------

def test_mo02_same_model_asks_overwrite_before_llm(tmp_path):
    """MO-02 : fiche existante même modèle → demande "Écraser ?" avant appel LLM, réponse N → exit 0."""
    import extract

    note_path = tmp_path / "note.md"
    note_path.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.generate_note") as mock_gen,
        patch("builtins.input", return_value="N") as mock_input,
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(
                _DUMMY_CONFIG,
                "https://youtu.be/ABC123",
                model_override="gemini-2.5-flash",
            )

    assert exc_info.value.code == 0
    mock_gen.assert_not_called()
    # Vérifier que le prompt contient "Écraser ?" et le nom du modèle
    prompt_arg = mock_input.call_args[0][0]
    assert "Écraser ?" in prompt_arg
    assert "gemini-2.5-flash" in prompt_arg


def test_mo02_same_model_overwrite_accepted(tmp_path):
    """MO-02 variante : réponse 'o' → generate_note appelé, fichier écrasé."""
    import extract

    note_path = tmp_path / "note.md"
    note_path.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouveau contenu") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=note_path),
        patch("builtins.input", return_value="o"),
    ):
        extract._run_single(
            _DUMMY_CONFIG,
            "https://youtu.be/ABC123",
            model_override="gemini-2.5-flash",
        )

    mock_gen.assert_called_once()


# ---------------------------------------------------------------------------
# MO-03 — --model X + fiche existante modèle différent → options (a)/(r)/(N) avant LLM
# ---------------------------------------------------------------------------

def test_mo03_different_model_shows_options_before_llm(tmp_path):
    """MO-03 : modèle différent → message (a)/(r)/(N) avant appel LLM, réponse N → exit 0."""
    import extract

    note_path = tmp_path / "note.md"
    note_path.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")  # **Model** : gemini-2.5-flash

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.generate_note") as mock_gen,
        patch("builtins.input", return_value="n") as mock_input,
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(
                _DUMMY_CONFIG,
                "https://youtu.be/ABC123",
                model_override="gemini-2.0-flash",  # different from gemini-2.5-flash in fiche
            )

    assert exc_info.value.code == 0
    mock_gen.assert_not_called()
    prompt_arg = mock_input.call_args[0][0]
    assert "gemini-2.5-flash" in prompt_arg  # ancien modèle
    assert "gemini-2.0-flash" in prompt_arg  # nouveau modèle
    assert "(a)" in prompt_arg
    assert "(r)" in prompt_arg


def test_mo03_different_model_replace_generates(tmp_path):
    """MO-03 variante : réponse 'r' → generate_note appelé avec overwrite."""
    import extract

    note_path = tmp_path / "note.md"
    note_path.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="nouveau contenu") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=note_path),
        patch("builtins.input", return_value="r"),
    ):
        extract._run_single(
            _DUMMY_CONFIG,
            "https://youtu.be/ABC123",
            model_override="gemini-2.0-flash",
        )

    mock_gen.assert_called_once()


# ---------------------------------------------------------------------------
# MO-04 — --model X + fiche existante modèle inconnu → message "modèle inconnu"
# ---------------------------------------------------------------------------

def test_mo04_unknown_model_shows_unknown_message(tmp_path):
    """MO-04 : modèle inconnu (header absent) → message "modèle inconnu" + options (a)/(r)/(N)."""
    import extract

    note_path = tmp_path / "note.md"
    note_path.write_text(_FICHE_NO_MODEL, encoding="utf-8")  # pas de **Model**

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=note_path),
        patch("extract.generate_note") as mock_gen,
        patch("builtins.input", return_value="n") as mock_input,
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(
                _DUMMY_CONFIG,
                "https://youtu.be/ABC123",
                model_override="gemini-2.0-flash",
            )

    assert exc_info.value.code == 0
    mock_gen.assert_not_called()
    prompt_arg = mock_input.call_args[0][0]
    assert "modèle inconnu" in prompt_arg
    assert "gemini-2.0-flash" in prompt_arg  # modèle actuel
    assert "(a)" in prompt_arg


# ---------------------------------------------------------------------------
# MO-05 — --model X + --gist + fiche existante même modèle → publication sans régénération
# ---------------------------------------------------------------------------

def test_mo05_gist_same_model_publish_no_regen(tmp_path):
    """MO-05 : --model X + --gist + fiche existante même modèle → gist sans régénération."""
    import extract

    existing = tmp_path / "existing.md"
    existing.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")  # **Model** : gemini-2.5-flash

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=existing),
        patch("extract.generate_note") as mock_gen,
        patch("extract.publish_gist", return_value="https://gist.github.com/user/abc") as mock_pub,
    ):
        extract._run_single(
            _DUMMY_CONFIG,
            "https://youtu.be/ABC123",
            gist=True,
            model_override="gemini-2.5-flash",
        )

    mock_gen.assert_not_called()
    mock_pub.assert_called_once_with(existing)


# ---------------------------------------------------------------------------
# MO-06 — --model X + --gist + modèle différent + choix (a) → archivage + régénération + gist
# ---------------------------------------------------------------------------

def test_mo06_gist_different_model_archive_regen_publish(tmp_path):
    """MO-06 : modèle différent + choix (a) → archive_existing + generate_note + publish_gist."""
    import extract

    existing = tmp_path / "existing.md"
    existing.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")  # **Model** : gemini-2.5-flash

    new_note = tmp_path / "new_note.md"

    with (
        patch("extract.yaspin", return_value=_make_spinner()),
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=existing),
        patch("extract.fetch_metadata", return_value=_DUMMY_METADATA),
        patch("extract.build_file_path", return_value=new_note),
        patch("extract.fetch_transcript", return_value=([], "fr")),
        patch("extract.format_transcript_for_prompt", return_value=""),
        patch("extract.generate_note", return_value="fiche") as mock_gen,
        patch("extract.validate_note", return_value=(True, [])),
        patch("extract.write_note", return_value=new_note),
        patch("extract.publish_gist", return_value="https://gist.github.com/user/abc") as mock_pub,
        patch("extract.archive_existing") as mock_arch,
        patch("builtins.input", return_value="a"),
    ):
        extract._run_single(
            _DUMMY_CONFIG,
            "https://youtu.be/ABC123",
            gist=True,
            model_override="gemini-2.0-flash",
        )

    mock_arch.assert_called_once_with(existing)
    mock_gen.assert_called_once()
    mock_pub.assert_called_once_with(new_note)


# ---------------------------------------------------------------------------
# MO-07 — --model X + --gist + modèle différent + choix (N) → aucun LLM, aucun gist
# ---------------------------------------------------------------------------

def test_mo07_gist_different_model_cancel(tmp_path):
    """MO-07 : modèle différent + choix (N) → aucun appel LLM, aucun gist, exit 0."""
    import extract

    existing = tmp_path / "existing.md"
    existing.write_text(_FICHE_MODEL_FLASH, encoding="utf-8")  # **Model** : gemini-2.5-flash

    with (
        patch("extract.extract_video_id", return_value="ABC123"),
        patch("extract._find_existing_fiche", return_value=existing),
        patch("extract.generate_note") as mock_gen,
        patch("extract.publish_gist") as mock_pub,
        patch("builtins.input", return_value="n"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            extract._run_single(
                _DUMMY_CONFIG,
                "https://youtu.be/ABC123",
                gist=True,
                model_override="gemini-2.0-flash",
            )

    assert exc_info.value.code == 0
    mock_gen.assert_not_called()
    mock_pub.assert_not_called()
