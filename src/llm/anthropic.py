from __future__ import annotations

"""Provider LLM Anthropic (Claude API).

Utilise l'API Messages d'Anthropic.
Endpoint : https://api.anthropic.com/v1/messages
"""

import requests

from src.llm.base import LLMProvider, LLMResponse, LLMAPIError


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
MAX_TOKENS = 8192


class AnthropicProvider(LLMProvider):
    """Provider Anthropic Claude via API REST."""

    CONTEXT_WINDOWS = {
        "claude-haiku-4-5": 200000,
        "claude-haiku-4-5-20251001": 200000,
        "claude-sonnet-4-20250514": 200000,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API Anthropic et retourne la réponse."""
        self.validate_context_fit(system_prompt, user_prompt)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
        }

        try:
            resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            body = resp.text if "resp" in dir() else ""
            raise LLMAPIError(f"Erreur API Anthropic : {e}\nRéponse : {body}")

        data = resp.json()

        try:
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
        except (KeyError, IndexError) as e:
            raise LLMAPIError(f"Réponse Anthropic inattendue : {e}")

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        )
