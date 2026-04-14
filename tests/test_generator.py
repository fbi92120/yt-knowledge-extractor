from __future__ import annotations

"""Tests unitaires — src/generator.py (fonctions pures, sans appel LLM)."""

import pytest

from src.generator import build_system_prompt, build_user_prompt


# ---------------------------------------------------------------------------
# Kwargs de base pour build_system_prompt
# ---------------------------------------------------------------------------

_BASE_KWARGS = dict(
    output_language="fr",
    url="https://youtu.be/ABC123",
    channel="TestChannel",
    processed_date="2026-04-13",
    duration="10:00",
    video_id="ABC123",
    chapters=None,
    description="",
    model="gemini-2.0-flash",
)


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------

def test_build_system_prompt_chapters_none_injects_placeholder():
    result = build_system_prompt(**_BASE_KWARGS)
    assert "None (infer from content)" in result


def test_build_system_prompt_chapters_list_injects_str():
    chapters = [{"title": "Intro", "start_time": 0}]
    result = build_system_prompt(**{**_BASE_KWARGS, "chapters": chapters})
    assert str(chapters) in result


def test_build_system_prompt_no_keyerror():
    """Tous les placeholders {…} sont substitués sans lever KeyError."""
    result = build_system_prompt(**_BASE_KWARGS)
    assert isinstance(result, str)
    assert len(result) > 100


def test_build_system_prompt_contains_url():
    result = build_system_prompt(**_BASE_KWARGS)
    assert "https://youtu.be/ABC123" in result


def test_build_system_prompt_contains_channel():
    result = build_system_prompt(**_BASE_KWARGS)
    assert "TestChannel" in result


def test_build_system_prompt_contains_model():
    result = build_system_prompt(**_BASE_KWARGS)
    assert "gemini-2.0-flash" in result


def test_build_system_prompt_contains_video_id_in_links():
    """video_id est injecté dans les liens youtu.be du template."""
    result = build_system_prompt(**_BASE_KWARGS)
    assert "youtu.be/ABC123" in result


def test_build_system_prompt_chapters_empty_list_treated_as_none():
    """Liste vide (falsy) → même comportement que None."""
    result = build_system_prompt(**{**_BASE_KWARGS, "chapters": []})
    assert "None (infer from content)" in result


# ---------------------------------------------------------------------------
# build_user_prompt
# ---------------------------------------------------------------------------

def test_build_user_prompt_no_sources_no_section():
    result = build_user_prompt("transcript text", "")
    assert "Sources extraites" not in result
    assert "transcript text" in result


def test_build_user_prompt_with_sources_adds_section():
    result = build_user_prompt("transcript text", "Atomic Habits — James Clear")
    assert "Sources extraites" in result
    assert "Atomic Habits — James Clear" in result


def test_build_user_prompt_transcript_present():
    transcript = "[00:00:00] bonjour\n[00:01:00] monde"
    result = build_user_prompt(transcript, "")
    assert transcript in result


def test_build_user_prompt_sources_none_equivalent_to_empty():
    """filtered_sources vide → pas de section sources dans le prompt."""
    result = build_user_prompt("texte", "")
    assert result.count("Sources") == 0
