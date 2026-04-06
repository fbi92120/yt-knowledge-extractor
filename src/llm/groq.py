from __future__ import annotations

"""Provider LLM Groq — provider par défaut (gratuit).

Utilise l'API REST OpenAI-compatible de Groq.
Endpoint : https://api.groq.com/openai/v1/chat/completions
"""

import requests

from src.llm.base import LLMProvider, LLMResponse, LLMAPIError


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """Provider Groq via API REST."""

    CONTEXT_WINDOWS = {
        "llama-3.3-70b-versatile": 128000,
        "llama-3.1-8b-instant": 131072,
        "gemma2-9b-it": 8192,
        "mixtral-8x7b-32768": 32768,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API Groq et retourne la réponse."""
        self.validate_context_fit(system_prompt, user_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
        }

        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise LLMAPIError(f"Erreur API Groq : {e}")

        data = resp.json()

        try:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
        except (KeyError, IndexError) as e:
            raise LLMAPIError(f"Réponse Groq inattendue : {e}")

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )
