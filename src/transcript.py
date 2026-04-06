from __future__ import annotations

"""Extraction du transcript horodaté depuis YouTube.

Utilise youtube-transcript-api pour récupérer les sous-titres
dans la langue configurée. Retourne une liste de segments
avec timestamp (secondes) et texte.
"""

import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

_api = YouTubeTranscriptApi()


class NoTranscriptError(Exception):
    """Aucun sous-titre disponible pour cette vidéo."""
    pass


def extract_video_id(url: str) -> str:
    """Extrait le video_id depuis une URL YouTube.

    Supporte : youtu.be/ID, youtube.com/watch?v=ID, youtube.com/shorts/ID

    Raises:
        ValueError: si l'URL n'est pas reconnue
    """
    # youtu.be/ID
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    # youtube.com/watch?v=ID
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]

        # youtube.com/shorts/ID ou youtube.com/embed/ID
        match = re.match(r"^/(shorts|embed)/([a-zA-Z0-9_-]+)", parsed.path)
        if match:
            return match.group(2)

    raise ValueError(
        f"URL YouTube non reconnue : {url}\n"
        "Formats acceptés : youtu.be/ID, youtube.com/watch?v=ID, youtube.com/shorts/ID"
    )


def fetch_transcript(video_id: str, language: str) -> tuple[list[dict], str]:
    """Récupère le transcript horodaté.

    Args:
        video_id: identifiant YouTube
        language: langue souhaitée (ex: 'fr')

    Returns:
        (segments, actual_language) — segments = [{"text": str, "start": float, "duration": float}]
        actual_language peut différer si fallback

    Raises:
        NoTranscriptError: si aucun sous-titre disponible
    """
    try:
        transcript_list = _api.list(video_id)
    except TranscriptsDisabled:
        raise NoTranscriptError(
            "Aucun sous-titre disponible pour cette vidéo. "
            "Envisagez yt-dlp + Whisper (hors scope V1)."
        )
    except VideoUnavailable:
        raise NoTranscriptError(
            "Vidéo indisponible (privée, supprimée ou URL invalide)."
        )

    # Essayer la langue demandée en priorité
    try:
        transcript = transcript_list.find_transcript([language])
        snippets = transcript.fetch()
        segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in snippets]
        return segments, language
    except NoTranscriptFound:
        pass

    # Fallback : chercher une langue générée automatiquement
    try:
        transcript = transcript_list.find_generated_transcript([language])
        snippets = transcript.fetch()
        segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in snippets]
        return segments, language
    except NoTranscriptFound:
        pass

    # Dernier recours : prendre la première langue disponible
    available = list(transcript_list)
    if not available:
        raise NoTranscriptError(
            "Aucun sous-titre disponible pour cette vidéo. "
            "Envisagez yt-dlp + Whisper (hors scope V1)."
        )

    fallback = available[0]
    snippets = fallback.fetch()
    segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in snippets]
    actual_language = fallback.language_code
    return segments, actual_language


def format_transcript_for_prompt(segments: list[dict]) -> str:
    """Formate les segments en texte [HH:MM:SS] pour le prompt LLM et la section 10.

    Returns:
        Texte formaté, un segment par ligne : [HH:MM:SS] texte
    """
    lines = []
    for seg in segments:
        ts = format_timestamp(seg["start"])
        text = seg["text"].strip()
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """Convertit des secondes en format HH:MM:SS."""
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
