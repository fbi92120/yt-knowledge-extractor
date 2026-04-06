from __future__ import annotations

"""Provider LLM Google Gemini.

Utilise l'API REST Google Generative Language.
Endpoint : https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
"""

import requests

from src.llm.base import LLMProvider, LLMResponse, LLMAPIError


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """Provider Google Gemini via API REST."""

    CONTEXT_WINDOWS = {
        "gemini-2.5-flash": 1_048_576,
        "gemini-2.5-pro": 1_048_576,
        "gemini-2.0-flash": 1_048_576,
        "gemini-2.0-flash-lite": 1_048_576,
    }

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Appelle l'API Gemini et retourne la réponse."""
        self.validate_context_fit(system_prompt, user_prompt)

        url = f"{GEMINI_API_BASE}/{self.model}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            body = resp.text if "resp" in dir() else ""
            raise LLMAPIError(f"Erreur API Gemini : {e}\nRéponse : {body}")

        data = resp.json()

        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
        except (KeyError, IndexError) as e:
            raise LLMAPIError(f"Réponse Gemini inattendue : {e} — data={data}")

        return LLMResponse(
            content=content,
            model=self.model,
            usage={
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            },
        )
