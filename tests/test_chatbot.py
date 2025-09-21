"""Dialogue tests for the conversational banking backend."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.chatbot.engine import ChatbotEngine
from src.chatbot.services import (
    InMemoryAccountService,
    InMemoryAdvisorMessagingService,
    InMemoryTransferService,
)


@pytest.fixture()
def chatbot():
    account_service = InMemoryAccountService()
    transfer_service = InMemoryTransferService()
    advisor_service = InMemoryAdvisorMessagingService()
    engine = ChatbotEngine(
        account_service=account_service,
        transfer_service=transfer_service,
        advisor_service=advisor_service,
    )
    return engine, account_service, transfer_service, advisor_service


def test_account_opening_happy_path(chatbot):
    engine, account_service, *_ = chatbot

    response = engine.handle_message("I want to open a new account")
    assert "full name" in response.lower()

    response = engine.handle_message("Alice Johnson")
    assert "type of account" in response.lower()

    response = engine.handle_message("checking")
    assert "how much" in response.lower()

    response = engine.handle_message("500")
    assert "look correct" in response.lower()

    response = engine.handle_message("yes")
    assert "account" in response.lower()
    assert account_service.opened_accounts[0]["id"] == "ACC0001"
    assert not engine.state.active


def test_account_opening_recover_from_invalid_inputs(chatbot):
    engine, account_service, *_ = chatbot

    engine.handle_message("open account")
    engine.handle_message("Alex Smith")

    response = engine.handle_message("investment")
    assert "didn't recognize" in response.lower()
    assert engine.state.step == "collect_account_type"

    response = engine.handle_message("savings")
    assert "how much" in response.lower()

    response = engine.handle_message("not a number")
    assert "number" in response.lower()
    assert engine.state.step == "collect_initial_deposit"

    engine.handle_message("250")
    engine.handle_message("yes")
    assert account_service.opened_accounts


def test_money_transfer_happy_path(chatbot):
    engine, _, transfer_service, _ = chatbot

    response = engine.handle_message("Can you transfer money for me?")
    assert "which account" in response.lower()

    engine.handle_message("CHK-001")
    engine.handle_message("SAV-002")
    response = engine.handle_message("75.25")
    assert "look right" in response.lower()

    response = engine.handle_message("yes")
    assert "transfer" in response.lower()
    assert transfer_service.transfers[0]["amount"] == "75.25"
    assert not engine.state.active


def test_money_transfer_validation_error(chatbot):
    engine, *_ = chatbot

    engine.handle_message("transfer money")
    engine.handle_message("CHK-001")
    engine.handle_message("CHK-002")

    response = engine.handle_message("-50")
    assert "greater than zero" in response.lower()
    assert engine.state.step == "collect_amount"

    response = engine.handle_message("twenty")
    assert "wasn't able" in response.lower()
    assert engine.state.step == "collect_amount"


def test_advisor_messaging_happy_path(chatbot):
    engine, _, _, advisor_service = chatbot

    response = engine.handle_message("I need to message my advisor")
    assert "discuss" in response.lower()

    engine.handle_message("Retirement planning")
    engine.handle_message("I have a question about contribution limits.")
    response = engine.handle_message("yes")
    assert "ticket" in response.lower()
    assert advisor_service.messages[0]["topic"] == "Retirement planning"
    assert not engine.state.active


def test_advisor_messaging_user_cancels(chatbot):
    engine, _, _, advisor_service = chatbot

    engine.handle_message("contact advisor")
    engine.handle_message("College savings")
    engine.handle_message("How should I rebalance my accounts?")
    response = engine.handle_message("no")
    assert "won't send" in response.lower()
    assert not advisor_service.messages
    assert not engine.state.active


def test_cancel_command_resets_state(chatbot):
    engine, *_ = chatbot

    engine.handle_message("open account")
    engine.handle_message("Jordan Doe")
    assert engine.state.active

    response = engine.handle_message("cancel")
    assert "canceled the current request" in response.lower()
    assert not engine.state.active

    response = engine.handle_message("hello")
    assert "open accounts" in response.lower()
