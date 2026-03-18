"""Support for babybuddy buttons."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_NAME, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from . import BabyBuddyCoordinator
from .client import get_datetime_from_time
from .const import (
    ATTR_CHILD,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_START,
    ATTR_TIMERS,
    BUTTON_TYPES,
    DOMAIN,
    _LOGGER,
    BabyBuddyButtonDescription,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up babybuddy button entities."""
    babybuddy_coordinator: BabyBuddyCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities(
        [
            BabyBuddyTimerButton(babybuddy_coordinator, description)
            for description in BUTTON_TYPES
        ]
    )


class BabyBuddyTimerButton(CoordinatorEntity, ButtonEntity):
    """Babybuddy button entity to start a timer."""

    coordinator: BabyBuddyCoordinator
    entity_description: BabyBuddyButtonDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        entity_description: BabyBuddyButtonDescription,
    ) -> None:
        """Initialize the Babybuddy button entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{entity_description.key}"

        if self.coordinator.data and self.coordinator.data[0]:
            children = self.coordinator.data[0]
            if len(children) == 1:
                child = children[0]
                self._attr_device_info = {
                    "identifiers": {(DOMAIN, child[ATTR_ID])},
                    "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
                }
            else:
                self._attr_device_info = {
                    "identifiers": {(DOMAIN, "hub")},
                    "name": "Baby Buddy Hub",
                    "manufacturer": "Baby Buddy",
                }

    @property
    def name(self) -> str | None:
        """Return the name of the button."""
        return self.entity_description.name

    async def async_press(self) -> None:
        """Handle the button press."""
        child_id = self.coordinator.selected_timer_child_id
        if not child_id:
            # Fallback to the first child if multiple exist and none is selected somehow,
            # or the only child if there's only one.
            if self.coordinator.data and self.coordinator.data[0]:
                child_id = self.coordinator.data[0][0][ATTR_ID]
            else:
                _LOGGER.error("No child found to start timer for.")
                return

        data: dict[str, Any] = {
            ATTR_CHILD: child_id,
            ATTR_START: get_datetime_from_time(dt_util.now()),
        }

        # The timer name will be exactly the name of the control button (e.g. "Start Feeding Timer"
        # without "Baby Buddy" prefix, or we can just send "Feeding")
        # Let's send a concise name based on the key
        if "feeding" in self.entity_description.key:
            data[ATTR_NAME] = "Feeding"
        elif "sleeping" in self.entity_description.key:
            data[ATTR_NAME] = "Sleeping"

        await self.coordinator.client.async_post(ATTR_TIMERS, data)
        await self.coordinator.async_request_refresh()
