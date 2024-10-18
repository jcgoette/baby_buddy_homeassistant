"""Test babybuddy config flow."""

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.babybuddy.const import (
    _LOGGER,
    CONFIG_FLOW_VERSION,
    DEFAULT_NAME,
    DOMAIN,
)

from .const import MOCK_CONFIG, MOCK_OPTIONS


async def test_successful_config_flow(hass: HomeAssistant):
    """Test a successful config flow."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    # Check that the config flow is complete and a new entry is created with the input data
    assert result["data"] == MOCK_CONFIG
    assert result["handler"] == DOMAIN
    assert result["options"] == {}
    assert result["result"]
    assert result["result"].state is ConfigEntryState.LOADED
    assert (
        result["result"].unique_id
        == f"{MOCK_CONFIG[CONF_HOST]}-{MOCK_CONFIG[CONF_API_KEY]}"
    )
    assert result["title"] == f"{DEFAULT_NAME} ({MOCK_CONFIG[CONF_HOST]})"
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["version"] == CONFIG_FLOW_VERSION


async def test_options_flow(
    hass: HomeAssistant, setup_baby_buddy_entry_live: MockConfigEntry
):
    """Test an options flow."""
    # Go through options flow
    result = await hass.config_entries.options.async_init(
        setup_baby_buddy_entry_live.entry_id
    )

    # Verify that the first options step is a user form
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Enter some fake data into the form
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=MOCK_OPTIONS,
    )

    _LOGGER.debug(f"test_options_flow result = {result}")

    # Verify that the flow finishes
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify that the options were updated
    assert result["data"] == MOCK_OPTIONS
