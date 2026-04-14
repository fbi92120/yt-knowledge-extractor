from __future__ import annotations

"""Tests unitaires — src/llm/ (sans appel réseau)."""

import pytest

from src.llm import get_provider, PROVIDERS
from src.llm.base import LLMProvider, ContextTooLargeError, COMPLETION_BUFFER
from src.llm.groq import GroqProvider
from src.llm.gemini import GeminiProvider
from src.llm.anthropic import AnthropicProvider
from src.llm.openai import OpenAIProvider
from src.llm.ollama import OllamaProvider


# ---------------------------------------------------------------------------
# get_provider — factory
# ---------------------------------------------------------------------------

def test_get_provider_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Provider inconnu"):
        get_provider("inexistant", model="x")


def test_get_provider_unknown_lists_available_providers():
    with pytest.raises(ValueError) as exc:
        get_provider("inexistant", model="x")
    for name in PROVIDERS.keys():
        assert name in str(exc.value)


def test_get_provider_groq_returns_correct_class():
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="test")
    assert isinstance(provider, GroqProvider)


def test_get_provider_gemini_returns_correct_class():
    provider = get_provider("gemini", model="gemini-2.0-flash", api_key="test")
    assert isinstance(provider, GeminiProvider)


def test_get_provider_anthropic_returns_correct_class():
    provider = get_provider("anthropic", model="claude-3-5-haiku-20241022", api_key="test")
    assert isinstance(provider, AnthropicProvider)


def test_get_provider_openai_returns_correct_class():
    provider = get_provider("openai", model="gpt-4o", api_key="test")
    assert isinstance(provider, OpenAIProvider)


def test_get_provider_ollama_returns_correct_class():
    provider = get_provider("ollama", model="llama3", api_key=None)
    assert isinstance(provider, OllamaProvider)


def test_get_provider_stores_model():
    provider = get_provider("groq", model="llama-3.1-8b-instant", api_key="k")
    assert provider.model == "llama-3.1-8b-instant"


def test_get_provider_stores_api_key():
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="my-key")
    assert provider.api_key == "my-key"


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------

def test_estimate_tokens_empty_string():
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="test")
    assert provider.estimate_tokens("") == 0


def test_estimate_tokens_350_chars_gives_100_tokens():
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="test")
    assert provider.estimate_tokens("a" * 350) == 100  # int(350 / 3.5)


def test_estimate_tokens_truncates_not_rounds():
    """int() tronque — 7 chars → int(7/3.5) = int(2.0) = 2."""
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="test")
    assert provider.estimate_tokens("a" * 7) == 2


# ---------------------------------------------------------------------------
# validate_context_fit
# ---------------------------------------------------------------------------

def test_validate_context_fit_unknown_model_no_error():
    """Modèle absent de CONTEXT_WINDOWS → aucune erreur."""
    provider = get_provider("groq", model="modele-inconnu", api_key="test")
    provider.validate_context_fit("system", "user")  # pas de raise


def test_validate_context_fit_short_prompt_no_error():
    """Court prompt → tient dans toutes les fenêtres."""
    provider = get_provider("groq", model="llama-3.3-70b-versatile", api_key="test")
    provider.validate_context_fit("court", "prompt")  # pas de raise


def test_validate_context_fit_exactly_at_limit_no_error():
    """Exactement à la limite → pas d'erreur (condition strictement >)."""
    # gemma2-9b-it : 8192 tokens, buffer 4000 → 4192 disponibles
    provider = get_provider("groq", model="gemma2-9b-it", api_key="test")
    available = GroqProvider.CONTEXT_WINDOWS["gemma2-9b-it"] - COMPLETION_BUFFER  # 4192
    # int(len / 3.5) == available → len = int(available * 3.5)
    text = "a" * int(available * 3.5)  # 14672 chars → 4192 tokens
    provider.validate_context_fit(text, "")  # pas de raise


def test_validate_context_fit_one_token_above_raises():
    """1 token au-dessus de la limite → ContextTooLargeError."""
    provider = get_provider("groq", model="gemma2-9b-it", api_key="test")
    available = GroqProvider.CONTEXT_WINDOWS["gemma2-9b-it"] - COMPLETION_BUFFER  # 4192
    # 4 chars supplémentaires → int((14672+4) / 3.5) = int(4193.14) = 4193 > 4192
    text = "a" * (int(available * 3.5) + 4)
    with pytest.raises(ContextTooLargeError):
        provider.validate_context_fit(text, "")


def test_validate_context_fit_error_mentions_model():
    """Le message d'erreur mentionne le nom du modèle."""
    provider = get_provider("groq", model="gemma2-9b-it", api_key="test")
    available = GroqProvider.CONTEXT_WINDOWS["gemma2-9b-it"] - COMPLETION_BUFFER
    text = "a" * (int(available * 3.5) + 4)
    with pytest.raises(ContextTooLargeError, match="gemma2-9b-it"):
        provider.validate_context_fit(text, "")


def test_validate_context_fit_error_mentions_token_counts():
    """Le message d'erreur mentionne les tokens estimés et la fenêtre disponible."""
    provider = get_provider("groq", model="gemma2-9b-it", api_key="test")
    available = GroqProvider.CONTEXT_WINDOWS["gemma2-9b-it"] - COMPLETION_BUFFER
    text = "a" * (int(available * 3.5) + 4)
    with pytest.raises(ContextTooLargeError) as exc:
        provider.validate_context_fit(text, "")
    msg = str(exc.value)
    assert "Tokens estimés" in msg
    assert "Fenêtre disponible" in msg
