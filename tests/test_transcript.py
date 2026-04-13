from __future__ import annotations

"""Tests unitaires — src/transcript.py (fonctions pures, sans appel réseau)."""

import pytest

from src.transcript import extract_video_id, format_timestamp, format_transcript_for_prompt


# ---------------------------------------------------------------------------
# format_timestamp
# ---------------------------------------------------------------------------

def test_format_timestamp_zero():
    assert format_timestamp(0) == "00:00:00"

def test_format_timestamp_84():
    assert format_timestamp(84) == "00:01:24"

def test_format_timestamp_float_truncation():
    """84.9 → 84 secondes (troncature, pas arrondi)."""
    assert format_timestamp(84.9) == "00:01:24"

def test_format_timestamp_boundary_before_1h():
    assert format_timestamp(3599) == "00:59:59"

def test_format_timestamp_exact_1h():
    assert format_timestamp(3600) == "01:00:00"

def test_format_timestamp_above_2h():
    assert format_timestamp(7261) == "02:01:01"


# ---------------------------------------------------------------------------
# format_transcript_for_prompt
# ---------------------------------------------------------------------------

def test_format_transcript_empty():
    assert format_transcript_for_prompt([]) == ""

def test_format_transcript_single_segment():
    segments = [{"text": "bonjour", "start": 0.0, "duration": 2.0}]
    assert format_transcript_for_prompt(segments) == "[00:00:00] bonjour"

def test_format_transcript_strips_whitespace():
    segments = [{"text": "  texte avec espaces  ", "start": 0.0, "duration": 1.0}]
    assert format_transcript_for_prompt(segments) == "[00:00:00] texte avec espaces"

def test_format_transcript_multiple_segments():
    segments = [
        {"text": "premier", "start": 0.0, "duration": 2.0},
        {"text": "deuxième", "start": 84.0, "duration": 3.0},
    ]
    result = format_transcript_for_prompt(segments)
    lines = result.split("\n")
    assert len(lines) == 2
    assert lines[0] == "[00:00:00] premier"
    assert lines[1] == "[00:01:24] deuxième"


# ---------------------------------------------------------------------------
# extract_video_id
# ---------------------------------------------------------------------------

def test_extract_video_id_youtu_be():
    assert extract_video_id("https://youtu.be/ABC123") == "ABC123"

def test_extract_video_id_youtube_watch():
    assert extract_video_id("https://www.youtube.com/watch?v=ABC123") == "ABC123"

def test_extract_video_id_youtube_watch_extra_params():
    assert extract_video_id("https://www.youtube.com/watch?v=ABC123&t=42&list=PL123") == "ABC123"

def test_extract_video_id_shorts():
    assert extract_video_id("https://youtube.com/shorts/ABC123") == "ABC123"

def test_extract_video_id_embed():
    assert extract_video_id("https://youtube.com/embed/ABC123") == "ABC123"

def test_extract_video_id_invalid_raises():
    with pytest.raises(ValueError, match="URL YouTube non reconnue"):
        extract_video_id("https://example.com/video")

def test_extract_video_id_empty_raises():
    with pytest.raises(ValueError):
        extract_video_id("")
