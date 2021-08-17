"""Exceptions for Babybuddy integration."""

from homeassistant.exceptions import HomeAssistantError


class BabbyBuddyError(HomeAssistantError):
    """Base Exception for Babybuddy error."""


class ConnectError(BabbyBuddyError):
    """Raise connection error..."""


class AuthorizationError(BabbyBuddyError):
    """Raise authroization exception."""


class ValidationError(BabbyBuddyError):
    """Raise an exception if required field value is not valid."""
