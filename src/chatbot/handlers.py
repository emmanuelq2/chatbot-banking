"""Intent handlers for the conversational banking assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .services import AccountService, AdvisorMessagingService, TransferService
from .state import ConversationState


@dataclass
class HandlerResult:
    """Represents the outcome of a handler invocation."""

    reply: str
    completed: bool = False
    error: bool = False


class BaseHandler:
    """Common logic shared by concrete handlers."""

    intent_name: str
    handler_key: str

    def start(self, state: ConversationState) -> HandlerResult:
        state.intent_name = self.intent_name
        state.handler_key = self.handler_key
        state.step = self.first_step
        state.slots.clear()
        return self._prompt_for_current_step(state)

    @property
    def first_step(self) -> str:  # pragma: no cover - abstract property
        raise NotImplementedError

    def handle(self, utterance: str, state: ConversationState) -> HandlerResult:  # pragma: no cover - abstract method
        raise NotImplementedError

    def _prompt_for_current_step(self, state: ConversationState) -> HandlerResult:
        raise NotImplementedError  # pragma: no cover - implemented by subclasses


class AccountOpeningHandler(BaseHandler):
    """Guides the user through opening a new account."""

    intent_name = "account_opening"
    handler_key = "account_opening"

    def __init__(self, service: AccountService, *, account_types: Iterable[str]):
        self._service = service
        normalized = [account_type.lower() for account_type in account_types]
        self._account_types = tuple(dict.fromkeys(normalized))

    @property
    def first_step(self) -> str:
        return "collect_full_name"

    def _prompt_for_current_step(self, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_full_name":
            return HandlerResult("Sure, let's open a new account. What's your full name?")
        if step == "collect_account_type":
            choices = ", ".join(account_type.title() for account_type in self._account_types)
            return HandlerResult(f"Thanks. What type of account would you like to open? Options: {choices}.")
        if step == "collect_initial_deposit":
            return HandlerResult("Got it. How much would you like to deposit to get started?")
        if step == "confirm_submission":
            summary = (
                f"Open a {state.slots['account_type'].title()} account for {state.slots['full_name']} "
                f"with an initial deposit of ${state.slots['initial_deposit']:.2f}."
            )
            return HandlerResult(summary + " Does everything look correct? (yes/no)")
        return HandlerResult("I'm not sure what to ask next. Let's start over.", error=True, completed=True)

    def handle(self, utterance: str, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_full_name":
            return self._handle_full_name(utterance, state)
        if step == "collect_account_type":
            return self._handle_account_type(utterance, state)
        if step == "collect_initial_deposit":
            return self._handle_initial_deposit(utterance, state)
        if step == "confirm_submission":
            return self._handle_confirmation(utterance, state)
        return HandlerResult("Let's restart that account application.", completed=True, error=True)

    def _handle_full_name(self, utterance: str, state: ConversationState) -> HandlerResult:
        full_name = utterance.strip()
        if not full_name:
            return HandlerResult("I didn't catch your name. Could you share your full name?", error=True)
        state.slots["full_name"] = full_name
        state.step = "collect_account_type"
        return self._prompt_for_current_step(state)

    def _handle_account_type(self, utterance: str, state: ConversationState) -> HandlerResult:
        account_type = utterance.strip().lower()
        if account_type not in self._account_types:
            choices = ", ".join(account_type.title() for account_type in self._account_types)
            return HandlerResult(
                f"I didn't recognize that account type. Please choose one of the following: {choices}.",
                error=True,
            )
        state.slots["account_type"] = account_type
        state.step = "collect_initial_deposit"
        return self._prompt_for_current_step(state)

    def _handle_initial_deposit(self, utterance: str, state: ConversationState) -> HandlerResult:
        cleaned = utterance.replace(",", "").strip()
        try:
            amount = float(cleaned)
        except ValueError:
            return HandlerResult("Please provide the deposit amount as a number.", error=True)
        if amount <= 0:
            return HandlerResult("The deposit amount must be greater than zero. How much would you like to deposit?", error=True)
        state.slots["initial_deposit"] = amount
        state.step = "confirm_submission"
        return self._prompt_for_current_step(state)

    def _handle_confirmation(self, utterance: str, state: ConversationState) -> HandlerResult:
        normalized = utterance.strip().lower()
        if normalized in {"yes", "y", "confirm"}:
            account_id = self._service.open_account(
                full_name=state.slots["full_name"],
                account_type=state.slots["account_type"],
                initial_deposit=state.slots["initial_deposit"],
            )
            return HandlerResult(
                f"All set! Your new account ({account_id}) is ready. Is there anything else I can help you with?",
                completed=True,
            )
        if normalized in {"no", "n", "cancel"}:
            return HandlerResult("No problem, I won't submit that application. Let me know if you need anything else.", completed=True)
        return HandlerResult("Please reply with yes or no so I know whether to submit the application.", error=True)


class MoneyTransferHandler(BaseHandler):
    """Handles fund transfer conversations."""

    intent_name = "money_transfer"
    handler_key = "money_transfer"

    def __init__(self, service: TransferService):
        self._service = service

    @property
    def first_step(self) -> str:
        return "collect_from_account"

    def _prompt_for_current_step(self, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_from_account":
            return HandlerResult("Sure thing. Which account should the money come from?")
        if step == "collect_to_account":
            return HandlerResult("Thanks. What account are we sending the funds to?")
        if step == "collect_amount":
            return HandlerResult("How much money should I transfer?")
        if step == "confirm_transfer":
            summary = (
                f"Transfer ${state.slots['amount']:.2f} from {state.slots['from_account']} "
                f"to {state.slots['to_account']}."
            )
            return HandlerResult(summary + " Does that look right? (yes/no)")
        return HandlerResult("I'm not sure how to proceed with that transfer. Let's start again.", completed=True, error=True)

    def handle(self, utterance: str, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_from_account":
            return self._handle_from_account(utterance, state)
        if step == "collect_to_account":
            return self._handle_to_account(utterance, state)
        if step == "collect_amount":
            return self._handle_amount(utterance, state)
        if step == "confirm_transfer":
            return self._handle_confirmation(utterance, state)
        return HandlerResult("Let's cancel that transfer for now.", completed=True, error=True)

    def _handle_from_account(self, utterance: str, state: ConversationState) -> HandlerResult:
        account = utterance.strip()
        if not account:
            return HandlerResult("I need the account number to continue. Which account should we use?", error=True)
        state.slots["from_account"] = account
        state.step = "collect_to_account"
        return self._prompt_for_current_step(state)

    def _handle_to_account(self, utterance: str, state: ConversationState) -> HandlerResult:
        account = utterance.strip()
        if not account:
            return HandlerResult("Please tell me where to send the money.", error=True)
        if account == state.slots.get("from_account"):
            return HandlerResult("The destination must be different from the source account. Where should the funds go?", error=True)
        state.slots["to_account"] = account
        state.step = "collect_amount"
        return self._prompt_for_current_step(state)

    def _handle_amount(self, utterance: str, state: ConversationState) -> HandlerResult:
        cleaned = utterance.replace(",", "").strip()
        try:
            amount = float(cleaned)
        except ValueError:
            return HandlerResult("I wasn't able to read that dollar amount. How much should I transfer?", error=True)
        if amount <= 0:
            return HandlerResult("The transfer amount must be greater than zero. How much should I move?", error=True)
        state.slots["amount"] = amount
        state.step = "confirm_transfer"
        return self._prompt_for_current_step(state)

    def _handle_confirmation(self, utterance: str, state: ConversationState) -> HandlerResult:
        normalized = utterance.strip().lower()
        if normalized in {"yes", "y", "confirm"}:
            transfer_id = self._service.transfer(
                from_account=state.slots["from_account"],
                to_account=state.slots["to_account"],
                amount=state.slots["amount"],
            )
            return HandlerResult(
                f"Done! Transfer {transfer_id} is complete. Anything else I can help with?",
                completed=True,
            )
        if normalized in {"no", "n", "cancel"}:
            return HandlerResult("Okay, I canceled that transfer. Let me know if you change your mind.", completed=True)
        return HandlerResult("Please respond with yes or no so I can complete the transfer.", error=True)


class AdvisorMessagingHandler(BaseHandler):
    """Handles secure messaging between the user and their advisor."""

    intent_name = "secure_advisor_message"
    handler_key = "advisor_message"

    def __init__(self, service: AdvisorMessagingService):
        self._service = service

    @property
    def first_step(self) -> str:
        return "collect_topic"

    def _prompt_for_current_step(self, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_topic":
            return HandlerResult("Happy to help. What would you like to discuss with your advisor?")
        if step == "collect_message":
            return HandlerResult("Great. What details should I include in the secure message?")
        if step == "confirm_message":
            preview = state.slots["message"]
            topic = state.slots["topic"]
            return HandlerResult(
                f"I'll send your advisor a message about '{topic}' saying: '{preview}'. Shall I send it now? (yes/no)"
            )
        return HandlerResult("I ran into an issue preparing that advisor message. Let's start over.", completed=True, error=True)

    def handle(self, utterance: str, state: ConversationState) -> HandlerResult:
        step = state.step
        if step == "collect_topic":
            return self._handle_topic(utterance, state)
        if step == "collect_message":
            return self._handle_message(utterance, state)
        if step == "confirm_message":
            return self._handle_confirmation(utterance, state)
        return HandlerResult("Let's try composing that message again later.", completed=True, error=True)

    def _handle_topic(self, utterance: str, state: ConversationState) -> HandlerResult:
        topic = utterance.strip()
        if not topic:
            return HandlerResult("Please share a short topic so your advisor knows what to expect.", error=True)
        state.slots["topic"] = topic
        state.step = "collect_message"
        return self._prompt_for_current_step(state)

    def _handle_message(self, utterance: str, state: ConversationState) -> HandlerResult:
        message = utterance.strip()
        if not message:
            return HandlerResult("I'll need a bit more detail to send a helpful message. What should I include?", error=True)
        state.slots["message"] = message
        state.step = "confirm_message"
        return self._prompt_for_current_step(state)

    def _handle_confirmation(self, utterance: str, state: ConversationState) -> HandlerResult:
        normalized = utterance.strip().lower()
        if normalized in {"yes", "y", "send"}:
            ticket_id = self._service.send_message(topic=state.slots["topic"], message=state.slots["message"])
            return HandlerResult(
                f"All right, I've delivered that message. Your advisor will reply under ticket {ticket_id}.",
                completed=True,
            )
        if normalized in {"no", "n", "cancel"}:
            return HandlerResult("Okay, I won't send that. Let me know if you want to try again.", completed=True)
        return HandlerResult("Please answer yes or no so I know whether to send the message.", error=True)
