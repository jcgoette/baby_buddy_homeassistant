"""Test babybuddy sensors."""

import asyncio
from datetime import timedelta

import pytest

from custom_components.babybuddy.const import (
    ATTR_ACTION_ADD_FEEDING,
    ATTR_ACTION_ADD_PUMPING,
    ATTR_ACTION_ADD_SLEEP,
    ATTR_ACTION_ADD_TUMMY_TIME,
    ATTR_AMOUNT,
    ATTR_DURATION,
    ATTR_ICON_BABY,
    ATTR_ICON_BABY_BOTTLE,
    ATTR_ICON_MOTHER_NURSE,
    ATTR_ICON_SLEEP,
    ATTR_ICON_TIMER_SAND,
    ATTR_MILESTONE,
    ATTR_NOTES,
    ATTR_TAGS,
    DOMAIN,
)
from homeassistant.components.sensor import SensorStateClass
from homeassistant.components.sensor.const import ATTR_STATE_CLASS
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ICON,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_INT_10,
    MOCK_BABY_NAME,
    MOCK_BABY_SWITCH_ID,
    MOCK_DURATION,
    MOCK_SERVICE_ADD_FEEDING_START_STOP,
    MOCK_SERVICE_ADD_FEEDING_TIMER,
    MOCK_SERVICE_ADD_PUMPING_START_STOP,
    MOCK_SERVICE_ADD_PUMPING_TIMER,
    MOCK_SERVICE_ADD_SLEEP_START_STOP,
    MOCK_SERVICE_ADD_SLEEP_TIMER,
    MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP,
    MOCK_SERVICE_ADD_TUMMY_TIME_TIMER,
)


@pytest.fixture
async def test_timer(hass: HomeAssistant):
    """A fixture that returns a simple value."""
    baby_entity_id = MOCK_BABY_SWITCH_ID
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        target={ATTR_ENTITY_ID: baby_entity_id},
        blocking=True,
    )
    switch_state = hass.states.get(baby_entity_id)

    assert switch_state
    assert switch_state.attributes[ATTR_ICON] == ATTR_ICON_TIMER_SAND
    assert switch_state.state == STATE_ON

    await asyncio.sleep(ATTR_INT_10)

    yield

    # make sure switch was cleaned up
    await asyncio.sleep(ATTR_INT_10)  # wait for "debounced_refresh"
    switch_state = hass.states.get(baby_entity_id)

    assert switch_state
    assert switch_state.attributes[ATTR_ICON] == ATTR_ICON_TIMER_SAND
    assert switch_state.state == STATE_OFF


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_feeding_start_stop(
    hass: HomeAssistant,
) -> None:
    """Test the "add feeding" service call via start/stop."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_feeding"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_FEEDING,
        MOCK_SERVICE_ADD_FEEDING_START_STOP,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_BABY_BOTTLE
    assert (
        state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_FEEDING_START_STOP[ATTR_NOTES]
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_FEEDING_START_STOP[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_FEEDING_START_STOP[ATTR_AMOUNT])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live", "test_timer")
async def test_service_add_feeding_timer(
    hass: HomeAssistant,
) -> None:
    """Test the "add feeding" service call via timer."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_feeding"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_FEEDING,
        MOCK_SERVICE_ADD_FEEDING_TIMER,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert dt_util.parse_duration(state.attributes[ATTR_DURATION]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert state.attributes[ATTR_ICON] == ATTR_ICON_BABY_BOTTLE
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_FEEDING_TIMER[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_FEEDING_TIMER[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_FEEDING_TIMER[ATTR_AMOUNT])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_pumping_start_stop(
    hass: HomeAssistant,
) -> None:
    """Test the "add pumping" service call via start/stop."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_pumping"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_PUMPING,
        MOCK_SERVICE_ADD_PUMPING_START_STOP,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_MOTHER_NURSE
    assert (
        state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_PUMPING_START_STOP[ATTR_NOTES]
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_PUMPING_START_STOP[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_PUMPING_START_STOP[ATTR_AMOUNT])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live", "test_timer")
async def test_service_add_pumping_timer(
    hass: HomeAssistant,
) -> None:
    """Test the "add pumping" service call via timer."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_pumping"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_PUMPING,
        MOCK_SERVICE_ADD_PUMPING_TIMER,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert dt_util.parse_duration(state.attributes[ATTR_DURATION]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert state.attributes[ATTR_ICON] == ATTR_ICON_MOTHER_NURSE
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_PUMPING_TIMER[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_PUMPING_TIMER[ATTR_TAGS]
    assert state.state == str(MOCK_SERVICE_ADD_PUMPING_TIMER[ATTR_AMOUNT])


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_sleep_start_stop(
    hass: HomeAssistant,
) -> None:
    """Test the "add sleep" service call via start/stop."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_sleep"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_SLEEP,
        MOCK_SERVICE_ADD_SLEEP_START_STOP,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_SLEEP
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_SLEEP_START_STOP[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_SLEEP_START_STOP[ATTR_TAGS]
    assert state.state == str(int(MOCK_DURATION.total_seconds() / 60))


@pytest.mark.usefixtures("setup_baby_buddy_entry_live", "test_timer")
async def test_service_add_sleep_timer(
    hass: HomeAssistant,
) -> None:
    """Test the "add sleep" service call via timer."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_sleep"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_SLEEP,
        MOCK_SERVICE_ADD_SLEEP_TIMER,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert dt_util.parse_duration(state.attributes[ATTR_DURATION]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert state.attributes[ATTR_ICON] == ATTR_ICON_SLEEP
    assert state.attributes[ATTR_NOTES] == MOCK_SERVICE_ADD_SLEEP_TIMER[ATTR_NOTES]
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_SLEEP_TIMER[ATTR_TAGS]
    assert state.state == "0"  # int() on ~10 sec == 0


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_tummy_time_start_stop(
    hass: HomeAssistant,
) -> None:
    """Test the "add tummy time" service call via start/stop."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_tummy_time"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_TUMMY_TIME,
        MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_ICON] == ATTR_ICON_BABY
    assert (
        state.attributes[ATTR_MILESTONE]
        == MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP[ATTR_MILESTONE]
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert (
        state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP[ATTR_TAGS]
    )
    assert state.state == str(int(MOCK_DURATION.total_seconds() / 60))


@pytest.mark.usefixtures("setup_baby_buddy_entry_live", "test_timer")
async def test_service_add_tummy_time_timer(
    hass: HomeAssistant,
) -> None:
    """Test the "add tummy time" service call via timer."""

    entity_id = f"sensor.{MOCK_BABY_NAME}_last_tummy_time"
    await hass.services.async_call(
        DOMAIN,
        ATTR_ACTION_ADD_TUMMY_TIME,
        MOCK_SERVICE_ADD_TUMMY_TIME_TIMER,
        target={ATTR_ENTITY_ID: MOCK_BABY_SWITCH_ID},
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert dt_util.parse_duration(state.attributes[ATTR_DURATION]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert state.attributes[ATTR_ICON] == ATTR_ICON_BABY
    assert (
        state.attributes[ATTR_MILESTONE]
        == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER[ATTR_MILESTONE]
    )
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_TAGS] == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER[ATTR_TAGS]
    assert state.state == "0"  # int() on ~10 sec == 0
