"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_DIAPER_CHANGE,
    ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
    ATTR_ACTION_ADD_HEIGHT,
    ATTR_ACTION_ADD_NOTE,
    ATTR_ACTION_ADD_TEMPERATURE,
    ATTR_ACTION_ADD_WEIGHT,
    ATTR_ACTION_DELETE_LAST_ENTRY,
    ATTR_AMOUNT,
    ATTR_BABYBUDDY_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_BMI,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_COLOR,
    ATTR_DESCRIPTIVE,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_LAST_NAME,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PICTURE,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_TAGS,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DIAPER_COLORS,
    DIAPER_TYPES,
    DOMAIN,
    ERROR_CHILD_SENSOR_SELECT,
    LOGGER,
    SENSOR_TYPES,
    BabyBuddyEntityDescription,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .errors import ValidationError


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


class BabyBuddySensor(CoordinatorEntity, SensorEntity):
    """Base class for babybuddy sensors."""

    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_device_info = {
            "configuration_url": f"{coordinator.entry.data[CONF_HOST]}:{coordinator.entry.data[CONF_PORT]}{coordinator.entry.data[CONF_PATH]}/children/{child[ATTR_SLUG]}/dashboard/",
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }


class BabyBuddyChildSensor(BabyBuddySensor):
    """Representation of a babybuddy child sensor."""

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = f"Baby {child['first_name']} {child['last_name']}"
        self._attr_unique_id = (
            f"{coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}"
        )
        self._attr_native_value = child[ATTR_BIRTH_DATE]
        self._attr_icon = ATTR_ICON_CHILD_SENSOR
        self._attr_device_class = ATTR_BABYBUDDY_CHILD

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        return self.child

    @property
    def entity_picture(self) -> str | None:
        """Return babybuddy picture."""
        image: str | None = self.child[ATTR_PICTURE]
        return image


class BabyBuddyChildDataSensor(BabyBuddySensor):
    """Representation of a child data sensor."""

    entity_description: BabyBuddyEntityDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        description: BabyBuddyEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self.entity_description = description
        self._attr_unique_id = f"{self.coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{description.key}"

    @property
    def name(self) -> str:
        """Return the name of the babybuddy sensor."""
        sensor_type = self.entity_description.key
        if sensor_type[-1] == "s":
            sensor_type = sensor_type[:-1]
        return f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} last {sensor_type}"

    @property
    def native_value(self) -> StateType:
        """Return entity state."""
        if self.child[ATTR_ID] not in self.coordinator.data[1]:
            return None
        data: dict[str, str] = self.coordinator.data[1][self.child[ATTR_ID]][
            self.entity_description.key
        ]
        if not data:
            return None
        if callable(self.entity_description.state_key):
            return self.entity_description.state_key(data)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return dt_util.parse_datetime(data[self.entity_description.state_key])

        return data[self.entity_description.state_key]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {}
        if self.child[ATTR_ID] in self.coordinator.data[1]:
            attrs = self.coordinator.data[1][self.child[ATTR_ID]][
                self.entity_description.key
            ]
            if self.entity_description.key == ATTR_CHANGES:
                wet_and_solid: tuple[bool, bool] = (
                    self.coordinator.data[1][self.child[ATTR_ID]][
                        self.entity_description.key
                    ].get(ATTR_WET, False),
                    self.coordinator.data[1][self.child[ATTR_ID]][
                        self.entity_description.key
                    ].get(ATTR_SOLID, False),
                )
                if wet_and_solid == (True, False):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[0]
                if wet_and_solid == (False, True):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[1]
                if wet_and_solid == (True, True):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[2]

        return attrs

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return entity unit of measurement."""
        return self.coordinator.entry.options.get(
            self.entity_description.key,
            self.entity_description.native_unit_of_measurement,
        )
