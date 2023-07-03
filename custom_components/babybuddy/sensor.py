"""Platform for babybuddy sensor integration."""  # pylint: disable=logging-fstring-interpolation
from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any

import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.input_datetime import ATTR_TIMESTAMP
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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
    ATTR_BMI,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_COLOR,
    ATTR_DESCRIPTIVE,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_LAST_NAME,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PICTURE,
    ATTR_PUMPING,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DIAPER_COLORS,
    DIAPER_TYPES,
    DOMAIN,
    ERROR_CHILD_SENSOR_SELECT,
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
    """Set up the babybuddy sensors."""
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
        "add_bmi",
        {
            vol.Required(ATTR_BMI): cv.positive_float,
            vol.Optional(ATTR_DATE): cv.date,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_bmi",
    )
    platform.async_register_entity_service(
        "add_diaper_change",
        {
            vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
            vol.Optional(ATTR_TYPE): vol.In(DIAPER_TYPES),
            vol.Optional(ATTR_COLOR): vol.In(DIAPER_COLORS),
            vol.Optional(ATTR_AMOUNT): cv.positive_int,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_diaper_change",
    )
    platform.async_register_entity_service(
        "add_head_circumference",
        {
            vol.Required(ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE): cv.positive_float,
            vol.Optional(ATTR_DATE): cv.date,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_head_circumference",
    )
    platform.async_register_entity_service(
        "add_height",
        {
            vol.Required(ATTR_HEIGHT): cv.positive_float,
            vol.Optional(ATTR_DATE): cv.date,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_height",
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
        "add_pumping",
        {
            vol.Required(ATTR_AMOUNT): cv.positive_int,
            vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
            vol.Optional(ATTR_NOTES): cv.string,
        },
        "async_add_pumping",
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
    """Base class for babybuddy sensors."""

    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_device_info = {
            "configuration_url": f"{coordinator.config_entry.data[CONF_HOST]}:{coordinator.config_entry.data[CONF_PORT]}{coordinator.config_entry.data[CONF_PATH]}/children/{child[ATTR_SLUG]}/dashboard/",
            "default_name": f"Baby {child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
            "identifiers": {(DOMAIN, child[ATTR_ID])},
        }

    async def async_add_bmi(
        self,
        bmi: float,
        date: date | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add BMI entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_BMI: bmi,
        }
        if date:
            data[ATTR_DATE] = date
        if notes:
            data[ATTR_NOTES] = notes

        date_now = dt_util.now().date()
        await self.coordinator.client.async_post(ATTR_BMI, data, date_now)
        await self.coordinator.async_request_refresh()

    async def async_add_diaper_change(
        self,
        type: str | None = None,  # pylint: disable=redefined-builtin
        time: datetime | time | None = None,  # pylint: disable=redefined-outer-name
        color: str | None = None,
        amount: int | None = None,
        notes: str | None = None,
    ) -> None:
        """Add diaper change entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
        }
        if time:
            try:
                date_time = get_datetime_from_time(time)
                data[ATTR_TIME] = date_time
            except ValidationError as err:
                _LOGGER.error(err)
                return
        if type:
            data[ATTR_WET] = type == "Wet and Solid" or type.lower() == ATTR_WET
            data[ATTR_SOLID] = type == "Wet and Solid" or type.lower() == ATTR_SOLID
        if color:
            data[ATTR_COLOR] = color.lower()
        if amount:
            data[ATTR_AMOUNT] = amount
        if notes:
            data[ATTR_NOTES] = notes

        date_time_now = get_datetime_from_time(dt_util.now())
        await self.coordinator.client.async_post(ATTR_CHANGES, data, date_time_now)
        await self.coordinator.async_request_refresh()

    async def async_add_head_circumference(
        self,
        head_circumference: float,
        date: date | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add head circumference entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE: head_circumference,
        }
        if date:
            data[ATTR_DATE] = date
        if notes:
            data[ATTR_NOTES] = notes

        date_now = dt_util.now().date()
        await self.coordinator.client.async_post(
            ATTR_HEAD_CIRCUMFERENCE_DASH, data, date_now
        )
        await self.coordinator.async_request_refresh()

    async def async_add_height(
        self,
        height: float,
        date: date | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add height entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_HEIGHT: height,
        }
        if date:
            data[ATTR_DATE] = date
        if notes:
            data[ATTR_NOTES] = notes

        date_now = dt_util.now().date()
        await self.coordinator.client.async_post(ATTR_HEIGHT, data, date_now)
        await self.coordinator.async_request_refresh()

    async def async_add_note(
        self,
        note: str,
        time: datetime | time | None = None,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Add note entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {ATTR_CHILD: self.child[ATTR_ID], ATTR_NOTE: note}
        if time:
            try:
                date_time = get_datetime_from_time(time)
                data[ATTR_TIME] = date_time
            except ValidationError as err:
                _LOGGER.error(err)
                return

        date_time_now = get_datetime_from_time(dt_util.now())
        await self.coordinator.client.async_post(ATTR_NOTES, data, date_time_now)
        await self.coordinator.async_request_refresh()

    async def async_add_pumping(
        self,
        amount: float,
        time: datetime | time | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add a pumping entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_AMOUNT: amount,
        }
        if time:
            try:
                date_time = get_datetime_from_time(time)
                data[ATTR_TIME] = date_time
            except ValidationError as err:
                _LOGGER.error(err)
                return
        if notes:
            data[ATTR_NOTES] = notes

        date_time_now = get_datetime_from_time(dt_util.now())
        await self.coordinator.client.async_post(ATTR_PUMPING, data, date_time_now)
        await self.coordinator.async_request_refresh()

    async def async_add_temperature(
        self,
        temperature: float,
        time: datetime | time | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add a temperature entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_TEMPERATURE: temperature,
        }
        if time:
            try:
                date_time = get_datetime_from_time(time)
                data[ATTR_TIME] = date_time
            except ValidationError as err:
                _LOGGER.error(err)
                return
        if notes:
            data[ATTR_NOTES] = notes

        date_time_now = get_datetime_from_time(dt_util.now())
        await self.coordinator.client.async_post(ATTR_TEMPERATURE, data, date_time_now)
        await self.coordinator.async_request_refresh()

    async def async_add_weight(
        self,
        weight: float,
        date: date | None = None,  # pylint: disable=redefined-outer-name
        notes: str | None = None,
    ) -> None:
        """Add weight entry."""
        if not isinstance(self, BabyBuddyChildSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_WEIGHT: weight,
        }
        if date:
            data[ATTR_DATE] = date
        if notes:
            data[ATTR_NOTES] = notes

        date_now = dt_util.now().date()
        await self.coordinator.client.async_post(ATTR_WEIGHT, data, date_now)
        await self.coordinator.async_request_refresh()

    async def async_delete_last_entry(self) -> None:
        """Delete last data entry."""
        if not isinstance(self, BabyBuddyChildDataSensor):
            _LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
            return

        if self.extra_state_attributes.get(ATTR_ID) is None:
            _LOGGER.error(f"{self.entity_description.key} entry is not available.")
            return
        await self.coordinator.client.async_delete(
            self.entity_description.key, self.extra_state_attributes[ATTR_ID]
        )
        await self.coordinator.async_request_refresh()


class BabyBuddyChildSensor(BabyBuddySensor):
    """Representation of a babybuddy child sensor."""

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = f"Baby {child['first_name']} {child['last_name']}"
        self._attr_unique_id = (
            f"{coordinator.config_entry.data[CONF_API_KEY]}-{child[ATTR_ID]}"
        )
        self._attr_native_value = child[ATTR_BIRTH_DATE]
        self._attr_icon = "mdi:baby-face-outline"
        self._attr_device_class = ATTR_TIMESTAMP
        self._attr_device_class = "babybuddy_child"

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
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{description.key}"

    @property
    def name(self) -> str:
        """Return the name of the babybuddy sensor."""
        type = self.entity_description.key  # pylint: disable=redefined-builtin
        if type[-1] == "s":
            type = type[:-1]
        return f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} last {type}"

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
                wet_and_solid: tuple(bool, bool) = (
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
        return self.coordinator.config_entry.options.get(
            self.entity_description.key,
            self.entity_description.native_unit_of_measurement,
        )
