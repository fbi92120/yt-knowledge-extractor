from __future__ import annotations

"""Provider LLM Ollama (local).

Utilise l'API REST locale d'Ollama.
Endpoint par défaut : http://localhost:11434/api/generate
"""

from src.llm.base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Provider Ollama local via API REST."""

    CONTEXT_WINDOWS = {
        "default": 8192,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API Ollama locale et retourne la réponse."""
        raise NotImplementedError("À implémenter (même pattern que Groq)")
