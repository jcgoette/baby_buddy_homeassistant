"""Services for the babybuddy integration."""

from __future__ import annotations

from datetime import date, time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DATE, ATTR_ID, ATTR_TEMPERATURE, ATTR_TIME
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util, slugify

from .const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_CHILD,
    ATTR_ACTION_ADD_DIAPER_CHANGE,
    ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
    ATTR_ACTION_ADD_HEIGHT,
    ATTR_ACTION_ADD_NOTE,
    ATTR_ACTION_ADD_TEMPERATURE,
    ATTR_ACTION_ADD_WEIGHT,
    ATTR_ACTION_DELETE_LAST_ENTRY,
    ATTR_AMOUNT,
    ATTR_BIRTH_DATE,
    ATTR_BMI,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_CHILDREN,
    ATTR_COLOR,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_LAST_NAME,
    ATTR_NOTE,
    ATTR_NOTES,
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
)
from .coordinator import BabyBuddyCoordinator
from .errors import ValidationError
from .sensor import BabyBuddyChildSensor

SERVICE_ADD_CHILD_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(ATTR_BIRTH_DATE, default=dt_util.now().date()): cv.date,
        vol.Required(ATTR_FIRST_NAME): cv.string,
        vol.Required(ATTR_LAST_NAME): cv.string,
    }
)
COMMON_FIELDS: dict[vol.Required | vol.Optional, Any] = {
    vol.Required(ATTR_CHILD): cv.entity_id,
    vol.Optional(ATTR_NOTES): cv.string,
    vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [str]),
}


async def __async_extract_entry_coordinator(call: ServiceCall) -> BabyBuddyCoordinator:
    """Extract entry and coordinator from a service call."""
    entry = None
    for entry in call.hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
    if not entry:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
        )
    coordinator: BabyBuddyCoordinator = entry.runtime_data
    return coordinator


async def async_add_child(call: ServiceCall) -> None:
    """Add new child."""
    coordinator = await __async_extract_entry_coordinator(call)

    await coordinator.client.async_post(ATTR_CHILDREN, call.data)
    await coordinator.async_request_refresh()


