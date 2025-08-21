"""Platform for babybuddy binary switch integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildTimerSwitch


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
