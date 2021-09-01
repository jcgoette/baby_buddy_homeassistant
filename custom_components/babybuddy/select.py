"""Support for Babybuddy selects."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import SELECTOR_TYPES, BabyBuddySelectDescription


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Babybuddy select entities for feeding and diaper change."""
    async_add_entities([BabyBuddySelect(entity) for entity in SELECTOR_TYPES])


class BabyBuddySelect(SelectEntity, RestoreEntity):
    """Babybuddy select entity for feeding and diaper change."""

    _attr_should_poll = False
    entity_description: BabyBuddySelectDescription

    def __init__(self, entity_description: BabyBuddySelectDescription) -> None:
        """Initialize the Babybuddy select entity."""
        self._attr_unique_id = entity_description.key
        self._attr_options = entity_description.options
        self.entity_description = entity_description
        self._attr_current_option = None

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
