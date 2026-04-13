from __future__ import annotations

"""Test de structure — vérifie la conformité de la fiche générée.

Vérifications (SPECS.md Bloc 5) :
1. 8 sections obligatoires présentes
2. Chapitrage : entre 6 et 12 lignes
3. Au moins 3 concepts
4. Au moins 1 formulation notable
5. Section "Mes notes" vide (placeholder uniquement)
6. Transcript complet présent après ---
7. Au moins 1 lien ?t= valide
8. Sous-sections 'Questions ouvertes' présentes
   (### Soulevées dans la vidéo et ### Ouvertures suggérées)
"""

import re

from src.validator import REQUIRED_SECTIONS


def test_required_sections_present(generated_note_content):
    """Les 8 sections obligatoires sont présentes."""
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in generated_note_content, f"Section manquante : {section}"


def test_chapter_table_rows(generated_note_content):
    """Le tableau de chapitrage contient entre 6 et 12 lignes."""
    rows = re.findall(r"^\|\s*\d+\s*\|", generated_note_content, re.MULTILINE)
    assert 6 <= len(rows) <= 12, f"Chapitrage hors bornes : {len(rows)} blocs (attendu 6-12)"


def test_minimum_concepts(generated_note_content):
    """Au moins 3 concepts sont présents."""
    concepts = re.findall(r"^#{3,4}\s+.+\[▶", generated_note_content, re.MULTILINE)
    assert len(concepts) >= 3, f"Concepts insuffisants : {len(concepts)} (minimum 3)"


def test_notable_formulations(generated_note_content):
    """Au moins 1 formulation notable est présente."""
    quotes = re.findall(r'^>\s*["\u00ab]', generated_note_content, re.MULTILINE)
    assert len(quotes) >= 1, "Aucune formulation notable détectée"


def test_personal_notes_empty(generated_note_content):
    """La section 'Mes notes' ne contient que le placeholder."""
    match = re.search(
        r"## Mes notes\s*\n(.*?)(?=\n## |\n---|\Z)",
        generated_note_content,
        re.DOTALL,
    )
    assert match is not None, "Section 'Mes notes' absente"
    content = match.group(1).strip()
    assert content == "*(espace libre)*", f"'Mes notes' non vide : {content!r}"


def test_transcript_present(generated_note_content):
    """Le transcript complet est présent après le séparateur ---."""
    assert "<!-- TRANSCRIPT HORODATÉ COMPLET" in generated_note_content
    after = generated_note_content.split("<!-- TRANSCRIPT HORODATÉ COMPLET")[1]
    lines = re.findall(r"^\[[\d:]+\]", after, re.MULTILINE)
    assert len(lines) > 0, "Transcript présent mais aucun segment horodaté"


def test_valid_timestamp_links(generated_note_content):
    """Au moins 1 lien ?t= avec un format numérique valide."""
    links = re.findall(r"\?t=(\d+)", generated_note_content)
    assert len(links) >= 1, "Aucun lien horodaté (?t=) détecté"


def test_open_questions_subsections(generated_note_content):
    """Les deux sous-sections de 'Questions ouvertes' sont présentes."""
    assert "### Soulevées dans la vidéo" in generated_note_content, \
        "Sous-section manquante : '### Soulevées dans la vidéo'"
    assert "### Ouvertures suggérées" in generated_note_content, \
        "Sous-section manquante : '### Ouvertures suggérées'"
