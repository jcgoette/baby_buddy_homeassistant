"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_ID, CONF_API_KEY, CONF_HOST, CONF_PATH, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import get_datetime_from_time
from .const import (
    ATTR_BABYBUDDY_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_DESCRIPTIVE,
    ATTR_DURATION,
    ATTR_END,
    ATTR_FIRST_NAME,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_PICTURE,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_START,
    ATTR_TAGS,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_WET,
    DIAPER_TYPES,
    DOMAIN,
    BabyBuddySelectEntityDescription,
    BabyBuddySensorEntityDescription,
)
from .coordinator import BabyBuddyCoordinator
from .errors import ValidationError

COMMON_FIELDS: dict[vol.Optional | vol.Exclusive, Any] = {
    vol.Exclusive(ATTR_TIMER, group_of_exclusion="timer_or_start"): cv.boolean,
    vol.Exclusive(ATTR_START, group_of_exclusion="timer_or_start"): vol.Any(
        cv.datetime, cv.time
    ),
    vol.Optional(ATTR_END): vol.Any(cv.datetime, cv.time),
    vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [str]),
}


class BabyBuddyEntity(CoordinatorEntity[BabyBuddyCoordinator], Entity):
    """Base class for babybuddy sensors."""

    coordinator: BabyBuddyCoordinator

    def __init__(
        self, coordinator: BabyBuddyCoordinator, child: dict[str, Any]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.child = child
        self._attr_device_info = DeviceInfo(
            configuration_url=f"{coordinator.entry.data[CONF_HOST]}:{coordinator.entry.data[CONF_PORT]}{coordinator.entry.data[CONF_PATH]}/children/{child[ATTR_SLUG]}/dashboard/",
            identifiers={(DOMAIN, child[ATTR_ID])},
            name=f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        )


class BabyBuddyChildSensorEntity(BabyBuddyEntity, SensorEntity):
    """Representation of a babybuddy child sensor."""

    def __init__(
        self, coordinator: BabyBuddyCoordinator, child: dict[str, Any]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_device_class = ATTR_BABYBUDDY_CHILD
        self._attr_entity_picture = self.child.get(ATTR_PICTURE, None)
        self._attr_extra_state_attributes = self.child
        self._attr_icon = ATTR_ICON_CHILD_SENSOR
        self._attr_name = f"Baby {self.child['first_name']} {self.child['last_name']}"
        self._attr_native_value = self.child[ATTR_BIRTH_DATE]
        self._attr_unique_id = (
            f"{coordinator.entry.data[CONF_API_KEY]}-{self.child[ATTR_ID]}"
        )


class BabyBuddyDataSensorEntity(BabyBuddyEntity, SensorEntity):
    """Representation of a child data sensor."""

    entity_description: BabyBuddySensorEntityDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict[str, Any],
        description: BabyBuddySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self.entity_description = description
        self._attr_extra_state_attributes = self.get_extra_state_attributes()
        self._attr_name = f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} last {self.entity_description.name}"
        self._attr_native_unit_of_measurement = self.coordinator.entry.options.get(
            self.entity_description.key,
            self.entity_description.native_unit_of_measurement,
        )
        self._attr_native_value = self.get_attr_native_value()
        self._attr_unique_id = f"{self.coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{description.key}"

    def get_attr_native_value(self) -> StateType | datetime:
        """Return entity state."""
        data = self.coordinator.data[self.child[ATTR_ID]][self.entity_description.key]
        if not data:
            return None
        if callable(self.entity_description.state_key):
            return self.entity_description.state_key(data[ATTR_DURATION])
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            if data_timestamp := dt_util.parse_datetime(
                data[self.entity_description.state_key]
            ):
                return data_timestamp

        return data[self.entity_description.state_key]

    def get_extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {}

        attrs = self.coordinator.data[self.child[ATTR_ID]][self.entity_description.key]
        if self.entity_description.key == ATTR_CHANGES:
            wet_and_solid: tuple[bool, bool] = (
                self.coordinator.data[self.child[ATTR_ID]][
                    self.entity_description.key
                ].get(ATTR_WET, False),
                self.coordinator.data[self.child[ATTR_ID]][
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


class BabyBuddyChildTimerSwitch(BabyBuddyEntity, SwitchEntity):
    """Representation of a babybuddy timer switch."""

    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = (
            f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} {ATTR_TIMER}"
        )
        self._attr_unique_id = (
            f"{self.coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{ATTR_TIMER}"
        )
        self._attr_icon = ATTR_ICON_TIMER_SAND

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        timer_data = self.coordinator.data[self.child[ATTR_ID]][ATTR_TIMERS]
        # In Babybuddy 2.0 'active' is not in the JSON response, so return
        # True if any timers are returned, as only active timers are
        # returned.
        if not timer_data:
            return False
        if timer_data.get("active"):
            return True
        if len(timer_data) > 0:
            return True
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


class BabyBuddySelect(BabyBuddyEntity, SelectEntity, RestoreEntity):
    """Babybuddy select entity for feeding and diaper change."""

    _attr_should_poll = False
    coordinator: BabyBuddyCoordinator
    entity_description: BabyBuddySelectEntityDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        entity_description: BabyBuddySelectEntityDescription,
    ) -> None:
        """Initialize the Babybuddy select entity."""
        super().__init__(coordinator, child)
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
