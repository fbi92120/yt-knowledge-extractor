from __future__ import annotations

"""Tests unitaires — src/validator.py."""

import pytest

from src.validator import validate_note, build_warning_header, REQUIRED_SECTIONS


# ---------------------------------------------------------------------------
# Fixture : fiche valide minimale
# ---------------------------------------------------------------------------

def _valid_note() -> str:
    """Construit une fiche minimale passant toutes les validations."""
    chapters = "\n".join(f"| {i} | Bloc {i} | 00:0{i}:00 | [▶](https://youtu.be/X?t={i*60}) |" for i in range(1, 7))
    concepts = "\n".join(
        f"#### Concept {i} [▶ 00:0{i}:00](https://youtu.be/X?t={i*60})\n**Définition selon l'auteur** : def {i}."
        for i in range(1, 4)
    )
    return f"""\
# Titre de la vidéo

## Thèse centrale
La thèse de l'auteur.

## Chapitrage inféré
| # | Bloc thématique | Début | Lien direct |
|---|---|---|---|
{chapters}

## Carte des idées
Paragraphe narratif [▶ 00:01:00](https://youtu.be/X?t=60).

## Concepts clés
{concepts}

## Formulations notables
> "Citation exacte de l'auteur."
> [▶ 00:02:00](https://youtu.be/X?t=120)

## Questions ouvertes

### Soulevées dans la vidéo
Question [▶ 00:03:00](https://youtu.be/X?t=180).

### Ouvertures suggérées
Ouverture [inférence].

## Mes notes
*(espace libre)*

## Sources & références
Aucune source identifiée.

---
<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->
[00:00:00] premier segment
[00:01:00] deuxième segment
"""


# ---------------------------------------------------------------------------
# validate_note — fiche valide
# ---------------------------------------------------------------------------

def test_valid_note_returns_true_no_warnings():
    is_valid, warnings = validate_note(_valid_note())
    assert is_valid is True
    assert warnings == []


# ---------------------------------------------------------------------------
# validate_note — sections manquantes (une par une)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_missing_section_produces_one_warning(section):
    note = _valid_note().replace(f"## {section}", "## SUPPRIMÉE")
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any(section in w for w in warnings), f"Avertissement attendu pour '{section}'"
    section_warnings = [w for w in warnings if section in w]
    assert len(section_warnings) == 1


# ---------------------------------------------------------------------------
# validate_note — chapitrage hors bornes
# ---------------------------------------------------------------------------

def _note_with_n_chapters(n: int) -> str:
    rows = "\n".join(f"| {i} | Bloc {i} | 00:0{i % 10}:00 | lien |" for i in range(1, n + 1))
    return _valid_note().replace(
        "\n".join(f"| {i} | Bloc {i} | 00:0{i}:00 | [▶](https://youtu.be/X?t={i*60}) |" for i in range(1, 7)),
        rows,
    )


def test_chapter_count_5_produces_warning():
    note = _note_with_n_chapters(5)
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Chapitrage incomplet" in w for w in warnings)


def test_chapter_count_6_no_warning():
    _, warnings = validate_note(_valid_note())
    assert not any("Chapitrage" in w for w in warnings)


def test_chapter_count_13_produces_warning():
    note = _note_with_n_chapters(13)
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Chapitrage trop détaillé" in w for w in warnings)


def test_chapter_count_12_no_warning():
    note = _note_with_n_chapters(12)
    _, warnings = validate_note(note)
    assert not any("Chapitrage" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_note — concepts insuffisants
# ---------------------------------------------------------------------------

def test_concepts_2_produces_warning():
    # Retire le 3e concept en supprimant "Concept 3"
    note = _valid_note().replace(
        "#### Concept 3 [▶ 00:03:00](https://youtu.be/X?t=180)\n**Définition selon l'auteur** : def 3.",
        "",
    )
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Concepts insuffisants" in w for w in warnings)


def test_concepts_3_no_warning():
    _, warnings = validate_note(_valid_note())
    assert not any("Concepts" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_note — formulations notables
# ---------------------------------------------------------------------------

def test_no_formulation_produces_warning():
    note = _valid_note().replace('> "Citation exacte de l\'auteur."', "")
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("formulation notable" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_note — section "Mes notes"
# ---------------------------------------------------------------------------

def test_mes_notes_generated_content_produces_warning():
    note = _valid_note().replace("*(espace libre)*", "Contenu généré par le LLM.")
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Mes notes" in w for w in warnings)


def test_mes_notes_exact_placeholder_no_warning():
    _, warnings = validate_note(_valid_note())
    assert not any("Mes notes" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_note — transcript
# ---------------------------------------------------------------------------

def test_transcript_marker_absent_produces_warning():
    note = _valid_note().replace("<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->", "")
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Transcript horodaté complet absent" in w for w in warnings)


def test_transcript_marker_present_no_segments_produces_warning():
    note = _valid_note().replace(
        "[00:00:00] premier segment\n[00:01:00] deuxième segment",
        "",
    )
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("Transcript présent mais vide" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_note — liens ?t=
# ---------------------------------------------------------------------------

def test_no_timestamp_link_produces_warning():
    # Remplace tous les ?t= par ?x= pour casser les liens
    note = _valid_note().replace("?t=", "?x=")
    is_valid, warnings = validate_note(note)
    assert is_valid is False
    assert any("lien horodaté" in w for w in warnings)


# ---------------------------------------------------------------------------
# build_warning_header
# ---------------------------------------------------------------------------

def test_build_warning_header_empty():
    assert build_warning_header([]) == ""


def test_build_warning_header_single():
    result = build_warning_header(["Section manquante : Thèse centrale"])
    assert "Section manquante : Thèse centrale" in result
    assert result.startswith("⚠️")
    assert result.count("- ") == 1


def test_build_warning_header_multiple():
    warnings = ["Avertissement 1", "Avertissement 2", "Avertissement 3"]
    result = build_warning_header(warnings)
    assert result.count("- ") == 3
    for w in warnings:
        assert w in result
