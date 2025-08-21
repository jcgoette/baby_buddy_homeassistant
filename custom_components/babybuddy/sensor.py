"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_DIAPER_CHANGE,
    ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
    ATTR_ACTION_ADD_HEIGHT,
    ATTR_ACTION_ADD_NOTE,
    ATTR_ACTION_ADD_TEMPERATURE,
    ATTR_ACTION_ADD_WEIGHT,
    ATTR_ACTION_DELETE_LAST_ENTRY,
    ATTR_AMOUNT,
    ATTR_BABYBUDDY_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_BMI,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_COLOR,
    ATTR_DESCRIPTIVE,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_LAST_NAME,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PICTURE,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_TAGS,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DIAPER_COLORS,
    DIAPER_TYPES,
    DOMAIN,
    ERROR_CHILD_SENSOR_SELECT,
    LOGGER,
    SENSOR_TYPES,
    BabyBuddyEntityDescription,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildDataSensor, BabyBuddyChildSensor
from .errors import ValidationError


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy sensors."""
    coordinator = entry.runtime_data.coordinator
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update entities."""
        update_items(coordinator, tracked, async_add_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()


@callback
def update_items(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add new sensors for new endpoint entries."""
    if coordinator.data is not None:
        new_entities = []
        for child in coordinator.data[0]:
            if child[ATTR_ID] not in tracked:
                tracked[child[ATTR_ID]] = BabyBuddyChildSensor(coordinator, child)
                new_entities.append(tracked[child[ATTR_ID]])
            for description in SENSOR_TYPES:
                if (
                    coordinator.data[1][child[ATTR_ID]].get(description.key)
                    and f"{child[ATTR_ID]}_{description.key}" not in tracked
                ):
                    tracked[f"{child[ATTR_ID]}_{description.key}"] = (
                        BabyBuddyChildDataSensor(coordinator, child, description)
                    )
                    new_entities.append(tracked[f"{child[ATTR_ID]}_{description.key}"])
        if new_entities:
            async_add_entities(new_entities)
