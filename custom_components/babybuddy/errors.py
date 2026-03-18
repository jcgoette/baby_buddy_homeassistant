"""Exceptions for babybuddy integration."""

from homeassistant.exceptions import HomeAssistantError


class BabyBuddyError(HomeAssistantError):
    """Base Exception for Babybuddy error."""


class ConnectError(BabyBuddyError):
    """Raise connection error..."""


class AuthorizationError(BabyBuddyError):
    """Raise authorization exception."""


class ValidationError(BabyBuddyError):
    """Raise an exception if required field value is not valid."""
