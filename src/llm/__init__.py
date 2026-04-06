from __future__ import annotations

"""LLM providers — abstraction multi-provider pour la génération de fiches."""

import importlib

PROVIDERS = {
    "groq": "src.llm.groq.GroqProvider",
    "gemini": "src.llm.gemini.GeminiProvider",
    "anthropic": "src.llm.anthropic.AnthropicProvider",
    "openai": "src.llm.openai.OpenAIProvider",
    "ollama": "src.llm.ollama.OllamaProvider",
}


def get_provider(provider_name: str, model: str, api_key: str | None = None):
    """Factory — retourne le provider LLM configuré.

    Args:
        provider_name: clé du provider (groq, anthropic, openai, ollama)
        model: nom du modèle à utiliser
        api_key: clé API (None pour ollama)

    Returns:
        Instance de LLMProvider

    Raises:
        ValueError: si le provider n'est pas reconnu
    """
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Provider inconnu : '{provider_name}'. "
            f"Providers disponibles : {', '.join(PROVIDERS.keys())}"
        )

    module_path, class_name = PROVIDERS[provider_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)
    return provider_class(model=model, api_key=api_key)
