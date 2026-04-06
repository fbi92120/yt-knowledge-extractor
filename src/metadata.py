"""Extraction des métadonnées YouTube et filtrage des sources.

Utilise yt-dlp pour récupérer titre, chaîne, durée, description
et chapitres natifs. Filtre les sources intellectuelles depuis
la description (auteur ou titre identifiable uniquement).
"""

from __future__ import annotations

import re

import yt_dlp


class VideoUnavailableError(Exception):
    """Vidéo privée, supprimée ou inaccessible."""
    pass


def fetch_metadata(url: str) -> dict:
    """Extrait les métadonnées de la vidéo via yt-dlp.

    Returns:
        dict avec : title, channel, duration, description, chapters, upload_date

    Raises:
        VideoUnavailableError: si la vidéo est privée ou supprimée
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise VideoUnavailableError(
            f"Vidéo indisponible (privée, supprimée ou URL invalide) : {e}"
        )

    duration_secs = info.get("duration", 0)
    duration_str = _format_duration(duration_secs)

    upload_date_raw = info.get("upload_date", "")
    upload_date = (
        f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]}"
        if len(upload_date_raw) == 8
        else upload_date_raw
    )

    return {
        "title": info.get("title", ""),
        "channel": info.get("channel", info.get("uploader", "")),
        "duration": duration_str,
        "duration_seconds": duration_secs,
        "description": info.get("description", ""),
        "chapters": extract_chapters(info),
        "upload_date": upload_date,
    }


def extract_chapters(info: dict) -> list[dict] | None:
    """Extrait les chapitres YouTube natifs s'ils existent.

    Returns:
        Liste de {"title": str, "start_time": float} ou None
    """
    chapters = info.get("chapters")
    if not chapters:
        return None

    return [
        {"title": ch.get("title", ""), "start_time": ch.get("start_time", 0)}
        for ch in chapters
    ]


def filter_sources(description: str) -> str:
    """Filtre les sources intellectuelles depuis la description YouTube.

    Conserve uniquement les entrées avec auteur ou titre identifiable.
    Exclut : réseaux sociaux, sponsors, affiliés, auto-promotion.

    Returns:
        Description filtrée ou chaîne vide si aucune source qualifiée
    """
    if not description:
        return ""

    # Domaines à exclure (réseaux sociaux, auto-promotion, affiliés)
    excluded_domains = re.compile(
        r"(instagram\.com|twitter\.com|x\.com|tiktok\.com|facebook\.com|"
        r"fb\.com|linkedin\.com|discord\.gg|t\.me|telegram\.me|"
        r"twitch\.tv|patreon\.com|buymeacoffee\.com|ko-fi\.com|"
        r"amzn\.to|bit\.ly|tinyurl\.com)",
        re.IGNORECASE,
    )

    # Mots-clés indiquant du contenu commercial
    commercial_keywords = re.compile(
        r"(sponsor|code promo|promo code|affilié|affiliate|partenaire|"
        r"abonne|subscribe|rejoins|follow|merch|boutique|shop)",
        re.IGNORECASE,
    )

    filtered_lines = []
    for line in description.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Ignorer les lignes purement commerciales
        if commercial_keywords.search(stripped):
            continue

        # Ignorer les lignes avec uniquement un lien exclu
        if excluded_domains.search(stripped):
            continue

        # Garder les lignes qui contiennent un lien avec du contexte textuel
        # (titre, auteur) ou des références sans lien (livres, articles)
        has_url = re.search(r"https?://", stripped)
        has_text_context = len(re.sub(r"https?://\S+", "", stripped).strip()) > 10

        if has_url and has_text_context:
            filtered_lines.append(stripped)
        elif not has_url and _looks_like_reference(stripped):
            filtered_lines.append(stripped)

    return "\n".join(filtered_lines)


def _looks_like_reference(text: str) -> bool:
    """Heuristique : la ligne ressemble à une référence intellectuelle."""
    # Contient des guillemets (titre d'oeuvre), un tiret (auteur — titre),
    # ou des mots-clés de référence
    ref_patterns = re.compile(
        r'(«|»|"|"|\u2014|\u2013|— |– |livre|book|article|étude|study|paper|'
        r"source|référence|reference)",
        re.IGNORECASE,
    )
    return bool(ref_patterns.search(text))


def _format_duration(seconds: int) -> str:
    """Formate une durée en secondes vers MM:SS ou HH:MM:SS."""
    if seconds <= 0:
        return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
