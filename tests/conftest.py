from __future__ import annotations

"""Fixtures partagées pour les tests end-to-end.

La fixture `generated_note` lance le pipeline complet une seule fois
par session sur l'URL de référence. Skip automatique si GROQ_API_KEY absente.
"""

import os

import pytest
from dotenv import load_dotenv

from src.transcript import extract_video_id, fetch_transcript, format_transcript_for_prompt
from src.metadata import fetch_metadata
from src.generator import generate_note
from src.writer import build_file_path, write_note

load_dotenv()


REFERENCE_URL = "https://youtu.be/T_GqhyYqTD4"


@pytest.fixture(scope="session")
def generated_note_path(tmp_path_factory):
    """Lance le pipeline complet sur l'URL de référence et retourne le Path du fichier."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY non définie — smoke test sauté")

    tmpdir = tmp_path_factory.mktemp("yt_output")

    config = {
        "transcript_language": "fr",
        "llm": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5",
            "api_key": api_key,
        },
        "output": {
            "mode": "local",
            "local_path": str(tmpdir),
        },
        "output_language": "fr",
    }

    video_id = extract_video_id(REFERENCE_URL)
    metadata = fetch_metadata(REFERENCE_URL)
    segments, _ = fetch_transcript(video_id, "fr")
    formatted = format_transcript_for_prompt(segments)
    note = generate_note(config, video_id, REFERENCE_URL, metadata, segments, formatted)

    file_path = build_file_path(
        config, metadata["channel"], metadata["upload_date"], metadata["title"]
    )
    return write_note(file_path, note, [])


@pytest.fixture(scope="session")
def generated_note_content(generated_note_path):
    """Contenu texte de la fiche générée."""
    return generated_note_path.read_text(encoding="utf-8")
