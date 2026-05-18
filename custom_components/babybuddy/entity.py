"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_ID, CONF_API_KEY, CONF_HOST, CONF_PATH, CONF_PORT
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from .const import (
    ATTR_BABYBUDDY_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_DESCRIPTIVE,
    ATTR_FIRST_NAME,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_PICTURE,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_START,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_WET,
    DIAPER_TYPES,
    DOMAIN,
    BabyBuddyEntityDescription,
    BabyBuddySelectDescription,
)
from .coordinator import BabyBuddyCoordinator


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
            timers = self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS, [])
            return len(timers) > 0
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return first active timer's attributes plus a count of all running timers."""
        if not self.is_on:
            return {}
        timers = self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS, [])
        attrs: dict[str, Any] = dict(timers[0]) if timers else {}
        attrs["timer_count"] = len(timers)
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start a new timer."""
        await self.coordinator.client.async_post(
            ATTR_TIMERS,
            {"child": self.child[ATTR_ID], "start": dt_util.now().isoformat()},
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Delete the most recently started active timer."""
        timers = self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS, [])
        if timers:
            await self.coordinator.client.async_delete(ATTR_TIMERS, timers[0][ATTR_ID])
        await self.coordinator.async_request_refresh()


class BabyBuddyTimerSensor(BabyBuddySensor):
    """Representation of a single running babybuddy timer."""

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        timer_id: int,
    ) -> None:
        """Initialize the timer sensor."""
        super().__init__(coordinator, child)
        self._timer_id = timer_id
        self._attr_unique_id = (
            f"{coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-timer-{timer_id}"
        )
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = ATTR_ICON_TIMER_SAND
        child_slug = slugify(f"{child[ATTR_FIRST_NAME]}_{child[ATTR_LAST_NAME]}")
        self.entity_id = f"sensor.{child_slug}_timer_{timer_id}"

    def _get_timer(self) -> dict | None:
        if not self.coordinator.data:
            return None
        if self.child[ATTR_ID] not in self.coordinator.data[1]:
            return None
        for t in self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS, []):
            if t[ATTR_ID] == self._timer_id:
                return t
        return None

    @property
    def name(self) -> str:
        """Return name using the timer's own name when available."""
        timer = self._get_timer()
        timer_name = timer.get("name") if timer else None
        suffix = timer_name if timer_name else str(self._timer_id)
        return f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} timer {suffix}"

    @property
    def available(self) -> bool:
        """Return True only while the timer is still running."""
        return self._get_timer() is not None

    @property
    def native_value(self) -> Any:
        """Return the timer start time as the sensor state."""
        timer = self._get_timer()
        if not timer:
            return None
        return dt_util.parse_datetime(timer[ATTR_START])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all timer fields as attributes."""
        return self._get_timer() or {}


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
