"""Test babybuddy sensors."""

import pytest

from custom_components.babybuddy.const import (
    ATTR_ACTION_ADD_CHILD,
    ATTR_BABYBUDDY_CHILD,
    ATTR_FIRST_NAME,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_LAST_NAME,
    DOMAIN,
)
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ICON
from homeassistant.core import HomeAssistant

from .const import MOCK_BABY_SENSOR_ID, MOCK_SERVICE_ADD_CHILD_SCHEMA


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_child(
    hass: HomeAssistant,
) -> None:
    """Test the "add child" service call."""

    entity_id = MOCK_BABY_SENSOR_ID
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_CHILD,
        MOCK_SERVICE_ADD_CHILD_SCHEMA,
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == ATTR_BABYBUDDY_CHILD
    assert (
        state.attributes[ATTR_FIRST_NAME]
        == MOCK_SERVICE_ADD_CHILD_SCHEMA[ATTR_FIRST_NAME]
    )
    assert state.attributes[ATTR_ICON] == ATTR_ICON_CHILD_SENSOR
    assert (
        state.attributes[ATTR_LAST_NAME]
        == MOCK_SERVICE_ADD_CHILD_SCHEMA[ATTR_LAST_NAME]
    )
