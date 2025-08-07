"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_CHILD, LOGGER, SENSOR_TYPES
from .coordinator import BabyBuddyCoordinator
from .entity import BabyBuddyChildSensorEntity, BabyBuddyDataSensorEntity


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy sensors."""
    coordinator: BabyBuddyCoordinator = entry.runtime_data
    known_devices: set[str] = set()

    # Add devices after integration setup
    # https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/dynamic-devices/
    def _check_device() -> None:
        current_devices = set(coordinator.data)
        if new_devices := current_devices - known_devices:
            LOGGER.debug(f"Added new children devices: {new_devices}")
            known_devices.update(new_devices)
            for device_id in new_devices:
                child_dict = coordinator.data[device_id][ATTR_CHILD]
                async_add_entities(
                    [BabyBuddyChildSensorEntity(coordinator, child_dict)],
                    update_before_add=True,
                )
                async_add_entities(
                    [
                        BabyBuddyDataSensorEntity(
                            coordinator,
                            child_dict,
                            description,
                        )
                        for description in SENSOR_TYPES
                    ],
                    update_before_add=True,
                )

    _check_device()

    # Update coordinator to fetch all the data from the service. Every update _check_device
    # will check if there are new devices to create entities for and add them to Home Assistant.
    entry.async_on_unload(coordinator.async_add_listener(_check_device))
