from __future__ import annotations

from typing import Iterable, Optional

from .configuration import IntentConfig


class IntentRouter:
    """Very small keyword-based intent router."""

    def __init__(self, intents: Iterable[IntentConfig]):
        self._intents = list(intents)

    def match(self, utterance: str) -> Optional[IntentConfig]:
        """Return the first matching intent for ``utterance``."""

        if not utterance:
            return None

        cleaned = utterance.lower()
        for intent in self._intents:
            for keyword in intent.keywords:
                if keyword in cleaned:
                    return intent
        return None
