"""Support for babybuddy selects."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SELECTOR_TYPES, BabyBuddySelectDescription
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddySelect


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up babybuddy select entities for feeding and diaper change."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [BabyBuddySelect(coordinator, entity) for entity in SELECTOR_TYPES]
    )
