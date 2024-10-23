"""Global fixtures for babybuddy integration."""

from __future__ import annotations

# from unittest.mock import patch
import pytest
from pytest_socket import enable_socket

from custom_components.babybuddy.const import DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import MOCK_CONFIG

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def enable_socket_fixture():
    """Enable sockets."""
    enable_socket()


# This fixture enables loading custom integrations in all tests.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    return


@pytest.fixture
async def setup_baby_buddy_entry_live(hass: HomeAssistant):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    return result["result"]
