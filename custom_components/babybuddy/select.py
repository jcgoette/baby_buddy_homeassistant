"""Support for babybuddy selects."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BabyBuddyCoordinator
from .const import (
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_TIMER_FOR_CHILD,
    DOMAIN,
    SELECTOR_TYPES,
    BabyBuddySelectDescription,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up babybuddy select entities for feeding and diaper change."""
    babybuddy_coordinator: BabyBuddyCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    entities = [BabyBuddySelect(babybuddy_coordinator, entity) for entity in SELECTOR_TYPES]
    
    if babybuddy_coordinator.data and len(babybuddy_coordinator.data[0]) > 1:
        entities.append(BabyBuddyChildSelect(babybuddy_coordinator))
        
    async_add_entities(entities)


class BabyBuddySelect(CoordinatorEntity, SelectEntity, RestoreEntity):
    """Babybuddy select entity for feeding and diaper change."""

    _attr_should_poll = False
    coordinator: BabyBuddyCoordinator
    entity_description: BabyBuddySelectDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        entity_description: BabyBuddySelectDescription,
    ) -> None:
        """Initialize the Babybuddy select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{entity_description.key}"
        self._attr_options = entity_description.options
        self.entity_description = entity_description
        self._attr_current_option = None

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

    async def async_added_to_hass(self) -> None:
        """Restore last state when added."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        if option not in self.options:
            raise ValueError(f"Invalid option for {self.entity_id}: {option}")

        self._attr_current_option = option
        self.async_write_ha_state()


class BabyBuddyChildSelect(CoordinatorEntity, SelectEntity, RestoreEntity):
    """Babybuddy select entity for choosing which child a timer applies to."""

    _attr_should_poll = False
    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator) -> None:
        """Initialize the Babybuddy select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{ATTR_TIMER_FOR_CHILD}"
        self._attr_name = "Timer for Child"
        self._attr_icon = "mdi:baby-face-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "hub")},
            "name": "Baby Buddy Hub",
            "manufacturer": "Baby Buddy",
        }
        
        self.children_map = {}
        for child in coordinator.data[0]:
            name = f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}".strip()
            self.children_map[name] = child[ATTR_ID]
            
        self._attr_options = list(self.children_map.keys())
        self._attr_current_option = self._attr_options[0] if self._attr_options else None
        
        # Initialize the coordinator's selected child ID
        if self._attr_current_option:
            self.coordinator.selected_timer_child_id = self.children_map[self._attr_current_option]

    async def async_added_to_hass(self) -> None:
        """Restore last state when added."""
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self._attr_options:
            self._attr_current_option = last_state.state
            self.coordinator.selected_timer_child_id = self.children_map[self._attr_current_option]

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        if option not in self.options:
            raise ValueError(f"Invalid option for {self.entity_id}: {option}")

        self._attr_current_option = option
        self.coordinator.selected_timer_child_id = self.children_map[option]
        self.async_write_ha_state()
