"""Services for the babybuddy integration."""

from __future__ import annotations

from functools import wraps
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ENTITY_ID,
    ATTR_ID,
    ATTR_NAME,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util, slugify

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_BMI,
    ATTR_ACTION_ADD_CHILD,
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
    ATTR_BIRTH_DATE,
    ATTR_BMI,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_CHILDREN,
    ATTR_COLOR,
    ATTR_END,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_HEAD_CIRCUMFERENCE_DASH,
    ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ATTR_HEIGHT,
    ATTR_LAST_NAME,
    ATTR_METHOD,
    ATTR_MILESTONE,
    ATTR_NAP,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_PUMPING,
    ATTR_SLEEP,
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
    FEEDING_METHODS,
    FEEDING_TYPES,
    LOGGER,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .errors import ValidationError

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
COMMON_FIELDS_TIMER: dict[vol.Required | vol.Optional | vol.Exclusive, Any] = {
    vol.Required(ATTR_CHILD): cv.entity_id,
    vol.Exclusive(ATTR_TIMER, group_of_exclusion="timer_or_start"): cv.boolean,
    vol.Exclusive(ATTR_START, group_of_exclusion="timer_or_start"): vol.Any(
        cv.datetime, cv.time
    ),
    vol.Optional(ATTR_END): vol.Any(cv.datetime, cv.time),
    vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [str]),
}


async def __async_extract_entry_coordinator(call: ServiceCall) -> BabyBuddyCoordinator:
    """Extract coordinator from a service call."""
    hass: HomeAssistant = call.hass
    entry: BabyBuddyConfigEntry = hass.config_entries.async_loaded_entries(DOMAIN)[0]
    entry = er.async_get(hass).async_get(call.data.get(ATTR_CHILD))

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
    coordinator = entry.runtime_data.coordinator
    return coordinator


async def __setup_service_data(
    call: ServiceCall, coordinator: BabyBuddyCoordinator
) -> dict[str, Any]:
    """Extract data with child ID from a service call."""
    data = call.data.copy()

    if (
        data.get(ATTR_CHILD)
        and isinstance(data[ATTR_CHILD], str)
        and data[ATTR_CHILD].startswith("switch.")
    ):
        data[ATTR_CHILD] = [
            child[ATTR_ID]
            for child in coordinator.data[0]
            if (
                f"switch.{slugify(f'{child["first_name"]} {child["last_name"]} Timer')}"
                == call.data[ATTR_CHILD]
            )
        ][0]

    if (
        data.get(ATTR_CHILD)
        and isinstance(data[ATTR_CHILD], str)
        and data[ATTR_CHILD].startswith("sensor.")
    ):
        data[ATTR_CHILD] = [
            child[ATTR_ID]
            for child in coordinator.data[0]
            if (
                f"sensor.{slugify(f'Baby {child["first_name"]} {child["last_name"]}')}"
                == call.data[ATTR_CHILD]
            )
        ][0]

    if call.data.get(ATTR_ENTITY_ID):
        data[ATTR_CHILD] = [
            child[ATTR_ID]
            for child in coordinator.data[0]
            if (
                child["first_name"].lower()
                == call.data[ATTR_ENTITY_ID].split(".")[1].split("_")[0]
                and child["last_name"].lower()
                == call.data[ATTR_ENTITY_ID].split(".")[1].split("_")[1]
            )
        ][0]

    if not data.get(ATTR_CHILD):
        data[ATTR_CHILD] = [
            child[ATTR_ID]
            for child in coordinator.data[0]
            if (
                f"sensor.{slugify(f'Baby {child["first_name"]} {child["last_name"]}')}"
                == call.data[ATTR_CHILD]
                or f"switch.{slugify(f'{child["first_name"]} {child["last_name"]} Timer')}"
                == call.data[ATTR_CHILD]
            )
        ][0]

    # might have a timer...
    if data.get(ATTR_TIMER):
        for child in coordinator.data[0]:
            if (
                f"sensor.{slugify(f'Baby {child["first_name"]} {child["last_name"]}')}"
                == call.data[ATTR_CHILD]
                or f"switch.{slugify(f'{child["first_name"]} {child["last_name"]} Timer')}"
                == call.data[ATTR_CHILD]
            ):
                # do we actually have a timer?
                if child.get(ATTR_TIMERS):
                    data[ATTR_TIMER] = [
                        child[ATTR_TIMERS]["id"] for child in coordinator.data[0]
                    ]
            # if not, let's delete that key
            else:
                del data[ATTR_TIMER]

    return data