async def async_add_bmi(call: ServiceCall) -> None:
    """Add BMI entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = call.data.copy()
    for i in coordinator.data[0]:
        if (
            f"sensor.{slugify(f'Baby {i["first_name"]} {i["last_name"]}')}"
            == call.data["child"]
        ):
            data["child"] = i["id"]

    # date_now = dt_util.now().date()
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_BMI, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_diaper_change(call: ServiceCall) -> None:
    """Add diaper change entry."""
    coordinator = await __async_extract_entry_coordinator(call)

    data = {
        ATTR_CHILD: call.data[ATTR_CHILD],
    }

    if call.data[ATTR_TIME]:
        try:
            date_time = get_datetime_from_time(call.data[ATTR_TIME])
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if call.data[ATTR_TYPE]:
        data[ATTR_WET] = (
            call.data[ATTR_TYPE] == "Wet and Solid"
            or call.data[ATTR_TYPE].lower() == ATTR_WET
        )
        data[ATTR_SOLID] = (
            call.data[ATTR_TYPE] == "Wet and Solid"
            or call.data[ATTR_TYPE].lower() == ATTR_SOLID
        )
    if call.data[ATTR_COLOR]:
        data[ATTR_COLOR] = call.data[ATTR_COLOR].lower()
    if call.data[ATTR_AMOUNT]:
        data[ATTR_AMOUNT] = call.data[ATTR_AMOUNT]
    if call.data[ATTR_NOTES]:
        data[ATTR_NOTES] = call.data[ATTR_NOTES]
    if call.data[ATTR_TAGS]:
        data[ATTR_TAGS] = call.data[ATTR_TAGS]

    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_CHANGES, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_head_circumference(call: ServiceCall) -> None:
    """Add head circumference entry."""
    if not isinstance(self, BabyBuddyChildSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return
    data = {
        ATTR_CHILD: self.child[ATTR_ID],
        ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE: head_circumference,
    }
    if date:
        data[ATTR_DATE] = date
    if notes:
        data[ATTR_NOTES] = notes
    if tags:
        data[ATTR_TAGS] = tags

    date_now = dt_util.now().date()
    await self.coordinator.client.async_post(
        ATTR_HEAD_CIRCUMFERENCE_DASH, data, date_now
    )
    await self.coordinator.async_request_refresh()


async def async_add_height(call: ServiceCall) -> None:
    """Add height entry."""
    if not isinstance(self, BabyBuddyChildSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return
    data = {
        ATTR_CHILD: self.child[ATTR_ID],
        ATTR_HEIGHT: height,
    }
    if date:
        data[ATTR_DATE] = date
    if notes:
        data[ATTR_NOTES] = notes
    if tags:
        data[ATTR_TAGS] = tags

    date_now = dt_util.now().date()
    await self.coordinator.client.async_post(ATTR_HEIGHT, data, date_now)
    await self.coordinator.async_request_refresh()


async def async_add_note(call: ServiceCall) -> None:
    """Add note entry."""
    if not isinstance(self, BabyBuddyChildSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return
    data = {ATTR_CHILD: self.child[ATTR_ID], ATTR_NOTE: note}
    if time:
        try:
            date_time = get_datetime_from_time(time)
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if tags:
        data[ATTR_TAGS] = tags

    date_time_now = get_datetime_from_time(dt_util.now())
    await self.coordinator.client.async_post(ATTR_NOTES, data, date_time_now)
    await self.coordinator.async_request_refresh()


async def async_add_temperature(call: ServiceCall) -> None:
    """Add a temperature entry."""
    if not isinstance(self, BabyBuddyChildSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return
    data = {
        ATTR_CHILD: self.child[ATTR_ID],
        ATTR_TEMPERATURE: temperature,
    }
    if time:
        try:
            date_time = get_datetime_from_time(time)
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if notes:
        data[ATTR_NOTES] = notes
    if tags:
        data[ATTR_TAGS] = tags

    date_time_now = get_datetime_from_time(dt_util.now())
    await self.coordinator.client.async_post(ATTR_TEMPERATURE, data, date_time_now)
    await self.coordinator.async_request_refresh()


async def async_add_weight(call: ServiceCall) -> None:
    """Add weight entry."""
    if not isinstance(self, BabyBuddyChildSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return
    data = {
        ATTR_CHILD: self.child[ATTR_ID],
        ATTR_WEIGHT: weight,
    }
    if date:
        data[ATTR_DATE] = date
    if notes:
        data[ATTR_NOTES] = notes
    if tags:
        data[ATTR_TAGS] = tags

    date_now = dt_util.now().date()
    await self.coordinator.client.async_post(ATTR_WEIGHT, data, date_now)
    await self.coordinator.async_request_refresh()


async def async_delete_last_entry(call: ServiceCall) -> None:
    """Delete last data entry."""
    if not isinstance(self, BabyBuddyChildDataSensor):
        LOGGER.debug(ERROR_CHILD_SENSOR_SELECT)
        return

    if self.extra_state_attributes.get(ATTR_ID) is None:
        LOGGER.error(f"{self.entity_description.key} entry is not available.")
        return
    await self.coordinator.client.async_delete(
        self.entity_description.key, self.extra_state_attributes[ATTR_ID]
    )
    await self.coordinator.async_request_refresh()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the babybuddy integration."""

    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_CHILD,
        async_add_child,
        SERVICE_ADD_CHILD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_BMI,
        async_add_bmi,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_BMI): cv.positive_float,
                vol.Optional(ATTR_DATE): cv.date,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_DIAPER_CHANGE,
        async_add_diaper_change,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
                vol.Optional(ATTR_TYPE): vol.In(DIAPER_TYPES),
                vol.Optional(ATTR_COLOR): vol.In(DIAPER_COLORS),
                vol.Optional(ATTR_AMOUNT): cv.positive_float,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE,
        async_add_head_circumference,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE): cv.positive_float,
                vol.Optional(ATTR_DATE): cv.date,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_HEIGHT,
        async_add_height,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_HEIGHT): cv.positive_float,
                vol.Optional(ATTR_DATE): cv.date,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_NOTE,
        async_add_note,
        vol.Schema(
            {
                vol.Required(ATTR_NOTE): cv.string,
                vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
                vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [str]),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_TEMPERATURE,
        async_add_temperature,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_TEMPERATURE): cv.positive_float,
                vol.Optional(ATTR_TIME): vol.Any(cv.datetime, cv.time),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_WEIGHT,
        async_add_weight,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_WEIGHT): cv.positive_float,
                vol.Optional(ATTR_DATE): cv.date,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN, ATTR_ACTION_DELETE_LAST_ENTRY, async_delete_last_entry, vol.Schema({})
    )
