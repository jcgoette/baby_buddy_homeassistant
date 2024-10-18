"""Global fixtures for babybuddy integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from custom_components.babybuddy.const import _LOGGER, DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_socket import enable_socket

from .const import MOCK_CONFIG

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def enable_socket_fixture():
    enable_socket()


# This fixture enables loading custom integrations in all tests.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    yield


@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with (
        patch("homeassistant.components.persistent_notification.async_create"),
        patch("homeassistant.components.persistent_notification.async_dismiss"),
    ):
        yield


@pytest.fixture()
async def setup_baby_buddy_entry_live(hass: HomeAssistant):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    _LOGGER.debug(f"setup_baby_buddy_entry_live result = {result}")
    _LOGGER.debug(f"setup_baby_buddy_entry_live result['result'] = {result['result']}")

    return result["result"]
