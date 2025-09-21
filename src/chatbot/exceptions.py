"""Custom exceptions used by the chatbot backend."""


class ChatbotError(Exception):
   """Base class for chatbot related errors."""


class IntentNotFoundError(ChatbotError):
    """Raised when no intent matches a user utterance."""


class HandlerNotFoundError(ChatbotError):
    """Raised when a handler cannot be found for the matched intent."""


class ValidationError(ChatbotError):
    """Raised when user input fails validation within a handler."""
