"""Conversation state management utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ConversationState:
    """Tracks the state of an ongoing conversation."""

    intent_name: Optional[str] = None
    handler_key: Optional[str] = None
    step: Optional[str] = None
    slots: Dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        """Reset the conversation to its initial state."""

        self.intent_name = None
        self.handler_key = None
        self.step = None
        self.slots.clear()

    @property
    def active(self) -> bool:
        """Return ``True`` if the conversation is within a flow."""

        return self.intent_name is not None and self.handler_key is not None
