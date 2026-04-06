from __future__ import annotations

"""Interface abstraite pour les providers LLM.

Définit le contrat que chaque provider (Groq, Anthropic, OpenAI, Ollama)
doit respecter : génération de texte, estimation de tokens,
et validation de la fenêtre de contexte.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Réponse structurée d'un provider LLM."""

    content: str    # texte généré
    model: str      # modèle utilisé
    usage: dict     # {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}


class ContextTooLargeError(Exception):
    """Levée quand le transcript dépasse la fenêtre de contexte du modèle."""
    pass


class LLMAPIError(Exception):
    """Levée sur erreur API du provider LLM."""
    pass


COMPLETION_BUFFER = 4000


class LLMProvider(ABC):
    """Classe abstraite pour tous les providers LLM."""

    CONTEXT_WINDOWS: dict[str, int] = {}

    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Envoie les prompts au LLM et retourne la réponse structurée."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimation conservative du nombre de tokens.

        Heuristique : len(text) / 3.5 pour le français.
        """
        return int(len(text) / 3.5)

    def validate_context_fit(self, system_prompt: str, user_prompt: str) -> None:
        """Vérifie que les prompts tiennent dans la fenêtre de contexte.

        Raises:
            ContextTooLargeError: si les prompts + buffer dépassent la fenêtre
        """
        context_window = self.CONTEXT_WINDOWS.get(self.model)
        if context_window is None:
            return

        prompt_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_prompt)
        available = context_window - COMPLETION_BUFFER
        if prompt_tokens > available:
            raise ContextTooLargeError(
                f"Transcript trop long pour {self.model}.\n"
                f"Tokens estimés : {prompt_tokens}\n"
                f"Fenêtre disponible : {available} (contexte {context_window} − buffer {COMPLETION_BUFFER})\n"
                f"Réduisez le transcript ou utilisez un modèle avec une fenêtre plus large."
            )
