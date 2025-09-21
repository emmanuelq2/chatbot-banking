"""Conversation orchestration for the banking assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Sequence

from .configuration import load_intents
from .exceptions import HandlerNotFoundError
from .handlers import (
    AccountOpeningHandler,
    AdvisorMessagingHandler,
    BaseHandler,
    HandlerResult,
    MoneyTransferHandler,
)
from .router import IntentRouter
from .services import AccountService, AdvisorMessagingService, TransferService
from .state import ConversationState


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "intents.json"


class ChatbotEngine:
    """Routes user utterances to the appropriate banking flow."""

    cancel_keywords = {"cancel", "stop", "start over", "nevermind", "never mind"}

    def __init__(
        self,
        *,
        account_service: AccountService,
        transfer_service: TransferService,
        advisor_service: AdvisorMessagingService,
        config_path: Optional[Path] = None,
        state: Optional[ConversationState] = None,
    ) -> None:
        self.state = state or ConversationState()
        self._intents = load_intents(config_path or DEFAULT_CONFIG_PATH)
        self._router = IntentRouter(self._intents)
        self._handlers: Dict[str, BaseHandler] = self._build_handlers(
            account_service=account_service,
            transfer_service=transfer_service,
            advisor_service=advisor_service,
        )

    def _build_handlers(
        self,
        *,
        account_service: AccountService,
        transfer_service: TransferService,
        advisor_service: AdvisorMessagingService,
    ) -> Dict[str, BaseHandler]:
        account_types: Sequence[str] = ()
        for intent in self._intents:
            if intent.handler == "account_opening":
                account_types = intent.entities.get("account_type", ())
                break
        if not account_types:
            account_types = ("checking", "savings")
        return {
            "account_opening": AccountOpeningHandler(account_service, account_types=account_types),
            "money_transfer": MoneyTransferHandler(transfer_service),
            "advisor_message": AdvisorMessagingHandler(advisor_service),
        }

    def handle_message(self, utterance: str) -> str:
        """Process a user utterance and return the assistant's reply."""

        normalized = utterance.strip()
        if not normalized:
            return "Could you share more detail so I can help?"

        if normalized.lower() in self.cancel_keywords:
            self.state.reset()
            return "Okay, I've canceled the current request. How else can I help?"

        if self.state.active:
            rerouted = self._maybe_reroute(utterance)
            if rerouted is not None:
                return rerouted

        handler, result = self._route_to_handler(utterance)

        if result.completed:
            self.state.reset()
        return result.reply

    def _route_to_handler(self, utterance: str) -> tuple[Optional[BaseHandler], HandlerResult]:
        if not self.state.active:
            intent = self._router.match(utterance)
            if intent is None:
                return None, HandlerResult("I'm not sure how to help with that just yet, but I can open accounts, transfer funds, or message your advisor.", error=True)
            handler = self._handlers.get(intent.handler)
            if handler is None:
                raise HandlerNotFoundError(f"No handler registered for key '{intent.handler}'")
            result = handler.start(self.state)
            return handler, result

        handler = self._handlers.get(self.state.handler_key or "")
        if handler is None:
            self.state.reset()
            raise HandlerNotFoundError(f"Active handler '{self.state.handler_key}' is not registered")
        result = handler.handle(utterance, self.state)
        return handler, result

    def _maybe_reroute(self, utterance: str) -> Optional[str]:
        """Check if the utterance looks like a new intent and reroute if needed."""

        intent = self._router.match(utterance)
        if intent and intent.handler != self.state.handler_key:
            handler = self._handlers.get(intent.handler)
            if handler is None:
                raise HandlerNotFoundError(f"No handler registered for key '{intent.handler}'")
            self.state.reset()
            result = handler.start(self.state)
            if result.completed:
                self.state.reset()
            return result.reply
        return None
