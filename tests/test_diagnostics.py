"""Test babybuddy diagnostics."""

import pytest

from custom_components.babybuddy.const import DOMAIN
from custom_components.babybuddy.diagnostics import async_get_config_entry_diagnostics
from homeassistant.components.diagnostics.const import REDACTED
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_get_config_entry_diagnostics(hass: HomeAssistant):
    """Test config entry diagnostics."""
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    # Ensure sensitive data in config_entry is redacted
    assert diagnostics["config_entry"]["data"][CONF_API_KEY] == REDACTED
    assert diagnostics["config_entry"]["data"][CONF_HOST] == REDACTED
