"""Test babybuddy sensors."""

import pytest

from custom_components.babybuddy.const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_DIAPER_CHANGE,
    ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
    ATTR_ACTION_ADD_HEIGHT,
    ATTR_ACTION_ADD_NOTE,
    ATTR_ACTION_ADD_TEMPERATURE,
    ATTR_ACTION_ADD_WEIGHT,
    ATTR_BMI,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_ICON_HEAD,
    ATTR_ICON_HEIGHT,
    ATTR_ICON_NOTE,
    ATTR_ICON_PAPER_ROLL,
    ATTR_ICON_SCALE,
    ATTR_ICON_THERMOMETER,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_TAGS,
    ATTR_WEIGHT,
    DOMAIN,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.sensor.const import ATTR_STATE_CLASS
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

from .const import (
    MOCK_BABY_NAME,
    MOCK_BABY_SENSOR_ID,
    MOCK_SERVICE_ADD_BMI_SCHEMA,
    MOCK_SERVICE_ADD_DIAPER_CHANGE,
    MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE,
    MOCK_SERVICE_ADD_HEIGHT,
    MOCK_SERVICE_ADD_NOTE,
    MOCK_SERVICE_ADD_TEMPERATURE,
    MOCK_SERVICE_ADD_WEIGHT,
)


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_bmi(
    hass: HomeAssistant,
) -> None:
    """Test the "add bmi" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_bmi"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_BMI,
        MOCK_SERVICE_ADD_BMI_SCHEMA,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_SCALE
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_BMI_SCHEMA[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_BMI_SCHEMA[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_BMI_SCHEMA[ATTR_BMI])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_diaper_change(
    hass: HomeAssistant,
) -> None:
    """Test the "add diaper change" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_change"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_DIAPER_CHANGE,
        MOCK_SERVICE_ADD_DIAPER_CHANGE,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP
    assert state.attributes[ATTR_ICON] == ATTR_ICON_PAPER_ROLL
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_DIAPER_CHANGE[ATTR_NOTES]
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_DIAPER_CHANGE[ATTR_TAGS]
    assert (
        dt_util.parse_datetime(state.state) == MOCK_SERVICE_ADD_DIAPER_CHANGE[ATTR_TIME]
    )


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_head_circumference(
    hass: HomeAssistant,
) -> None:
    """Test the "add head circumference" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_head_circumference"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
        MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_HEAD
    assert (
        state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE[ATTR_NOTES]
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE[ATTR_TAGS]
    assert state.state == str(
        MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE[ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE]
    )


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_height(
    hass: HomeAssistant,
) -> None:
    """Test the "add height" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_height"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_HEIGHT,
        MOCK_SERVICE_ADD_HEIGHT,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_HEIGHT
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_HEIGHT[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_HEIGHT[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_HEIGHT[ATTR_HEIGHT])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_note(
    hass: HomeAssistant,
) -> None:
    """Test the "add note" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_note"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_NOTE,
        MOCK_SERVICE_ADD_NOTE,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_NOTE
    assert state.attributes[ATTR_NOTE] == MOCK_SERVICE_ADD_NOTE[ATTR_NOTE]
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_NOTE[ATTR_TAGS]
    assert dt_util.parse_datetime(state.state) == MOCK_SERVICE_ADD_NOTE[ATTR_TIME]


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_temperature(
    hass: HomeAssistant,
) -> None:
    """Test the "add temperature" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_temperature"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_TEMPERATURE,
        MOCK_SERVICE_ADD_TEMPERATURE,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_THERMOMETER
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_TEMPERATURE[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_TEMPERATURE[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_TEMPERATURE[ATTR_TEMPERATURE])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_weight(
    hass: HomeAssistant,
) -> None:
    """Test the "add weight" service call."""

    baby_entity_id = MOCK_BABY_SENSOR_ID
    entity_id = f"sensor.{MOCK_BABY_NAME}_last_weight"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_WEIGHT,
        MOCK_SERVICE_ADD_WEIGHT,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_SCALE
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_WEIGHT[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_WEIGHT[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_WEIGHT[ATTR_WEIGHT])
