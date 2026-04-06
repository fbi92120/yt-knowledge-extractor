from __future__ import annotations

"""Provider LLM Anthropic (Claude API).

Utilise l'API Messages d'Anthropic.
"""

from src.llm.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    """Provider Anthropic Claude via API REST."""

    CONTEXT_WINDOWS = {
        "claude-sonnet-4-20250514": 200000,
        "claude-haiku-4-5-20251001": 200000,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API Anthropic et retourne la réponse."""
        raise NotImplementedError("À implémenter (même pattern que Groq)")
