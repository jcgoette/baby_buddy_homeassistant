"""Platform for babybuddy binary switch integration."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_NAME, CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_FEEDING,
    ATTR_ACTION_ADD_PUMPING,
    ATTR_ACTION_ADD_SLEEP,
    ATTR_ACTION_ADD_TUMMY_TIME,
    ATTR_AMOUNT,
    ATTR_CHILD,
    ATTR_END,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_METHOD,
    ATTR_MILESTONE,
    ATTR_NAP,
    ATTR_NOTES,
    ATTR_PUMPING,
    ATTR_SLEEP,
    ATTR_START,
    ATTR_TAGS,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_TUMMY_TIMES,
    ATTR_TYPE,
    DOMAIN,
    FEEDING_METHODS,
    FEEDING_TYPES,
    LOGGER,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildTimerSwitch
from .errors import ValidationError


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy switches."""
    coordinator = entry.runtime_data.coordinator
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update the status of entities."""
        update_items(coordinator, tracked, async_add_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()


@callback
def update_items(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add timer switches to new child."""
    new_entities = []
    if coordinator.data:
        for child in coordinator.data[0]:
            if child[ATTR_ID] not in tracked:
                tracked[child[ATTR_ID]] = BabyBuddyChildTimerSwitch(coordinator, child)
                new_entities.append(tracked[child[ATTR_ID]])
        if new_entities:
            async_add_entities(new_entities)