async def __set_common_fields(
    call: ServiceCall, data: dict[str, Any]
) -> dict[str, Any]:
    """Set data common fields."""

    if data.get(ATTR_TIMER):
        if not self.is_on:
            raise ValidationError("Timer not found or stopped. Timer must be active.")
        data[ATTR_TIMER] = self.extra_state_attributes[ATTR_ID]
    else:
        data[ATTR_START] = get_datetime_from_time(
            call.data.get(ATTR_START) or dt_util.now()
        )
        data[ATTR_END] = get_datetime_from_time(
            call.data.get(ATTR_END) or dt_util.now()
        )

    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    return data


async def async_add_child(call: ServiceCall) -> None:
    """Add new child."""
    coordinator = await __async_extract_entry_coordinator(call)

    await coordinator.client.async_post(ATTR_CHILDREN, call.data)
    await coordinator.async_request_refresh()


async def async_add_bmi(call: ServiceCall) -> None:
    """Add BMI entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    # date_now = dt_util.now().date()
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_BMI, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_diaper_change(call: ServiceCall) -> None:
    """Add diaper change entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_TIME):
        try:
            date_time = get_datetime_from_time(call.data[ATTR_TIME])
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if call.data.get(ATTR_TYPE):
        data[ATTR_WET] = (
            call.data[ATTR_TYPE] == "Wet and Solid"
            or call.data[ATTR_TYPE].lower() == ATTR_WET
        )
        data[ATTR_SOLID] = (
            call.data[ATTR_TYPE] == "Wet and Solid"
            or call.data[ATTR_TYPE].lower() == ATTR_SOLID
        )
    if call.data.get(ATTR_COLOR):
        data[ATTR_COLOR] = call.data[ATTR_COLOR].lower()
    if call.data.get(ATTR_AMOUNT):
        data[ATTR_AMOUNT] = call.data[ATTR_AMOUNT]
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data[ATTR_NOTES]
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data[ATTR_TAGS]

    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_CHANGES, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_head_circumference(call: ServiceCall) -> None:
    """Add head circumference entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_DATE):
        data[ATTR_DATE] = call.data.get(ATTR_DATE)
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    # date_now = dt_util.now().date()
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(
        ATTR_HEAD_CIRCUMFERENCE_DASH, data, date_time_now
    )
    await coordinator.async_request_refresh()


async def async_add_height(call: ServiceCall) -> None:
    """Add height entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_DATE):
        data[ATTR_DATE] = call.data.get(ATTR_DATE)
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    # date_now = dt_util.now().date()
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_HEIGHT, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_note(call: ServiceCall) -> None:
    """Add note entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_TIME):
        try:
            date_time = get_datetime_from_time(call.data.get(ATTR_TIME))
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_NOTES, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_temperature(call: ServiceCall) -> None:
    """Add a temperature entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_TIME):
        try:
            date_time = get_datetime_from_time(call.data.get(ATTR_TIME))
            data[ATTR_TIME] = date_time
        except ValidationError as error:
            LOGGER.error(error)
            return
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_TEMPERATURE, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_add_weight(call: ServiceCall) -> None:
    """Add weight entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    if call.data.get(ATTR_DATE):
        data[ATTR_DATE] = call.data.get(ATTR_DATE)
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)
    if call.data.get(ATTR_TAGS):
        data[ATTR_TAGS] = call.data.get(ATTR_TAGS)

    # date_now = dt_util.now().date()
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(ATTR_WEIGHT, data, date_time_now)
    await coordinator.async_request_refresh()


async def async_delete_last_entry(call: ServiceCall) -> None:
    """Delete last data entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)
    entity = call.hass.states.get(call.data.get(ATTR_ENTITY_ID))
    key = call.data[ATTR_ENTITY_ID].split(".")[1].split("_")[3]

    await coordinator.client.async_delete(key, entity.attributes.get(ATTR_ID))
    await coordinator.async_request_refresh()


