from __future__ import annotations

"""Provider LLM OpenAI.

Utilise l'API Chat Completions d'OpenAI.
"""

from src.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """Provider OpenAI via API REST."""

    CONTEXT_WINDOWS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API OpenAI et retourne la réponse."""
        raise NotImplementedError("À implémenter (même pattern que Groq)")
