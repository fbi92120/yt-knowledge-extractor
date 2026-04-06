from __future__ import annotations

"""Test de smoke — vérifie le pipeline complet sur une URL de référence.

URL de référence : https://youtu.be/T_GqhyYqTD4
Chaîne : @SamouraiDansant
Transcript FR auto-généré disponible.

Vérifie que le fichier .md est créé et non vide.
"""


def test_smoke_generates_file(generated_note_path):
    """Le pipeline complet génère un fichier .md non vide."""
    assert generated_note_path.exists(), f"Fichier non créé : {generated_note_path}"
    assert generated_note_path.suffix == ".md"
    assert generated_note_path.stat().st_size > 0, "Fichier vide"