async def async_start_timer(call: ServiceCall) -> None:
    """Start a new timer for child."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    try:
        data[ATTR_START] = get_datetime_from_time(
            call.data.get(ATTR_START) or dt_util.now()
        )
    except ValidationError as error:
        LOGGER.error(error)
        return
    if call.data.get(ATTR_NAME):
        data[ATTR_NAME] = call.data.get(ATTR_NAME)

    await coordinator.client.async_post(ATTR_TIMERS, data)
    await coordinator.async_request_refresh()


async def async_add_feeding(call: ServiceCall) -> None:
    """Add a feeding entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    try:
        data = await __set_common_fields(call, data)
    except ValidationError as error:
        LOGGER.error(error)
        return

    data.update(
        {
            ATTR_TYPE: data[ATTR_TYPE].lower(),
            ATTR_METHOD: data[ATTR_METHOD].lower(),
        }
    )

    if call.data.get(ATTR_AMOUNT):
        data[ATTR_AMOUNT] = call.data.get(ATTR_AMOUNT)
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)

    await coordinator.client.async_post(ATTR_FEEDINGS, data)
    await coordinator.async_request_refresh()


async def async_add_pumping(call: ServiceCall) -> None:
    """Add a pumping entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    try:
        data = await __set_common_fields(call, data)
    except ValidationError as error:
        LOGGER.error(error)
        return

    data[ATTR_AMOUNT] = call.data.get(ATTR_AMOUNT)

    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)

    await coordinator.client.async_post(ATTR_PUMPING, data)
    await coordinator.async_request_refresh()


async def async_add_sleep(call: ServiceCall) -> None:
    """Add a sleep entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    try:
        data = await __set_common_fields(call, data)
    except ValidationError as error:
        LOGGER.error(error)
        return

    if call.data.get(ATTR_NAP):
        data[ATTR_NAP] = call.data.get(ATTR_NAP)
    if call.data.get(ATTR_NOTES):
        data[ATTR_NOTES] = call.data.get(ATTR_NOTES)

    await coordinator.client.async_post(ATTR_SLEEP, data)
    await coordinator.async_request_refresh()


async def async_add_tummy_time(call: ServiceCall) -> None:
    """Add a tummy time entry."""
    coordinator = await __async_extract_entry_coordinator(call)
    data = await __setup_service_data(call, coordinator)

    try:
        data = await __set_common_fields(call, data)
    except ValidationError as error:
        LOGGER.error(error)
        return

    if call.data.get(ATTR_MILESTONE):
        data[ATTR_MILESTONE] = call.data.get(ATTR_MILESTONE)

    await coordinator.client.async_post(ATTR_TUMMY_TIMES, data)
    await coordinator.async_request_refresh()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the babybuddy integration."""

    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_CHILD,
        async_add_child,
        schema=SERVICE_ADD_CHILD_SCHEMA,
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
                vol.Required(ATTR_CHILD): cv.entity_id,
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
        DOMAIN,
        ATTR_ACTION_DELETE_LAST_ENTRY,
        async_delete_last_entry,
        vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_id,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "start_timer",
        async_start_timer,
        vol.Schema(
            {
                vol.Optional(ATTR_START): vol.Any(cv.datetime, cv.time),
                vol.Optional(ATTR_NAME): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_FEEDING,
        async_add_feeding,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_TYPE): vol.In(FEEDING_TYPES),
                vol.Required(ATTR_METHOD): vol.In(FEEDING_METHODS),
                vol.Optional(ATTR_AMOUNT): cv.positive_float,
                vol.Optional(ATTR_NOTES): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_PUMPING,
        async_add_pumping,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Required(ATTR_AMOUNT): cv.positive_float,
                vol.Optional(ATTR_NOTES): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_SLEEP,
        async_add_sleep,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Optional(ATTR_NAP): cv.boolean,
                vol.Optional(ATTR_NOTES): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_TUMMY_TIME,
        async_add_tummy_time,
        vol.Schema(
            {
                **COMMON_FIELDS,
                vol.Optional(ATTR_MILESTONE): cv.string,
            }
        ),
    )
