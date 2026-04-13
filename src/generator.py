from __future__ import annotations

"""Génération de la fiche de connaissance via LLM.

Orchestre la construction du prompt système et utilisateur,
appelle le provider LLM configuré, et assemble la fiche
Markdown complète incluant le transcript horodaté.
"""

from datetime import date

from src.llm import get_provider
from src.metadata import filter_sources


SYSTEM_PROMPT_TEMPLATE = """\
You are a knowledge extraction assistant. Your task is to analyze
a YouTube video transcript and produce a structured knowledge note
in {output_language}.

## Output structure — follow exactly, in this order

### 1. Header (do not label this section)
# [Video title]
**URL** : {url} · **Channel** : {channel} · **Processed** : {date} · **Duration** : {duration} · **Model** : {model}

### 2. Central thesis
## Thèse centrale
3 to 5 sentences. What is the video's main argument or position?
What idea does the author defend from start to finish?

Each sentence must reflect a position explicitly stated in this transcript.
A thesis that could describe another video on the same topic is a failure.

The thesis must capture the author's specific argument or provocation — not a description of the topic.
Ask yourself: what does the author DEFEND or ARGUE, not what the video is ABOUT.
Bad example: "This video discusses the crisis of the knowledge economy due to AI."
Good example: "The knowledge economy is dead. The author argues we must transition to an economy of judgment where human value lies in discernment, not accumulation."

### 3. Inferred chapter breakdown
## Chapitrage inféré
A markdown table with 6 to 12 thematic blocks.
Columns: # | Bloc thématique | Début | Lien direct

Rules:
- Infer the structure from the content — there is no predefined outline.
- If native YouTube chapters are provided in {chapters}, use them as a base and refine.
- Format timestamps as HH:MM:SS.
- Generate direct links as: https://youtu.be/{video_id}?t={{seconds}}
- Choose granularity based on content density (6 blocks minimum, 12 maximum).

### 4. Idea map
## Carte des idées
A narrative paragraph (not a list) describing how the arguments connect.
Include inline timestamps at key transitions: [▶ HH:MM:SS](link)
Show the logical progression: what the author starts from,
what tension or problem is identified, how it is resolved or concluded.

### 5. Key concepts
## Concepts clés
For each significant concept identified in the video:

#### [Concept name] [▶ HH:MM:SS](link)
**Définition selon l'auteur** : how the author defines it in their own words — never a generic definition.
**Exemple utilisé** : the specific example the author uses to illustrate the concept.

Minimum 3 concepts required.
If fewer than 3 are identifiable, prepend the entire output with:
⚠️ AVERTISSEMENT : moins de 3 concepts identifiés dans cette vidéo.

### 6. Notable formulations
## Formulations notables
Direct quotes from the transcript, reproduced verbatim — never paraphrased.

Format:
> "Exact quote as spoken"
> [▶ HH:MM:SS](link)

### 7. Open questions
## Questions ouvertes

### Soulevées dans la vidéo
Questions explicitly raised or left unanswered by the author.
Each question must reference the transcript segment where the tension appears: [▶ HH:MM:SS](link)
No anchor identifiable : omit.

### Ouvertures suggérées
Implications or "what next?" questions the content surfaces beyond what the author states.
These are interpretive — label each one with [inférence] (square brackets, no asterisks).
Never project from assumed user profile or topic category.

### 8. Personal notes
## Mes notes
*(espace libre)*

DO NOT generate any content in this section.
Leave only the heading and the italic placeholder exactly as shown above.
The placeholder must be exactly: *(espace libre)*
Do not split it, do not add spaces inside the asterisks.

### 9. Sources and references
## Sources & références
Filtered from the YouTube video description provided in {description}.

Include ONLY sources with an identifiable author or title:
books, articles, studies, named websites, named tools.

Ignore: social media links, generic URLs, sponsor mentions,
channel promotion, affiliate links, timestamps-only references.

Format: - [Title or author name](URL)

If no qualifying sources are found: write exactly "Aucune source identifiée."

## Absolute rules — never violate these
1. Never invent a timestamp. If you cannot anchor an element, omit the timestamp rather than approximating.
2. Notable quotes must be verbatim from the transcript. Never paraphrase a citation.
3. Concept definitions must reflect the author's own usage, never a generic or Wikipedia definition.
4. Do not generate any content for "Mes notes". Leave it empty.
5. Read the full transcript before structuring. Do not process by chunks.
6. The sources section contains only items from {description}, never invented references.

IMPORTANT: Do NOT include section 10 (transcript). It will be appended automatically after your response.\
"""


def build_system_prompt(
    output_language: str,
    url: str,
    channel: str,
    processed_date: str,
    duration: str,
    video_id: str,
    chapters: list[dict] | None,
    description: str,
    model: str,
) -> str:
    """Construit le prompt système depuis le template SPECS.md Bloc 3."""
    chapters_str = "None (infer from content)" if not chapters else str(chapters)
    return SYSTEM_PROMPT_TEMPLATE.format(
        output_language=output_language,
        url=url,
        channel=channel,
        date=processed_date,
        duration=duration,
        video_id=video_id,
        chapters=chapters_str,
        description=description,
        model=model,
    )


def build_user_prompt(formatted_transcript: str, filtered_sources: str) -> str:
    """Assemble le prompt utilisateur avec transcript + sources filtrées."""
    parts = ["## Transcript complet\n", formatted_transcript]
    if filtered_sources:
        parts.append("\n\n## Sources extraites de la description\n")
        parts.append(filtered_sources)
    return "\n".join(parts)


def generate_note(
    config: dict,
    video_id: str,
    url: str,
    metadata: dict,
    transcript_segments: list[dict],
    formatted_transcript: str,
) -> str:
    """Orchestre la génération complète de la fiche.

    1. Charge le provider LLM
    2. Construit les prompts
    3. Valide la fenêtre de contexte
    4. Appelle le LLM
    5. Ajoute le transcript horodaté programmatiquement (section 10)

    Returns:
        Contenu Markdown complet de la fiche
    """
    llm_config = config["llm"]
    provider = get_provider(
        provider_name=llm_config["provider"],
        model=llm_config["model"],
        api_key=llm_config.get("api_key"),
    )

    filtered_sources = filter_sources(metadata["description"])

    system_prompt = build_system_prompt(
        output_language=config.get("output_language", "fr"),
        url=url,
        channel=metadata["channel"],
        processed_date=date.today().isoformat(),
        duration=metadata["duration"],
        video_id=video_id,
        chapters=metadata["chapters"],
        description=metadata["description"],
        model=llm_config["model"],
    )

    user_prompt = build_user_prompt(formatted_transcript, filtered_sources)

    # validate_context_fit est appelé dans provider.generate()
    response = provider.generate(system_prompt, user_prompt)

    # Section 10 : transcript horodaté ajouté programmatiquement
    note = response.content.rstrip()
    note += "\n\n---\n<!-- TRANSCRIPT HORODATÉ COMPLET — réservé v2 -->\n"
    note += formatted_transcript

    return note
