"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ID,
    ATTR_NAME,
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
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_DIAPER_CHANGE,
    ATTR_ACTION_ADD_FEEDING,
    ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
    ATTR_ACTION_ADD_HEIGHT,
    ATTR_ACTION_ADD_NOTE,
    ATTR_ACTION_ADD_PUMPING,
    ATTR_ACTION_ADD_SLEEP,
    ATTR_ACTION_ADD_TEMPERATURE,
    ATTR_ACTION_ADD_TUMMY_TIME,
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
    ATTR_END,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_METHOD,
    ATTR_MILESTONE,
    ATTR_NAP,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PICTURE,
    ATTR_PUMPING,
    ATTR_SLEEP,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_START,
    ATTR_TAGS,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_TUMMY_TIMES,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DIAPER_COLORS,
    DIAPER_TYPES,
    DOMAIN,
    ERROR_CHILD_SENSOR_SELECT,
    FEEDING_METHODS,
    FEEDING_TYPES,
    LOGGER,
    SELECTOR_TYPES,
    SENSOR_TYPES,
    BabyBuddyEntityDescription,
    BabyBuddySelectDescription,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .errors import ValidationError


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
        self._attr_unique_id = (
            f"{self.coordinator.entry.data[CONF_API_KEY]}-{entity_description.key}"
        )
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
