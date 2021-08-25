"""Platform for Baby Buddy sensor integration."""
from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any

import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.input_datetime import ATTR_TIMESTAMP
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_HOST,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BabyBuddyCoordinator
from .client import get_datetime_from_time
from .const import (
    ATTR_AMOUNT,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_COLOR,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PICTURE,
    ATTR_SOLID,
    ATTR_TIMERS,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DEFAULT_DIAPER_TYPE,
    DIAPER_COLORS,
    DIAPER_TYPES,
    DOMAIN,
    SENSOR_TYPES,
    BabyBuddyEntityDescription,
)
from .errors import ValidationError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Babybuddy sensors."""
    babybuddy_coordinator: BabyBuddyCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update entities."""
        update_items(babybuddy_coordinator, tracked, async_add_entities)

    config_entry.async_on_unload(
        babybuddy_coordinator.async_add_listener(update_entities)
    )

    update_entities()

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "add_diaper_change",
        {
            vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
            vol.Required(ATTR_TYPE, default=DEFAULT_DIAPER_TYPE): vol.In(DIAPER_TYPES),
            vol.Optional(ATTR_COLOR): vol.In(DIAPER_COLORS),
            vol.Optional(ATTR_AMOUNT): cv.positive_int,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_diaper_change",
    )

    platform.async_register_entity_service(
        "add_temperature",
        {
            vol.Required(ATTR_TEMPERATURE): cv.positive_float,
            vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_temperature",
    )
    platform.async_register_entity_service(
        "add_weight",
        {
            vol.Required(ATTR_WEIGHT): cv.positive_float,
            vol.Optional(ATTR_DATE): cv.date,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_weight",
    )
    platform.async_register_entity_service(
        "add_note",
        {
            vol.Required(ATTR_NOTE): cv.string,
            vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
        },
        "async_add_note",
    )
    platform.async_register_entity_service(
        "delete_last_entry",
        {},
        "async_delete_last_entry",
    )


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
                if description.key == ATTR_TIMERS:
                    continue
                if (
                    coordinator.data[1][child[ATTR_ID]].get(description.key)
                    and f"{child[ATTR_ID]}_{description.key}" not in tracked
                ):
                    tracked[
                        f"{child[ATTR_ID]}_{description.key}"
                    ] = BabyBuddyChildDataSensor(coordinator, child, description)
                    new_entities.append(tracked[f"{child[ATTR_ID]}_{description.key}"])
        if new_entities:
            async_add_entities(new_entities)


class BabyBuddySensor(CoordinatorEntity, SensorEntity):
    """Base class for Babybuddy sensors."""

    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "default_name": f"Baby {child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }

    async def async_add_diaper_change(
        self,
        type: str,
        time: datetime | time | None = None,
        color: str | None = None,
        amount: int | None = None,
        notes: str | None = None,
    ) -> None:
        """Add diaper change entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug("Babybuddy child sensor should be selected. Ignoring.")
            return
        try:
            date_time = get_datetime_from_time(time or dt_util.now())
        except ValidationError as err:
            _LOGGER.error(err)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_TIME: date_time,
            ATTR_WET: type == "Wet and Solid" or type.lower() == ATTR_WET,
            ATTR_SOLID: type == "Wet and Solid" or type.lower() == ATTR_SOLID,
        }
        if color:
            data[ATTR_COLOR] = color.lower()
        if amount:
            data[ATTR_AMOUNT] = amount
        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_CHANGES, data)
        await self.coordinator.async_request_refresh()

    async def async_add_temperature(
        self,
        temperature: float,
        time: datetime | time | None = None,
        notes: str | None = None,
    ) -> None:
        """Add a temperature entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug("Babybuddy child sensor should be selected. Ignoring.")
            return
        try:
            date_time = get_datetime_from_time(time or dt_util.now())
        except ValidationError as err:
            _LOGGER.error(err)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_TEMPERATURE: temperature,
            ATTR_TIME: date_time,
        }
        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_TEMPERATURE, data)
        await self.coordinator.async_request_refresh()

    async def async_add_weight(
        self, weight: float, date: date | None = None, notes: str | None = None
    ) -> None:
        """Add weight entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug("Babybuddy child sensor should be selected. Ignoring.")
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_WEIGHT: weight,
            ATTR_DATE: date or dt_util.now().date(),
        }
        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_WEIGHT, data)
        await self.coordinator.async_request_refresh()

    async def async_add_note(
        self, note: str, time: datetime | time | None = None
    ) -> None:
        """Add note entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug("Babybuddy child sensor should be selected. Ignoring.")
            return
        try:
            date_time = get_datetime_from_time(time or dt_util.now())
        except ValidationError as err:
            _LOGGER.error(err)
            return
        data = {ATTR_CHILD: self.child[ATTR_ID], ATTR_NOTE: note, ATTR_TIME: date_time}

        await self.coordinator.client.async_post(ATTR_NOTES, data)
        await self.coordinator.async_request_refresh()

    async def async_delete_last_entry(self) -> None:
        """Delete last data entry."""
        if not isinstance(self, BabyBuddyChildDataSensor):
            _LOGGER.debug("Babybuddy child data sensor should be selected. Ignoring.")
            return

        if self.state == None:
            _LOGGER.error(f"{self.entity_description.key} entry is not available.")
            return
        await self.coordinator.client.async_delete(
            self.entity_description.key, self.extra_state_attributes[ATTR_ID]
        )
        await self.coordinator.async_request_refresh()


class BabyBuddyChildSensor(BabyBuddySensor):
    """Representation of a Babybuddy child sensor."""

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = f"Baby {child['first_name']} {child['last_name']}"
        self._attr_unique_id = (
            f"{coordinator.config_entry.data[CONF_HOST]}-{child[ATTR_ID]}"
        )
        self._attr_state = child[ATTR_BIRTH_DATE]
        self._attr_icon = "mdi:baby-face-outline"
        self._attr_device_class = ATTR_TIMESTAMP
        self._attr_device_class = "babybuddy__child"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for Babybuddy."""
        return self.child

    @property
    def entity_picture(self) -> str | None:
        """Return Baby Buddy picture."""
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
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_HOST]}-{child[ATTR_ID]}-{description.key}"

    @property
    def name(self) -> str:
        """Return the name of the Babybuddy sensor."""
        type = self.entity_description.key
        if type[-1] == "s":
            type = type[:-1]
        return f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} last {type}"

    @property
    def state(self) -> StateType:
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
        return data[self.entity_description.state_key]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {}
        if self.child[ATTR_ID] in self.coordinator.data[1]:
            attrs = self.coordinator.data[1][self.child[ATTR_ID]][
                self.entity_description.key
            ]
        return attrs

    @property
    def unit_of_measurement(self) -> str | None:
        """Return entity unit of measurement."""
        return self.coordinator.config_entry.options.get(
            self.entity_description.key,
            self.entity_description.unit_of_measurement,
        )
