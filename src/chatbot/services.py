from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class AccountService:
    """Interface for creating new bank accounts."""

    def open_account(self, *, full_name: str, account_type: str, initial_deposit: float) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class TransferService:
    """Interface for executing money transfers between accounts."""

    def transfer(self, *, from_account: str, to_account: str, amount: float) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class AdvisorMessagingService:
    """Interface for sending secure messages to a financial advisor."""

    def send_message(self, *, topic: str, message: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class InMemoryAccountService(AccountService):
    """Simple in-memory account service used for testing and demos."""

    opened_accounts: List[Dict[str, str]] = field(default_factory=list)

    def open_account(self, *, full_name: str, account_type: str, initial_deposit: float) -> str:
        account_id = f"ACC{len(self.opened_accounts) + 1:04d}"
        self.opened_accounts.append(
            {
                "id": account_id,
                "full_name": full_name,
                "account_type": account_type,
                "initial_deposit": f"{initial_deposit:.2f}",
            }
        )
        return account_id


@dataclass
class InMemoryTransferService(TransferService):
    """In-memory implementation of ``TransferService``."""

    transfers: List[Dict[str, str]] = field(default_factory=list)

    def transfer(self, *, from_account: str, to_account: str, amount: float) -> str:
        transfer_id = f"TRX{len(self.transfers) + 1:04d}"
        self.transfers.append(
            {
                "id": transfer_id,
                "from_account": from_account,
                "to_account": to_account,
                "amount": f"{amount:.2f}",
            }
        )
        return transfer_id


@dataclass
class InMemoryAdvisorMessagingService(AdvisorMessagingService):
    """In-memory implementation of ``AdvisorMessagingService``."""

    messages: List[Dict[str, str]] = field(default_factory=list)

    def send_message(self, *, topic: str, message: str) -> str:
        ticket_id = f"MSG{len(self.messages) + 1:04d}"
        self.messages.append(
            {
                "id": ticket_id,
                "topic": topic,
                "message": message,
            }
        )
        return ticket_id
