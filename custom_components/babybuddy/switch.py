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


class BabyBuddyChildTimerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a babybuddy timer switch."""

    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_name = (
            f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} {ATTR_TIMER}"
        )
        self._attr_unique_id = (
            f"{self.coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{ATTR_TIMER}"
        )
        self._attr_icon = ATTR_ICON_TIMER_SAND
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        if self.child[ATTR_ID] in self.coordinator.data[1]:
            timer_data = self.coordinator.data[1][self.child[ATTR_ID]][ATTR_TIMERS]
            # In Babybuddy 2.0 'active' is not in the JSON response, so return
            # True if any timers are returned, as only active timers are
            # returned.
            return timer_data.get("active", len(timer_data) > 0)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        attrs: dict[str, Any] = {}
        if self.is_on:
            attrs = self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS)
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start a new timer."""
        await self.async_start_timer()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Delete active timer."""
        timer_id = self.extra_state_attributes[ATTR_ID]
        await self.coordinator.client.async_delete(ATTR_TIMERS, timer_id)
        await self.coordinator.async_request_refresh()
