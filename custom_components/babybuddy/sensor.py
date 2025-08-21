"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SENSOR_TYPES
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildDataSensor, BabyBuddyChildSensor


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
