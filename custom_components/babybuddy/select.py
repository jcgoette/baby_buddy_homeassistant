"""Support for babybuddy selects."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SELECTOR_TYPES
from .coordinator import BabyBuddyCoordinator
from .entity import BabyBuddySelect


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up babybuddy select entities for feeding and diaper change."""
    coordinator: BabyBuddyCoordinator = entry.runtime_data
    async_add_entities(
        [BabyBuddySelect(coordinator, entity) for entity in SELECTOR_TYPES],
        update_before_add=True,
    )
