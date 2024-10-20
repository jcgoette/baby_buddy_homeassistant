"""Test babybuddy config flow."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.babybuddy.const import CONFIG_FLOW_VERSION, DEFAULT_NAME, DOMAIN
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import (
    ATTR_STEP_ID_USER,
    INVALID_CONFIG_AUTHORIZATIONERROR,
    INVALID_CONFIG_CONNECTERROR,
    MOCK_CONFIG,
    MOCK_OPTIONS,
)


async def test_successful_config_flow(hass: HomeAssistant):
    """Test a successful config flow."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == ATTR_STEP_ID_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    # Check that the config flow is complete and a new entry is created with the input data
    assert result["data"] == MOCK_CONFIG
    assert result["handler"] == DOMAIN
    assert result["options"] == {}
    assert result["result"].state is ConfigEntryState.LOADED
    assert (
        result["result"].unique_id
        == f"{MOCK_CONFIG[CONF_HOST]}-{MOCK_CONFIG[CONF_API_KEY]}"
    )
    assert result["title"] == f"{DEFAULT_NAME} ({MOCK_CONFIG[CONF_HOST]})"
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["version"] == CONFIG_FLOW_VERSION


async def test_unsuccessful_config_flow_authorization_error(hass: HomeAssistant):
    """Test an unsuccessful config flow due to authorization error."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == ATTR_STEP_ID_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=INVALID_CONFIG_AUTHORIZATIONERROR
    )

    # Check that the config flow is complete and a new entry is created with the input data
    assert result["errors"] == {"api_key": "invalid_auth"}
    assert result["type"] == FlowResultType.FORM


async def test_unsuccessful_config_flow_connect_error(hass: HomeAssistant):
    """Test an unsuccessful config flow due to connect error."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == ATTR_STEP_ID_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=INVALID_CONFIG_CONNECTERROR
    )

    assert result["errors"] == {"base": "cannot_connect"}
    assert result["type"] == FlowResultType.FORM


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

    # Verify that the flow finishes
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify that the options were updated
    assert result["data"] == MOCK_OPTIONS
