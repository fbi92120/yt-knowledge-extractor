from __future__ import annotations

"""Tests unitaires — src/metadata.py (fonctions pures, sans appel réseau)."""

import pytest

from src.metadata import extract_chapters, filter_sources, _format_duration


# ---------------------------------------------------------------------------
# filter_sources
# ---------------------------------------------------------------------------

def test_filter_sources_empty_description():
    assert filter_sources("") == ""


def test_filter_sources_excluded_domain_instagram():
    desc = "Suivez-moi sur https://instagram.com/mon-compte"
    assert filter_sources(desc) == ""


def test_filter_sources_excluded_domain_twitter():
    desc = "Mon twitter https://twitter.com/user"
    assert filter_sources(desc) == ""


def test_filter_sources_commercial_keyword_sponsor():
    desc = "Ce contenu est sponsorisé par https://example.com"
    assert filter_sources(desc) == ""


def test_filter_sources_commercial_keyword_affilie():
    desc = "Lien affilié : https://example.com/produit"
    assert filter_sources(desc) == ""


def test_filter_sources_url_only_no_text_context():
    """URL seule sans texte identifiable (< 10 chars hors URL) → filtrée."""
    desc = "https://example.com/article-sans-titre"
    assert filter_sources(desc) == ""


def test_filter_sources_text_plus_url_kept():
    """Titre identifiable + URL → conservée."""
    line = "The Intelligent Investor — Benjamin Graham https://archive.org/book"
    result = filter_sources(line)
    assert result == line


def test_filter_sources_reference_without_url_guillemets():
    """Ligne sans URL mais avec guillemets français → conservée."""
    line = "«L'économie de la connaissance» — Auteur Célèbre"
    result = filter_sources(line)
    assert result == line


def test_filter_sources_reference_without_url_dash():
    """Ligne sans URL mais avec tiret — (em dash) → conservée."""
    line = "Deep Work — Cal Newport"
    result = filter_sources(line)
    assert result == line


def test_filter_sources_reference_keyword_livre():
    """Ligne contenant le mot 'livre' → conservée."""
    line = "livre : Thinking Fast and Slow, Daniel Kahneman"
    result = filter_sources(line)
    assert result == line


def test_filter_sources_no_qualifying_source():
    """Description sans aucune source qualifiée → chaîne vide."""
    desc = "\n".join([
        "Abonne-toi à la chaîne !",
        "https://patreon.com/mon-compte",
        "https://discord.gg/mon-serveur",
        "Code promo : PROMO10",
    ])
    assert filter_sources(desc) == ""


def test_filter_sources_mixed_keeps_only_qualifying():
    """Description mixte → seules les lignes qualifiées conservées."""
    qualifying = "Atomic Habits — James Clear https://jamesclear.com/atomic-habits"
    desc = "\n".join([
        "Suivez sur https://instagram.com/compte",
        qualifying,
        "Sponsor : https://example.com",
    ])
    result = filter_sources(desc)
    assert result == qualifying


# ---------------------------------------------------------------------------
# extract_chapters
# ---------------------------------------------------------------------------

def test_extract_chapters_no_key():
    assert extract_chapters({}) is None


def test_extract_chapters_none_value():
    assert extract_chapters({"chapters": None}) is None


def test_extract_chapters_empty_list():
    assert extract_chapters({"chapters": []}) is None


def test_extract_chapters_valid():
    info = {
        "chapters": [
            {"title": "Introduction", "start_time": 0},
            {"title": "Partie 1", "start_time": 120.5},
        ]
    }
    result = extract_chapters(info)
    assert result == [
        {"title": "Introduction", "start_time": 0},
        {"title": "Partie 1", "start_time": 120.5},
    ]


def test_extract_chapters_missing_title_defaults_to_empty():
    info = {"chapters": [{"start_time": 0}]}
    result = extract_chapters(info)
    assert result[0]["title"] == ""


def test_extract_chapters_missing_start_time_defaults_to_zero():
    info = {"chapters": [{"title": "Intro"}]}
    result = extract_chapters(info)
    assert result[0]["start_time"] == 0


# ---------------------------------------------------------------------------
# _format_duration
# ---------------------------------------------------------------------------

def test_format_duration_zero():
    assert _format_duration(0) == "00:00"


def test_format_duration_negative():
    assert _format_duration(-10) == "00:00"


def test_format_duration_under_1h():
    assert _format_duration(3599) == "59:59"


def test_format_duration_exact_1h():
    assert _format_duration(3600) == "01:00:00"


def test_format_duration_above_2h():
    assert _format_duration(7261) == "02:01:01"
