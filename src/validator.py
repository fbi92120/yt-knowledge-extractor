from __future__ import annotations

"""Validation de la structure de la fiche générée.

Vérifie les sections obligatoires, les minimums (chapitrage,
concepts, citations) et les contraintes (section "Mes notes" vide,
transcript présent, liens horodatés valides).

Ne bloque jamais l'écriture — retourne des avertissements.
"""

import re


REQUIRED_SECTIONS = [
    "Thèse centrale",
    "Chapitrage inféré",
    "Carte des idées",
    "Concepts clés",
    "Formulations notables",
    "Questions ouvertes",
    "Mes notes",
    "Sources & références",
]


def validate_note(content: str) -> tuple[bool, list[str]]:
    """Valide la structure de la fiche générée.

    Returns:
        (is_valid, warnings) — is_valid=True si aucun avertissement
    """
    warnings = []

    # 1. Sections obligatoires
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in content:
            warnings.append(f"Section manquante : {section}")

    # 2. Chapitrage : entre 6 et 12 lignes dans le tableau
    chapter_rows = re.findall(r"^\|\s*\d+\s*\|", content, re.MULTILINE)
    if len(chapter_rows) < 6:
        warnings.append(
            f"Chapitrage incomplet : {len(chapter_rows)} blocs détectés, minimum 6 attendus."
        )
    elif len(chapter_rows) > 12:
        warnings.append(
            f"Chapitrage trop détaillé : {len(chapter_rows)} blocs détectés, maximum 12 attendus."
        )

    # 3. Au moins 3 concepts
    concepts = re.findall(r"^#{3,4}\s+.+\[▶", content, re.MULTILINE)
    if len(concepts) < 3:
        warnings.append(
            f"Concepts insuffisants : {len(concepts)} détectés, minimum 3 attendus."
        )

    # 4. Au moins 1 formulation notable
    quotes = re.findall(r'^>\s*"', content, re.MULTILINE)
    if len(quotes) < 1:
        warnings.append("Aucune formulation notable détectée.")

    # 5. Section "Mes notes" ne contient que le placeholder
    mes_notes_match = re.search(
        r"## Mes notes\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
    )
    if mes_notes_match:
        notes_content = mes_notes_match.group(1).strip()
        if notes_content and notes_content != "*(espace libre)*":
            warnings.append(
                "Section 'Mes notes' contient du contenu généré (devrait être vide)."
            )

    # 6. Transcript complet présent après ---
    if "<!-- TRANSCRIPT HORODATÉ COMPLET" not in content:
        warnings.append("Transcript horodaté complet absent.")
    else:
        after_marker = content.split("<!-- TRANSCRIPT HORODATÉ COMPLET")[1]
        transcript_lines = re.findall(r"^\[[\d:]+\]", after_marker, re.MULTILINE)
        if len(transcript_lines) < 1:
            warnings.append("Transcript présent mais vide (aucun segment horodaté).")

    # 7. Au moins 1 lien ?t= valide
    time_links = re.findall(r"\?t=(\d+)", content)
    if len(time_links) < 1:
        warnings.append("Aucun lien horodaté (?t=) détecté.")

    return (len(warnings) == 0, warnings)


def build_warning_header(warnings: list[str]) -> str:
    """Formate les avertissements pour insertion en tête de fiche.

    Returns:
        Bloc d'avertissements formaté ou chaîne vide
    """
    if not warnings:
        return ""

    lines = ["⚠️ **AVERTISSEMENTS DE VALIDATION**\n"]
    for w in warnings:
        lines.append(f"- {w}")
    lines.append("\n---\n")
    return "\n".join(lines)
